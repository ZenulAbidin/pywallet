import binascii
import hashlib
from .bitaps import *
from .blockchain_info import *
from .blockchair import *
from .blockcypher import *
from .blockstream import *
from .coinify import *
from .esplora import *
from .f2pool import *
from .fullnode import *
from .mempool_space import *
from .smartbit import *
from .viabtc import *

def tx_hash_btc(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest())

def broadcast_transaction_btc(raw_transaction_hex: bytes, rpc_nodes=[], esplora_nodes=[]):
    errors = []
    try:
        broadcast_transaction_btc_bitaps(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btc_blockchain_info(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btc_blockchair(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btc_blockcypher(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btc_blockstream(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)
    
    try:
        broadcast_transaction_btc_coinify(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btc_f2pool(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btc_mempool_space(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    try:
        broadcast_transaction_btc_smartbit(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)


    try:
        broadcast_transaction_btc_viabtc(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)

    for node in rpc_nodes:
        try:
            broadcast_transaction_btc_full_node(raw_transaction_hex.decode(), node['user'], node['pass'], node['host'], node['port'])
        except NetworkException as e:
            errors.append(e)
            
    for node in esplora_nodes:
        try:
            broadcast_transaction_btc_esplora(raw_transaction_hex.decode(), node['host'])
        except NetworkException as e:
            errors.append(e)

    return errors