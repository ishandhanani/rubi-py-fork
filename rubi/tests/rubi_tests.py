import os
from _decimal import Decimal
from typing import Dict

import yaml
from web3 import Web3
from web3.contract import Contract

from rubi import Network, Client, RubiconMarket, RubiconRouter, ERC20


class TestNetwork:
    def test_init_from_yaml(self, test_network: Network, web3: Web3):
        path = f"{os.path.dirname(os.path.abspath(__file__))}/test_network_config"
        with open(f"{path}/test_config.yaml", 'r') as file:
            network_config = yaml.safe_load(file)

        network = Network(
            path=path,
            w3=web3,
            **network_config
        )

        assert network.name == test_network.name
        assert network.chain_id == test_network.chain_id
        assert network.rpc_url == test_network.rpc_url
        assert network.explorer_url == test_network.explorer_url
        assert network.currency == test_network.currency


class TestClient:
    def test_init(self, account_1: Dict, test_network: Network):
        client = Client(
            network=test_network,
            wallet=account_1['address'],
            key=account_1['key']
        )
        # Test client creation
        assert isinstance(client, Client)
        # Test if the wallet attribute is set correctly when a valid wallet address is provided.
        assert client.wallet == account_1["address"]
        # Test if the key attribute is set correctly when a key is provided.
        assert client.key == account_1['key']
        # Test if the market/router have correct types and are init
        assert isinstance(client.market, RubiconMarket)
        assert isinstance(client.router, RubiconRouter)
        # Test if the _pairs attribute is initialized as an empty dictionary.
        assert len(client._pairs.keys()) == 0
        # Test if the message_queue attribute is set to None when no queue is provided.
        assert client.message_queue is None

    def test_add_pair(self, test_client: Client, cow: Contract, eth: Contract):
        pair_name = "COW/ETH"

        test_client.add_pair(pair_name=pair_name)

        assert len(test_client.get_pairs_list()) == 1
        assert test_client.get_pairs_list()[0] == pair_name

        pair = test_client.get_pair(pair_name=pair_name)
        assert pair.base_asset.address == cow.address
        assert pair.quote_asset.address == eth.address

    def test_update_pair_allowance(
        self,
        rubicon_market: Contract,
        test_client_for_account_1: Client,
        cow_interface_for_account_1: ERC20,
        eth_interface_for_account_1: ERC20
    ):
        pair_name = "COW/ETH"

        initial_cow_allowance = cow_interface_for_account_1.allowance(
            owner=cow_interface_for_account_1.wallet,
            spender=rubicon_market.address
        )
        initial_eth_allowance = eth_interface_for_account_1.allowance(
            owner=eth_interface_for_account_1.wallet,
            spender=rubicon_market.address
        )

        # in fixtures these are initialized with the max approval value
        max_approval = 2 ** 256 - 1

        assert initial_cow_allowance == max_approval
        assert initial_eth_allowance == max_approval

        test_client_for_account_1.update_pair_allowance(
            pair_name=pair_name,
            new_base_asset_allowance=Decimal("12"),
            new_quote_asset_allowance=Decimal("100"),
        )

        new_cow_allowance = cow_interface_for_account_1.allowance(
            owner=cow_interface_for_account_1.wallet,
            spender=rubicon_market.address
        )
        new_eth_allowance = eth_interface_for_account_1.allowance(
            owner=eth_interface_for_account_1.wallet,
            spender=rubicon_market.address
        )

        assert new_cow_allowance != initial_cow_allowance
        assert new_cow_allowance == cow_interface_for_account_1.to_integer(Decimal("12"))

        assert new_eth_allowance != initial_eth_allowance
        assert new_eth_allowance == eth_interface_for_account_1.to_integer(Decimal("100"))

    def test_delete_pair(self, test_client_for_account_1: Client, cow: Contract, eth: Contract):
        pair_name = "COW/ETH"

        assert len(test_client_for_account_1.get_pairs_list()) == 1
        assert test_client_for_account_1.get_pairs_list()[0] == pair_name

        pair = test_client_for_account_1.get_pair(pair_name)
        assert pair.base_asset.address == cow.address
        assert pair.quote_asset.address == eth.address

        test_client_for_account_1.remove_pair(pair_name)

        assert len(test_client_for_account_1.get_pairs_list()) == 0