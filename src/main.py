import logging
import math
import os
import threading
import time
import traceback
import uuid
from multiprocessing.pool import ThreadPool
from typing import Dict

import numpy as np
import pandas as pd
from dotenv import load_dotenv, find_dotenv
from prometheus_client import start_http_server, Summary
from quant_sdk import Client

import src.custom_kraken_connector.connector as kraken
from src.client.custom_sdk_client import CustomClient
from src.helpers import log_order_to_db, handle_log_file_creation
from src.util.util import make_milli_timestamp

load_dotenv(find_dotenv())

##########

# logging specs
fmt_normal = "%(asctime)s [%(levelname)s] - %(message)s"
log_path = os.path.join(os.getcwd(), "log/arbitrage-algo.log")
handle_log_file_creation(log_path, True)
# Creating logger
algo_logs = logging.getLogger(__name__)
algo_logs.setLevel(logging.DEBUG)

# Handler - 1
file = logging.FileHandler(log_path, mode='a')
fmt_file = "%(asctime)s::[%(levelname)s]::[%(filename)s > %(funcName)s() > %(lineno)s]::%(message)s"
fileformat = logging.Formatter(fmt_file)
file.setLevel(logging.DEBUG)
file.setFormatter(fileformat)

# Handler - 2
stream = logging.StreamHandler()
streamformat = logging.Formatter(fmt_normal)
stream.setLevel(logging.INFO)
stream.setFormatter(streamformat)

# Adding all handlers to the logs
algo_logs.addHandler(file)
algo_logs.addHandler(stream)

##########


algo_logs.info('Algo starting')

#
# logging.getLogger("requests").setLevel(logging.WARNING)
# logging.getLogger("urllib3").setLevel(logging.WARNING)


##### Metrics #####
ORDER_RESPONSE_TIMES = Summary('execute_order_func_times', 'Time it takes to place both legs of an arbitrage trade.')


