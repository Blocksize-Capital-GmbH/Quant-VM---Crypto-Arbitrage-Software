#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import enum
import os
import logging
import time
import datetime
from typing import Tuple
import psycopg2
import pandas as pd
from dotenv import load_dotenv


import src.sql_queries


class DBMode(enum.Enum):
    PROD = "PROD"
    TEST = "TEST"
    DEV = "DEV"


class SDKClient(enum.Enum):
    TEST = "TEST"
    REAL = "REAL"


class DBConnector:
    """
    Class to create and maintain connections to the PostgreSQL database

    Input:
        mode = "PROD", "TEST", or "DEV" corresponds to the respective databases
        logger = python logging.logger object, instance variable of LoggerWrapper
    """
    def __init__(self,  logger, mode=DBMode.DEV):
        self._mode = mode
        self._logger = logger
        self._db_config = self._load_db_config()
        self._connection = None
        self.create_db_connection()
        self.connection.rollback()
        self._connection.autocommit = True

    def __enter__(self):
        if not self._connection or self._connection.closed == 1:
            self.create_db_connection()
        return self._connection

    def __exit__(self, type, value, traceback):
        self.disconnect()

    @property
    def connection(self):
        return self._connection

    @property
    def logger(self):
        return self._logger

    def _load_db_config(self):
        load_dotenv()
        config = {
            "db_host": os.getenv("DB_HOST"),
            "db_port": os.getenv("DB_PORT"),
            "db_user": os.getenv("DB_USER"),
            "db_pass": os.getenv("DB_PASS"),
        }

        if self._mode == DBMode.PROD:
            config["db_name"] = os.getenv("DB_NAME")
        elif self._mode == DBMode.TEST:
            config["db_name"] = os.getenv("DB_NAME_TEST")
        elif self._mode == DBMode.DEV:
            config["db_name"] = os.getenv("DB_NAME_DEV")
        else:
            raise IndexError(f"Unknown mode inserted{self._mode}")

        return config

    def create_db_connection(self):
        try:
            self._connection = psycopg2.connect(
                user=self._db_config["db_user"],
                password=self._db_config["db_pass"],
                host=self._db_config["db_host"],
                port=self._db_config["db_port"],
                database=self._db_config["db_name"]
            )
            show_version(self._connection)

        except (Exception, psycopg2.Error):
            self.logger.error(
                f"Error connecting to PostgreSQL database",  exc_info=True
            )
            return None

    def disconnect(self):
        close_database_engine(self._connection)
        self._connection = None

    def execute_dql(self, query):
        """Executes selection query on the database."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                response = cursor.fetchall()
            return response
        except psycopg2.Error as exc:
            self.logger.error(f"Query that failed: {query}", exc_info=True)

    def execute_dml(self, query):
        """Executes modification query on the database."""
        try:
            with self.connection.cursor() as cursor:
                result = cursor.execute(query)
                pass
        except psycopg2.Error as exc:
            self.logger.error(f"Query that failed: {query}", exc_info=True)


class DBConnectorTest(DBConnector):
    def __init__(self,  logger, mode=DBMode.DEV):
        super(DBConnectorTest, self).__init__(logger, mode)

    def create_db_connection(self):
        try:
            self._connection = []
            show_version(self._connection)

        except (Exception, psycopg2.Error):
            self.logger.error(
                f"Error connecting to PostgreSQL database",  exc_info=True
            )
            return None


# TODO Migrate all db connection calls to the class DbConnection
# Left: db_queries.py, helpers.py, metric.py, metrics_v3.py
def load_configuration_of_database_connection(test_db=False):
    load_dotenv()
    if test_db:
        return {
            "db_host": os.getenv("DB_HOST"),
            "db_port": os.getenv("DB_PORT"),
            "db_user": os.getenv("DB_USER"),
            "db_pass": os.getenv("DB_PASS"),
            "db_name": os.getenv("DB_NAME_TEST")
        }
    else:
        return {
            "db_host": os.getenv("DB_HOST"),
            "db_port": os.getenv("DB_PORT"),
            "db_user": os.getenv("DB_USER"),
            "db_pass": os.getenv("DB_PASS"),
            "db_name": os.getenv("DB_NAME")
        }


def create_database_engine(credentials, logger=None):
    try:
        db_connection = psycopg2.connect(
            user=credentials["db_user"],
            password=credentials["db_pass"],
            host=credentials["db_host"],
            port=credentials["db_port"],
            database=credentials["db_name"]
        )
        show_version(db_connection, logger)

        return db_connection
    except (Exception, psycopg2.Error) as error:
        logging.error(f"Error connecting to PostgreSQL database",  exc_info=True)
        return None


def close_database_engine(engine, logger=None):
    engine.close()
    if logger:
        logger.info(f"You are disconnected from database")
    else:
        logging.info(f"You are disconnected from database")


def show_version(engine, logger=None):
    with engine.cursor() as cursor:
        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        if logger:
            logger.info(f"You are connected into the - {record}")
        else:
            logging.info(f"You are connected into the - {record}")


def get_best_quote(order_book_side, needed_quantity) -> Tuple[float, float]:
    agg_quantity = 0
    vwap = 0
    # check if there is enough liquidity in level 1 data
    if float(order_book_side[0][1]) >= needed_quantity:
        return float(order_book_side[0][0]), float(order_book_side[0][1])

    # if not enough liquidity dig into level 2 and compute vwap
    for price, amount in order_book_side:
        price = float(price)
        amount = float(amount)

        remaining_quantity = needed_quantity - agg_quantity
        if agg_quantity >= needed_quantity:
            break
        if amount < remaining_quantity:
            take_amount = amount
        else:
            take_amount = remaining_quantity

        agg_quantity += take_amount
        vwap += take_amount * float(price)

    return [vwap / needed_quantity, needed_quantity]


def handle_log_file_creation(path: str, create_directory: bool = False):
    if create_directory:
        print('Building intermediate paths')
        os.makedirs(os.path.join('/', *path.split('/')[:-1]), exist_ok=True)
    print('Checking file paths')
    new_path = increase_file_tag(path)
    return new_path


def increase_file_tag(path, counter: int = 0):
    """renames a file from path_k -> path_(k+1)"""
    file_name, file_type = path.split(".")

    def generate_path_from_counter(_count):
        if _count == 0:
            _full_path = f'{file_name}.{file_type}'
        else:
            _full_path = f'{file_name}_{_count}.{file_type}'
        return _full_path

    full_path_counted = generate_path_from_counter(counter)
    print(os.path.isfile(full_path_counted), full_path_counted)
    if not os.path.isfile(full_path_counted):
        if counter == 0:
            open(full_path_counted, 'a').close()
            return full_path_counted
        else:
            old_path = generate_path_from_counter(counter - 1)
            os.rename(old_path, full_path_counted)
            print(f"renamed {old_path} -> {full_path_counted}")
            increase_file_tag(path, counter - 1)
    else:
        increase_file_tag(path, counter + 1)


def visualize_order_book(title, order_books, filename=None, suffix='png', dpi=300):
    import matplotlib.pyplot as plt

    plt.title(title)
    for order_book in order_books:
        plt.plot([item[0] for item in order_book['bids']], [item[1] for item in order_book['bids']], label=f"{order_book['exchange']}, bids")
        plt.plot([item[0] for item in order_book['asks']], [item[1] for item in order_book['asks']], label=f"{order_book['exchange']}, asks")
    plt.ylim(0, 200)
    plt.legend()
    if filename:
        plt.savefig(filename + "." + suffix, dpi=dpi)
    else:
        plt.show()
    plt.close()


def convert_timestamp_to_datetime(timestamp, logger):
    if isinstance(timestamp, int) or isinstance(timestamp, float):
        try:
            date = datetime.datetime.fromtimestamp(timestamp)
            return pd.to_datetime(timestamp, unit="s", utc=True)
        except pd._libs.tslibs.np_datetime.OutOfBoundsDatetime:
            try:
                return pd.to_datetime(timestamp, unit="ms", utc=True)
            except Exception as error:
                logger.error(error)
    else:
        return timestamp


def convert_datetime_to_unix(date_time):
    date_time = str(pd.to_datetime(date_time, utc=True).replace(tzinfo=None))
    pattern = '%Y-%m-%d %H:%M:%S.%f'
    date_time = datetime.datetime.strptime(date_time, pattern)
    print(date_time.microsecond)
    print(date_time.microsecond * 1e-6)
    epoch = time.mktime(time.strptime(str(date_time), pattern)) \
            + (date_time.microsecond * 1e-6)
    return round(epoch, 3)


if __name__ == '__main__':
    pass
