import requests
import os
import time
from enum import Enum
from dotenv import load_dotenv


class APIVersion(Enum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"


tickers = ["BTCUSD", "BTCEUR", "ETHUSD", "ETHEUR"]
currencies = ["EUR", "USD"]
exchanges = ["KRAKEN", "BITFINEX", "BITSTAMP"]
order_statuses = ["OPEN", "CLOSED", "FAILED", "PARTIALLYFILLED"]
intervals = ["1s", "5s", "30s", "60s", "1m", "5m", "15m", "30m", "1h", "2h", "6h", "12h", "24h"]

base_url = {APIVersion.PRODUCTION: "https://api.blocksize.capital/v1", APIVersion.DEVELOPMENT: "https://api-dev.blocksize.capital/v1"}

# description of endpoints:
# https://docs.blocksize.capital/#/

get_end_points_simple = ["/data/vwap/latest/", "/data/ohlc/latest/"]
get_end_points_with_to_and_from_time = [ "/data/vwap/historic/", "/data/ohlc/historic/"]
get_end_points_exchanges = ["/positions/exchanges"]
get_end_point_orders = "/trading/orders"
post_end_point_simulated_orders = "/trading/orders/simulated"
post_end_point_orders = "/trading/orders"
get_end_point_id = "/trading/orders/id/"
get_end_point_id_logs = get_end_point_id
get_end_point_status = "/trading/orders/status/"
put_end_point_cancel = "/trading/orders/"
get_end_point_positions = "/positions/exchanges"
post_withdraw = "/positions/withdraw"


def get_create_order(base_currency="BTC", quote_currency="USD", quantity=1.5, direction="BUY", type="MARKET", exchange_list=["BITSTAMP", "COINBASE"], unlimited="true", disable_logging="false"):
    return {
        "BaseCurrency": base_currency,
        "QuoteCurrency": quote_currency,
        "Quantity": quantity,
        "Direction": direction,
        "Type": type,
        "ExchangeList": exchange_list,
        "Unlimited": unlimited,
        "DisableLogging": disable_logging
    }


def get_withdraw_structure(api_key_id, currency, amount, target_identifier):
    return {
        "api_key_id": api_key_id,
        "currency": currency,
        "amount": amount,
        "target_identifier": target_identifier
    }


def api_put_query(base_url, end_point, api_key):
    endpoint_to_execute = f'{base_url}{end_point}'
    response = requests.put(endpoint_to_execute, headers={"x-api-key": api_key})
    return response


def api_get_query(base_url, end_point, api_key):
    endpoint_to_execute = f'{base_url}{end_point}'
    response = requests.get(endpoint_to_execute, headers={"x-api-key": api_key})
    return response


def api_post_query(base_url, end_point, data, api_key):
    endpoint_to_execute = f'{base_url}{end_point}'
    response = requests.post(endpoint_to_execute, headers={"x-api-key": api_key}, data=data)
    return response


def test_of_endpoints_with_to_and_from_time(from_shift, to_shift):
    time_from = int(time.time() - from_shift)
    time_to = int(time.time() - to_shift)

    for ticker in tickers:
        for timeframe in intervals:
            for end_point in get_end_points_with_to_and_from_time:
                final_endpoint = end_point + f"{ticker}/{timeframe}" + f"?from={time_from}&to={time_to}"
                response = api_get_query(base_url[version], final_endpoint, api_keys[version])
                if response.ok:
                    print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
                else:
                    print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")


def test_of_endpoints_simple():
    for ticker in tickers:
        for timeframe in intervals:
            for end_point in get_end_points_simple:
                final_endpoint = end_point+f"{ticker}/{timeframe}"
                response = api_get_query(base_url[version], final_endpoint, api_keys[version])
                if response.ok:
                    print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
                else:
                    print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")


def test_of_endpoints_exchanges(exchanges, limit=100):
    for ticker in tickers:
        for end_point in get_end_points_exchanges:
            final_endpoint = end_point+f"?exchanges={exchanges}&ticker={ticker}&limit={limit}"
            response = api_get_query(base_url[version], final_endpoint, api_keys[version])
            if response.ok:
                print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
            else:
                print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")


def test_of_simulation_order(order):
    final_endpoint = post_end_point_simulated_orders
    response = api_post_query(base_url[version], final_endpoint, order, api_keys[version])
    if response.ok:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
    else:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")
    return response.json()


def test_of_real_order(order):
    final_endpoint = post_end_point_orders
    response = api_post_query(base_url[version], final_endpoint, order, api_keys[version])
    if response.ok:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
    else:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")
    return response.json()


def test_of_all_orders_statuses():
    final_endpoint = get_end_point_orders
    response = api_get_query(base_url[version], final_endpoint, api_keys[version])
    if response.ok:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
    else:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")


def test_of_order_status(order_id):
    final_endpoint = get_end_point_id+f"{order_id}"
    response = api_get_query(base_url[version], final_endpoint, api_keys[version])
    if response.ok:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
        return response.json()
    else:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")
        return response.text


def test_of_order_logs(order_id):
    final_endpoint = get_end_point_id+f"{order_id}/logs"
    response = api_get_query(base_url[version], final_endpoint, api_keys[version])
    if response.ok:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
    else:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")


def test_of_order_cancel(order_id):
    final_endpoint = put_end_point_cancel+f"{order_id}/cancel"
    response = api_put_query(base_url[version], final_endpoint, api_keys[version])
    if response.ok:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
    else:
        print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")


def test_of_order_statuses():
    for status in order_statuses:
        final_endpoint = get_end_point_status + f"{status}"
        response = api_get_query(base_url[version], final_endpoint, api_keys[version])
        if response.ok:
            print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
        else:
            print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")


def test_of_position_exchange():
    for quotecurrency in currencies:
        final_endpoint = get_end_point_positions + f"?quotecurrency={quotecurrency}"
        response = api_get_query(base_url[version], final_endpoint, api_keys[version])
        if response.ok:
            print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Response: {response.json()}")
            return response.json()
        else:
            print(f"{final_endpoint}: Duration: {response.elapsed.total_seconds()}s Status: {response.status_code} Response: {response.text}")


if __name__ == '__main__':
    load_dotenv("../.env")
    api_key = os.getenv("API_KEY_BLOCKSIZE")
    api_dev_key = os.getenv("API_DEV_KEY_API_KEY_BLOCKSIZE")
    api_keys = {APIVersion.PRODUCTION: api_key, APIVersion.DEVELOPMENT: api_dev_key}
    version = APIVersion.DEVELOPMENT

    #test_of_endpoints_simple()
    #test_of_endpoints_with_to_and_from_time(10000, 8000)
    exchange = ','.join(exchanges)
    #test_of_endpoints_exchanges(exchange, limit=20)

    #order_metadata = test_of_simulation_order(get_create_order())
    #order_id = order_metadata['order']['order_id']
    #test_of_all_orders_statuses()

    scenarios = [
        #('KRAKEN', "BTC", "USD", "SELL", 0.001), no funds
        ('HITBTC', "ETH", "USD", "SELL", 0.01),
        ('HITBTC', "ETH", "USD", "BUY", 0.01),
        ("BITFINEX", "ETH", "EUR", "BUY", 0.01),
        ("BITFINEX", "ETH", "EUR", "SELL", 0.01),
        #("BITPANDA", "ETH", "EUR", "BUY", 0.01), no funds
        ("BITVAVO", "ETH", "EUR", "SELL", 0.01),
        ("BITVAVO", "ETH", "EUR", "BUY", 0.01),
        ("DIGIFINEX", "ETH", "USDT", "SELL", 3),
        ("DIGIFINEX", "ETH", "USDT", "BUY", 0.02),
    ]

    funds = test_of_position_exchange()
    for scenario in scenarios:
        order_metadata = test_of_real_order(get_create_order(exchange_list=[scenario[0]], base_currency=scenario[1], quote_currency=scenario[2], direction=scenario[3], quantity=scenario[4]))
        if order_metadata != {} and 'failed_reason' not in order_metadata:
            print(f'Succesful scenario {scenario}')
            order_id = order_metadata['order']['order_id']
            status = test_of_order_status(order_id)
            order_logs = test_of_order_logs(order_id)
        else:
            print(f'Order not executed for scenario {scenario}')

    #test_of_order_logs(order_id)
    #test_of_order_statuses()
    #test_of_position_exchange()
