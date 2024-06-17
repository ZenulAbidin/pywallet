#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for address transaction, balance, and UTXO fetcher."""

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
            # A race condition prevents us from immediately querying the local server.
            time.sleep(0.5)
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
            time.sleep(0.5)
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
            time.sleep(0.5)
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
            time.sleep(0.5)
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
        try:
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.BlockstreamTXHistoryResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client = BlockstreamClient(
                [
                    "3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V",
                    "bc1plytzh6jqwltfq6l0ujt5ucz9csrlff4rfnxwmy3tkepkeyj3y2gskcf48c",
                ],
                coin="BTC",
                chain="main",
                base_url=f"http://localhost:{port}",
            )
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
                args=[BitcoinMainUnit.BlockstreamUTXOResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client.endpoint = f"http://localhost:{port}"
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
                args=[BitcoinMainUnit.BlockstreamUTXOResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client.endpoint = f"http://localhost:{port}"
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
            time.sleep(0.5)
            client.endpoint = f"http://localhost:{port}"
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
        try:
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.MempoolSpaceTXHistoryResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client = MempoolSpaceClient(
                [
                    "3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V",
                    "bc1plytzh6jqwltfq6l0ujt5ucz9csrlff4rfnxwmy3tkepkeyj3y2gskcf48c",
                ],
                coin="BTC",
                chain="main",
                base_url=f"http://localhost:{port}",
            )
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
                args=[BitcoinMainUnit.MempoolSpaceUTXOResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client.endpoint = f"http://localhost:{port}"
            utxos = client.get_utxos()
            exit_server(port)
            server.terminate()
            with open("/tmp/outputproto", "w") as f:
                f.write(str([t.SerializeToString() for t in utxos]))
            self.assertEqual(
                [t.SerializeToString() for t in utxos],
                BitcoinMainUnit.MempoolSpaceExpectedUTXOs,
            )

            port = gen_random_port()
            server = multiprocessing.Process(
                target=spawn_server,
                args=[BitcoinMainUnit.MempoolSpaceUTXOResponseManager, port],
            )
            server.start()
            time.sleep(0.5)
            client.endpoint = f"http://localhost:{port}"
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
            time.sleep(0.5)
            client.endpoint = f"http://localhost:{port}"
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
