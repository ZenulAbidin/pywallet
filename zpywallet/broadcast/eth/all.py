import hashlib
from .blockcypher import *
from .etherscan import *
from .fullnode import *
from .mew import *

def broadcast_transaction_eth(raw_transaction_hex: bytes, rpc_nodes=[]):
    errors = []

    try:
        broadcast_transaction_eth_etherscan(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_eth_blockcypher(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_eth_etherscan(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    for node in rpc_nodes:
        try:
            broadcast_transaction_eth_generic(raw_transaction_hex.decode(), node)
        except NetworkException as e:
            errors.append(e)
            
    return hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest(), errors