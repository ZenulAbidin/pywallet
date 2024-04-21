#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for address transaction, balance, and UTXO fetcher."""

import unittest
from zpywallet.address import CryptoClient
from zpywallet.errors import NetworkException


class TestAddress(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_btc_address(self):
        """Test fetching Bitcoin addresses."""
        b = CryptoClient(
            [
                "3KzZceAGsA7HRxFzgbZxVJMAV9TJa8o97V",
                "bc1plytzh6jqwltfq6l0ujt5ucz9csrlff4rfnxwmy3tkepkeyj3y2gskcf48c",
            ],
            coin="BTC",
            chain="main",
        )
        try:

            b.get_transaction_history()
            b.get_utxos()
            b.get_balance()
        except NetworkException:
            pass

    def test_001_btctest_address(self):
        """Test fetching Bitcoin testnet addressses"""
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
        b = CryptoClient(
            ["ltc1q9pw48v23gq9d2lqcss8yaqeh7fqzu4wrt6m6nr"], coin="LTC", chain="main"
        )
        try:

            b.get_transaction_history()
            b.get_utxos()
            b.get_balance()
        except NetworkException:
            pass
