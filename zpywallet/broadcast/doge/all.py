import asyncio
import binascii
import hashlib
from .blockcypher import *
from .dogechain import *
from .fullnode import *


def tx_hash_doge(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest())

async def broadcast_transaction_doge(raw_transaction_hex: bytes, rpc_nodes=[]):
    raw_transaction_hex = raw_transaction_hex.decode()
    tasks = []

    tasks.append(asyncio.create_task(broadcast_transaction_doge_blockcypher(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_doge_dogechain(raw_transaction_hex)))
    for node in rpc_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_doge_full_node(raw_transaction_hex, node)))
    
    await asyncio.gather(*tasks, return_exceptions=True)