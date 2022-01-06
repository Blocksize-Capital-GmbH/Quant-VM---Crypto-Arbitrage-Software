#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import logging
import os
from src import util
import uuid
import time

from typing import Union, List
from quant_sdk import Client
import numpy as np


class TestClient(Client):
    def __init__(self, api_key, logger_wrapper: util.LoggerWrapper = None):
        super().__init__(api_key)
        if logger_wrapper is None:
            logger_wrapper = util.LoggerWrapper(entity_name=__name__, location='sdk_logs.log')
        self.logger_wrapper = logger_wrapper
        self.logger_wrapper.logger.info("Test SDK Client")
        self.orders = {}
        self.__close_orders_in_seconds = 10

    @property
    def close_orders_in_seconds(self):
        return self.__close_orders_in_seconds

    @close_orders_in_seconds.setter
    def close_orders_in_seconds(self, close_orders_in_seconds):
        self.__close_orders_in_seconds = close_orders_in_seconds


    def place_order(self,
                    order_type: str,
                    base: str,
                    quote: str,
                    direction: str,
                    quantity: Union[str, float, int],
                    limit_price=0,
                    exchanges: Union[str, List[str]] = None):

        self.logger_wrapper.logger.info(f"Place order {order_type} {base}{quote} {direction} {quantity} {limit_price} {exchanges}")

        timestamp = datetime.datetime.now()
        order_id = str(uuid.uuid4())
        order_structure = {
            'order': {
                'order_id': order_id,
                'base_currency': base,
                'quote_currency': quote,
                'direction': direction,
                'type': order_type,
                'quantity': str(quantity),
                'bsc_token_id': uuid.uuid4(),
                'user_id': uuid.uuid4(),
                'limit_price': limit_price,
                'order_timestamp': timestamp, #1634283294366
                'simulated': False
            },
            "exchanges": exchanges
        }

        self.orders[order_id] = order_structure
        return order_structure

    def get_order_book(self, exchanges: Union[str, List[str]], base: str, quote: str, depth: int = 1):
        result = []
        margin = 100
        for exchange in exchanges:
            shift = np.random.uniform(-20, 20)
            order_book = {'exchange': exchange, "bids": [], "asks": []}

            bids_multiplier = np.random.uniform(3, 6)
            asks_multiplier = np.random.uniform(3, 6)
            bid_function = lambda x: [x + 1, (x + 1) * bids_multiplier]
            ask_function = lambda x: [-x - 1, (x + 1) * asks_multiplier]

            for order_depth in range(depth):
                vanilla_bid = bid_function(order_depth)
                vanilla_ask = ask_function(order_depth)
                order_book["bids"].append([margin + vanilla_bid[0] + shift, vanilla_bid[1]])
                order_book["asks"].append([margin + vanilla_ask[0] + shift, vanilla_ask[1]])
            result.append(order_book)

        return result

    def cancel_order(self, order_id: str):
        order = self.orders.get(order_id, None)
        if order:
            order['aggregated_status'] = Client.ORDER_STATUS_CODE_FAILED
            return order
        else:
            return {"failed state": "order not found"}

    def query_funds(self, quote_currency: str = 'EUR'):
        funds = 10000
        result = {"funds": []}
        for exchange in ["KRAKEN", "BINANCE", "BITFINEX", "BITPANDA"]:
            balance = []
            for currency in ["EUR", "BTC", "LINK", "ETH", "USD"]:
                balance.append({'currency': currency, 'amount': funds})
            result['funds'].append({'name': exchange, 'balances': balance})
        return result

    def order_status(self, order_id: str):
        try:
            order_structure = self.orders[order_id]
            now = datetime.datetime.now()
            timestamp = order_structure['order']['order_timestamp']

            return {
                'userid': 'o2hrQIoqpMbl86I4n1YNnwogjmx1',
                'orderid': order_id,
                'order': order_structure['order'],
                'trade_status': [
                    {
                        'trade': {
                            'trade_id': uuid.uuid4(), 'exchange': order_structure['exchanges'], 'trade_action': 0, 'trade_quantity': order_structure['order']['quantity']
                        },
                        'execution_status': 1,
                        'status_report': {
                            'trade_status': 1,
                            'exchange_trade_id': '',
                            'placed_timestamp': 0,
                            'closed_timestamp': 0,
                            'executed_quantity': '0',
                            'executed_price': '0',
                            'status_timestamp': order_structure['order']['order_timestamp'] + datetime.timedelta(seconds=1),
                            'failed_reason': 0,
                            'error_string': '',
                            'fees': '0',
                            'fee_currency': order_structure['order']['base_currency']
                        }
                    }
                ],
                'aggregated_status': Client.ORDER_STATUS_CODE_OPEN if now - timestamp < datetime.timedelta(seconds=self.close_orders_in_seconds) else Client.ORDER_STATUS_CODE_CLOSED}
        except NameError as exc:
            return {"failed_reason": "Order not found"}
        except Exception as exc:
            logging.error("Fundamental error", exc_info=True)