class Brain:
    __name: str

    def __init__(self, settings: Dict):
        self.client = CustomClient(os.getenv('API_KEY_BLOCKSIZE'), algo_logs)

        if settings is not None:
            self.BASE = settings['BASE'].upper()
            self.QUOTE = settings['QUOTE'].upper()

            self.PAIR = self.BASE + self.QUOTE

            self.EXCHANGES = list(settings['EXCHANGES'].keys())
            self.EXCHANGE_1 = self.EXCHANGES[0].upper()
            self.EXCHANGE_2 = self.EXCHANGES[1].upper()

            self.FEES_EXCHANGE_1 = settings['EXCHANGES'][self.EXCHANGE_1]['FEES']
            self.FEES_EXCHANGE_2 = settings['EXCHANGES'][self.EXCHANGE_2]['FEES']

            self.THRESHOLD_EXCHANGE_1 = settings['EXCHANGES'][self.EXCHANGE_1]['THRESHOLD']
            self.THRESHOLD_EXCHANGE_2 = settings['EXCHANGES'][self.EXCHANGE_2]['THRESHOLD']

            self.PRECISION = settings['PRECISION']
            self.TRADE_SIZE = settings['TRADE_SIZE']
            self.FUND_UPDATE_LOCK_PERIOD = settings['FUND_UPDATE_LOCK_PERIOD']
            self.MIN_TRADE_SIZE = settings['MIN_TRADE_SIZE']
            self.SLIPPAGE_BUFFER_BPS = settings['SLIPPAGE_BUFFER_BPS']
            self.FUND_BUFFER = settings['FUND_BUFFER']
        else:
            raise AlgoSettingsError('Settings not correctly specified')

        ### STATES ###
        self.FUND_UPDATE_LOCK_END: int = 0  # funds will not be updated before reaching this timestamp
        self._init_funds()

    # todo rename
    def _init_funds(self):
        ### funds ###
        self.funds = pd.DataFrame(index=[self.EXCHANGE_1, self.EXCHANGE_2], columns=[self.BASE, self.QUOTE],
                                  dtype='float64')
        self.update_funds()

    ### Step 0 ###
    def take_snapshot(self):
        algo_logs.debug(f"Taking snapshot")
        try:
            order_book_adj = self.get_order_books_and_fee_adjust()
        except Exception as ex:
            # raise ex
            algo_logs.error("Error fetching order_books")
            algo_logs.error(ex)
            algo_logs.error(traceback.format_exc())
        try:
            # !HINT! : Check one direction for arbitrage
            spread_1 = self.scan_for_arbitrage(sell_exchange=self.EXCHANGE_1,
                                               buy_exchange=self.EXCHANGE_2,
                                               order_book_adj=order_book_adj,
                                               threshold=self.THRESHOLD_EXCHANGE_1)

            # !HINT! : Check the opposite
            spread_2 = self.scan_for_arbitrage(sell_exchange=self.EXCHANGE_2,
                                               buy_exchange=self.EXCHANGE_1,
                                               order_book_adj=order_book_adj,
                                               threshold=self.THRESHOLD_EXCHANGE_2)
            algo_logs.info(f"{self.EXCHANGE_1}:{self.EXCHANGE_2}: {round(spread_1, 3)}\t\t"
                           f"{self.EXCHANGE_2}:{self.EXCHANGE_1}: {round(spread_2, 3)}")
        except Exception as ex:
            # raise ex
            algo_logs.error("Error fetching snapshot")
            algo_logs.error(ex)
            algo_logs.error(traceback.format_exc())

    ### Step 1 ###
    def get_order_books_and_fee_adjust(self):
        book_pool = ThreadPool()
        # in this setup it's always Binance as first exchange
        order_book_bitpanda_thread = book_pool.apply_async(self.client.get_order_book,
                                                           kwds={"exchanges": ["BITPANDA"], "base": self.BASE,
                                                                 "quote": self.QUOTE, "depth": 100})

        order_book_kraken_thread = book_pool.apply_async(kraken.get_order_book,
                                                         kwds={"base": self.BASE, "quote": self.QUOTE, "depth": 100})

        order_book_bitpanda = order_book_bitpanda_thread.get()
        order_book_kraken = order_book_kraken_thread.get()

        best_quote_bid_ex_1 = helpers.get_best_quote(order_book_bitpanda[0]["bids"], self.MIN_TRADE_SIZE)
        best_quote_ask_ex_1 = helpers.get_best_quote(order_book_bitpanda[0]["asks"], self.MIN_TRADE_SIZE)

        best_quote_bid_ex_2 = helpers.get_best_quote(order_book_kraken["bids"], self.MIN_TRADE_SIZE)
        best_quote_ask_ex_2 = helpers.get_best_quote(order_book_kraken["asks"], self.MIN_TRADE_SIZE)

        bid_price_ex_1_adj = float(best_quote_bid_ex_1[0]) * (1 - self.FEES_EXCHANGE_1 * 0.0001)
        ask_price_ex_1_adj = float(best_quote_ask_ex_1[0]) * (1 + self.FEES_EXCHANGE_1 * 0.0001)

        bid_price_ex_2_adj = float(best_quote_bid_ex_2[0]) * (1 - self.FEES_EXCHANGE_2 * 0.0001)
        ask_price_ex_2_adj = float(best_quote_ask_ex_2[0]) * (1 + self.FEES_EXCHANGE_2 * 0.0001)

        order_books_adj = {
            self.EXCHANGE_1: {
                'BID': (bid_price_ex_1_adj, best_quote_bid_ex_1[1]),
                'ASK': (ask_price_ex_1_adj, best_quote_ask_ex_1[1])
            },
            self.EXCHANGE_2: {
                'BID': (bid_price_ex_2_adj, best_quote_bid_ex_2[1]),
                'ASK': (ask_price_ex_2_adj, best_quote_ask_ex_2[1])
            },
        }
        algo_logs.debug(f"order_book {order_books_adj}")
        book_pool.close()
        book_pool.join()
        return order_books_adj

    ### Step 2 ###
    def scan_for_arbitrage(self, sell_exchange, buy_exchange, order_book_adj, threshold):
        bid_price_ex_1 = order_book_adj[sell_exchange]['BID'][0]
        ask_price_ex_2 = order_book_adj[buy_exchange]['ASK'][0]

        spread = (bid_price_ex_1 / ask_price_ex_2 - 1) * 10000
        if spread < threshold:
            # !HINT! : No arbitrage opportunity found STOP HERE
            return spread

        # !HINT! : Arbitrage opportunity detected; Determine order parameters
        self.extract_and_validate_parameters(sell_exchange=sell_exchange, buy_exchange=buy_exchange,
                                             order_book_adj=order_book_adj)
        return spread

    ### Step 3 ###
    def extract_and_validate_parameters(self, sell_exchange, buy_exchange, order_book_adj):
        """
        order_params = {
            'VOLUME_BASE': 0,
            'BUY_EXCHANGE': None,
            'SELL_EXCHANGE': None,
        }
        :param buy_exchange:
        :param sell_exchange:
        :param order_book_adj:
        :return:
        """
        prices = [order_book_adj[sell_exchange]['BID'][0], order_book_adj[buy_exchange]['ASK'][0]]
        quantity_ex_sell = float(order_book_adj[sell_exchange]['BID'][1])
        quantity_ex_buy = float(order_book_adj[buy_exchange]['ASK'][1])

        trade_volume = min(quantity_ex_sell, quantity_ex_buy, self.TRADE_SIZE)
        trade_volume = round_down(trade_volume, self.PRECISION)

        # fixme migrate to minimum order sizes based on quote currencies as is usual for exchanges
        trade_volume_quote_est = trade_volume * max(prices) * (1 + (self.SLIPPAGE_BUFFER_BPS / 10000))

        if trade_volume < self.MIN_TRADE_SIZE:
            algo_logs.info("NOT ENOUGH LIQUIDITY")
            algo_logs.debug(f"PLANNED VOLUME: {trade_volume}\nNEEDED VOLUME: {self.MIN_TRADE_SIZE}")
            algo_logs.debug(f"VOLUME {sell_exchange}: {quantity_ex_sell}")
            algo_logs.debug(f"VOLUME {buy_exchange}: {quantity_ex_buy}")
            return

        # !HINT! : Check for fund availability / validate parameters
        # todo check this for LINK funds are not correctly monitored
        funds_base = self.funds.loc[sell_exchange, self.BASE]
        funds_quote = self.funds.loc[buy_exchange, self.QUOTE]

        enough_base = (funds_base - trade_volume) > (self.TRADE_SIZE * self.FUND_BUFFER)
        enough_quote = (funds_quote - trade_volume_quote_est) > (self.TRADE_SIZE * self.FUND_BUFFER * max(prices))

        if enough_base and enough_quote:
            # !HINT! : lock in funds and place trade
            # lock funds and fund_updating
            self.FUND_UPDATE_LOCK_END = int(time.time()) + self.FUND_UPDATE_LOCK_PERIOD
            algo_logs.debug(f"FUND UPDATES SUSPENDED UNTIL {self.FUND_UPDATE_LOCK_END}")
            # todo check this for LINK funds are not correctly monitored
            algo_logs.debug("FUNDS ARE BEING LOCKED-IN")
            self.funds.loc[buy_exchange, self.BASE] += trade_volume
            self.funds.loc[buy_exchange, self.QUOTE] -= trade_volume_quote_est

            self.funds.loc[sell_exchange, self.BASE] -= trade_volume
            self.funds.loc[sell_exchange, self.QUOTE] += trade_volume_quote_est

            self.execute_trade(buy_exchange=buy_exchange, sell_exchange=sell_exchange, quantity=trade_volume)
            time.sleep(1)

        else:
            algo_logs.info("NOT ENOUGH FUNDS TO CONDUCT TRANSACTION")

    ### Step 4 ###
    def execute_trade(self, buy_exchange, sell_exchange, quantity):
        pool = ThreadPool(processes=3)

        start_time = make_milli_timestamp()
        algo_logs.debug("placing trades")
        buy_thread = pool.apply_async(self.place_order, (),
                                      {
                                          "order_type": Client.MARKET_ORDER,
                                          'base': self.BASE,
                                          'quote': self.QUOTE,
                                          'direction': 'BUY',
                                          'quantity': quantity,
                                          'exchanges': buy_exchange,
                                      })
        sell_thread = pool.apply_async(self.place_order, (),
                                       {
                                           "order_type": Client.MARKET_ORDER,
                                           'base': self.BASE,
                                           'quote': self.QUOTE,
                                           'direction': 'SELL',
                                           'quantity': quantity,
                                           'exchanges': sell_exchange,
                                       })

        buy_order = buy_thread.get()
        sell_order = sell_thread.get()

        end_time = make_milli_timestamp()
        algo_logs.info(f'Duration order placement:, {round(end_time - start_time, 6)}ms')
        algo_logs.info(f'Buy: {buy_order}')

        algo_logs.info(f'Sell: {sell_order}')
        t = threading.Thread(target=self.log_collection,
                             kwargs={"buy_order": buy_order, "sell_order": sell_order, "buy_exchange": buy_exchange,
                                     "sell_exchange": sell_exchange})
        t.start()
        pool.close()
        pool.join()

    def log_collection(self, buy_order, sell_order, buy_exchange, sell_exchange):
        algo_logs.debug("logging order")
        """This function logs the two legs of an arbitrage trade collection"""
        combo_id = uuid.uuid4()
        timestamp = make_milli_timestamp()

        # Buy leg
        extract_and_log("buy", combo_id, timestamp, buy_exchange, buy_order, self.__name)
        extract_and_log("sell", combo_id, timestamp, sell_exchange, sell_order, self.__name)

    def set_name(self, name):
        self.__name = name

    def update_funds(self):
        try:
            balances = self.client.query_funds()
            for exchange in balances['funds']:
                if exchange['name'] in self.EXCHANGES:
                    name = exchange['name']
                    for curr in exchange['balances']:
                        if curr['currency'] in self.funds.columns:
                            self.funds.loc[name, curr['currency']] = float(curr['amount'])
            algo_logs.debug(self.funds.to_string())
            return self.funds
        except Exception as ex:
            algo_logs.error("funds could not be updated")
            algo_logs.error(ex)
            algo_logs.error(traceback.format_exc())
            return

    @ORDER_RESPONSE_TIMES.time()
    def place_order(self, **kwargs):
        """
        function created as a wrapper to time the order executions
        :param kwargs:
        :return:
        """
        algo_logs.debug(kwargs)
        return self.client.place_order(**kwargs)


