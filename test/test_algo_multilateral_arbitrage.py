#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pytest
import psycopg2
import time
import src.util
import unittest
import unittest.mock
from src.algo_multilateral_arbitrage import ArbitrageInstance
from src.helpers import DBMode
from src.buildblocks import init_logger, init_sdk_client


@unittest.mock.patch("psycopg2.connect")
def init_mock_instance(algo_id, algo_configuration, mock_connect):
    mock_connect.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = [
        'Mock database connection'
    ]
    mock_connect.return_value.cursor.return_value.__enter__.return_value.fetchall.return_value = algo_id
    mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value.fetchall.side_effect = algo_configuration
    logger_wrapper = init_logger()

    test_algo_name = "A-tests-multi-lateral"
    client_sdk = init_sdk_client(logger_wrapper, sdk_client=src.helpers.SDKClient.TEST)
    client_sdk.close_orders_in_seconds = 0.1

    instance = ArbitrageInstance(
        algo_name=test_algo_name,
        logger_wrapper=logger_wrapper,
        client=client_sdk,
        update_order_sleep=1
    )

    instance.trade_algorithm()

    # sleeps due to sleep in the
    time.sleep(5)
    return instance


def test_simple_algorithmic_trader():
    algo_id = [(1,)]
    algo_config = [
        [(1, 'BASE', 'LINK'), (1, 'QUOTE', 'EUR'), (1, 'LOT_SIZE', '5'), (1, 'MIN_LOT_SIZE', '2'), (1, 'PRESCISION', '2'), (1, 'FUND_UPDATE_LOCK_PERIOD', '120'), (1, 'SLIPPAGE_BUFFER_BPS', '10'), (1, 'FUND_UPDATES', '120'), (1, 'FUND_BUFFER', '0.4'), (1, 'EXCHANGES', 'KRAKEN'), (1, 'EXCHANGES', 'BITPANDA')],
        [(1, 2, 'LINK', 4, 'EUR', 'LINKEUR'), (2, 1, 'BTC', 4, 'EUR', 'BTCEUR'), (3, 1, 'BTC', 5, 'USD', 'BTCUSD'), (4, 6, 'ETH', 4, 'EUR', 'ETHEUR')],
        [(2, 'BITFINEX'), (3, 'BITPANDA'), (4, 'KRAKEN')],
        [(1, 'LINK', 'EUR', 'LINKEUR'), (2, 'BTC', 'EUR', 'BTCEUR'), (4, 'ETH', 'EUR', 'ETHEUR')],
        [(1, 'LINK', 'EUR', 'LINKEUR'), (2, 'BTC', 'EUR', 'BTCEUR'), (3, 'BTC', 'USD', 'BTCUSD')],
        [(1, 'LINK', 'EUR', 'LINKEUR'), (3, 'BTC', 'USD', 'BTCUSD'), (4, 'ETH', 'EUR', 'ETHEUR')]
    ]
    instance = init_mock_instance(algo_id, algo_config)

    assert len(instance.exchanges) == 3
    assert len(instance.configuration) == 11
    assert len(instance.currencies) == 5
    assert len(instance.currency_pair_exchange_association) == 4
    assert len(instance.fee_map) == 3

    calls = [item for item in instance.db_connector.connection.mock_calls if 'execute' in item[0]]
    query_call = [item.args[0] for item in calls]
    inserts_updates = [item.args[0] for item in calls if ('INSERT' in item.args[0] or 'UPDATE' in item.args[0])]

    assert len(query_call) > 8
    assert len(inserts_updates) == 9
    del instance


def test_2_exchange_algorithmic_trader():
    algo_id = [(1,)]
    algo_config = [
        [(1, 'BASE', 'LINK'), (1, 'QUOTE', 'EUR'), (1, 'LOT_SIZE', '5'), (1, 'MIN_LOT_SIZE', '2'), (1, 'PRESCISION', '2'), (1, 'FUND_UPDATE_LOCK_PERIOD', '120'), (1, 'SLIPPAGE_BUFFER_BPS', '10'), (1, 'FUND_UPDATES', '120'), (1, 'FUND_BUFFER', '0.4'), (1, 'EXCHANGES', 'KRAKEN'), (1, 'EXCHANGES', 'BITPANDA')],
        [(1, 2, 'LINK', 4, 'EUR', 'LINKEUR'), (2, 1, 'BTC', 4, 'EUR', 'BTCEUR'), (3, 1, 'BTC', 5, 'USD', 'BTCUSD'), (4, 6, 'ETH', 4, 'EUR', 'ETHEUR')],
        [(2, 'BITFINEX'), (3, 'BITPANDA'), (4, 'KRAKEN')],
        [(1, 'LINK', 'EUR', 'LINKEUR'), (2, 'BTC', 'EUR', 'BTCEUR'), (4, 'ETH', 'EUR', 'ETHEUR')],
        [(1, 'LINK', 'EUR', 'LINKEUR'), (2, 'BTC', 'EUR', 'BTCEUR'), (3, 'BTC', 'USD', 'BTCUSD')],
        [(1, 'LINK', 'EUR', 'LINKEUR'), (3, 'BTC', 'USD', 'BTCUSD'), (4, 'ETH', 'EUR', 'ETHEUR')]
    ]
    instance = init_mock_instance(algo_id, algo_config)
