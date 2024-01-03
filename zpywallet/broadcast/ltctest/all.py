import hashlib
from .blockchair import *
from .blockcypher import *
from .blockstream import *
from .fullnode import *

def broadcast_transaction_ltctest(raw_transaction_hex: bytes, rpc_nodes=[]):
    errors = []

    try:
        broadcast_transaction_ltctest_blockchair(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_ltctest_blockcypher(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_ltctest_blockstream(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    for node in rpc_nodes:
        try:
            broadcast_transaction_ltctest_full_node(raw_transaction_hex.decode(), node['user'], node['pass'], node['host'], node['port'])
        except NetworkException as e:
            errors.append(e)
            
    return hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest(), errors