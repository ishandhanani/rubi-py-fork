import logging as log
import os
from multiprocessing import Queue
from typing import Union

import requests
from dotenv import load_dotenv

from rubi import Client, OrderBook, OrderEvent, EmitOfferEvent

# load from env file
load_dotenv("../../local.env")

# you local.env should look like this:
# HTTP_NODE_URL={ the url of the node you are using to connect to the network }
# DEV_WALLET={ your wallet address 0x... }
# DEV_KEY={ your private key }

# set logging config
log.basicConfig(level=log.INFO)

# set the env variables
http_node_url = os.getenv("HTTP_NODE_URL")
wallet = os.getenv("DEV_WALLET")
key = os.getenv("DEV_KEY")


# Create order handler
def on_order(order: OrderEvent) -> None:
    """This is a simple order event handler that checks if the offer is an ETH offer, and if so get the current ETH
    price from Coinbase."""

    log.info(f"{order}")

    pair = client.get_pair(pair_name=order.pair_name)

    if pair.base_asset.symbol == "WETH":
        response = requests.get("https://api.coinbase.com/v2/prices/ETH-USD/spot")
        data = response.json()

        if response.status_code == 200:
            price = data["data"]["amount"]
            print(f"the current ETH price on coinbase is: {price}")
        else:
            raise Exception("Error: Unable to retrieve price")


# Create orderbook handler
def on_orderbook(orderbook: OrderBook) -> None:
    """Handle new orderbook"""
    log.info(orderbook)


# create a queue to receive messages
queue = Queue()

# create client
client = Client.from_http_node_url(
    http_node_url=http_node_url,
    custom_token_addresses_file="custom_token_addresses.yaml",
    wallet=wallet,
    key=key,
    message_queue=queue,
)

# add pair
client.add_pair(pair_name="WETH/USDC")

# start listening to offer events created by your wallet on the WETH/USDC market and the WETH/USDC orderbook
client.start_event_poller("WETH/USDC", event_type=EmitOfferEvent)
client.start_orderbook_poller("WETH/USDC")

while True:
    message: Union[OrderBook, OrderEvent] = queue.get(block=True)

    if isinstance(message, OrderBook):
        on_orderbook(orderbook=message)
    elif isinstance(message, OrderEvent):
        on_order(order=message)
    else:
        raise Exception("Unexpected message fetched from queue")
