#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for creating signed transactions."""

"""We're going to have to do this the hard way and make up some utxos."""


import unittest
from zpywallet.address.btc import BitcoinAddress
from zpywallet.destination import Destination
from zpywallet.network import BitcoinMainNet, BitcoinSegwitMainNet
from zpywallet.transactions.encode import create_transaction
from zpywallet.utils.keys import PrivateKey, PublicKey
from zpywallet.utxo import UTXO
from zpywallet import Wallet
from zpywallet.nodes.btc import btc_nodes
from zpywallet.transactions.decode import transaction_size_simple


b = BitcoinAddress(['16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM'])
bc = BitcoinAddress(['bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c'])
bc2 = BitcoinAddress(['16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM', 'bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c'])
b.sync()
bc.sync()
bc2.transactions = b.transactions + bc.transactions

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
        saved_utxos = b.get_utxos()
        destinations = [Destination(BitcoinMainNet, "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001),
                        Destination(BitcoinMainNet, "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002)]
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
        if len(utxos) > 0:
            create_transaction(utxos, destinations, network=BitcoinMainNet, full_nodes=btc_nodes)

    def test_001_fake_segwit_sign(self):
        """Test creating Satoshi-like segwit transactions which have no segwit inputs, so f=alling back to legacy signing."""
        # To make things clear, we will use fake UTXOs from this address,
        # derived from private key 0, which nobody can spend.
        # We will use a fake private key (1) since we do not need to broadcast
        # it anywhere, and that particular functionality has its own unit test.
        saved_utxos = b.get_utxos()
        destinations = [Destination(BitcoinSegwitMainNet, "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001),
                        Destination(BitcoinSegwitMainNet, "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002)]
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
            _u._output['script_pubkey'] = PublicKey.script(u.address, BitcoinSegwitMainNet)
            utxos.append(_u)
        if len(utxos) > 0:
            create_transaction(utxos, destinations, network=BitcoinSegwitMainNet, full_nodes=btc_nodes)

    def test_002_segwit_sign(self):
        """Test creating Satoshi-like segwit transactions, all segwit inputs."""
        # To make things clear, we will use fake UTXOs from this address,
        # derived from private key 0, which nobody can spend.
        # We will use a fake private key (1) since we do not need to broadcast
        # it anywhere, and that particular functionality has its own unit test.
        saved_utxos = bc.get_utxos()
        destinations = [Destination(BitcoinSegwitMainNet, "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001),
                        Destination(BitcoinSegwitMainNet, "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002)]
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
            _u._output['script_pubkey'] = PublicKey.script(u.address, BitcoinSegwitMainNet)
            utxos.append(_u)
        if len(utxos) > 0:
            create_transaction(utxos, destinations, network=BitcoinSegwitMainNet, full_nodes=btc_nodes)
    
    def test_003_segwit_sign_partial(self):
        """Test creating Satoshi-like segwit transactions, mixed segwit and legacy inputs."""
        # To make things clear, we will use fake UTXOs from this address,
        # derived from private key 0, which nobody can spend.
        # We will use a fake private key (1) since we do not need to broadcast
        # it anywhere, and that particular functionality has its own unit test.
        saved_utxos = bc2.get_utxos()
        destinations = [Destination(BitcoinSegwitMainNet, "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001),
                        Destination(BitcoinSegwitMainNet, "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002)]
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
            _u._output['script_pubkey'] = PublicKey.script(u.address, BitcoinSegwitMainNet)
            utxos.append(_u)
        if len(utxos) > 0:
            create_transaction(utxos, destinations, network=BitcoinSegwitMainNet, full_nodes=btc_nodes)

    def test_004_sign_with_change(self):
        """Test creating Satoshi-like transactions with change calculation"""
        # To make things clear, we will use fake UTXOs from this address,
        # derived from private key 0, which nobody can spend.
        # We will use a fake private key (1) since we do not need to broadcast
        # it anywhere, and that particular functionality has its own unit test.
        saved_utxos = bc2.get_utxos()
        destinations = [Destination(BitcoinSegwitMainNet, "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001),
                        Destination(BitcoinSegwitMainNet, "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002)]
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
            _u._output['script_pubkey'] = PublicKey.script(u.address, BitcoinSegwitMainNet)
            utxos.append(_u)
        if len(utxos) > 0:
            temp_transaction = create_transaction(utxos, destinations, network=BitcoinSegwitMainNet, full_nodes=btc_nodes)
            fee_rate = 1
            size = transaction_size_simple(temp_transaction)
            total_inputs = sum([i.amount(in_standard_units=False) for i in utxos])
            total_outputs = sum([o.amount(in_standard_units=False) for o in destinations])
            if total_inputs < total_outputs + size*fee_rate:
                raise ValueError("Not enough balance for this transaction")
            change_value = total_inputs - total_outputs - size*fee_rate
            if change_value > 0:
                change = Destination(BitcoinSegwitMainNet, '16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM', change_value / 1e8)
                destinations.append(change)
                create_transaction(utxos, destinations, network=BitcoinSegwitMainNet, full_nodes=btc_nodes)