import asyncio
import binascii
import hashlib
from .blockchair import broadcast_transaction_ltc_blockchair
from .blockcypher import broadcast_transaction_ltc_blockcypher
from .fullnode import broadcast_transaction_ltc_full_node
from ...nodes.ltc import ltc_nodes


def tx_hash_ltc(raw_transaction_hex):
    """Calculate the hash of a Litecoin transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    return binascii.hexlify(
        hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest()
    )


async def broadcast_transaction_ltc(raw_transaction_hex, **kwargs):
    """Broadcast a Litecoin transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    rpc_nodes = kwargs.get("rpc_nodes") or []

    tasks = []

    tasks.append(
        asyncio.create_task(broadcast_transaction_ltc_blockchair(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(broadcast_transaction_ltc_blockcypher(raw_transaction_hex))
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
    except Exception:
        pass
