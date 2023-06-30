# -*- coding: utf-8 -*-
"""
This module contains the methods for creating a crypto wallet.
"""

from os import urandom
import base64

from .mnemonic import Mnemonic
from .utils.bip32 import (
    HDWallet
)

from .utils.keys import (
    PrivateKey
)

from .utils.aes import encrypt, decrypt
from .utils.utils import ensure_str

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


def create_wallet(mnemonic=None, network='BTC', children=10, strength=128):
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



def create_wallet_json(network='BTC', mnemonic=None, strength=128, children=10):
    """Generate a new wallet JSON from a mnemonic phrase, optionally randomly generated

    Args:
    :param mnemonic: The key to use to generate this wallet. It may be a long
        string. Do not use a phrase from a book or song, as that will
        be guessed and is not secure. My advice is to not supply this
        argument and let me generate a new random key for you.
    :param network: The network to create this wallet for
    Return:
        dict: A JSON wallet object with fields.
    
    Usage:
        w = create_wallet(network='BTC', children=1000)
    """

    net = HDWallet.get_network(network)

    if mnemonic is None:
        my_wallet = HDWallet.from_random(strength=strength, network=network)
        mnemonic = my_wallet.mnemonic_phrase
    else:
        my_wallet = HDWallet.from_mnemonic(mnemonic=mnemonic, network=network)


    wallet = {
        "coin": net.COIN,
        "seed": mnemonic,
        "private_key": "",
        "public_key": "",
        "xprivate_key": "",
        "xpublic_key": "",
        "address": "",
        "wif": "",
        "children": []
    }


    # account level
    wallet["private_key"] = my_wallet.private_key.to_hex()
    wallet["public_key"] = my_wallet.public_key.to_hex()

    have_private_base58 = True
    have_public_base58 = True

    try:
        wallet["xprivate_key"] = my_wallet.serialize_b58(private=True)
    except ValueError:
        have_private_base58 = False

    try:
        wallet["xpublic_key"] = my_wallet.serialize_b58(private=False)
    except ValueError:
        have_public_base58 = False

    wallet["address"] = my_wallet.address()
    if network != 'ethereum' and network.upper() != 'ETH':
        wallet["wif"] = ensure_str(my_wallet.private_key.to_wif())

    prime_child_wallet = my_wallet.get_child(0, is_prime=True)
    if have_private_base58:
        wallet["xpublic_key_prime"] = prime_child_wallet.serialize_b58(private=False)

    # prime children
    for child in range(children):
        data = {}
        child_wallet = my_wallet.get_child(child, is_prime=False, as_private=False)
        if have_public_base58:
            data["xpublic_key"] = child_wallet.serialize_b58(private=False)
        data["address"] = child_wallet.address()
        data["path"] = "m/" + str(child)
        if net.BIP32_PATH:
            data["bip32_path"] = net.BIP32_PATH + str(child_wallet.child_number)
        wallet["children"].append(data)

    return wallet

def create_keypair(network='BTC'):
    """Generates a random private/public keypair.

    Args:
    :param network: The network to create this wallet for

    Return:
        PrivateKey, PublicKey: a tuple of a private key and public key.
    
    Usage:
        w = create_wallet(network='BTC', children=10)
    """

    net = HDWallet.get_network(network)
    random_bytes = urandom(32)
    prv = PrivateKey(random_bytes, network=net)
    pub = prv.public_key
    return prv, pub

class Wallet:
    """Data class representing a cryptocurrency wallet."""

    def __init__(self, network, seed_phrase, receive_gap_limit, change_gap_limit, transaction_history, password):
        self.network = network
        self.receive_gap_limit = receive_gap_limit
        self.change_gap_limit = change_gap_limit
        self.transaction_history = transaction_history
        # We do not save the password. Instead, we are going to generate a base64-encrypted
        # serialization of this wallet file using the password.
        self.serialization = {}
        self.serialization["network"] = network # We will figure out how to serialize this later.
        self.serialization["seed_phrase"] = encrypt(seed_phrase, password) # AES-256-CBC encryption
        self.serialization["receive_gap_limit"] = receive_gap_limit
        self.serialization["change_gap_limit"] = change_gap_limit
        self.serialization["transaction_history"] = transaction_history #TODO serialize to JSON

