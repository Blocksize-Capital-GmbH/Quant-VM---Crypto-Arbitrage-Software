import datetime
import os
import sys
import time
import logging

from dotenv import load_dotenv
from prometheus_client import start_http_server, Summary

from quant_sdk import Client

# Create a metric to track time spent and requests made.
REQUEST_TIME_ORDER_BOOKS = Summary('req_order_books', 'Time spent processing order books request')
REQUEST_TIME_VWAP_LATEST = Summary('req_vwap_latest', 'Time spent processing vwap latest request')
REQUEST_TIME_OHLC_LATEST = Summary('req_ohlc_latest', 'Time spent processing ohlc latest request')


# Decorate function with metric.
@REQUEST_TIME_ORDER_BOOKS.time()
def make_request_order_books():
    client.get_order_book(["BINANCE", "BEQUANT", "BITPANDA", "KRAKEN"], "BTC", "EUR")


@REQUEST_TIME_VWAP_LATEST.time()
def make_request_vwap_latest():
    client.get_vwap("ETH", "EUR", Client.INTERVAL_2H)


# Decorate function with metric.
@REQUEST_TIME_OHLC_LATEST.time()
def make_request_ohlc_latest():
    client.get_ohlc("BTC", "EUR", Client.INTERVAL_1S)


if __name__ == '__main__':
    sys.path.append(os.getcwd())
    load_dotenv()
    client = Client(os.getenv("API_KEY_BLOCKSIZE"))

    duration_of_sleep = 10

    # Start up the server to expose the metrics.
    start_http_server(8000)
    print(f"[{datetime.datetime.now()}] starting dashboard data service")
    # Generate some requests.
    while True:
        print(f"[{datetime.datetime.now()}] running loop")
        try:
            make_request_order_books()
            make_request_vwap_latest()
            make_request_ohlc_latest()
            time.sleep(duration_of_sleep)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            logging.error(f"{datetime.datetime.now().isoformat()} Exception during latency measurement", exc_info=True)
