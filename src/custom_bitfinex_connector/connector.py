import requests


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
