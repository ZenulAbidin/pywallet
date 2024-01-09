# -*- coding: utf-8 -*-
"""
This module contains the methods for creating a crypto wallet.
"""

from os import urandom
from functools import reduce

from .mnemonic import Mnemonic
from .utils.bip32 import (
    HDWallet
)

from .utils.keys import (
    PrivateKey
)

from .generated import wallet_pb2

from .network import (
    BitcoinSegwitMainNet,
    BitcoinMainNet,
    BitcoinSegwitTestNet,
    BitcoinTestNet,
    LitecoinSegwitMainNet,
    LitecoinMainNet,
    LitecoinBTCSegwitMainNet,
    LitecoinBTCMainNet,
    LitecoinSegwitTestNet,
    LitecoinTestNet,
    EthereumMainNet,
    DogecoinMainNet,
    DogecoinBTCMainNet,
    DogecoinTestNet,
    DashMainNet,
    DashInvertedTestNet,
    DashBTCMainNet,
    DashTestNet,
    DashInvertedMainNet,
    BitcoinCashMainNet,
    BlockcypherTestNet
)

from .address.bcy.loadbalancer import BCYAddress
from .address.btc.loadbalancer import BitcoinAddress
from .address.btctest.loadbalancer import BitcoinTestAddress
from .address.dash.loadbalancer import DashAddress
from .address.doge.loadbalancer import DogecoinAddress
from .address.eth.loadbalancer import EthereumAddress
from .address.ltc.loadbalancer import LitecoinAddress

from .utils.aes import encrypt

