#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for address transaction, balance, and UTXO fetcher."""

# FIXME make these tests deterministic so that they always pass even without network connectivity.
# This would require mocking some of the HTTP endpoints.

import random
import time
import unittest

import requests
from zpywallet.address import (
    CryptoClient,
    BlockcypherClient,
    BlockstreamClient,
    MempoolSpaceClient,
)
from zpywallet.errors import NetworkException
from .mock.btc import BitcoinMainUnit
from .mock.server import gen_random_port, spawn_server, exit_server

import multiprocessing


class TestAddress(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        pass

    def tearDown(self):
        """Tear down test fixtures."""
        pass

    def test_000_btc_blockcypher_address(self):
        """Test fetching Bitcoin addresses with Blockcypher using mocked data."""
        port = gen_random_port()
        client = BlockcypherClient(
            [
                "3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V",
                "bc1plytzh6jqwltfq6l0ujt5ucz9csrlff4rfnxwmy3tkepkeyj3y2gskcf48c",
            ],
            coin="BTC",
            chain="main",
            base_url=f"http://localhost:{port}",
        )
        try:
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockcypherTXHistoryResponseManager, port],
            )
            server.start()
            tx_history = client.get_transaction_history()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                [t.SerializeToString() for t in tx_history],
                BitcoinMainUnit.BlockcypherExpectedTransactions,
            )

            # Each call for the utxo set or the balance also gets the transaction history.
            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockcypherTXHistoryResponseManager, port],
            )
            server.start()
            client.base_url = f"http://localhost:{port}"
            utxos = client.get_utxos()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                [t.SerializeToString() for t in utxos],
                BitcoinMainUnit.BlockcypherExpectedUTXOs,
            )

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockcypherTXHistoryResponseManager, port],
            )
            server.start()
            client.base_url = f"http://localhost:{port}"
            balance = client.get_balance()
            exit_server(port)
            server.terminate()
            self.assertEqual(balance, BitcoinMainUnit.BlockcypherExpectedBalance)

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockcypherHeightResponseManager, port],
            )
            server.start()
            client.base_url = f"http://localhost:{port}"
            block_height = client.get_block_height()
            exit_server(port)
            # server.terminate()   # handled below along with the failure case
            self.assertEqual(
                block_height, BitcoinMainUnit.BlockcypherExpectedBlockHeight
            )
        except NetworkException:
            self.fail(
                "NetworkException should not occur with a mock server. Is the port in use?"
            )
        finally:
            # This terminates the last server created whether there was an error or not.
            server.terminate()

    def test_001_btc_blockstream_address(self):
        """Test fetching Bitcoin addresses with Blockstream using mocked data."""
        port = gen_random_port()
        client = BlockstreamClient(
            [
                "3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V",
                "bc1plytzh6jqwltfq6l0ujt5ucz9csrlff4rfnxwmy3tkepkeyj3y2gskcf48c",
            ],
            coin="BTC",
            chain="main",
            base_url=f"http://localhost:{port}",
        )
        try:
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockstreamTXHistoryResponseManager, port],
            )
            server.start()
            tx_history = client.get_transaction_history()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                [t.SerializeToString() for t in tx_history],
                BitcoinMainUnit.BlockstreamExpectedTransactions,
            )

            # Each call for the utxo set or the balance also gets the transaction history.
            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockstreamTXHistoryResponseManager, port],
            )
            server.start()
            client.base_url = f"http://localhost:{port}"
            utxos = client.get_utxos()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                [t.SerializeToString() for t in utxos],
                BitcoinMainUnit.BlockstreamExpectedUTXOs,
            )

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockstreamTXHistoryResponseManager, port],
            )
            server.start()
            client.base_url = f"http://localhost:{port}"
            balance = client.get_balance()
            exit_server(port)
            server.terminate()
            self.assertEqual(balance, BitcoinMainUnit.BlockstreamExpectedBalance)

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockstreamHeightResponseManager, port],
            )
            server.start()
            client.base_url = f"http://localhost:{port}"
            block_height = client.get_block_height()
            exit_server(port)
            # server.terminate()   # handled below along with the failure case
            self.assertEqual(
                block_height, BitcoinMainUnit.BlockstreamExpectedBlockHeight
            )
        except NetworkException:
            self.fail(
                "NetworkException should not occur with a mock server. Is the port in use?"
            )
        finally:
            # This terminates the last server created whether there was an error or not.
            server.terminate()

    def test_002_btc_mempoolspace_address(self):
        """Test fetching Bitcoin addresses with MempoolSpace using mocked data."""
        port = gen_random_port()
        client = MempoolSpaceClient(
            [
                "3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V",
                "bc1plytzh6jqwltfq6l0ujt5ucz9csrlff4rfnxwmy3tkepkeyj3y2gskcf48c",
            ],
            coin="BTC",
            chain="main",
            base_url=f"http://localhost:{port}",
        )
        try:
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.MempoolSpaceTXHistoryResponseManager, port],
            )
            server.start()
            tx_history = client.get_transaction_history()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                [t.SerializeToString() for t in tx_history],
                BitcoinMainUnit.MempoolSpaceExpectedTransactions,
            )

            # Each call for the utxo set or the balance also gets the transaction history.
            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.MempoolSpaceTXHistoryResponseManager, port],
            )
            server.start()
            client.base_url = f"http://localhost:{port}"
            utxos = client.get_utxos()
            exit_server(port)
            server.terminate()
            self.assertEqual(
                [t.SerializeToString() for t in utxos],
                BitcoinMainUnit.MempoolSpaceExpectedUTXOs,
            )

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.MempoolSpaceTXHistoryResponseManager, port],
            )
            server.start()
            client.base_url = f"http://localhost:{port}"
            balance = client.get_balance()
            exit_server(port)
            server.terminate()
            self.assertEqual(balance, BitcoinMainUnit.MempoolSpaceExpectedBalance)

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.MempoolSpaceHeightResponseManager, port],
            )
            server.start()
            client.base_url = f"http://localhost:{port}"
            block_height = client.get_block_height()
            exit_server(port)
            # server.terminate()   # handled below along with the failure case
            self.assertEqual(
                block_height, BitcoinMainUnit.MempoolSpaceExpectedBlockHeight
            )
        except NetworkException:
            self.fail(
                "NetworkException should not occur with a mock server. Is the port in use?"
            )
        finally:
            # This terminates the last server created whether there was an error or not.
            server.terminate()

    def test_001_btctest_address(self):
        """Test fetching Bitcoin testnet addressses"""
        return
        b = CryptoClient(
            [
                "2NDNwoqdNvJ2jkBD8B6VVxNntpuKR4tkTSz",
                "tb1qtnl457a54cz5gq0zgyf4n2xt7n9uuqxzs8jwrp",
            ],
            coin="BTC",
            chain="TEST",
        )
        try:

            b.get_transaction_history()
            b.get_utxos()
            b.get_balance()
        except NetworkException:
            pass

    def test_002_dash_address(self):
        """Test fetching Dash addressses"""
        return
        b = CryptoClient(
            ["XbzLCqAv8rkYmky6uEsxibHRUbHZU2XCKg"], coin="DASH", chain="main"
        )
        try:

            b.get_transaction_history()
            b.get_utxos()
            b.get_balance()
        except NetworkException:
            pass

    def test_003_doge_address(self):
        """Test fetching Dogecoin addressses"""
        return
        b = CryptoClient(
            ["D8xCRT245ax9TJVDfYZ1ErLTMtG186S9rx"], coin="DOGE", chain="main"
        )
        try:

            b.get_transaction_history()
            b.get_utxos()
            b.get_balance()
        except NetworkException:
            pass

    def test_004_eth_address(self):
        """Test fetching Ethereum addressses"""
        return
        b = CryptoClient(
            ["0x383d4669f177182f2c8c90cecd291190ea04edad"], coin="ETH", chain="main"
        )
        try:

            # b.get_transaction_history()  # On EVM chains, this scans all blocks and takes forever.
            b.get_balance()
        except NetworkException:
            pass

    def test_005_ltc_address(self):
        """Test fetching Litecoin addressses"""
        return
        b = CryptoClient(
            ["ltc1q9pw48v23gq9d2lqcss8yaqeh7fqzu4wrt6m6nr"], coin="LTC", chain="main"
        )
        try:

            b.get_transaction_history()
            b.get_utxos()
            b.get_balance()
        except NetworkException:
            pass
