import asyncio
import binascii
import hashlib
from .blockcypher import *
from .dogechain import *
from .fullnode import *
from ...nodes.doge import *


def tx_hash_doge(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest())

async def broadcast_transaction_doge(raw_transaction_hex, **kwargs):
    rpc_nodes = kwargs.get('rpc_nodes') or []

    tasks = []

    tasks.append(asyncio.create_task(broadcast_transaction_doge_blockcypher(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_doge_dogechain(raw_transaction_hex)))
    for node in rpc_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_doge_full_node(raw_transaction_hex, **node)))
    for node in doge_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_doge_full_node(raw_transaction_hex, **node)))
    
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        pass