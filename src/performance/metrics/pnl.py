#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import numpy as np
import pandas

import quant_sdk

from src.helpers import DBMode
import src.util
from src.performance.metrics import Metric, MetricRow


# todo (maybe) change to ceiling the data. Data point has to be shown for the completed period in grafana.
#  So at the end of the period not the beginning
class PnL(Metric):
    """
    Performance calculator of Profit&Loss
    """

    def __init__(self, algo_name, algorithm_id, mode: DBMode, logger_wrapper: src.util.LoggerWrapper, interval: str = "1d", metric_name: str = None, metric_id: int = None):
        super().__init__(algo_name, algorithm_id, metric_name, metric_id, interval, mode, logger_wrapper)
        if metric_name is None:
            metric_name = f"pnl_{interval}"
        self.metric_name = metric_name
        # todo create an interval class which incorporates all the interval based functions
        #  many things are 1:1 duplicates from order volume
        self.extra_intervals = self.set_extra_intervals()

    def transform_and_aggregate(self, df: pandas.DataFrame):
        convertor = lambda x: datetime.datetime.fromtimestamp(x[0])

        df[Metric.UNIX_TIME] = (np.floor(df[Metric.TIMESTAMP].view(np.int64) / 1e9 / self.interval_s) * self.interval_s).astype(int)
        dates = df[[Metric.UNIX_TIME]].apply(convertor, axis=1, raw=True)
        df[Metric.INTERVAL_TIME] = dates

        currency_pairs = df[Metric.CURRENCY_PAIR].unique()
        df_agg = []
        for currency_pair_id in currency_pairs:
            # determinantion of unit
            unit_id = self.get_unit_id(currency_pair_id)

            # selection by currency pair
            subselection = df[df[Metric.CURRENCY_PAIR] == currency_pair_id]

            # set measurement unit
            subselection[Metric.UNIT_NAME] = unit_id

            # calculation of the aggregation
            try:
                result = subselection.groupby([Metric.INTERVAL_TIME]).apply(self.transformation)
            except TypeError as exc:
                result = pandas.DataFrame()

            # store the result
            df_agg.append(result)

        return df_agg

    def transformation(self, data: pandas.DataFrame):
        currency_id = data[Metric.CURRENCY_PAIR].iloc[0]
        currency = self.currencies[self.currencies[Metric.CURRENCY_PAIR_ID] == currency_id][Metric.CURRENCY_ID]

        net_traded_base = data[data[Metric.DIRECTION] == quant_sdk.Client.BUY][Metric.QUANTITY].sum() - data[
            data[Metric.DIRECTION] == quant_sdk.Client.SELL][Metric.QUANTITY].sum()
        net_traded_quote = \
            (data[data[Metric.DIRECTION] == quant_sdk.Client.SELL][Metric.QUANTITY] *
             data[data[Metric.DIRECTION] == quant_sdk.Client.SELL][Metric.PRICE]).sum() - \
            (data[data[Metric.DIRECTION] == quant_sdk.Client.BUY][Metric.QUANTITY] *
             data[data[Metric.DIRECTION] == quant_sdk.Client.BUY][Metric.PRICE]).sum()

        # 0 - base currency, 1 - quote currency
        base_currency = currency.iloc[0, 0]
        quote_currency = currency.iloc[0, 1]
        net_traded_base -= data[data[Metric.FEE_CURRENCY] == base_currency][Metric.FEE_CURRENCY].sum()
        net_traded_quote -= data[data[Metric.FEE_CURRENCY] == quote_currency][Metric.FEE_CURRENCY].sum()

        last_price = data[data[Metric.TIMESTAMP] == data[Metric.TIMESTAMP].max()][Metric.PRICE].median()

        net_traded_btc_in_base = net_traded_base * last_price
        value_diff_in_eur = net_traded_btc_in_base + net_traded_quote
        return pandas.Series([value_diff_in_eur, 1] )


if __name__ == '__main__':
    from src.client import test_sdk_client
    import quant_sdk as sdk
    import src.sql_queries

    db_connection = src.helpers.DBConnector(
        logger=None, mode=DBMode.DEV
    )

    logger = src.util.base_logger(__name__, "test-logs/debug.log", db_connection=db_connection)
    client = test_sdk_client.TestClient("ABC", logger)

    response = client.place_order(
        order_type=sdk.Client.MARKET_ORDER,
        base="BTC",
        quote="EUR",
        direction=sdk.Client.BUY,
        quantity=0.5,
        exchanges="BINANCE"
    )
    status = client.order_status(response['order']['order_id'])

    query = src.sql_queries.insert_into_order_log(1, 1, status, logger)
    db_connection.execute_dml(query)

    order_v = PnL(
        algo_name="A-tests-multi-lateral",
        algorithm_id=1,
        interval="1h",
        mode=DBMode.DEV,
        metric_id=1,
        logger_wrapper=src.util.LoggerWrapper("Order_Volume")
    )
    order_v.call()
