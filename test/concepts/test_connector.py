import binance
import bfxapi
import json
import asyncio
import krakenex
from pykrakenapi import KrakenAPI

settings_BTC = {
    'BASE': 'BTC',
    'QUOTE': 'EUR',
    'EXCHANGES': {
        'BINANCE': {
            'FEES': 10,  # in bps
            'THRESHOLD': 0
        },
        'BITFINEX': {
            'FEES': 20,  # in bps
            'THRESHOLD': 0
        },
    }
}


if __name__ == '__main__':
    # kraken
    api = krakenex.API()
    kraken_api = KrakenAPI(api)
    info = kraken_api.get_asset_info()
    print(info)
    info = kraken_api.get_tradable_asset_pairs()
    print(info)

    # bitfinex
    bfx = bfxapi.Client()
    info = asyncio.run(bfx.rest.get_public_tickers(["ALL"]))
    traded_info1 = [item[0][1:] for item in info]
    print(f"Bitfinex pairs: {traded_info1}")

    # binance
    client_binance = binance.Client()
    info = client_binance.get_exchange_info()
    traded_info2 = [symbol['baseAsset']+symbol['quoteAsset'] for symbol in info['symbols'] if symbol['status'] == 'TRADING']
    print(f"Binance pairs: {traded_info2}")

    # joint quotes
    joint_quotes = [item for item in traded_info1 if item not in traded_info2]
    print(f"Joint pairs {joint_quotes}")


