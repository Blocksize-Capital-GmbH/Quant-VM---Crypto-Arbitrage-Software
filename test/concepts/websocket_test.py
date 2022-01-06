import asyncio
import json
from websockets import connect


async def hello(uri):
    async with connect(uri, compression=None) as websocket:
        await websocket.send(json.dumps({'method': "subscribe", 'topic': "allMiniTickers", 'symbols': ["$all"]}))
        msg = await websocket.recv()
        msg_json = json.loads(msg)
        for item in msg_json['data']:
            symbol = item['s']
            print(symbol)

        #async with connect(uri, compression=None) as websocket:
        #    await websocket.send(json.dumps({'method': "subscribe", 'topic': "marketDepth", 'symbols': [symbol]}))
        #    msg = await websocket.recv()
        #    msg_json = json.loads(msg)
        #    print(f"Order book: {msg_json}")


if __name__ == '__main__':
    asyncio.run(hello("wss://dex.binance.org/api/ws"))
