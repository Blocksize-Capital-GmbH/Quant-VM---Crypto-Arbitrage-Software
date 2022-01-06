#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import math
from typing import Union, List
from abc import abstractmethod

import pandas as pd
from src.base_with_database_logger import BaseWithDatabaseAndLogger

import src.performance.metrics as util
import src.sql_queries
from src.base_with_database_logger import BaseWithDatabaseAndLogger

class MetricRow:
    def __repr__(self):
        return f"MetricRow(" \
               f"metric_id: {self.metric_id}, " \
               f"timestamp: {self.timestamp}, " \
               f"value: {self.value}, " \
               f"algorithm_id: {self.algorithm_id}, " \
               f"unit_id: {self.unit_id}"\
               f")"

    def __str__(self):
        return f"{{metric_id: {self.metric_id}, timestamp: {self.timestamp}, value: {self.value}, algo_name: {self.algorithm_id}, unit_id: {self.unit_id}}}"

    def __init__(self, metric_id, timestamp, value, algorithm_id, unit_id):
        self.metric_id: str = metric_id
        self.timestamp: int = timestamp
        self.value: Union[float, int, str] = value
        self.algorithm_id: str = algorithm_id
        self.unit_id = unit_id


class Metric(BaseWithDatabaseAndLogger):
    TIMESTAMP = "ORL_TIMESTAMP"
    DIRECTION = "ORL_DIRECTION"
    FEE_CURRENCY = "ORL_FEE_CURRENCY"
    FEE = "ORL_FEE"
    QUANTITY = "ORL_QUANTITY"
    PRICE = "ORL_PRICE"
    CURRENCY_PAIR = "ORL_CUP_ID"
    UNIX_TIME = "UNIX_TIME"
    BASE = "BASE"
    QUOTE = "QUOTE"
    INTERVAL_TIME = "INTERVAL_TIME"
    CURRENCY_PAIR_ID = "CUP_ID"
    CURRENCY_ID = "CUR_ID"
    CURRENCY_CODE = "CUR_CODE"
    UNIT_NAME = "UNIT_OF_VALUE"

    def __init__(self, algo_name, algorithm_id, metric_name, metric_id,
                 interval, mode, logger_wrapper):
        super().__init__(mode, logger_wrapper, open_db_connection=True)
        self.algo_name = algo_name
        self.algorithm_id = algorithm_id
        self.metric_name = metric_name
        self.interval = interval
        self.metric_id = metric_id
        self.__interval_s = util.interval_converter(interval)  # implement for interval class
        self.extra_intervals = self.set_extra_intervals()

        query = src.sql_queries.query_algo_specific_currency_pairs(
            self.algo_name
        )
        dataframe = pd.read_sql(query, self.db_connector.connection)
        self.currencies = dataframe

    @property
    def interval_s(self):
        return self.__interval_s

    def insert(self, raw_data: List[MetricRow]):
        for item in raw_data:
            statement = src.sql_queries.insert_into_metric(**item.__dict__)
            self.db_connector.execute_dml(statement)

    def call(self):
        """
        :return:
        """
        timestamp = datetime.datetime.now()
        raw_data = self.get_data(timestamp)
        results = self.transform_and_aggregate(raw_data)
        raw_insert_data = self.series_to_rows(results)
        self.insert(raw_insert_data)

    def set_extra_intervals(self):
        interval_s = util.interval_converter(self.interval)
        if interval_s <= 60:
            return 5
        elif interval_s <= 86400:
            return 2
        else:
            return 1

    @abstractmethod
    def transform_and_aggregate(self, df: pd.DataFrame):
        pass

    @staticmethod
    def get_start_time(now, interval, extra_intervals) -> datetime:
        interval_s = util.interval_converter(interval)
        start_date = datetime.datetime(1970, 1, 1)
        delta = (now - start_date).total_seconds()
        floored_time = math.floor(int(delta) / interval_s) - extra_intervals
        floored_time *= interval_s
        return datetime.datetime.fromtimestamp(floored_time)

    def series_to_rows(self, datasets) -> List[MetricRow]:
        row_data = []
        for data in datasets:
            for timestamp, row in data.iterrows():
                value = float(row[0])
                unit = int(row[1])
                metric_data = MetricRow(self.metric_id, timestamp, value, self.algorithm_id, unit)
                row_data.append(metric_data)

        return row_data

    def get_data(self, timestamp):
        start_time = self.get_start_time(timestamp, self.interval, self.extra_intervals)
        data = self.get_order_logs(start_time=start_time, end_time=timestamp)
        return data

    def get_order_logs(self, start_time, end_time):
        statement = src.sql_queries.select_order_log_closed_orders(start_time, end_time, self.algorithm_id)
        df = pd.read_sql(statement, self.db_connector.connection)
        return df

    def get_unit_id(self, currency_pair_id, side="BASE"):
        if side == "BASE":
            index = 0
        elif side == "QUOTE":
            index = 1
        else:
            raise UnknownSideError("Unknown side")

        currency_pair_info = self.currencies[self.currencies[Metric.CURRENCY_PAIR_ID] == currency_pair_id]
        currency_pair_codes = currency_pair_info[Metric.CURRENCY_CODE]
        unit_id_query = src.sql_queries.select_id_of_unit_by_symbol(currency_pair_codes.iloc[0, index])
        return self.db_connector.execute_dql(unit_id_query)[0][0]


class UnknownSideError(Exception):
    pass


class IntervalFormatError(Exception):
    """
    Raised when a time interval could not be parsed correctly.
    """


if __name__ == '__main__':
    pass