#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

from src.util import LoggerWrapper
from src.helpers import DBMode, DBConnector, SDKClient
from src.client.custom_sdk_client import CustomClient
from src.client.test_sdk_client import TestClient


def init_logger(mode=DBMode.DEV):
    logger_wrapper = LoggerWrapper(entity_name=__name__, location="test-logs/debug.log", db_connector=None)
    db_connector = DBConnector(
        logger=logger_wrapper, mode=mode
    )
    logger_wrapper.db_connector = db_connector

    return logger_wrapper


def init_sdk_client(logger_wrapper, sdk_client: SDKClient):
    if sdk_client == SDKClient.REAL:
        return CustomClient(os.getenv('API_KEY_BLOCKSIZE'), logger_wrapper=logger_wrapper)
    elif sdk_client == SDKClient.TEST:
        return TestClient(os.getenv('API_KEY_BLOCKSIZE'), logger_wrapper=logger_wrapper)
    else:
        raise Exception("Unimplemented SDK client")
