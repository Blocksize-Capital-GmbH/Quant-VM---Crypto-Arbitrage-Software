#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import os

from src.client import CustomClient

from src import util
import src.sql_queries
from src.base_with_database_logger import BaseWithDatabaseAndLogger
from src.helpers import load_configuration_of_database_connection, create_database_engine


class QueryBalance(BaseWithDatabaseAndLogger):

    def __init__(self, client=None, logger=None, db_engine=None):
        super().__init__(logger, db_engine)
        self.__logger = logger

        if client:
            self.client = client
        else:
            self.client = CustomClient(
                os.getenv('API_KEY_BLOCKSIZE'), logger=self.logger
            )

    @property
    def logger(self):
        return self.__logger

    def get_balances(self, exchanges, cryptos):
        timestamp = int(time.time())
        balances_raw_resp = self.client.query_funds()
        balances_all = balances_raw_resp.get('funds')
        data = []
        for item in balances_all:
            exchange = item.get('name')
            if exchange not in exchanges:
                continue
            balance = item.get('balances')
            # if exchange should have data and it doesn't stop balance collection and return None
            #  reason: with incomplete balance statements we end up with wrong portfolio values
            if balance is None:
                print(f"exchange data was missing, exchange: {exchange}")
                print(balances_raw_resp)
                return None
            for balance_item in balance:
                if balance_item.get('currency') not in cryptos:
                    continue
                data.append({
                    'timestamp': timestamp,
                    'currency': balance_item.get('currency'),
                    'amount': balance_item.get('amount'),
                    'exchange': exchange,
                    'quote_price': balance_item.get('quote_price'),
                    'quote_currency': balance_item.get('quote')
                })
        return data

    def balance_to_db(self, exchanges, cryptos):
        data = self.get_balances(exchanges, cryptos)
        if data is None:
            return
        with self.database_engine.cursor() as cursor:
            for line in data:
                query_to_execute = src.sql_queries.insert_into_balances(**line)
                status = cursor.execute(query_to_execute)
            self.database_engine.commit()

    def fill_database(self, exchanges, currencies):
        active = True
        while active:
            try:
                self.balance_to_db(exchanges, currencies)
                time.sleep(60)
            except Exception as ex:
                self.logger.error(f"Error during log of balances", exc_info=True)


if __name__ == '__main__':
    logger = util.base_logger(__name__, "test-logs/debug.log")
    test_db = True

    try:
        database_credentials = load_configuration_of_database_connection(test_db=test_db)
        db_engine = create_database_engine(database_credentials, logger)

        client_sdk = CustomClient(os.getenv('API_KEY_BLOCKSIZE'), logger=logger)
        balance = QueryBalance(client=client_sdk, logger=logger, db_engine=db_engine)
        balance.fill_database(["BITFINEX", "BITPANDA", "KRAKEN"], ["BTC", "LINK", "EUR", "XRP", "ETH"])
    except Exception as exc:
        logger.critical(f"Critical error", exc_info=True)
