from metrics.order_volume import OrderVolume

__algo_name = 'ALGO-BTC:EUR--BITFINEX:BINANCE'


def main_test():
    pass


def fill_historic_test():
    ovq_1h_q = OrderVolume(__algo_name, interval="1h", side="QUOTE")
    ovq_1h_q.insert_whole_historic()


if __name__ == '__main__':
    main_test()
    fill_historic_test()
