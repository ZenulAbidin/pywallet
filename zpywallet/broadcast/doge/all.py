import binascii
import hashlib
from .blockcypher import *
from .dogechain import *
from .fullnode import *


def tx_hash_doge(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest())

def broadcast_transaction_doge(raw_transaction_hex: bytes, rpc_nodes=[]):
    errors = []
    try:
        broadcast_transaction_doge_blockcypher(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_doge_dogechain(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    for node in rpc_nodes:
        try:
            broadcast_transaction_doge_full_node(raw_transaction_hex.decode(), node['user'], node['pass'], node['host'], node['port'])
        except NetworkException as e:
            errors.append(e)

    return errors