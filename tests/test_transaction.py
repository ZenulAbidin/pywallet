#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for creating signed transactions."""

"""We're going to have to do this the hard way and make up some utxos."""


import unittest
from zpywallet.address.btc import BitcoinAddress
from zpywallet.destination import Destination
from zpywallet.network import BitcoinMainNet
from zpywallet.transactions.encode import create_transaction
from zpywallet.utils.keys import PrivateKey, PublicKey
from zpywallet.utxo import UTXO
from zpywallet import Wallet
from zpywallet.nodes.btc import btc_nodes

class TestAddress(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_legacy_sign(self):
        """Test creating Satoshi-like legacy transactions."""
        # To make things clear, we will use fake UTXOs from this address,
        # derived from private key 0, which nobody can spend.
        # We will use a fake private key (1) since we do not need to broadcast
        # it anywhere, and that particular functionality has its own unit test.
        b = BitcoinAddress(['16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM'])
        b.sync()
        saved_utxos = b.get_utxos()
        destinations = [Destination(BitcoinMainNet, "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001, in_standard_units=True),
                        Destination(BitcoinMainNet, "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002, in_standard_units=True)]
        # The (1) private key has a sweeper attached to it so its balanace should always be zero.
        # Therefore, the wallet.create_transaction method should fail with not enough funds.
        #wallet = Wallet(BitcoinMainNet, None, "", receive_gap_limit=1)
        utxos = []
        for u in saved_utxos:
            _u = UTXO(None, None, _unsafe_internal_testing_only={'amount': u.amount})
            _u._output['amount'] = u.amount
            _u._output['address'] = u.address
            _u._output['height'] = u.height
            _u._output['confirmed'] = u.confirmed
            _u._output['txid'] = u.txid
            _u._output['index'] = u.index
            _u._output['private_key'] = PrivateKey.from_int(1).to_wif()
            _u._output['script_pubkey'] = PublicKey.script(u.address, BitcoinMainNet)
            utxos.append(_u)
        if len(utxos > 0):
            create_transaction(utxos, destinations, network=BitcoinMainNet, full_nodes=btc_nodes)