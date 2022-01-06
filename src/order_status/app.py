#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask import Flask, request
import logging
import asyncio
import websockets
import src.order_status.order_status

logging.basicConfig(level=logging.INFO)
app = Flask("OrderStatus")


@app.route("/",  methods=['GET'])
def default():
    logger.info("Connected to / handler")
    return "The server is alive\n"


@app.route("/enqueue_order",  methods=['POST', 'PUT'])
async def enqueue_order(order_struct):
    logger.info("Order to process")
    return await order_status_instance.enqueue_order(order_struct)


@app.route("/cancel_order",  methods=['POST', 'PUT'])
async def cancel_order(order_id):
    logger.info("Order to process")
    return await order_status_instance.cancel_order(order_id)


async def server(websocket, path):
    # Get received data from websocket
    data = await websocket.recv()

    # Send response back to client to acknowledge receiving message
    print(f"Message {data} received")
    await websocket.send("Thanks for your message: " + data)


order_status_instance = src.order_status.order_status.OrderStatus()

if __name__ == '__main__':
    logger = logging.getLogger("Server")

    # Create websocket server
    start_server = websockets.serve(server, "localhost", 8081)

    # Start and run websocket server forever
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

    #app.run('0.0.0.0', port=8080, debug=False, threaded=True)
