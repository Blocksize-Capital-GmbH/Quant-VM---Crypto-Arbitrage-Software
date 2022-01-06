#!/usr/bin/python3
# -*- coding: utf-8 -*-

from abc import ABCMeta
import src.helpers
import src.util
from src.helpers import DBMode


class BaseWithDatabaseAndLogger(metaclass=ABCMeta):

    def __init__(
            self,
            mode: DBMode,
            logger_wrapper: src.util.LoggerWrapper,
            open_db_connection=False
    ):
        """
        Input:
        mode => "DEV", "TEST", "PROD"
        logger_wrapper => instance of src.util.LoggerWrapper - carries a
        logging.logger object as _logger instance variable
        """
        self.__mode = mode
        self.__logger_wrapper = logger_wrapper
        self.__db_connector = None

        if self.logger_wrapper.db_connector is not None:
            # inherit the db_connector from the logger wrapper
            self.__db_connector = self.logger_wrapper.db_connector
        else:
            # there is no DB connection to share
            if open_db_connection:
                self.__db_connector = src.helpers.DBConnector(
                    logger=self.logger_wrapper.logger, mode=self.__mode
                )
                self.__logger_wrapper.db_connector = self.__db_connector
                self.__logger_wrapper.add_db_handler()

    def __del__(self):
        if self.__db_connector.connection:
            self.__db_connector.connection.close()

    @property
    def logger_wrapper(self):
        return self.__logger_wrapper

    @property
    def mode(self):
        return self.__mode

    @property
    def db_connector(self):
        return self.__db_connector

    @db_connector.setter
    def db_connector(self, db_connector):
        self.__db_connector = db_connector
