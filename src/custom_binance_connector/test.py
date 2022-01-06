from binance import Client

client = Client()

# get market depth

while True:
    depth = client.get_order_book(symbol='BTCEUR')
    print(depth["bids"][0], depth["asks"][0])
