#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import datetime
import src.client.test_sdk_client
from src.order_status.order_status import OrderStatus, order_sdk_tag, timeout_tag

if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    logger.addHandler(console)

    client_sdk = src.client.test_sdk_client.TestClient(logger)
    order_structure = client_sdk.place_order(client_sdk.BUY, "LINK", "BTC", 1, 0.001, 0, "BITPANDA")
    orders = OrderStatus(client=client_sdk, test=True, logger=logger)
    order_struct = {timeout_tag: datetime.datetime.now() + datetime.timedelta(seconds=1), order_sdk_tag: order_structure}
    asyncio.get_event_loop().run_until_complete(orders.enqueue_order(order_struct))
    asyncio.get_event_loop().run_until_complete(orders.resolve_orders())
