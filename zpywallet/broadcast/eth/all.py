import asyncio
import binascii
import hashlib
from .blockcypher import *
from .etherscan import *
from .fullnode import *
from .mew import *
from ...nodes.eth import *


def tx_hash_eth(raw_transaction_hex):
    return b"0x" + binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest())

async def broadcast_transaction_eth(raw_transaction_hex, **kwargs):
    rpc_nodes = kwargs.get('rpc_nodes') or []

    tasks = []

    tasks.append(asyncio.create_task(broadcast_transaction_eth_blockcypher(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_eth_mew(raw_transaction_hex)))
    for node in rpc_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_eth_generic(raw_transaction_hex, **node)))
    for node in eth_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_eth_generic(raw_transaction_hex, **node)))
    
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        pass