#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import numpy as np
import pandas as pd

import src.util
from src.helpers import DBMode
from src.performance.metrics import Metric

__algo_name = 'ALGO-BTC:EUR--BITFINEX:BINANCE'


# todo (maybe) change to ceiling the data. Data point has to be shown for the completed period in grafana.
#  So at the end of the period not the beginning
class OrderVolume(Metric):

    def __init__(self, algo_name, algorithm_id, mode: DBMode, logger_wrapper: src.util.LoggerWrapper, interval: str = "1d", side: str = "QUOTE", metric_name: str = None, metric_id: int = None):
        if metric_name is None:
            metric_name = f"order_volume_{interval}_{side.lower()}"
        super().__init__(algo_name, algorithm_id, metric_name, metric_id, interval, mode, logger_wrapper)
        self.metric_name = metric_name

        self.side = side
        # todo implement class/object wide interval_count
        self.extra_intervals = self.set_extra_intervals()

    def transform_and_aggregate(self, df: pd.DataFrame):
        # floor timestamps to interval
        convertor = lambda x: datetime.datetime.fromtimestamp(x[0])
        df_agg = []

        try:
            df[Metric.UNIX_TIME] = (np.floor(df[Metric.TIMESTAMP].view(np.int64) / 1e9 / self.interval_s) * self.interval_s).astype(int)
            dates = df[[Metric.UNIX_TIME]].apply(convertor, axis=1, raw=True)
            df[Metric.INTERVAL_TIME] = dates

            currency_pairs = df[Metric.CURRENCY_PAIR].unique()
            for currency_pair_id in currency_pairs:
                # determination of unit
                unit_id = self.get_unit_id(currency_pair_id, self.side)

                # selection by currency pair
                subselection = df[df[Metric.CURRENCY_PAIR] == currency_pair_id]

                # calculation
                trading_volume = subselection[[Metric.INTERVAL_TIME]].copy()
                if self.side == Metric.BASE:
                    trading_volume[Metric.VOLUME]: pd.DataFrame = subselection[Metric.QUANTITY]
                elif self.side == Metric.QUOTE:
                    trading_volume[Metric.VOLUME]: pd.DataFrame = subselection[Metric.QUANTITY] * subselection[Metric.PRICE]
                else:
                    raise ValueError("side is not correctly specified")

                # calculation of the aggregation
                data: pd.Series = trading_volume.groupby(Metric.INTERVAL_TIME).sum()

                # set measurement unit
                data[Metric.UNIT_NAME] = unit_id

                # store the result
                df_agg.append(data)
        except TypeError as exc:
            # empty list will be returned
            pass

        return df_agg


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
        base="LINK",
        quote="EUR",
        direction=sdk.Client.BUY,
        quantity=0.5,
        exchanges="BINANCE"
    )
    status = client.order_status(response['order']['order_id'])

    query = src.sql_queries.insert_into_order_log(1, 1, status, logger)
    db_connection.execute_dml(query)

    order_v = OrderVolume(
        algo_name="A-tests-multi-lateral",
        algorithm_id=1,
        interval="1h",
        side=Metric.BASE,
        mode=DBMode.DEV,
        metric_id=1,
        logger_wrapper=src.util.LoggerWrapper("Order_Volume")
    )
    order_v.call()
