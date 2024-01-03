import hashlib
from .bitaps import *
from .blockchair import *
from .blockcypher import *
from .blockstream import *
from .esplora import *
from .fullnode import *
from .mempool_space import *

def broadcast_transaction_btctest(raw_transaction_hex: bytes, rpc_nodes=[], esplora_nodes=[]):
    errors = []
    try:
        broadcast_transaction_btctest_bitaps(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btctest_blockchair(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btctest_blockcypher(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btctest_blockstream(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btctest_mempool_space(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    for node in rpc_nodes:
        try:
            broadcast_transaction_btctest_full_node(raw_transaction_hex.decode(), node['user'], node['pass'], node['host'], node['port'])
        except NetworkException as e:
            errors.append(e)
            
    for node in esplora_nodes:
        try:
            broadcast_transaction_btctest_esplora(raw_transaction_hex.decode(), node['host'])
        except NetworkException as e:
            errors.append(e)

    return hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest(), errors