#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os

import requests
from quant_sdk import Client

import src.util
import src.helpers
from src import util


class CustomClient(Client):

    def __init__(self, api_key, logger_wrapper: util.LoggerWrapper = None):
        super().__init__(api_key)
        if logger_wrapper is None:
            logger_wrapper = util.LoggerWrapper(entity_name=__name__, location='sdk_logs.log')
        self.logger_wrapper.logger.info("Real SDK Client")
        self.logger_wrapper = logger_wrapper

    def make_api_call(self, route: str, method: str, params=None, data=None, raw: bool = False):
        url = f'{self.base_url}{route}'
        response = requests.request(method=method, url=url, params=params, data=data, headers=self.headers)

        self.logger_wrapper.logger.debug(f"{route} | {response.status_code} | {response.elapsed.total_seconds()} | {response.json()}")

        if raw:
            return response
        else:
            return response.json()


if __name__ == '__main__':
    from dotenv import load_dotenv, find_dotenv
    from multiprocessing.pool import ThreadPool

    load_dotenv(find_dotenv())

    test_log = src.util.base_logger(__name__, 'test_logs/test_log.log', )

    client = CustomClient(os.getenv('API_KEY_BLOCKSIZE'), test_log)

    pool = ThreadPool(processes=5)

    fill_vals = [1] * 200


    def test_func(val):
        print(client.get_vwap("BTC", "EUR", "1s"))


    pool.map(test_func, fill_vals)
    pool.close()
    pool.join()
