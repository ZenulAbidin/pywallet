import asyncio
import binascii
import hashlib
from .blockchair import *
from .blockcypher import *
from .blockstream import *
from .fullnode import *


def tx_hash_ltctest(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest())

async def broadcast_transaction_ltctest(raw_transaction_hex: bytes, **kwargs):
    rpc_nodes = kwargs.get('rpc_nodes') or []
    raw_transaction_hex = raw_transaction_hex.decode()
    tasks = []

    tasks.append(asyncio.create_task(broadcast_transaction_ltctest_blockchair(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_ltctest_blockcypher(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_ltctest_blockstream(raw_transaction_hex)))
    for node in rpc_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_ltctest_full_node(raw_transaction_hex, **node)))
    
    await asyncio.gather(*tasks, return_exceptions=True)