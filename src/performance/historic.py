import threading

from metrics.order_volume import OrderVolume
from metrics.pnl import PnL

__algo_name = 'ALGO-BTC:EUR--BITFINEX:BINANCE'


def fill_historic():
    # Order volumes
    for interval in ["1h", "6h", "12h", "24h", "3d", "7d"]:
        for side in ["quote", "base"]:
            order_v = OrderVolume(__algo_name, interval=interval, side=side)
            order_v.insert_whole_historic()

    # Profit and Loss
    for interval in ["1h", "8h", "1d", "3d", "7d"]:
        order_v = PnL(__algo_name, interval=interval)
        order_v.insert_whole_historic()


if __name__ == '__main__':
    fill_historic()