class AlgoSettingsError(Exception):
    """Raised when there are no settings defined for trades"""
    pass


def round_down(num, precision):
    factor = 10 ** precision
    return math.floor(num * factor) / factor


def run(brain: Brain, intervals: Dict):
    snapshot_interval = intervals['SNAPSHOT_INTERVAL']
    fund_update_interval = intervals['FUND_UPDATE_INTERVAL']

    if brain.PAIR is None:
        raise ValueError('Pair has to be defined to start the algo')

    if brain.EXCHANGES is None or len(brain.EXCHANGES) < 2:
        raise ValueError('Exchanges has to be defined to start the algo')

    if snapshot_interval is None:
        raise ValueError('Please define an update interval either in brain or here.')

    # processes
    snapshot_thread = threading.Thread(target=snapshot_routine,
                                       kwargs={
                                           'brain': brain,
                                           'update_interval': snapshot_interval
                                       })

    fund_update_thread = threading.Thread(target=fund_update_routine,
                                          kwargs={
                                              'brain': brain,
                                              'update_interval': fund_update_interval
                                          })
    snapshot_thread.start()
    fund_update_thread.start()


def snapshot_routine(brain: Brain, update_interval):
    algo_logs.info("Starting Snapshot routine")
    last_check = np.ceil(time.time())
    counter = 0
    while True:
        counter += 1
        #### !HINT! : TIMING START ####
        while (last_check - time.time()) > 0:
            time.sleep(0.01)
            pass

        last_check += update_interval
        #### TIMING END ####
        try:
            brain.take_snapshot()
        except Exception as err:
            # raise err
            ## just continue looping
            algo_logs.error(err)
            algo_logs.error(traceback.format_exc())


