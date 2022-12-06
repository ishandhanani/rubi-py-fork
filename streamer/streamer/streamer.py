import os
import asyncio
import websockets
import logging as log
from web3 import Web3
from rubi import Rubicon
from dotenv import load_dotenv

load_dotenv()

# set the environment variable
node_ws = os.getenv("NODE_WS")

# error handle if the environment variable is not set
if node_ws is None:
    log.error("NODE_WS environment variable is not set, you either need to modify or create a .env file")
    exit()

# create the web3 object 
w3 = Web3(Web3.WebsocketProvider(node_ws))

# create the rubicon object
rubi = Rubicon(w3)

# create the websocket server
async def wob_view():

    # establish the websocket connection
    async with websockets.connect(node_ws) as ws:

        # create a subscription to the rubicon market contract
        subscription = '{"id": 1, "method": "eth_subscribe", "params": ["logs", {"address": "' + rubi.market.address + '"}]}'
        await ws.send(subscription)
        market_subscription = await ws.recv()
        log.info("market subscription: " + market_subscription)

        while True: 

            # receive and parse the data
            data = await ws.recv()
            parsed = rubi.parse_market_events(data)

            if parsed: 
                book = rubi.get_book(parsed['pay_gem'], parsed['buy_gem'])
                status = book.stream_update(parsed)

                if status: 
                    print('processed event:', parsed['event'], 'order id:', parsed['id'])
                else: 
                    print('issue processing event:', parsed['event'], 'order id:', parsed['id'])

asyncio.get_event_loop().run_until_complete(wob_view())
    
