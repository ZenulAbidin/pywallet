#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from .utils import (
    Wallet, HDPrivateKey, HDKey
)
from .utils.utils import ensure_bytes, ensure_str
from .network import *
import inspect


def generate_mnemonic(strength=128):
    _, seed = HDPrivateKey.master_key_from_entropy(strength=strength)
    return seed


def generate_child_id():
    now = datetime.now()
    seconds_since_midnight = (now - now.replace(
        hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    return int((int(now.strftime(
        '%y%m%d')) + seconds_since_midnight*1000000) // 100)


def create_address(network='btctest', xpub=None, child=None, path=0):
    assert xpub is not None

    if child is None:
        child = generate_child_id()

    if network == 'ethereum' or network.upper() == 'ETH':
        acct_pub_key = HDKey.from_b58check(xpub)

        keys = HDKey.from_path(
            acct_pub_key, '{change}/{index}'.format(change=path, index=child))

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

    net = get_network(network)

    return {
        "path": "m/" + str(wallet_obj.child_number) + "/" +str(child_wallet.child_number),
        "bip32_path": net.BIP32_PATH + str(wallet_obj.child_number) + "/" +str(child_wallet.child_number),
        "address": child_wallet.to_address(),
        # "xpublic_key": child_wallet.serialize_b58(private=False),
        # "wif": child_wallet.export_to_wif() # needs private key
    }


def get_network(network='btctest'):
    network = network.lower()

    if network == "bitcoin_testnet" or network == "btctest":
        return BitcoinTestNet
    elif network == "bitcoin" or network == "btc":
        return BitcoinMainNet
    elif network == "dogecoin" or network == "doge":
        return DogecoinMainNet
    elif network == "dogecoin_testnet" or network == "dogetest":
        return DogecoinTestNet
    elif network == "litecoin" or network == "ltc":
        return LitecoinMainNet
    elif network == "litecoin_testnet" or network == "ltctest":
        return LitecoinTestNet
    elif network == "bitcoin_cash" or network == "bch":
        return BitcoinCashMainNet
    elif network == "bitcoin_gold" or network == "btg":
        return BitcoinGoldMainNet
    elif network == "dash":
        return DashMainNet
    elif network == "dash_testnet" or network == 'dashtest':
        return DashTestNet
    elif network == "martex" or network == "mxt":
        return MarteXMainNet
    elif network == "martex_testnet" or network == 'martextest':
        return MarteXTestNet
    elif network == 'omni':
        return OmniMainNet
    elif network == 'omni_testnet':
        return OmniTestNet
    elif network == "feathercoin" or network == 'ftc':
        return FeathercoinMainNet
    elif network == "qtum":
        return QtumMainNet
    elif network == "qtum_testnet" or network == "qtumtest":
        return QtumTestNet
    elif network == "raven" or network == "rvn":
        return RavenMainNet
    elif network == "raven_testnet" or network == "rvntest":
        return RavenTestNet
    elif network == "bitcore" or network == "btx":
        return BitcoreMainNet
    elif network == "bitcore_testnet" or network == "btxtest":
        return BitcoreTestNet

    return BitcoinTestNet

def create_wallet(mnemonic=None, network='BTC'):
    """Generate a new wallet class from a mnemonic phrase, optionally randomly generated

    Args:
    :param mnemonic: The key to use to generate this wallet. It may be a long
        string. Do not use a phrase from a book or song, as that will
        be guessed and is not secure. My advice is to not supply this
        argument and let me generate a new random key for you.
    :param network: The network to create this wallet for

    Return:
        Wallet: a wallet class
    """
    if mnemonic is None:
        mnemonic = generate_mnemonic()

    return Wallet.from_master_secret(mnemonic=mnemonic, network=network)



def create_wallet_json(network='BTC', mnemonic=None, children=1):
    """Generate a new wallet JSON from a mnemonic phrase, optionally randomly generated

    Args:
    :param mnemonic: The key to use to generate this wallet. It may be a long
        string. Do not use a phrase from a book or song, as that will
        be guessed and is not secure. My advice is to not supply this
        argument and let me generate a new random key for you.
    :param network: The network to create this wallet for

    Return:
        dict: A JSON wallet object with fields.
    """
    if mnemonic is None:
        mnemonic = generate_mnemonic()


    net = get_network(network)
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
        my_wallet = Wallet.from_master_secret(
            network=network.upper(), mnemonic=mnemonic)

        # account level
        wallet["private_key"] = my_wallet.private_key.to_hex()
        wallet["public_key"] = my_wallet.public_key.to_hex()
        wallet["xprivate_key"] = my_wallet.serialize_b58(private=True)
        wallet["xpublic_key"] = my_wallet.serialize_b58(private=False)
        wallet["address"] = my_wallet.to_address()
        wallet["wif"] = ensure_str(my_wallet.private_key.export_to_wif())

        prime_child_wallet = my_wallet.get_child(0, is_prime=True)
        wallet["xpublic_key_prime"] = prime_child_wallet.serialize_b58(private=False)

        # prime children
        for child in range(children):
            child_wallet = my_wallet.get_child(child, is_prime=False, as_private=False)
            wallet["children"].append({
                "xpublic_key": child_wallet.serialize_b58(private=False),
                "address": child_wallet.to_address(),
                "path": "m/" + str(child),
                "bip32_path": net.BIP32_PATH + str(child_wallet.child_number),
            })

    return wallet
