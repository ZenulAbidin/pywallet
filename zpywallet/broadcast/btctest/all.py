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
from ...nodes.btctest import *

def tx_hash_btctest(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest())

async def broadcast_transaction_btctest(raw_transaction_hex, **kwargs):
    rpc_nodes = kwargs.get('rpc_nodes') or []
    esplora_nodes = kwargs.get('esplora_nodes') or []


    tasks = []

    tasks.append(asyncio.create_task(broadcast_transaction_btctest_bitaps(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btctest_blockchair(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btctest_blockcypher(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btctest_blockstream(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btctest_mempool_space(raw_transaction_hex)))
    for node in rpc_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_btctest_full_node(raw_transaction_hex, **node)))
    for node in btctest_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_btctest_full_node(raw_transaction_hex, **node)))
    for node in esplora_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_btctest_esplora(raw_transaction_hex, **node)))
    for node in btctest_esplora_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_btctest_esplora(raw_transaction_hex, **node)))
    
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        pass