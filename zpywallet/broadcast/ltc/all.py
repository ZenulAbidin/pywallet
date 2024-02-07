import asyncio
import binascii
import hashlib
from .blockchair import broadcast_transaction_ltc_blockchair
from .blockcypher import broadcast_transaction_ltc_blockcypher
from .blockstream import broadcast_transaction_ltc_blockstream
from .fullnode import broadcast_transaction_ltc_full_node
from ...nodes.ltc import ltc_nodes


def tx_hash_ltc(raw_transaction_hex):
    return binascii.hexlify(
        hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest()
    )


async def broadcast_transaction_ltc(raw_transaction_hex, **kwargs):
    rpc_nodes = kwargs.get("rpc_nodes") or []

    tasks = []

    tasks.append(
        asyncio.create_task(broadcast_transaction_ltc_blockchair(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(broadcast_transaction_ltc_blockcypher(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(broadcast_transaction_ltc_blockstream(raw_transaction_hex))
    )
    for node in rpc_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_ltc_full_node(raw_transaction_hex, **node)
            )
        )
    for node in ltc_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_ltc_full_node(raw_transaction_hex, **node)
            )
        )

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        pass
