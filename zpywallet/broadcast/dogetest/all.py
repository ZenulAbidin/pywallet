import asyncio
import binascii
import hashlib
from .fullnode import *


def tx_hash_dogetest(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest())

async def broadcast_transaction_dogetest(raw_transaction_hex: bytes, **kwargs):
    rpc_nodes = kwargs.get('rpc_nodes') or []
    raw_transaction_hex = raw_transaction_hex.decode()
    tasks = []

    for node in rpc_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_dogetest_full_node(raw_transaction_hex, **node)))
    
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        pass