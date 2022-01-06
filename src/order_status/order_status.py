#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Standard imports
import logging
import os
import threading
import time
import asyncio
from datetime import datetime
from multiprocessing.pool import ThreadPool

# Third party imports
import sortedcontainers
import numpy as np
from dotenv import load_dotenv

# Local imports
import src.client
import src.sql_queries
import src.helpers
from src.base_with_database_logger import BaseWithDatabaseAndLogger
from quant_sdk import Client
from src.helpers import DBMode


timeout_tag = "timeout"
order_sdk_tag = "order_sdk"
additional_info_tag = "additional_info"


class OrderStatus(BaseWithDatabaseAndLogger):
    def __init__(self, client=None, mode=DBMode.DEV, test=False, logger_instance=None, update_order_sleep=10):
        self.test: bool = test
        super().__init__(mode=mode, logger_wrapper=logger_instance, open_db_connection=False)
        self.counter: int = 1
        self.update_order_sleep = update_order_sleep
        self.max_threads_to_process_orders: int = 20
        self.storage_async_mutex = asyncio.Lock()
        self.storage_mutex = threading.Lock()
        self.__order_storage = sortedcontainers.SortedDict()
        self.state_mapper = {
            Client.ORDER_STATUS_CODE_OPEN: Client.ORDER_STATUS_OPEN,
            Client.ORDER_STATUS_CODE_CLOSED: Client.ORDER_STATUS_CLOSED,
            Client.ORDER_STATUS_CODE_FAILED: Client.ORDER_STATUS_FAILED,
            Client.ORDER_STATUS_CODE_PARTIALLY_FILLED: Client.ORDER_STATUS_PARTIALLY_FILLED
        }

        self.active = True
        if client:
            self.client = client
        else:
            self.client = Client(os.getenv("API_KEY_BLOCKSIZE"))

    @property
    def order_storage(self):
        return self.__order_storage

    async def cancel_order(self, order_id):
        async with self.storage_async_mutex:
            key_to_remove = None
            # search for key
            for key, order in self.order_storage.items():
                if order['order_id'] == order_id:
                    key_to_remove = key

            # remove key associated to the id
            if key_to_remove:
                self.client.cancel_order(order_id)

    def cancel_order_thread(self, order_id):
        with self.storage_mutex:
            key_to_remove = None
            # search for key
            for key, order in self.order_storage.items():
                if order['order_id'] == order_id:
                    key_to_remove = key

            # remove key associated to the id
            if key_to_remove:
                self.client.cancel_order(order_id)

    async def enqueue_order(self, order_struct):
        timeout = order_struct[timeout_tag]
        async with self.storage_async_mutex:
            self.order_storage[timeout] = order_struct

    def enqueue_order_thread(self, order_struct):
        timeout = order_struct[timeout_tag]
        with self.storage_mutex:
            self.order_storage[timeout] = order_struct

    async def update_open_orders(self):
        remove_keys = []
        async with self.storage_async_mutex:
            for key, order in self.order_storage.items():
                now = datetime.now()
                order_id = order[order_sdk_tag]['order']['order_id']
                if key > now:
                    self.client.cancel_order(order_id)

                order_data = self.client.order_status(order_id)
                order[order_sdk_tag] = order_data
                params = self.extract_order_details(order_data)
                status = params["status"]
                if status in [Client.ORDER_STATUS_CLOSED, Client.ORDER_STATUS_FAILED]:
                    self.update_order_log_entry(**params)
                    remove_keys.append(key)
                    print(f"[{self.counter}] updated order {params['order_id']}")

            for item in remove_keys:
                del self.order_storage[item]

    def update_open_orders_thread(self):
        remove_keys = []
        with self.storage_mutex:
            for key, order in self.order_storage.items():
                now = datetime.now()
                order_id = order[order_sdk_tag]['order']['order_id']
                if key > now:
                    self.client.cancel_order(order_id)

                order_data = self.client.order_status(order_id)
                order[order_sdk_tag] = order_data

                status = self.convert_status_code(order_data['aggregated_status'])
                if status in [Client.ORDER_STATUS_CLOSED, Client.ORDER_STATUS_FAILED]:
                    self.update_order_log_entry(order_data, order[additional_info_tag])
                    remove_keys.append(key)
                    self.logger_wrapper.logger.debug(f"[{self.counter}] updated order {order_data['orderid']}")

            for item in remove_keys:
                del self.order_storage[item]

    def update_order(self, order_id: str):
        order_data = self.client.order_status(order_id)
        params = self.extract_order_details(order_data)
        status = params["status"]
        if status in [Client.ORDER_STATUS_CLOSED, Client.ORDER_STATUS_FAILED]:
            self.update_order_log_entry(**params)
            print(f"[{self.counter}] updated order {params['order_id']}")
            self.counter += 1

    def extract_order_details(self, order_status_dict, additional_info):
        order_id = order_status_dict['orderid']
        status = self.convert_status_code(order_status_dict['aggregated_status'])
        filled_quantity = order_status_dict['trade_status'][0]['trade']['trade_quantity']
        price_executed = order_status_dict['trade_status'][0]['status_report']['executed_price']
        fee = order_status_dict['trade_status'][0]['status_report']['fees']
        fee_currency = order_status_dict['trade_status'][0]['status_report']['fee_currency']

        return {
            "order_id": order_id,
            "status": status,
            "filled_quantity": filled_quantity,
            "price_executed": price_executed,
            "fee": fee,
            "fee_currency": fee_currency,
            "algo_id": additional_info["algo_id"],
            "exchange_id": additional_info["exchange_id"]
        }

    def convert_status_code(self, code):
        return self.state_mapper[code]

    def disable_activity(self):
        self.active = False

    async def resolve_orders(self):
        while self.active:
            try:
                await self.update_open_orders()
                await asyncio.sleep(self.update_order_sleep)
            except Exception as ex:
                self.logger_wrapper.logger.error(f"Error", exc_info=True)

    def resolve_orders_thread(self):
        while self.active:
            try:
                self.update_open_orders_thread()
                time.sleep(self.update_order_sleep)
            except Exception as ex:
                self.logger_wrapper.logger.error(f"Error", exc_info=True)

    def resolve_orders_threaded(self):
        return self.resolve_orders_thread()

    def update_order_log_entry(self, order_data, additional_info):
        query2 = src.sql_queries.insert_into_order_log(additional_info['algo_id'], additional_info['exchange_id'], order_data, self.logger_wrapper.logger)
        self.db_connector.execute_dml(query2)


if __name__ == '__main__':
    logger = logging.getLogger()
    orders = OrderStatus(client=src.client.test_sdk_client.TestClient(logger))
    asyncio.get_event_loop().run_until_complete(orders.resolve_orders())
