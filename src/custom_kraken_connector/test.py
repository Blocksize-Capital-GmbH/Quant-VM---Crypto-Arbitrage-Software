import time

import requests
from dotenv import load_dotenv

load_dotenv()

base_url = 'https://api-pub.bitfinex.com/v2/'


def get_order_book(base, quote, depth: int = 25):
    symbol = generate_symbol(base, quote)
    url = f"{base_url}book/{symbol}/R0"
    response = requests.get(url=url, params={"len": depth})
    order_book = parse_order_book_response_data(response.json())
    return order_book


def generate_symbol(base, quote):
    return f"t{base}{quote}"


def parse_order_book_response_data(raw_quotes):
    order_book = {
        'asks': [],
        'bids': []
    }
    for quote in raw_quotes:
        # if volume is negative it's the ask side
        if quote[2] < 0:
            order_book["asks"].append([quote[1], abs(quote[2])])
        elif quote[2] > 0:
            order_book["bids"].append([quote[1], abs(quote[2])])
        else:
            raise ValueError("couldn't parse Bitfinex order book.")

    order_book['asks'] = sorted(order_book['asks'], key=lambda x: x[0])
    order_book['bids'] = list(reversed(sorted(order_book['bids'], key=lambda x: x[0])))

    return order_book


def test_run_order_books():
    base = "BTC"
    quote = "EUR"
    while True:
        order_book = get_order_book(base, quote)
        print(order_book)
        time.sleep(1)


def find_average_price(order_book_side, needed_quantity):
    agg_quantity = 0
    vwap = 0
    for price, amount in order_book_side:
        price = float(price)
        amount = float(amount)
        remaining_quantity = needed_quantity - agg_quantity
        if agg_quantity >= needed_quantity:
            break
        if amount < remaining_quantity:
            take_amount = amount
        else:
            take_amount = remaining_quantity
        agg_quantity += take_amount
        vwap += take_amount * float(price)
    return vwap / needed_quantity


if __name__ == '__main__':
    pass
    test_run_order_books()
    # _base = "BTC"
    # _quote = "EUR"
    #
    # book = get_order_book(base=_base, quote=_quote)
