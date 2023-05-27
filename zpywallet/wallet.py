# -*- coding: utf-8 -*-
"""
This module contains the methods for creating a crypto wallet.
"""

from datetime import datetime
from .utils import (
    Wallet
)
from .utils.utils import ensure_str


def generate_child_id():
    """
    Generates a child ID based on the current timestamp and returns it as an integer.

    The child ID is calculated by combining the current date and the number of seconds
    since midnight, scaled to fit within the range of an integer.

    Returns:
        int: The generated child ID.

    Usage:
        child_id = generate_child_id()
    """
    now = datetime.now()
    seconds_since_midnight = (now - now.replace(
        hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    return int((int(now.strftime(
        '%y%m%d')) + seconds_since_midnight*1000000) // 100)


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
        Wallet: a wallet class
    
    Usage:
        w = create_wallet(network='BTC', children=10)
    """
    if mnemonic is None:
        return Wallet.from_random(strength=strength, network=network)
    else:
        return Wallet.from_mnemonic(mnemonic=mnemonic, network=network)



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

    net = Wallet.get_network(network)
    
    if mnemonic is None:
        my_wallet = Wallet.from_random(strength=strength, network=network)
        mnemonic = my_wallet.mnemonic_phrase
    else:
        my_wallet = Wallet.from_mnemonic(mnemonic=mnemonic, network=network)


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
