import asyncio
import binascii
import hashlib
from .blockcypher import broadcast_transaction_doge_blockcypher
from .dogechain import broadcast_transaction_doge_dogechain
from .fullnode import broadcast_transaction_doge_full_node
from ...nodes.doge import doge_nodes


def tx_hash_doge(raw_transaction_hex):
    """Calculate the hash of a Dogecoin transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    return binascii.hexlify(
        hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest()
    )


async def broadcast_transaction_doge(raw_transaction_hex, **kwargs):
    """Broadcast a Dogecoin transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    rpc_nodes = kwargs.get("rpc_nodes") or []

    tasks = []

    tasks.append(
        asyncio.create_task(broadcast_transaction_doge_blockcypher(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(broadcast_transaction_doge_dogechain(raw_transaction_hex))
    )
    for node in rpc_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_doge_full_node(raw_transaction_hex, **node)
            )
        )
    for node in doge_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_doge_full_node(raw_transaction_hex, **node)
            )
        )

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        pass
