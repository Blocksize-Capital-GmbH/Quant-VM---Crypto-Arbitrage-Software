#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import json
import psycopg2
from typing import Dict, List, Tuple, Union
from abc import abstractmethod

import src.helpers
import src.util

from src.base_with_database_logger import BaseWithDatabaseAndLogger
from src.client.custom_sdk_client import CustomClient
from src.helpers import DBMode
import src.sql_queries


class TradingAlgorithm(BaseWithDatabaseAndLogger):
    def __init__(
            self,
            algo_name,
            mode,
            logger_wrapper: src.util.LoggerWrapper,
            open_db_connection=False,
            client=None
    ):
        super().__init__(mode, logger_wrapper, open_db_connection)
        self.__name: str = algo_name

        query_id = src.sql_queries.query_algo_id(self.name)
        raw_result = self.db_connector.execute_dql(query_id)
        if len(raw_result) == 1:
            self.__algo_id = raw_result[0][0]
        else:
            raise Exception("Too many results")

        self.__current_order_id = None
        self.logger_wrapper.order_id = self.__current_order_id

        if self.mode in (DBMode.DEV, DBMode.TEST):
            self.__simulation = True
        else:
            self.__simulation = False
        self.__configuration = self.load_config()

        if client:
            self.__client = client
        else:
            self.__client = CustomClient(
                os.getenv('API_KEY_BLOCKSIZE'),
                logger=self.logger_wrapper.logger
            )

        try:
            self.exchanges = None
            exchange_configs = self.configuration["EXCHANGES"]

            # TODO: remove BASE and QUOTE because they are replaced with
            self.base = self.configuration["BASE"]
            self.quote = self.configuration["QUOTE"]
            self.precision = self.configuration["PRESCISION"]
            self.lot_size = float(self.configuration["LOT_SIZE"])
            self.min_lot_size = float(self.configuration["MIN_LOT_SIZE"])
            self.fund_update_lock_period = self.configuration["FUND_UPDATE_LOCK_PERIOD"]
            self.slippage_buffer_bps = self.configuration["SLIPPAGE_BUFFER_BPS"]
            self.fund_buffer = float(self.configuration["FUND_BUFFER"])

            currencies = set()
            self.currency_pair_exchange_association = {}
            for currency_pair in self.configuration["CURRENCY_PAIRS"]:
                currencies.add(currency_pair['code_base'])
                currencies.add(currency_pair['code_quote'])
                self.currency_pair_exchange_association[currency_pair['symbol']] = []

                for exchange_key, exchange in self.configuration["EXCHANGES"].items():
                    for exchange_currency_pairs in exchange['CURRENCY PAIRS']:
                        if exchange_currency_pairs['symbol'] == currency_pair['symbol']:
                            self.currency_pair_exchange_association[currency_pair['symbol']].append(exchange_key)
                            break
            self.currencies = list(currencies)

            self.set_exchange_data(exchange_configs)
            self._init_fund_map()
            self.update_funds()

        except Exception:
            self.logger_wrapper.logger.error(
                "Error during configuration of the trader", exc_info=True
            )

    @abstractmethod
    def trade_algorithm(self):
        pass

    @property
    def client(self):
        return self.__client

    @property
    def algo_id(self):
        return self.__algo_id

    @property
    def current_order_id(self):
        return self.__current_order_id

    @property
    def name(self):
        return self.__name

    @property
    def simulation(self):
        return self.__simulation

    @property
    def configuration(self):
        return self.__configuration

    @property
    def client(self):
        return self.__client

    @name.setter
    def name(self, name):
        self.__name = name

    @current_order_id.setter
    def current_order_id(self, order_id):
        self.__current_order_id = order_id

    def set_exchange_data(self, exchanges_config: Dict[str, Dict[str, Union[float, Dict]]]):
        self.exchanges = list(exchanges_config.keys())
        for main_exchange, exchange_settings in exchanges_config.items():
            self.fee_map[main_exchange] = exchange_settings["FEE"]
            for ask_exchange in self.exchanges:
                if ask_exchange == main_exchange:
                    continue
                if main_exchange not in self.threshold_map.keys():
                    self.threshold_map[main_exchange] = {}
                if ask_exchange in exchange_settings["THRESHOLDS"].keys():
                    self.threshold_map[main_exchange][ask_exchange] = exchange_settings["THRESHOLDS"][ask_exchange]
                else:
                    self.threshold_map[main_exchange][ask_exchange] = exchange_settings["THRESHOLDS"]["DEFAULT"]

    def update_funds(self):
        balances_raw_resp = self.client.query_funds()
        balances_all = balances_raw_resp.get('funds')
        for item in balances_all:
            exchange = item.get('name')
            if exchange not in self.exchanges:
                continue
            balance = item.get('balances')
            # if exchange should have data and it doesn't stop balance collection and return None
            #  reason: with incomplete balance statements we end up with wrong portfolio values

            if balance is None:
                self.logger_wrapper.logger.debug(
                    f"exchange data was missing, exchange: {exchange}"
                )
                # Todo implement multiple retries
                self.update_funds()
                return None

            for balance_item in balance:
                currency = balance_item.get('currency')
                if currency not in self.currencies:
                    continue
                self.funds[exchange][currency] = float(balance_item.get("amount"))

    # Fund Management
    #
    def _init_fund_map(self):
        self.funds = {}
        for exchange in self.exchanges:
            self.funds[exchange]: Dict[str, float] = {}
            for currency in [self.base, self.quote]:
                self.funds[exchange][currency] = 0.0

    def load_config(self):
        try:
            with self.db_connector.connection as conn:
                with conn.cursor() as cursor:
                    # query of standard configuration for trading algorithm
                    algo_config_query = src.sql_queries.query_algo_configuration(self.name)
                    cursor.execute(algo_config_query)
                    result_algo_configuration = cursor.fetchall()

                    query_currency_pairs_with_symbols = src.sql_queries.query_currency_pairs()

                    # query of currencies associated to algorithm
                    currency_pairs_query = src.sql_queries.query_algo_specific_currency_pairs(self.name)
                    cursor.execute(currency_pairs_query)
                    result_currency_pairs = cursor.fetchall()
                    currency_pairs = [{"code_base": item[2], "code_quote": item[4], "symbol": item[5]} for item in result_currency_pairs]

                    # query for exchanges
                    cursor.execute(src.sql_queries.query_algo_exchange_association(self.name))
                    result_exchanges = cursor.fetchall()
                    exchanges = {exchange[1]: {'EXCHANGE_NAME': exchange[1], "ID": exchange[0]} for exchange in result_exchanges}

                    # currency pairs available at exchanges
                    for key, exchange in exchanges.items():
                        cursor.execute(src.sql_queries.query_exchange_currency_pairs(self.name, exchange['ID']))
                        result_currency_pair_exchange = cursor.fetchall()
                        exchanges[key]['CURRENCY PAIRS'] = [{"code_base": item[1], "code_quote": item[2], "symbol": item[3]} for item in result_currency_pair_exchange]

                    # TODO: fees
                    for key, exchange in exchanges.items():
                        exchanges[key]['FEE'] = {"BUY": 0, "SELL": 0, "LIMIT_BUY": 0, "LIMIT_SELL": 0}

                    # TODO: thresholds
                    for key, exchange in exchanges.items():
                        exchanges[key]['THRESHOLDS'] = {'DEFAULT': -25}

                    configuration = {item[1]: item[2] for item in result_algo_configuration}
                    configuration['CURRENCY_PAIRS'] = currency_pairs
                    configuration['EXCHANGES'] = exchanges

                    return configuration
        except(Exception, psycopg2.Error) as error:
            self.logger_wrapper.logger.error(f"Unable to fetch configuration from database", exc_info=True)

            with open("example_config.json") as config_file:
                configuration = json.load(config_file)
                return configuration
