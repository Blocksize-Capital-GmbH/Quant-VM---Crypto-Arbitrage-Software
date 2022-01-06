#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import math
import os
import time
from typing import Dict, Union

import psycopg2
import numpy as np

import src.sql_queries
from src.helpers import DBConnector

checking_file_path = 'Checking file paths'


class LoggerWrapper:
    """
    Class to handle logger -> provides functionality to smoothly instantiate
        base logger without db connection. Then add the db logging
        functionality with one function call.
    """
    # TODO make services use logger with their entity name
    def __init__(self, entity_name: str, location: str, order_id=None, db_connector=None):

        self._location = location
        self._fmt_console = "%(asctime)s - [%(levelname)s] - %(message)s"
        self._fmt_save = "%(asctime)s;[%(levelname)s];[%(filename)s > %(funcName)s() > %(lineno)s];%(message)s"
        self._db_connector = db_connector
        self._entity_name = entity_name
        self._logger = self._get_base_logger()
        self._order_id = order_id

        if db_connector is not None:
            self.add_db_handler()

    @property
    def entity_name(self):
        return self._entity_name

    @property
    def db_connector(self):
        return self._db_connector

    @property
    def logger(self):
        return self._logger

    @property
    def order_id(self):
        return self._order_id

    @entity_name.setter
    def entity_name(self, entity_name):
        self._entity_name = entity_name

    @db_connector.setter
    def db_connector(self, db_connector: DBConnector):
        self._db_connector = db_connector

    @order_id.setter
    def order_id(self, order_id):
        self._order_id = order_id

    def _get_file_path(self, path: str, create_directory: bool = False):
        if create_directory:
            print('Building intermediate paths')
            os.makedirs(os.path.join('/', *path.split('/')[:-1]),
                        exist_ok=True)
        print(checking_file_path)
        new_path = increase_file_tag(path)
        return new_path

    # TODO Change naming convention to algo_id + date and create new file per day
    # This is anyway way, way too complicated of a function for its purpose
    def _increase_file_tag(self, path, counter: int = 0):
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

    def _get_base_logger(self):
        # logging specs
        log_path = os.path.join(os.getcwd(), self._location)
        self._get_file_path(log_path, True)
        # Creating logger
        logger = logging.getLogger()
        logger.setLevel("DEBUG")

        # Handler - 1 - Files
        file_handler = logging.FileHandler(log_path, mode="a")
        file_format = logging.Formatter(self._fmt_save)
        file_format.default_msec_format = "%s.%03d"
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_format)

        # Handler - 2 - Stdout
        stream_handler = logging.StreamHandler()
        stream_format = logging.Formatter(self._fmt_console)
        stream_format.default_msec_format = "%s.%03d"
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(stream_format)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

        return logger

    def add_db_handler(self):
        try:
            # Handler 3 - Database - Custom Handler
            database_handler = PostgreSQLHandler(
                self.entity_name, self.db_connector, self.order_id
            )
            database_format = logging.Formatter(self._fmt_save)
            database_format.default_msec_format = "%s.%03d"
            database_handler.setLevel(logging.WARNING)
            database_handler.setFormatter(database_format)

            self._logger.addHandler(database_handler)
        except Exception as error:
            self._logger.error(error)


def handle_log_file_creation(path: str, create_directory: bool = False):
    if create_directory:
        print('Building intermediate paths')
        os.makedirs(os.path.join('/', *path.split('/')[:-1]), exist_ok=True)
    print(checking_file_path)
    new_path = increase_file_tag(path)
    return new_path


# TODO Change naming convention to algo_id + date and create new file per day
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


def check_path_names(path, file_type, create_directory: bool = False):
    if path is None or file_type is None:
        raise ValueError('Please provide path and filetype')
    if create_directory:
        print('Building intermediate path')
        os.makedirs(os.path.join('/', *path.split('/')[:-1]), exist_ok=True)
    print(checking_file_path)
    full_path = f'{path}.{file_type}'
    if os.path.isfile(full_path):
        print(f'\tAlready in use: {full_path}')
        counter = 1
        while True:
            new_path = f'{path}_{counter}.{file_type}'
            if os.path.isfile(new_path):
                print(f'\tAlready in use: {new_path}')
                counter += 1
                continue
            else:
                print(''.center(10, '-'))
                print(f'\tUsing: {new_path}')
                return new_path
    else:
        return full_path


def unix_milli():
    return int(np.ceil(time.time() * 1000))


def make_milli_timestamp():
    return int(np.ceil(time.time() * 1000))


def round_down(num, precision):
    factor = 10 ** precision
    return math.floor(num * factor) / factor


def get_configs_key(configs: Dict[str, Union[str, float, Dict]], key: str):
    try:
        return configs[key]
    except KeyError:
        print(key, "is missing in configs")
        return None
    except Exception as ex:
        raise ex


class AlgoSettingsError(Exception):
    """Raised when there are no settings defined for trades"""
    pass


class PostgreSQLHandler(logging.Handler):
    """
    A custom class derived from logging.Handler that logs levels >= WARNING
    to the "PROD_001"."SYSTEM_LOG" PostgreSQL table.
    """

    def __init__(self, entity_name, db_connector, order_id):
        super(PostgreSQLHandler, self).__init__()
        self._entity_name = entity_name
        self._current_order_id = None
        self._db_connector = db_connector
        self._db_connection = self.db_connector.connection
        self._order_id = order_id

    @property
    def entity_name(self):
        return self._entity_name

    @property
    def order_id(self):
        return self._order_id
    @property
    def db_connector(self):
        return self._db_connector

    @order_id.setter
    def order_id(self, order_id):
        self._order_id = order_id

    # TODO Make sure the instance variable gets set upon retrieving a new order id
    # in the algo
    # Not to be solved in a better way imo as other classes call emit()
    def set_order_id(self, current_order_id):
        self._current_order_id = current_order_id

    # Override
    def emit(self, record):
        try:
            level = record.levelname
            timestamp = record.asctime
            file = record.filename
            function = record.funcName
            line = record.lineno
            message = record.message
            args = (
                self.entity_name, self.order_id, timestamp, level, file,
                function, line, message
            )

            try:
                if self._db_connection.closed == 0:
                    with self._db_connection.cursor() as cursor:
                        cursor.execute(src.sql_queries.error_log_to_db(), args)
                        print("Success: Write to db")
                else:
                    self._db_connector.create_db_connection()
                    with self._db_connection.cursor() as cursor:
                        cursor.execute(src.sql_queries.error_log_to_db(), args)
                        print("Success: Write to db")

            except psycopg2.OperationalError as error:
                print(error)
                self._db_connection.create_db_conection()
                with self._db_connection.cursor() as cursor:
                    cursor.execute(src.sql_queries.error_log_to_db(), args)

        # TODO does not work as expected, handleError apparently takes logging.LogRecord
        # according to pycharm warning
        except Exception:
            self.handleError(record)


if __name__ == '__main__':
    pass
