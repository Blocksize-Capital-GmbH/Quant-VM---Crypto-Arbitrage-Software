#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import threading

from src.client import test_sdk_client

import src.helpers
import src.util
import src.algo_multilateral_arbitrage
import test_sdk_client


if __name__ == '__main__':
    logger = src.util.base_logger(__name__, "test-logs/debug.log")
    test_algo_name = "A-tests-multi-lateral"

    db_connector = src.helpers.DBconnection()
    configuration = src.helpers.load_config(test_algo_name, db_connector._connection)


    # instantiate arbitrage algorithm
    instance = src.algorithm.ArbitrageInstance(
        test_algo_name,
        simulation=True,
        configs_file="configs-link-eur.yaml",
        configuration=configuration,
        client=test_sdk_client.TestClient(logger),
        logger=logger,
        db_connector=db_connector
    )

    instance.trade_algorithm()
    time.sleep(0.8)
    del instance
