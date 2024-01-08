import asyncio
import binascii
import hashlib
from .bitaps import *
from .blockchair import *
from .blockcypher import *
from .blockstream import *
from .esplora import *
from .fullnode import *
from .mempool_space import *

def tx_hash_btctest(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest())

def broadcast_transaction_btctest(raw_transaction_hex: bytes, rpc_nodes=[], esplora_nodes=[]):
    raw_transaction_hex = raw_transaction_hex.decode()
    tasks = []

    tasks.append(asyncio.create_task(broadcast_transaction_btctest_bitaps(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btctest_blockchair(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btctest_blockcypher(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btctest_blockstream(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btctest_mempool_space(raw_transaction_hex)))
    for node in rpc_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_btctest_full_node(raw_transaction_hex, node)))
    for node in esplora_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_btctest_esplora(raw_transaction_hex, node)))
    
    asyncio.gather(*tasks, return_exceptions=True)