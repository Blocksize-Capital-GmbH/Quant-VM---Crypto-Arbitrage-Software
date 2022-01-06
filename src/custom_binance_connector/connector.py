from binance import Client

client = Client()


def get_order_book(base, quote):
    symbol = generate_symbol(base, quote)
    depth = client.get_order_book(symbol=symbol)
    order_book = {
        'bids': depth['bids'],
        'asks': depth['asks'],
    }
    return order_book


def generate_symbol(base, quote):
    return f"{base}{quote}"
