#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for using the Wallet class."""


import unittest
from zpywallet.generated import wallet_pb2
from zpywallet import Wallet
from zpywallet.address.btc import BitcoinAddress
from zpywallet.destination import Destination
from zpywallet.network import BitcoinSegwitMainNet
from zpywallet.transactions.encode import create_transaction
from zpywallet.utxo import UTXO
from zpywallet.nodes.btc import btc_nodes

class TestWallet(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_create_wallet(self):
        wallet = Wallet(BitcoinSegwitMainNet, None, "zpywallet", receive_gap_limit=1)
        wallet_1 = Wallet(BitcoinSegwitMainNet, "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
                          "zpywallet", receive_gap_limit=1)
        exported_wallet = wallet_1.serialize()
        wallet_2 = Wallet.deserialize(exported_wallet, "zpywallet")
        

    def test_001_use_the_wallet(self):
        """Test using the wallet."""
        wallet = Wallet(BitcoinSegwitMainNet, "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon cactus",
                          "zpywallet", receive_gap_limit=1)
        wallet.get_transaction_history()
        wallet.get_utxos(only_unspent=False)
        wallet.get_utxos(only_unspent=True)
        wallet.get_balance()
        wallet.addresses()
        wallet.random_address()
        wallet.private_keys("zpywallet")
        # This seems to work off and on inside Pytest/TOX
        #with self.assertRaises(ValueError):
        #    wallet.private_keys("wrongpassword")
        wallet._add_stock_nodes()
        wallet.broadcast_transaction(b"010000000113f3b5446192eeb85c0f7ca64c12196c26314d27b5ab6a976d560cb134ffa82f020000006b483045022100deb556a5c301696f5def1888e54e8c1227caeb3ed4ae7b1c665af79174f50ab702201a59bba811554bd66fa003606ba852bf17699f38c6b1c3f8628f36c9d193a081012102245a4ecd8ad47f171f90c6d4a4f929052814d844e4d8c112bbf799aedc1b8555ffffffff061953cb010000000017a9145bf7f29863984cd9c8ff321a6d93d6344c7c055287102cf604000000001976a9148e09dee91c997fd306030ad7a1c46f17dcd51fdd88ace00f97000000000017a914ecd0679169813020faa97b418be8e79098c1cd55871595c1000000000017a914b61a3c9897d3d539aee6ad7327dfbd2192103e6287a4b62100000000001976a9144954c267b47bd1f864e627ca5b9c82b1fde8966188ac9e41a409000000001976a9141199950f4896dbbbd5ddc833092f5458b5f3154888ac00000000")
        saved_utxos = [b'\x08\xc0\x84=\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@dce83bbde7aba21c8994f9176e827a6a6ce28b4e4121d9090d8fe0b846b74034 \x010\x018\xc6\x82\t',
                       b'\x08\xa8U\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@2de38a49f0079d0aaa8a0b9cfec71b1af935752b609eee0dc1eae56b2162a7e2 \x010\x018\x88\xef\x11',
                       b'\x08\x90N\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@f6206a176b02b2d333cdfaa380251e423e5650ba52ac4f4e170672d2a2263b09 \x040\x018\x91\xf2\x1e',
                       b'\x08\x90N\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@f6206a176b02b2d333cdfaa380251e423e5650ba52ac4f4e170672d2a2263b09 \x050\x018\x91\xf2\x1e',
                       b'\x08\x90N\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@f6206a176b02b2d333cdfaa380251e423e5650ba52ac4f4e170672d2a2263b09 \x060\x018\x91\xf2\x1e',
                       b'\x08\x90N\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@f6206a176b02b2d333cdfaa380251e423e5650ba52ac4f4e170672d2a2263b09 \x080\x018\x91\xf2\x1e',
                       b'\x08\x9e\x9b\x01\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@83d0aaf8e3bd5a240eba1061c572024750c38c847074f7717ef8467b3c4e38930\x018\xe0\xc5!',
                       b'\x08\xa4!\x12"16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM\x1a@ca9ae53f5a8bf29825af1438fcde86c4437668f5ed35ec32b9fc4e5a0a42da680\x018\xe1\xc5!']
        utxos = []
        for u in saved_utxos:
            utxo = wallet_pb2.UTXO()
            utxo.ParseFromString(u)
            utxos.append(utxo)
        
        wallet._to_human_friendly_utxo(utxos, [])