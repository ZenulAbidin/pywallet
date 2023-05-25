# -*- coding: utf-8 -*-
"""
This module contains the methods for creating a crypto wallet.
"""

from datetime import datetime
import inspect
from .utils import (
    Wallet, HDPrivateKey, HDKey
)
from .utils.utils import ensure_str

def generate_mnemonic(strength=128):
    _, seed = HDPrivateKey.master_key_from_entropy(strength=strength)
    return seed


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


def create_address(network='btctest', xpub=None, child=None, path=0):
    """
    Creates a cryptocurrency address based on the provided parameters.

    Args:
        network (str): The network for which the address should be created. Defaults to 'btctest'.
        xpub (str): The extended public key used for address generation.
        child (int): The child ID to use for address generation. If not provided, a child ID will
            be generated using the `generate_child_id` method.
        path (int): The path value used in the address derivation. Defaults to 0.

    Returns:
        dict: A dictionary containing the generated address information, including the path, BIP32
            path, and address itself.

    Raises:
        AssertionError: If the `xpub` argument is not provided.

    Usage:
        address_info = create_address(network='btctest', xpub='xpub...', child=123)
    """
    assert xpub is not None

    if child is None:
        child = generate_child_id()

    if network == 'ethereum' or network.upper() == 'ETH':
        acct_pub_key = HDKey.from_b58check(xpub)

        keys = HDKey.from_path(acct_pub_key, f"{path}/{child}")
        #'{change}/{index}'.format(change=path, index=child))

        res = {
            "path": "m/" + str(acct_pub_key.index) + "/" + str(keys[-1].index),
            "bip32_path": "m/44'/60'/0'/" + str(acct_pub_key.index) + "/" + str(keys[-1].index),
            "address": keys[-1].address(mode='hex')
        }

        if inspect.stack()[1][3] == "create_wallet":
            res["xpublic_key"] = keys[-1].to_b58check()

        return res

    # else ...
    wallet_obj = Wallet.deserialize(xpub, network=network.upper())
    child_wallet = wallet_obj.get_child(child, is_prime=False)

    net = Wallet.get_network(network)

    return {
        "path": "m/" + str(wallet_obj.child_number) + "/" +str(child_wallet.child_number),
        "bip32_path": net.BIP32_PATH + str(wallet_obj.child_number) + "/" +
        str(child_wallet.child_number), "address": child_wallet.address(),
        # "xpublic_key": child_wallet.serialize_b58(private=False),
        # "wif": child_wallet.export_to_wif() # needs private key
    }


def create_wallet(mnemonic=None, network='BTC', children=10):
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
        mnemonic = generate_mnemonic()

    return Wallet.from_mnemonic(mnemonic=mnemonic, network=network)



def create_wallet_json(network='BTC', mnemonic=None, children=10):
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
    if mnemonic is None:
        mnemonic = generate_mnemonic()


    net = Wallet.get_network(network)
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

    if network == 'ethereum' or network.upper() == 'ETH':
        wallet["coin"] = "ETH"

        master_key = HDPrivateKey.master_key_from_mnemonic(mnemonic)
        root_keys = HDKey.from_path(master_key, "m/44'/0'/0'")

        acct_priv_key = root_keys[-1]
        acct_pub_key = acct_priv_key.public_key

        wallet["private_key"] = acct_priv_key.to_hex()
        wallet["public_key"] = acct_pub_key.to_hex()
        wallet["xprivate_key"] = acct_priv_key.to_b58check()
        wallet["xpublic_key"] = acct_pub_key.to_b58check()

        child_wallet = create_address(
            network=network.upper(), xpub=wallet["xpublic_key"],
            child=0, path=0)
        wallet["address"] = child_wallet["address"]
        wallet["xpublic_key_prime"] = child_wallet["xpublic_key"]

        # get public info from first prime child
        for child in range(children):
            child_wallet = create_address(
                network=network.upper(), xpub=wallet["xpublic_key"],
                child=child, path=0
            )
            wallet["children"].append({
                "address": child_wallet["address"],
                "xpublic_key": child_wallet["xpublic_key"],
                "path": "m/" + str(child),
                "bip32_path": "m/44'/60'/0'/" + str(child),
            })

    else:
        my_wallet = Wallet.from_mnemonic(
            network=network.upper(), mnemonic=mnemonic)

        # account level
        wallet["private_key"] = my_wallet.private_key.to_hex()
        wallet["public_key"] = my_wallet.public_key.to_hex()
        wallet["xprivate_key"] = my_wallet.serialize_b58(private=True)
        wallet["xpublic_key"] = my_wallet.serialize_b58(private=False)
        wallet["address"] = my_wallet.address()
        wallet["wif"] = ensure_str(my_wallet.private_key.export_to_wif())

        prime_child_wallet = my_wallet.get_child(0, is_prime=True)
        wallet["xpublic_key_prime"] = prime_child_wallet.serialize_b58(private=False)

        # prime children
        for child in range(children):
            child_wallet = my_wallet.get_child(child, is_prime=False, as_private=False)
            wallet["children"].append({
                "xpublic_key": child_wallet.serialize_b58(private=False),
                "address": child_wallet.address(),
                "path": "m/" + str(child),
                "bip32_path": net.BIP32_PATH + str(child_wallet.child_number),
            })

    return wallet
