import asyncio
import binascii
import hashlib
from .blockcypher import *
from .fullnode import *
from ...nodes.dash import *


def tx_hash_dash(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest())

async def broadcast_transaction_dash(raw_transaction_hex, **kwargs):
    rpc_nodes = kwargs.get('rpc_nodes') or []

    tasks = []

    tasks.append(asyncio.create_task(broadcast_transaction_dash_blockcypher(raw_transaction_hex)))
    for node in rpc_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_dash_full_node(raw_transaction_hex, **node)))
    for node in dash_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_dash_full_node(raw_transaction_hex, **node)))
    
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        pass