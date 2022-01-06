#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
general notation is formed as bid-ask.
first exchange is the bid side (sell on side) and the second is the ask side (buy on side)
"""
import os
import datetime
import uuid
import threading
import yaml
import numpy as np
import psycopg2
from multiprocessing.pool import ThreadPool
from typing import Dict, List, Tuple, Union
from prometheus_client import Summary

import quant_sdk as sdk

import src.helpers
import src.sql_queries
import src.buildblocks
from src import util
from src.data_types import Signal
from src.trading_algorithm import TradingAlgorithm
from src.algorithm_exception import IncorrectStateException
from src.order_status.order_status import OrderStatus, timeout_tag, order_sdk_tag, additional_info_tag

ORDER_RESPONSE_TIMES = Summary('execute_order_func_times', 'Time it takes to place both legs of an arbitrage trade.')


# TODO rename files for algorithms referencing the content e.g. arbitrage_algorithm.py
# This will enhance the traceback of logs
class ArbitrageInstance(TradingAlgorithm):
    """
    Arbitrage instance
    In simulation mode the instance will not place any trades and will not send any trades
    everything else will be instantiated and will run as normal.
    configs_file is a yaml file located in the working directory or anywhere when a file path is given.
    """
    fee_map: Dict[str, float] = {}  # contains the fees for all
    exchanges: List[str]
    currencies: List[str]

    # todo generate from a default global threshold
    # todo be able to modify specific combinations
    threshold_map: Dict[str, Dict[str, float]] = {}
    # every exchange has a designated threshold for every possible
    # combination format {ex_1: {ex_2: thresh_1, ..., ex_n: thresh_n}, ..., ex_n: {ex_1: thresh_1, ...,
    # ex_(n-1): thresh_(n-1)}}

    lot_size: float
    min_lot_size: float

    base: str
    quote: str
    precision: float

    fund_update_lock_period: float
    slippage_buffer_bps: float
    fund_buffer: float

    funds: Dict[str, Dict[str, float]]

    def __init__(
            self,
            algo_name,
            client=None,
            logger_wrapper: src.util.LoggerWrapper=None,
            visualization=False,
            update_order_sleep=10
    ):
        super().__init__(
            algo_name=algo_name,
            client=client,
            mode=src.helpers.DBMode.TEST,
            open_db_connection=False,
            logger_wrapper=logger_wrapper
        )
        self.visualization = visualization
        self.logger_wrapper.logger.info("Constructor")

        self.orders_observer = OrderStatus(
            client=self.client,
            mode=self.mode,
            test=True,
            logger_instance=self.logger_wrapper,
            update_order_sleep=update_order_sleep
        )
        self.orders_observer_thread = threading.Thread(target=self.orders_observer.resolve_orders_threaded, args=())
        self.orders_observer_thread.start()

    def __del__(self):
        # virtual destructor
        self.orders_observer.disable_activity()
        self.orders_observer_thread.join()

        if self.orders_observer_thread.is_alive():
            self.logger_wrapper.logger.error(f"Service open orders service thread failed to stop")
        else:
            del self.orders_observer
        super(ArbitrageInstance, self).__del__()

    def trade_algorithm(self):
        for currency_pair in self.configuration["CURRENCY_PAIRS"]:
            basic_points_for_currency = 10000 # this comes from db table
            precision = 2 # this comes from db table
            exchanges_associated_to_pair = self.currency_pair_exchange_association[currency_pair['symbol']]
            order_books_raw = self.client.get_order_book(exchanges_associated_to_pair, currency_pair['code_base'], currency_pair["code_quote"], depth=50)

            # check presence of arbitrage opportunity without fees
            max_ask = max([order_book["asks"][0][0] for order_book in order_books_raw])
            min_bid = min([order_book["bids"][0][0] for order_book in order_books_raw])

            if max_ask > min_bid:
                # opportunity for arbitrage exists

                # calculation of maximal arbitrage opportunity for each exchange
                opportunities = {}
                for order_book in order_books_raw:
                    # extraction of fees
                    exchange = order_book['exchange']

                    asks_to_arbitrage = [order_item for order_item in order_book["asks"] if order_item[0] > min_bid]
                    bids_to_arbitrage = [order_item for order_item in order_book["bids"] if order_item[0] < max_ask]
                    volume_asks = sum([item[1] for item in asks_to_arbitrage])
                    price_asks = sum([item[1] * item[0] for item in asks_to_arbitrage])
                    volume_bids = sum([item[1] for item in bids_to_arbitrage])
                    price_bids = sum([item[1] * item[0] for item in bids_to_arbitrage])
                    opportunities[order_book['exchange']] = {'asks': [price_asks, volume_asks], 'bids': [price_bids, volume_bids]}

                if self.visualization:
                    self.logger_wrapper.logger.info(f"Opportunities: {opportunities}")
                    src.helpers.visualize_order_book("Raw orderbooks", order_books_raw)

                    # construction of fully arbitraged order book
                    unarbitraged_order_book = self.deselect_orders_in_interval(order_books_raw, min_bid, max_ask)
                    src.helpers.visualize_order_book("Order books after full arbitrage", unarbitraged_order_book)

                # additional checking/checking threshold
                orders_to_execute = self.prepare_orders(opportunities, currency_pair, basic_points_for_currency, precision)

                # check funds for trades
                orders_to_be_executed = self.check_funds_for_trades(orders_to_execute)

                # execute trades
                executed_trades = self.execute_orders(orders_to_be_executed)

                # check fulfillment of trades
                #self.check_fulfillment_of_orders(executed_trades)

    def log_executed_order(self, order_response, exchange):
        query_to_execute = src.sql_queries.insert_into_order_log(
            self.algo_id, exchange, order_response, self.logger_wrapper.logger
        )
        self.db_connector.execute_dml(query_to_execute)

    @staticmethod
    def deselect_orders_in_interval(order_books_raw, min_bid, max_ask):
        # construction of fully arbitraged order book
        unarbitraged_order_book = []
        for order_book in order_books_raw:
            asks_unable_to_arbitrage = [order_item for order_item in order_book["asks"] if order_item[0] <= min_bid]
            bids_unable_to_arbitrage = [order_item for order_item in order_book["bids"] if order_item[0] >= max_ask]
            exchange_order_book = {'exchange': order_book['exchange'], "asks": asks_unable_to_arbitrage, "bids": bids_unable_to_arbitrage}
            unarbitraged_order_book.append(exchange_order_book)
        return unarbitraged_order_book

    def prepare_orders(self, opportunities, currency_pair, basic_points_for_currency, precision):
        orders_to_execute = {}
        for exchange, opportunity in opportunities.items():
            fee_bid = self.fee_map[exchange]['BUY'] / basic_points_for_currency
            fee_ask = self.fee_map[exchange]['SELL'] / basic_points_for_currency

            orders_to_execute[exchange] = []
            # TODO: taking into account latency
            # calculate fees for transaction

            order = {
                "currency_pair": currency_pair,
                "status": "in preparation",
                "algo_id": self.algo_id,
                "exchange_id": self.configuration['EXCHANGES'][exchange]["ID"]
            }
            if opportunity['asks'][1] > 0 and opportunity['bids'][1] > 0:
                # exchange in the middle
                average_direction_of_trade = np.mean([opportunity['asks'][1], -opportunity['bids'][1]])

                # it can be improved
                order.update({
                    "volume": util.round_down(abs(opportunity['asks'][1] if average_direction_of_trade > 0 else opportunity['bids'][1]), precision),
                    "price": (opportunity['asks'][0] if average_direction_of_trade > 0 else opportunity['bids'][0]),
                    "type": ('BUY' if average_direction_of_trade > 0 else 'SELL')
                })
            elif opportunity['asks'][1] > 0 and opportunity['bids'][1] == 0:
                order.update({
                    "volume": util.round_down(abs(opportunity['asks'][1]), precision),
                    "price": opportunity['asks'][0],
                    "type": 'SELL',
                    "fees": opportunity['asks'][0] * fee_bid,
                    "currency_fee": currency_pair["code_quote"]
                })
            elif opportunity['bids'][1] > 0 and opportunity['asks'][1] == 0:
                order.update({
                    "volume": util.round_down(abs(opportunity['bids'][1]), precision),
                    "price": opportunity['asks'][0],
                    "type": 'BUY',
                    "fees": opportunity['bids'][0] * fee_ask,
                    "currency_fee": currency_pair["code_base"]
                })
            elif opportunity['bids'][1] == 0 and opportunity['asks'][1] == 0:
                # no opportunity detected
                continue
            else:
                raise IncorrectStateException("Fundamental algorithm error!")
            orders_to_execute[exchange].append(order)
            self.logger_wrapper.logger.debug(f"New order prepared: {order}")
        return orders_to_execute

    def execute_orders(self, orders_to_be_executed):
        executed_trades = []
        for exchange, orders in orders_to_be_executed.items():
            for order in orders:
                currency_pair = order["currency_pair"]
                response = self.client.place_order(
                    order_type=sdk.Client.MARKET_ORDER,
                    base=currency_pair["code_base"],
                    quote=currency_pair["code_quote"],
                    direction=(
                        sdk.Client.BUY if order["type"] == "BUY" else sdk.Client.SELL
                    ),
                    quantity=order["volume"],
                    exchanges=exchange
                )
                order["status"] = "submitted"
                self.current_order_id = response["order"]["order_id"]
                executed_trades.append((response, order))
                self.logger_wrapper.logger.debug(f"Order executed: {order}")
                self.orders_observer.enqueue_order_thread(
                    {
                        timeout_tag: datetime.datetime.now() + datetime.timedelta(minutes=1),
                        order_sdk_tag: response,
                        additional_info_tag:{
                            "algo_id": order["algo_id"],
                            "exchange_id": order["exchange_id"]
                        }
                    })
        return executed_trades

    def check_fulfillment_of_orders(self, executed_trades):
        for item in executed_trades:
            response, order = item
            status = self.client.order_status(response['order']['order_id'])
            if status['trade_status'][0]['execution_status'] == 1:
                order['status'] = 'finished'

                # log data into DB
                self.log_executed_order(status, response['exchanges'])
            else:
                # status of the order not finished
                order['status'] = 'unfinished'

    def check_funds_for_trades(self, orders_to_execute):
        # check funds for trades
        orders_to_be_executed = {}
        for exchange, orders in orders_to_execute.items():
            orders_to_be_executed[exchange] = []
            for order in orders:
                currency = order["currency_pair"]["code_quote"] if order["type"] == "BUY" else order["currency_pair"]["code_base"]
                funds_in_appropriate_currency = self.funds[exchange][currency]
                approximate_price = order["price"]
                if funds_in_appropriate_currency * (1 - self.fund_buffer) < approximate_price:
                    # limiting volume
                    order["volume"] = (1 - self.fund_buffer) * order["volume"]
                orders_to_be_executed[exchange].append(order)
        return orders_to_be_executed

    #########################################################
    # Signal calculation and determination [A]
    #########################################################

    ### Step A 1 ###
    def get_modified_snapshots(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        get the different order books and merge them

        inputs:
        None
        return format
        {
            exchange_1: {bid: {price: vwap_price, volume: agg_volume}, ask: {price: vwap_price, volume: agg_volume}},
            exchange_2: {bid: {price: vwap_price, volume: agg_volume}, ask: {price: vwap_price, volume: agg_volume}},
            exchange_n: {bid: {price: vwap_price, volume: agg_volume}, ask: {price: vwap_price, volume: agg_volume}},
        }
        """
        vwap_order_books = {}

        return vwap_order_books

    ### Step A 2 ###
    def find_opportunities(self, order_books: Dict[str, Dict[str, Dict[str, float]]]) -> List[Signal]:
        """
        inputs:
        Takes the order_books format from get_modified_snapshots()

        returns:

        """
        signals: List[Signal] = []
        for sell_ex in self.exchanges:
            for buy_ex in self.exchanges:
                if sell_ex == buy_ex:
                    continue
                signal = self.extract_arbitrage_ops(order_books, sell_ex, buy_ex)
                if signal is None:
                    continue
                signals.append(signal)

        return signals

    ### Step A 2.1 ###
    def extract_arbitrage_ops(self, order_books: Dict[str, Dict[str, Dict[str, float]]], sell_ex, buy_ex) -> Union[
        Signal, None]:
        """
        inputs:
        order_books is a subset of all order books which are being observed.
        The subset focuses on two exchanges
        returns:

        """
        basic_points = 10000
        signal = Signal()
        signal.sell_exchange = sell_ex
        signal.buy_exchange = buy_ex

        if sell_ex not in order_books.keys():
            logger.info(f"data for sell exchange [{sell_ex}] missing")
            return
        if buy_ex not in order_books.keys():
            logger.info(f"data for buy exchange [{buy_ex}] missing")
            return

        book_bid = order_books[sell_ex]
        book_ask = order_books[buy_ex]

        fee_bid = self.fee_map[sell_ex] / basic_points
        fee_ask = self.fee_map[buy_ex] / basic_points

        bid_price = book_bid["bid"]["price"]
        ask_price = book_ask["ask"]["price"]

        spread = (((bid_price * (1 - fee_bid)) / (ask_price * (1 + fee_ask))) - 1) * basic_points
        volume = min(book_bid["bid"]["volume"], book_ask["ask"]["volume"], self.lot_size)
        volume = util.round_down(volume, self.precision)

        signal.spread = spread
        signal.volume = volume

        signal.sell_price = bid_price
        signal.buy_price = ask_price

        return signal

    ### Step A 3.1 ###
    def check_thresholds(self, signals: List[Signal]) -> List[Signal]:
        """Check thresholds"""
        #
        signals = [self._check_threshold(signal) for signal in signals]

        # select only signals which meet the threshold
        signals = [signal for signal in signals if signal.above_thresh]
        return signals

    ### Step A 3.1.1 ###
    def _check_threshold(self, signal: Signal):
        """check whether the spread is above the specified threshold for the combination"""
        threshold = self.threshold_map[signal.sell_exchange][signal.buy_exchange]

        if signal.spread >= threshold:
            signal.above_thresh = True
        else:
            signal.above_thresh = False

        return signal

    ### Step A 3.2 ###
    def check_fund_availability(self, signals: List[Signal]) -> List[Signal]:
        executable_signals: List[Signal] = []
        for signal in signals:
            buy_exchange_funds = self.funds[signal.buy_exchange][self.quote]  # We use quote currency to buy
            sell_exchange_funds = self.funds[signal.sell_exchange][self.base]  # we use base currency for a sell

            volume_base = signal.volume
            volume_quote = signal.volume * signal.sell_price

            if buy_exchange_funds - (volume_quote * self.fund_buffer) < 0:
                continue
            if sell_exchange_funds - (volume_base * self.fund_buffer) < 0:
                continue
            executable_signals.append(signal)

        return executable_signals

    ### Step A 4 ###
    def select_signals(self, signals: List[Signal]) -> List[Signal]:
        """chooses the trade which is the highest above it's threshold in relative terms:
        (spread / threshold * volume)"""
        current_lead: Tuple[float, Signal] = (0, signals[0])

        for signal in signals:
            threshold = self.threshold_map[signal.sell_exchange][signal.buy_exchange]
            val = signal.spread / threshold * signal.volume
            if val > current_lead[0]:
                current_lead = (val, signal)

        # kept as a list if the selection
        return [current_lead[1]]

    #########################################################
    # Signal and trade execution [B]
    #########################################################

    ### Step B 1 ###
    def execute_arbitrage_signals(self, signals: List[Signal]):
        threads = []
        for signal in signals:
            t = threading.Thread(target=self.execute_trade, kwargs={"signal": signal}, daemon=True)
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()

    ### Step B 1.1 ###
    def execute_trade(self, signal):
        pool = ThreadPool(processes=2)

        buy_exchange = signal.buy_exchange
        sell_exchange = signal.sell_exchange
        volume = signal.volume

        start_time = util.unix_milli()

        buy_thread = pool.apply_async(self.place_order, (), {
            "order_type": sdk.Client.MARKET_ORDER,
            'base': self.base,
            'quote': self.quote,
            'direction': sdk.Client.BUY,
            'quantity': volume,
            'exchanges': buy_exchange,
        })

        sell_thread = pool.apply_async(self.place_order, (), {
            "order_type": sdk.Client.MARKET_ORDER,
            'base': self.base,
            'quote': self.quote,
            'direction': sdk.Client.SELL,
            'quantity': volume,
            'exchanges': sell_exchange
        })

        buy_order = buy_thread.get()
        sell_order = sell_thread.get()
        end_time = util.unix_milli()

        logger.info(f'Duration order placement: {round(end_time - start_time, 6)}ms')
        logger.info(f'Buy: {buy_order}')
        logger.info(f'Buy: {sell_order}')
        t = threading.Thread(target=self.log_executions,
                             kwargs={"buy_order": buy_order, "sell_order": sell_order, "buy_exchange": buy_exchange,
                                     "sell_exchange": sell_exchange})
        t.start()

    @ORDER_RESPONSE_TIMES.time()
    def place_order(self, **kwargs):
        """
        function created as a wrapper to time the order executions
        :param kwargs:
        :return:
        """
        logger.debug(kwargs)
        return self.client.place_order(**kwargs)

    def log_executions(self, buy_order, sell_order, buy_exchange, sell_exchange):
        """This function logs the two legs of an arbitrage trade collection"""
        logger.debug("logging order")
        combo_id = uuid.uuid4()
        timestamp = util.unix_milli()

        # Buy leg
        extract_and_log("buy", combo_id, timestamp, buy_exchange, buy_order, self.name())
        extract_and_log("sell", combo_id, timestamp, sell_exchange, sell_order, self.name())

    #########################################################
    # Settings
    #########################################################

    def load_configs_yaml(self) -> Dict[str, Union[float, str, Dict]]:
        configs: Dict
        with open(self.configs_file, 'r') as stream:
            try:
                configs = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logger.error(exc)
        return configs

    def set_threshold_map(self, thresh):
        threshold_map = {}
        for exchange in self.exchanges:
            if exchange not in threshold_map.keys():
                threshold_map[exchange] = {}
            for second_exchange in self.exchanges:
                if exchange == second_exchange:
                    continue
                threshold_map[exchange][second_exchange] = thresh
        self.threshold_map = threshold_map

    def set_fee_map(self, fees: Dict[str, float]):
        for exchange, fee in fees.items():
            self.fee_map[exchange] = fee


if __name__ == '__main__':
    logger_wrapper = src.buildblocks.init_logger(mode=src.helpers.DBMode.DEV)
    test_algo_name = "A-tests-multi-lateral"
    client_sdk = src.buildblocks.init_sdk_client(logger_wrapper, sdk_client=src.helpers.SDKClient.REAL)

    instance = ArbitrageInstance(
        algo_name=test_algo_name,
        logger_wrapper=logger_wrapper,
        client=client_sdk
    )

    while True:
        instance.trade_algorithm()
