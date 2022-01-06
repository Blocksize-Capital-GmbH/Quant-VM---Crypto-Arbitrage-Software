from typing import Dict, List

import requests

base_url = "https://api.kraken.com/0"


def get_order_book(base: str, quote: str, depth: int = 25):
    symbol = generate_symbol(base, quote)
    url = f"{base_url}/public/Depth"
    response = requests.get(url=url, params={"pair": symbol, "count": depth})
    if response.status_code != 200:
        return {
            'asks': [],
            'bids': []
        }
    order_book = parse_order_book_response_data(response.json())
    return order_book


def generate_symbol(base, quote):
    return f"{base}{quote}".upper()


def parse_order_book_response_data(raw_response):
    order_book: Dict[str, List] = {
        'asks': [],
        'bids': []
    }
    if raw_response["error"]:
        raise ValueError(f"Error fetching order book from Kraken {raw_response['error']}")

    raw_quotes = list(raw_response['result'].values())[0]

    order_book['asks'] = [quote[:2] for quote in raw_quotes['asks']]
    order_book['bids'] = [quote[:2] for quote in raw_quotes['bids']]

    return order_book
