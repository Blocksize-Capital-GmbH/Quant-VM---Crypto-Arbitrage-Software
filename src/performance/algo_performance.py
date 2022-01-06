#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import threading
import time
import asyncio
import importlib
import sortedcontainers
import logging

import src.util
from src.performance.metrics.order_volume import OrderVolume
from src.performance.metrics.pnl import PnL
import src.helpers
from src.base_with_database_logger import BaseWithDatabaseAndLogger
import src.sql_queries

__algo_name = 'ALGO-BTC:EUR--BITFINEX:BINANCE'


class NonexistentMetric(Exception):
    pass


class AlgorithmPerformance(BaseWithDatabaseAndLogger):
    metric_index = "index"
    algorithm_name = "algorithm"
    class_name = "class"
    instance = "instance"

    def __init__(self, open_db_connection, mode, logger_wrapper):
        super().__init__(open_db_connection=open_db_connection, mode=mode, logger_wrapper=logger_wrapper)
        self.metrics = sortedcontainers.SortedDict()
        self.synchronization_barrier = threading.Barrier(parties=2)
        self.update_metrics()

    async def run(self):
        while True:
            try:
                next_time_calculation, metric = self.metrics.popitem(index=0)
                actual_time = datetime.datetime.now()
                difference = next_time_calculation - actual_time
                if difference:
                    wait_s = difference.total_seconds()
                    await asyncio.sleep(wait_s)
                else:
                    metric.call()
                    next_invocation = actual_time + datetime.timedelta(seconds=metric.interval_s())
                    self.metrics[next_invocation] = metric

                datetime.datetime.now()
            except Exception as exc:
                logging.error(f"Mayor problem detected", exc_info=True)

    def run_thread(self):
        while True:
            try:
                next_time_calculation, metric_dict = self.metrics.popitem(index=0)
                actual_time = datetime.datetime.now()
                difference = (next_time_calculation - actual_time)
                wait_s = difference.total_seconds()
                if wait_s > 0:
                    self.metrics[next_time_calculation] = metric_dict
                    try:
                        self.synchronization_barrier.wait(timeout=wait_s)
                    except threading.BrokenBarrierError as exc:
                        # update of metrics and synchronization did not happen
                        # barrier timeouts
                        pass
                else:
                    metric_dict[AlgorithmPerformance.instance].call()
                    next_invocation = actual_time + datetime.timedelta(seconds=metric_dict[AlgorithmPerformance.instance].interval_s())
                    self.metrics[next_invocation] = metric_dict
            except KeyError as exc:
                # sorted dictionary is empty
                try:
                    # wait 1h
                    self.synchronization_barrier.wait(timeout=60*60)
                except threading.BrokenBarrierError as exc:
                    # barrier timeouts
                    pass
            except Exception as exc:
                logging.error(f"Mayor problem detected", exc_info=True)

    def get_metrics(self):
        return self.metrics

    def is_metric_id_present(self, algorithm_name, metric_id):
        for invocation_time, metric_structure in self.metrics.items():
            if metric_structure[AlgorithmPerformance.metric_index] == metric_id and metric_structure[AlgorithmPerformance.algorithm_name] == algorithm_name:
                return True
        return False

    @staticmethod
    def dictionary_arguments(raw_parameters):
        dictionary_args = {}
        for raw_parameter in raw_parameters:
            parameter_name = raw_parameter[2]
            parameter_value = raw_parameter[3]
            dictionary_args[parameter_name] = parameter_value
        return dictionary_args

    def synchronize_metrics(self):
        self.update_metrics()
        # inform the other thread that metrics were updated
        try:
            self.synchronization_barrier.wait(timeout=1)
        except threading.BrokenBarrierError as exc:
            # problem in the main thread operating metrics
            pass

    def update_metrics(self):
        try:
            module_metric = importlib.import_module("src.performance.metrics")
            with self.db_connector as connection:
                with connection.cursor() as cursor:
                    selection_of_algorithms = src.sql_queries.select_all_algorithms_with_status("INACTIVE")
                    cursor.execute(selection_of_algorithms)
                    algorithms = cursor.fetchall()

                    for algorithm in algorithms:
                        algorithm_id = algorithm[0]
                        algorithm_name = algorithm[1]
                        selection_of_metrics = src.sql_queries.select_from_metric_related_algorithm_from_metric_definition(algorithm_name)
                        cursor.execute(selection_of_metrics)
                        metrics = cursor.fetchall()

                        for metric in metrics:
                            metric_id = metric[0]
                            metric_class = metric[3]

                            if not self.is_metric_id_present(algorithm_name, metric_id):
                                selection_of_parameters = src.sql_queries.select_configuration_of_metric(metric_id=metric_id)
                                cursor.execute(selection_of_parameters)
                                raw_parameters = cursor.fetchall()

                                dictionary_args = AlgorithmPerformance.dictionary_arguments(raw_parameters)
                                dictionary_args.update(
                                    {
                                        "mode": self.mode,
                                        "logger_wrapper": self.logger_wrapper
                                    }
                                )

                                if metric_class in {"OrderVolume", "PnL"}:
                                    class_definition = getattr(module_metric, metric_class)
                                    instance = class_definition(algorithm_name, algorithm_id, **dictionary_args)
                                    interval = instance.interval_s
                                    next_calculation = datetime.datetime.now() + datetime.timedelta(seconds=interval)
                                    self.metrics[next_calculation] = {
                                        AlgorithmPerformance.metric_index: metric_id,
                                        AlgorithmPerformance.algorithm_name: algorithm_name,
                                        AlgorithmPerformance.class_name: metric_class,
                                        AlgorithmPerformance.instance: instance
                                    }
                                else:
                                    raise NonexistentMetric(f"Nonexistent metric class name {metric_class}")

        except Exception as exc:
            logging.critical(f"Fundamental problem detected", exc_info=True)


# todo create a distribution index (shows whether we have more BTC on exchange A or B)
#  this would probably show the strong BTC overweight on Bitfinex due to infrequent opportunities to get rebalanced
def main():
    """
    This function runs every x min and back calculates all fully complete intervals registered.
    :return:
    """
    threads = []
    for interval in ["1h", "6h", "12h", "24h", "3d", "7d"]:
        for side in ["quote", "base"]:
            metric = OrderVolume(__algo_name, interval=interval, side=side)
            try:
                t = threading.Thread(target=metric.continue_filling)
                t.start()
                threads.append(t)
            except Exception as ex:
                print("Error: unable to start thread_ order_volume" + interval + "_" + side)
                raise ex

    for interval in ["1h", "1d", "3d", "7d"]:
        metric = PnL(__algo_name, interval=interval)
        try:
            t = threading.Thread(target=metric.continue_filling)
            t.start()
            threads.append(t)
        except Exception as ex:
            print("Error: unable to start thread_ pnl" + interval)
            raise ex
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    algorithmic_performance = AlgorithmPerformance(open_db_connection=True, mode=src.helpers.DBMode.DEV, logger_wrapper=src.util.LoggerWrapper("ALGO"))
    print(algorithmic_performance.get_metrics())
    algorithmic_performance.update_metrics()
    print(algorithmic_performance.get_metrics())
    algorithmic_performance.run_thread()
