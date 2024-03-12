import asyncio
import binascii
import hashlib
from .fullnode import broadcast_transaction_dashtest_full_node


def tx_hash_dashtest(raw_transaction_hex):
    """Calculate the hash of a Dash testnet transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    return binascii.hexlify(
        hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest()
    )


async def broadcast_transaction_dashtest(raw_transaction_hex, **kwargs):
    """Broadcast a Dash testnet transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    rpc_nodes = kwargs.get("rpc_nodes") or []

    tasks = []

    for node in rpc_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_dashtest_full_node(raw_transaction_hex, **node)
            )
        )

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        pass
