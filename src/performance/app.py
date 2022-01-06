#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask import Flask, request
import logging
import asyncio
import threading
import src.helpers
import src.util
import src.performance.algo_performance

logging.basicConfig(level=logging.INFO)
app = Flask("OrderStatus")


@app.route("/",  methods=['GET'])
def default():
    logging.info("Connected to / handler")
    return "The server is alive\n"


@app.route("/reload_metrics",  methods=['POST', 'PUT'])
def reload_metrics():
    logging.info("Reload metrics")
    algorithm_performance_instance.synchronize_metrics()
    return "Reloaded"


@app.route("/show",  methods=['GET'])
def show_metrics():
    logging.info("Get metrics in place")
    metrics = str(algorithm_performance_instance.get_metrics())
    return metrics


if __name__ == '__main__':
    algorithm_performance_instance = src.performance.algo_performance.AlgorithmPerformance(
        open_db_connection=True,
        mode=src.helpers.DBMode.DEV,
        logger_wrapper=src.util.LoggerWrapper("ALGO")
    )

    thread = threading.Thread(target=algorithm_performance_instance.run_thread)
    thread.start()

    app.run(host="0.0.0.0", port=8080, debug=False)
    thread.join()