def generate_mnemonic(strength=128):
    """Creates a new seed phrase of the specified length"""
    if strength % 32 != 0:
        raise ValueError("strength must be a multiple of 32")
    if strength < 128 or strength > 256:
        raise ValueError("strength should be >= 128 and <= 256")
    entropy = urandom(strength // 8)
    mne = Mnemonic(language='english')
    mnemonic = mne.to_mnemonic(entropy)
    return mnemonic


def create_wallet(mnemonic=None, network=BitcoinSegwitMainNet, strength=128):
    """Generate a new wallet class from a mnemonic phrase, optionally randomly generated

    Args:
    :param mnemonic: The key to use to generate this wallet. It may be a long
        string. Do not use a phrase from a book or song, as that will
        be guessed and is not secure. My advice is to not supply this
        argument and let me generate a new random key for you.
    :param network: The network to create this wallet for
    :param children: Create this many child addresses for this wallet. Default
        is 10, You should not use the master private key itself for sending
        or receiving funds, as a best practice.

    Return:
        HDWallet: a wallet class
    
    Usage:
        w = create_wallet(network='BTC', children=10)
    """
    if mnemonic is None:
        return HDWallet.from_random(strength=strength, network=network)
    else:
        return HDWallet.from_mnemonic(mnemonic=mnemonic, network=network)


def create_keypair(network=BitcoinSegwitMainNet):
    """Generates a random private/public keypair.

    Args:
    :param network: The network to create this wallet for

    Return:
        PrivateKey, PublicKey: a tuple of a private key and public key.
    
    Usage:
        w = create_wallet(network='BTC', children=10)
    """

    random_bytes = urandom(32)
    prv = PrivateKey(random_bytes, network=network)
    pub = prv.public_key
    return prv, pub

class Wallet:
    """Data class representing a cryptocurrency wallet."""

    def __init__(self, network, seed_phrase, receive_gap_limit, change_gap_limit, password,
                providers, transactions=None, esplora_endpoints=None, fullnode_endpoints=None,
                blockcypher_token=None, alchemy_token=None, getblock_token=None, infura_token=None,
                quicknode_name: str = None, quicknode_token: str = None, max_cycles=100):
        
        self.wallet = wallet_pb2.Wallet()
        self.wallet.receive_gap_limit = receive_gap_limit
        self.wallet.change_gap_limit = change_gap_limit
        self.wallet.height = 0
        
        # We do not save the password. Instead, we are going to generate a base64-encrypted
        # serialization of this wallet file using the password.
        self.wallet.encrypted_seed_phrase = encrypt(seed_phrase, password) # AES-256-CBC encryption

        # Generate addresses and keys
        addresses = []

        providers = reduce(lambda x, y: x | y, providers)
        self.wallet.crypto_providers = providers

        hdwallet = HDWallet.from_mnemonic(mnemonic=seed_phrase, network=network)

        # Set properties
        if network == BitcoinSegwitMainNet:
            self.wallet.network = wallet_pb2.BITCOIN_SEGWIT_MAINNET
        elif network == BitcoinMainNet:
            self.wallet.network = wallet_pb2.BITCOIN_MAINNET
        elif network == BitcoinSegwitTestNet:
            self.wallet.network = wallet_pb2.BITCOIN_SEGWIT_TESTNET
        elif network == BitcoinTestNet:
            self.wallet.network = wallet_pb2.BITCOIN_TESTNET
        elif network == LitecoinSegwitMainNet:
            self.wallet.network = wallet_pb2.LITECOIN_SEGWIT_MAINNET
        elif network == LitecoinMainNet:
            self.wallet.network = wallet_pb2.LITECOIN_MAINNET
        elif network == LitecoinBTCSegwitMainNet:
            self.wallet.network = wallet_pb2.LITECOIN_BTC_SEGWIT_MAINNET
        elif network == LitecoinBTCMainNet:
            self.wallet.network = wallet_pb2.LITECOIN_BTC_MAINNET
        elif network == LitecoinSegwitTestNet:
            self.wallet.network = wallet_pb2.LITECOIN_SEGWIT_TESTNET
        elif network == LitecoinTestNet:
            self.wallet.network = wallet_pb2.LITECOIN_TESTNET
        elif network == EthereumMainNet:
            self.wallet.network = wallet_pb2.ETHEREUM_MAINNET
        elif network == DogecoinMainNet:
            self.wallet.network = wallet_pb2.DOGECOIN_MAINNET
        elif network == DogecoinBTCMainNet:
            self.wallet.network = wallet_pb2.DOGECOIN_BTC_MAINNET
        elif network == DogecoinTestNet:
            self.wallet.network = wallet_pb2.DOGECOIN_TESTNET
        elif network == DashMainNet:
            self.wallet.network = wallet_pb2.DASH_MAINNET
        elif network == DashInvertedMainNet:
            self.wallet.network = wallet_pb2.DASH_INVERTED_MAINNET
        elif network == DashBTCMainNet:
            self.wallet.network = wallet_pb2.DASH_BTC_MAINNET
        elif network == DashTestNet:
            self.wallet.network = wallet_pb2.DASH_TESTNET
        elif network == DashInvertedTestNet:
            self.wallet.network = wallet_pb2.DASH_INVERTED_TESTNET
        elif network == BitcoinCashMainNet:
            self.wallet.network = wallet_pb2.BITCOIN_CASH_MAINNET
        elif network == BlockcypherTestNet:
            self.wallet.network = wallet_pb2.BLOCKCYPHER_TESTNET
        else:
            raise ValueError("Unkown network")

        if fullnode_endpoints is not None:
            self.wallet.fullnode_endpoints.extend(fullnode_endpoints)

        if esplora_endpoints is not None:
            self.wallet.esplora_endpoints.extend(fullnode_endpoints)

        if blockcypher_token is not None:
            self.wallet.blockcypher_token = blockcypher_token
        if alchemy_token is not None:
            self.wallet.alchemy_token = alchemy_token
        if getblock_token is not None:
            self.wallet.getblock_token = getblock_token
        if infura_token is not None:
            self.wallet.infura_token = infura_token
        if quicknode_name is not None:
            # Nested if, to avoid lint errors.
            # Don't compact unless pylint-protobuf is updated with this.
            if quicknode_token is not None:
                self.wallet.quicknode_name = quicknode_name
                self.wallet.quicknode_token = quicknode_token

        for i in range(0, receive_gap_limit):
            privkey = hdwallet.get_child_for_path(f"{network.BIP32_PATH}0/{i}").private_key
            pubkey = privkey.public_key

            # Add an Address
            address = self.wallet.addresses.add()
            address.address = pubkey.address()
            address.pubkey = pubkey.to_hex()
            address.privkey = privkey.to_wif()

        for i in range(0, change_gap_limit):
            privkey = hdwallet.get_child_for_path(f"{network.BIP32_PATH}1/{i}").private_key
            pubkey = privkey.public_key
            
            # Add an Address
            address = self.wallet.addresses.add()
            address.address = pubkey.address()
            address.pubkey = pubkey.to_hex()
            address.privkey = privkey.to_wif()
            

        if network == BlockcypherTestNet:
            address_client = BCYAddress(providers, addresses, transactions=transactions,
                                              blockcypher_token=blockcypher_token,
                                              max_cycles=max_cycles
                                              )
        elif network == BitcoinSegwitMainNet or network == BitcoinMainNet:
            address_client = BitcoinAddress(providers, addresses, transactions=transactions,
                                              esplora_endpoints=esplora_endpoints,
                                              fullnode_endpoints=fullnode_endpoints,
                                              blockcypher_token=blockcypher_token,
                                              max_cycles=max_cycles
                                              )
        elif network == BitcoinSegwitTestNet or network == BitcoinTestNet:
            address_client = BitcoinTestAddress(providers, addresses, transactions=transactions,
                                              esplora_endpoints=esplora_endpoints,
                                              fullnode_endpoints=fullnode_endpoints,
                                              blockcypher_token=blockcypher_token,
                                              max_cycles=max_cycles
                                              )
        elif network == LitecoinSegwitMainNet or network == LitecoinMainNet or \
                network == LitecoinBTCSegwitMainNet or network == LitecoinBTCMainNet:
            address_client = LitecoinAddress(providers, addresses, transactions=transactions,
                                              fullnode_endpoints=fullnode_endpoints,
                                              blockcypher_token=blockcypher_token,
                                              max_cycles=max_cycles
                                              )
        elif network == DogecoinMainNet or network == DogecoinBTCMainNet:
            address_client = DogecoinAddress(providers, addresses, transactions=transactions,
                                              blockcypher_token=blockcypher_token,
                                              max_cycles=max_cycles
                                              )
        elif network == DashMainNet or network == DashInvertedMainNet or \
                network == DashBTCMainNet:
            address_client = DashAddress(providers, addresses, transactions=transactions,
                                              fullnode_endpoints=fullnode_endpoints,
                                              blockcypher_token=blockcypher_token,
                                              max_cycles=max_cycles
                                              )
        elif network == EthereumMainNet:
            address_client = EthereumAddress(providers, addresses, transactions=transactions,
                                              fullnode_endpoints=fullnode_endpoints,
                                              alchemy_token=alchemy_token,
                                              getblock_token=getblock_token,
                                              infura_token=infura_token,
                                              quicknode_name=quicknode_name,
                                              quicknode_token=quicknode_token,
                                              max_cycles=max_cycles)
        else:
            raise ValueError("No address client for this network")

        for tx in address_client.transactions:
            transaction = self.wallet.transactions.add()
            transaction.CopyFrom(tx)
