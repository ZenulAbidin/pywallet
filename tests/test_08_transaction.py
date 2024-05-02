#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for creating signed transactions."""

import unittest
from zpywallet.address import CryptoClient
from zpywallet.destination import Destination
from zpywallet.network import (
    BitcoinMainNet,
    BitcoinP2PKMainNet,
    BitcoinSegwitMainNet,
    BitcoinTestNet,
    EthereumMainNet,
)
from zpywallet.transactions.encode import (
    SIGHASH_ALL,
    assemble_segwit_payload,
    create_signatures_legacy,
    create_signatures_segwit,
    create_transaction,
)
from zpywallet.utils.keys import PrivateKey, PublicKey
from zpywallet.utxo import UTXO
from zpywallet.nodes.btc import btc_nodes
from zpywallet.nodes.eth import eth_nodes
from zpywallet.transactions.decode import transaction_size_simple
from zpywallet.generated import wallet_pb2
from zpywallet.address.provider import AddressProvider


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
        # Segwit outputs are fine.
        tx = wallet_pb2.Transaction()
        tx.ParseFromString(
            b'\n@0000000000000000000000000000000000000000000000000000000000000000\x10\x8c\x9e\xfa\xaf\x06\x18\x01 \xc0\xa23(\x90N0\x01z\xc2\x02\x12s\n@ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff\x18\x80\xad\xe2\x04**bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4\x12m\n@ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff\x10\x02\x18\x80\xad\xe2\x04*"1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH\x1a(\x08\xa0\xc2\x1e\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a2\x08\xa0\xc2\x1e\x12*bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c\x18\x01'  # noqa: E501
        )

        provider = AddressProvider([], transactions=[tx])
        saved_utxos = provider.get_utxos()
        destinations = [
            Destination(
                "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001, BitcoinMainNet
            ),
            Destination(
                "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002, BitcoinMainNet
            ),
        ]
        # The (1) private key has a sweeper attached to it so its balanace should always be zero.
        # Therefore, the wallet.create_transaction method should fail with not enough funds.
        utxos = []
        for u in saved_utxos:
            _u = UTXO(None, None, _internal_param_do_not_use={"amount": u.amount})
            _u._output["amount"] = u.amount
            _u._output["address"] = u.address
            _u._output["height"] = u.height
            _u._output["confirmed"] = u.confirmed
            _u._output["txid"] = u.txid
            _u._output["index"] = u.index
            _u._output["private_key"] = PrivateKey.from_int(1)
            _u._output["script_pubkey"] = PublicKey.address_script(
                u.address, BitcoinMainNet
            )
            utxos.append(_u)
        if len(utxos) > 0:
            create_transaction(
                utxos, destinations, network=BitcoinMainNet, full_nodes=btc_nodes
            )

    def test_001_fake_segwit_sign(self):
        """Test creating Satoshi-like segwit transactions which have no segwit
        inputs, so f=alling back to legacy signing.
        """
        # To make things clear, we will use fake UTXOs from this address,
        # derived from private key 0, which nobody can spend.
        # We will use a fake private key (1) since we do not need to broadcast
        # it anywhere, and that particular functionality has its own unit test.
        # Segwit output addresses are fine
        tx = wallet_pb2.Transaction()
        tx.ParseFromString(
            b'\n@0000000000000000000000000000000000000000000000000000000000000000\x10\x8c\x9e\xfa\xaf\x06\x18\x01 \xc0\xa23(\x90N0\x01z\xc2\x02\x12s\n@ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff\x18\x80\xad\xe2\x04**bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4\x12m\n@ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff\x10\x02\x18\x80\xad\xe2\x04*"1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH\x1a(\x08\xa0\xc2\x1e\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a2\x08\xa0\xc2\x1e\x12*bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c\x18\x01'  # noqa: E501
        )

        provider = AddressProvider([], transactions=[tx])
        saved_utxos = provider.get_utxos()
        destinations = [
            Destination(
                "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001, BitcoinSegwitMainNet
            ),
            Destination(
                "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002, BitcoinSegwitMainNet
            ),
        ]
        # The (1) private key has a sweeper attached to it so its balanace should always be zero.
        # Therefore, the wallet.create_transaction method should fail with not enough funds.
        utxos = []
        for u in saved_utxos:
            _u = UTXO(None, None, _internal_param_do_not_use={"amount": u.amount})
            _u._output["amount"] = u.amount
            _u._output["address"] = u.address
            _u._output["height"] = u.height
            _u._output["confirmed"] = u.confirmed
            _u._output["txid"] = u.txid
            _u._output["index"] = u.index
            _u._output["private_key"] = PrivateKey.from_int(1)
            _u._output["script_pubkey"] = PublicKey.address_script(
                u.address, BitcoinSegwitMainNet
            )
            utxos.append(_u)
        if len(utxos) > 0:
            create_transaction(
                utxos, destinations, network=BitcoinSegwitMainNet, full_nodes=btc_nodes
            )

    def test_002_segwit_sign(self):
        """Test creating Satoshi-like segwit transactions, all segwit inputs."""
        # To make things clear, we will use fake UTXOs from this address,
        # derived from private key 0, which nobody can spend.
        # We will use a fake private key (1) since we do not need to broadcast
        # it anywhere, and that particular functionality has its own unit test.
        tx = wallet_pb2.Transaction()
        tx.ParseFromString(
            b'\n@0000000000000000000000000000000000000000000000000000000000000000\x10\x8c\x9e\xfa\xaf\x06\x18\x01 \xc0\xa23(\x90N0\x01z\xd3\x01\x12s\n@ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff\x18\x80\xad\xe2\x04**bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4\x1a(\x08\xa0\xc2\x1e\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a2\x08\xa0\xc2\x1e\x12*bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c\x18\x01'  # noqa: E501
        )

        provider = AddressProvider([], transactions=[tx])
        saved_utxos = provider.get_utxos()
        destinations = [
            Destination(
                "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001, BitcoinSegwitMainNet
            ),
            Destination(
                "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002, BitcoinSegwitMainNet
            ),
        ]
        # The (1) private key has a sweeper attached to it so its balanace should always be zero.
        # Therefore, the wallet.create_transaction method should fail with not enough funds
        utxos = []
        for u in saved_utxos:
            _u = UTXO(None, None, _internal_param_do_not_use={"amount": u.amount})
            _u._output["amount"] = u.amount
            _u._output["address"] = u.address
            _u._output["height"] = u.height
            _u._output["confirmed"] = u.confirmed
            _u._output["txid"] = u.txid
            _u._output["index"] = u.index
            _u._output["private_key"] = PrivateKey.from_int(1)
            _u._output["script_pubkey"] = PublicKey.address_script(
                u.address, BitcoinSegwitMainNet
            )
            utxos.append(_u)
        if len(utxos) > 0:
            create_transaction(
                utxos, destinations, network=BitcoinSegwitMainNet, full_nodes=btc_nodes
            )

    def test_003_segwit_sign_partial(self):
        """Test creating Satoshi-like segwit transactions, mixed segwit and legacy inputs."""
        # To make things clear, we will use fake UTXOs from this address,
        # derived from private key 0, which nobody can spend.
        # We will use a fake private key (1) since we do not need to broadcast
        # it anywhere, and that particular functionality has its own unit test.
        tx = wallet_pb2.Transaction()
        tx.ParseFromString(
            b'\n@0000000000000000000000000000000000000000000000000000000000000000\x10\x8c\x9e\xfa\xaf\x06\x18\x01 \xc0\xa23(\x90N0\x01z\xc2\x02\x12s\n@ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff\x18\x80\xad\xe2\x04**bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4\x12m\n@ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff\x10\x02\x18\x80\xad\xe2\x04*"1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH\x1a(\x08\xa0\xc2\x1e\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a2\x08\xa0\xc2\x1e\x12*bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c\x18\x01'  # noqa: E501
        )

        provider = AddressProvider([], transactions=[tx])
        saved_utxos = provider.get_utxos()
        destinations = [
            Destination(
                "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001, BitcoinSegwitMainNet
            ),
            Destination(
                "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002, BitcoinSegwitMainNet
            ),
        ]
        # The (1) private key has a sweeper attached to it so its balanace should always be zero.
        # Therefore, the wallet.create_transaction method should fail with not enough funds.
        utxos = []
        for u in saved_utxos:
            _u = UTXO(None, None, _internal_param_do_not_use={"amount": u.amount})
            _u._output["amount"] = u.amount
            _u._output["address"] = u.address
            _u._output["height"] = u.height
            _u._output["confirmed"] = u.confirmed
            _u._output["txid"] = u.txid
            _u._output["index"] = u.index
            _u._output["private_key"] = PrivateKey.from_int(1)
            _u._output["script_pubkey"] = PublicKey.address_script(
                u.address, BitcoinSegwitMainNet
            )
            utxos.append(_u)
        if len(utxos) > 0:
            create_transaction(
                utxos, destinations, network=BitcoinSegwitMainNet, full_nodes=btc_nodes
            )

    def test_004_sign_with_change(self):
        """Test creating Satoshi-like transactions with change calculation"""
        # To make things clear, we will use fake UTXOs from this address,
        # derived from private key 0, which nobody can spend.
        # We will use a fake private key (1) since we do not need to broadcast
        # it anywhere, and that particular functionality has its own unit test.
        tx = wallet_pb2.Transaction()
        tx.ParseFromString(
            b'\n@0000000000000000000000000000000000000000000000000000000000000000\x10\x8c\x9e\xfa\xaf\x06\x18\x01 \xc0\xa23(\x90N0\x01z\xcb\x01\x12k\n@ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff\x18\x80\xad\xe2\x04*"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a(\x08\xa0\xc2\x1e\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a2\x08\xa0\xc2\x1e\x12*bc1q34aq5drpuwy3wgl9lhup9892qp6svr8ldzyy7c\x18\x01'  # noqa: E501
        )

        provider = AddressProvider([], transactions=[tx])
        saved_utxos = provider.get_utxos()
        destinations = [
            Destination(
                "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM", 0.00000001, BitcoinSegwitMainNet
            ),
            Destination(
                "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", 0.00000002, BitcoinSegwitMainNet
            ),
        ]
        # The (1) private key has a sweeper attached to it so its balanace should always be zero.
        # Therefore, the wallet.create_transaction method should fail with not enough funds.
        utxos = []
        for u in saved_utxos:
            _u = UTXO(None, None, _internal_param_do_not_use={"amount": u.amount})
            _u._output["amount"] = u.amount
            _u._output["address"] = u.address
            _u._output["height"] = u.height
            _u._output["confirmed"] = u.confirmed
            _u._output["txid"] = u.txid
            _u._output["index"] = u.index
            _u._output["private_key"] = PrivateKey.from_int(1)
            _u._output["script_pubkey"] = PublicKey.address_script(
                u.address, BitcoinSegwitMainNet
            )
            utxos.append(_u)
        if len(utxos) > 0:
            temp_transaction = create_transaction(
                utxos, destinations, network=BitcoinSegwitMainNet, full_nodes=btc_nodes
            )
            fee_rate = 1
            size = transaction_size_simple(temp_transaction)
            total_inputs = sum([i.amount(in_standard_units=False) for i in utxos])
            total_outputs = sum(
                [o.amount(in_standard_units=False) for o in destinations]
            )
            if total_inputs < total_outputs + size * fee_rate:
                raise ValueError("Not enough balance for this transaction")
            change_value = total_inputs - total_outputs - size * fee_rate
            if change_value > 0:
                change = Destination(
                    "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM",
                    change_value / 1e8,
                    BitcoinSegwitMainNet,
                )
                destinations.append(change)
                create_transaction(
                    utxos,
                    destinations,
                    network=BitcoinSegwitMainNet,
                    full_nodes=btc_nodes,
                )

    def test_005_eth_sign(self):
        return
        """Test creating EVM Ethereum transactions"""
        b = CryptoClient(["0xd73e8e2ac0099169e7404f23c6caa94cf1884384"], coin="ETH")

        destinations = [
            Destination(
                "0xea83c649dd49a6ec44c9e2943eb673a8fbb7bab6",
                0.00000002,
                EthereumMainNet,
            )
        ]

        utxos = []
        _u = UTXO(None, None, _internal_param_do_not_use={"amount": b.get_balance()[0]})
        _u._output["address"] = "0xd73e8e2ac0099169e7404f23c6caa94cf1884384"
        _u._output["private_key"] = (
            "0x0000000000000000000000000000000000000000000000000000000000000001"
        )
        utxos.append(_u)
        # There seems to be a bug where the stock ETH nodes do not allow connections from inside the Github Actions runner or at least from Tox
        try:
            create_transaction(
                utxos,
                destinations,
                network=EthereumMainNet,
                full_nodes=eth_nodes,
                gas=1,
                gasPrice=1,
            )
        except RuntimeError as e:
            pass

    def test_006_internal_legacy_sign(self):
        # This test case tests the internal signing methods to make sure that
        # They can sign arbitrary raw transactions properly.
        utxos = []
        p1 = PrivateKey.from_wif(
            "cThjSL4HkRECuDxUTnfAmkXFBEg78cufVBy3ZfEhKoxZo6Q38R5L",
            BitcoinTestNet,
        )

        bytes_1 = bytes.fromhex("0100000001")
        bytes_2_inputs = []
        bytes_3 = bytes.fromhex(
            "014062b007000000001976a914f86f0bc0a2232970ccdf4569815db500f126836188ac"
        )
        bytes_2_inputs.append(
            [
                bytes.fromhex(
                    "5e2383defe7efcbdc9fdd6dba55da148b206617bbb49e6bb93fce7bfbb459d44"
                )[::-1]
                + bytes.fromhex("01000000"),
                bytes.fromhex("01"),
                bytes.fromhex("ffffffff"),
                p1.public_key.p2pkh_script(),
                p1,
                SIGHASH_ALL,
                p1.public_key.hash160(),
                None,
                BitcoinTestNet,
            ]
        )
        bytes_4 = bytes.fromhex("00000000")

        signed_transaction = create_signatures_legacy(
            bytes_1, bytes_2_inputs, bytes_3, bytes_4
        )
        correct_signed_transaction = "0100000001449d45bbbfe7fc93bbe649bb7b6106b248a15da5dbd6fdc9bdfc7efede83235e010000006b483045022100e15a8ead9013d1de55e71f195c9dc613483f07c8a0692a2144ffa90506436822022062bc9466b9e1941037fc23e1cfadf24c8833f96942beb8f4340df60d506f784b012103969a4ac9b1521cfae44a929a614193b0467a20e0a15973cae9ba1efb9627d830ffffffff014062b007000000001976a914f86f0bc0a2232970ccdf4569815db500f126836188ac00000000"
        print(signed_transaction)
        print(correct_signed_transaction)
        self.assertEqual(signed_transaction, correct_signed_transaction)

    def test_007_internal_segwit_sign(self):
        # This test case tests the internal signing methods to make sure that
        # They can sign arbitrary raw transactions properly.

        utxos = []
        p1 = PrivateKey.from_hex(
            "bbc27228ddcb9209d7fd6f36b02f7dfa6252af40bb2f1cbc7a557da8027ff866",
            BitcoinP2PKMainNet,
        )
        p2 = PrivateKey.from_hex(
            "619c335025c7f4012e556c2a58b2506e30b8511b53ade95ea316fd8c3286feb9",
            BitcoinSegwitMainNet,
        )
        utxos.append(
            UTXO(
                None,
                None,
                _network=BitcoinP2PKMainNet,
                _internal_param_do_not_use={
                    "txid": "fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f",
                    "index": 0,
                    "amount": 625000000,
                    "private_key": p1,
                    "address_hash": p1.public_key.hash160(),
                    "nsequence": "eeffffff",
                },
            )
        )
        utxos.append(
            UTXO(
                None,
                None,
                _network=BitcoinSegwitMainNet,
                _internal_param_do_not_use={
                    "txid": "ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a",
                    "index": 1,
                    "amount": 600000000,
                    "private_key": p2,
                    "address_hash": p2.public_key.hash160(),
                    "nsequence": "ffffffff",
                },
            )
        )

        bytes_1 = bytes.fromhex("01000000000102")
        bytes_2_inputs = []
        bytes_3 = bytes.fromhex(
            "02202cb206000000001976a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac9093510d000000001976a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac"
        )
        bytes_2_inputs.append(
            [
                bytes.fromhex(
                    "fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f00000000"
                ),
                bytes.fromhex("00"),
                bytes.fromhex("eeffffff"),
                p1.public_key.p2pk_script(),
                p1,
                SIGHASH_ALL,
                p1.public_key.hash160(),
                None,
                BitcoinP2PKMainNet,
            ]
        )
        bytes_2_inputs.append(
            [
                bytes.fromhex(
                    "ef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a01000000"
                ),
                bytes.fromhex("00"),
                bytes.fromhex("ffffffff"),
                p2.public_key.p2wpkh_script(),
                p2,
                SIGHASH_ALL,
                p1.public_key.hash160(),
                assemble_segwit_payload(
                    utxos[1],
                    utxos,
                    bytes.fromhex("ffffffff"),
                    bytes_3[1:],
                    "11000000",
                ),
                BitcoinSegwitMainNet,
            ]
        )
        bytes_4 = bytes.fromhex("11000000")

        signed_transaction = create_signatures_segwit(
            bytes_1, bytes_2_inputs, bytes_3, bytes_4
        )
        correct_signed_transaction = "01000000000102fff7f7881a8099afa6940d42d1e7f6362bec38171ea3edf433541db4e4ad969f00000000494830450221008b9d1dc26ba6a9cb62127b02742fa9d754cd3bebf337f7a55d114c8e5cdd30be022040529b194ba3f9281a99f2b1c0a19c0489bc22ede944ccf4ecbab4cc618ef3ed01eeffffffef51e1b804cc89d182d279655c3aa89e815b1b309fe287d9b2b55d57b90ec68a0100000000ffffffff02202cb206000000001976a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac9093510d000000001976a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac000247304402203609e17b84f6a7d30c80bfa610b5b4542f32a8a0d5447a12fb1366d7f01cc44a0220573a954c4518331561406f90300e8f3358f51928d43c212a8caed02de67eebee0121025476c2e83188368da1ff3e292e7acafcdb3566bb0ad253f62fc70f07aeee635711000000"
        print(signed_transaction)
        print(correct_signed_transaction)
        self.assertEqual(signed_transaction, correct_signed_transaction)
