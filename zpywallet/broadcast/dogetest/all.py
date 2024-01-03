import hashlib
from .fullnode import *

def broadcast_transaction_dogetest(raw_transaction_hex: bytes, rpc_nodes=[]):
    errors = []
    for node in rpc_nodes:
        try:
            broadcast_transaction_dogetest_full_node(raw_transaction_hex.decode(), node['user'], node['pass'], node['host'], node['port'])
        except NetworkException as e:
            errors.append(e)

    return hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest(), errors