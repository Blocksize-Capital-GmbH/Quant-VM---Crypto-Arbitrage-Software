#!/usr/bin/python3
# -*- coding: utf-8 -*-

class Signal:
    """
    sell_exchange: str
    buy_exchange: str
    spread = 0.0
    volume = 0.0
    above_thresh = False
    execute = False
    """
    sell_exchange: str
    buy_exchange: str
    spread: float = None
    volume: float = None
    above_thresh = False
    execute = False

    sell_price: float = None
    buy_price: float = None

    def __repr__(self):
        return f"Signal(" \
               f"sell_exchange: {self.sell_exchange}, " \
               f"buy_exchange: {self.buy_exchange}, " \
               f"spread: {self.spread}, " \
               f"volume: {self.volume}, " \
               f"above_thresh: {self.above_thresh}, " \
               f"execute: {self.execute}, " \
               f"sell_price: {self.sell_price}, " \
               f"buy_price: {self.buy_price}" \
               f")"

    def __str__(self):
        return f"{{sell_exchange: {self.sell_exchange}, buy_exchange: {self.buy_exchange}, " \
               f"spread: {self.spread}, volume: {self.volume}, above_thresh: {self.above_thresh}, " \
               f"execute: {self.execute}, sell_price: {self.sell_price}, buy_price: {self.buy_price}}}"