def fund_update_routine(brain: Brain, update_interval):
    algo_logs.info("Starting fund update routine")
    last_check = np.ceil(time.time())
    counter = 0
    while True:
        counter += 1
        #### !HINT! : TIMING START ####
        while (last_check - time.time()) > 0:
            time.sleep(0.1)
            pass

        last_check += update_interval
        #### TIMING END ####
        try:
            if int(time.time()) > brain.FUND_UPDATE_LOCK_END:
                brain.update_funds()
            else:
                algo_logs.debug(f'Funds suspended until: {brain.FUND_UPDATE_LOCK_END}')
        except Exception as err:
            # raise err
            ## just continue looping
            algo_logs.error(err)
            last_check = time.time()
            algo_logs.error(traceback.format_exc())


def extract_and_log(side, combo_id, timestamp, exchange, data, algo_name):
    """extracts the actual data and logs the data to the db"""
    order_id = data["order"]["order_id"]
    base_currency = data["order"]["base_currency"]
    quote_currency = data["order"]["quote_currency"]
    quantity = data["order"]["quantity"]
    order_type = data["order"]["type"]

    log_order_to_db(order_id=order_id, combo_id=combo_id, timestamp=timestamp, base=base_currency, quote=quote_currency,
                    quantity=quantity, price_executed=None, direction=side, type=order_type, filled_quantity=None,
                    exchange=exchange, status="OPEN", fee=None, fee_currency=None, algo_name=algo_name)
    algo_logs.debug("logged to db")


if __name__ == '__main__':
    # !HINT! : Fund lock has to be very high due to inaccuracies in the delays and fund update
    # see chris_trades.csv
    _settings = {
        'BASE': 'LINK',
        'QUOTE': 'EUR',
        'EXCHANGES': {
            'BITPANDA': {
                'FEES': 15,  # in bps
                'THRESHOLD': 17
            },
            'KRAKEN': {
                'FEES': 26,  # in bps
                'THRESHOLD': -15
            },
        },
        'TRADE_SIZE': 23.79,
        'MIN_TRADE_SIZE': 2,
        'PRECISION': 5,
        'FUND_UPDATE_LOCK_PERIOD': 120,
        'SLIPPAGE_BUFFER_BPS': 10,
        'FUND_BUFFER': 2.5  # as a factor of Trade size
    }

    _intervals = {
        'SNAPSHOT_INTERVAL': 2,
        'FUND_UPDATE_INTERVAL': 120
    }

    algo_logs.info("Setting up Brain...")
    _brain = Brain(settings=_settings)
    _brain.set_name("ARB-GENERAL-v1")
    algo_logs.info("Starting routines...")
    run(brain=_brain, intervals=_intervals)
    # starts the metrics server
    start_http_server(8001)
