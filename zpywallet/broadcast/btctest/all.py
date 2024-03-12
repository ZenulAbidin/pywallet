import asyncio
import binascii
import hashlib
from .bitaps import broadcast_transaction_btctest_bitaps
from .blockchair import broadcast_transaction_btctest_blockchair
from .blockcypher import broadcast_transaction_btctest_blockcypher
from .blockstream import broadcast_transaction_btctest_blockstream
from .esplora import broadcast_transaction_btctest_esplora
from .fullnode import broadcast_transaction_btctest_full_node
from .mempool_space import broadcast_transaction_btctest_mempool_space
from ...nodes.btctest import btctest_nodes, btctest_esplora_nodes


def tx_hash_btctest(raw_transaction_hex):
    """Calculate the hash of a Bitcoin testnet transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    return binascii.hexlify(
        hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest()
    )


async def broadcast_transaction_btctest(raw_transaction_hex, **kwargs):
    """Broadcast a Bitcoin testnet transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    rpc_nodes = kwargs.get("rpc_nodes") or []
    esplora_nodes = kwargs.get("esplora_nodes") or []

    tasks = []

    tasks.append(
        asyncio.create_task(broadcast_transaction_btctest_bitaps(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(
            broadcast_transaction_btctest_blockchair(raw_transaction_hex)
        )
    )
    tasks.append(
        asyncio.create_task(
            broadcast_transaction_btctest_blockcypher(raw_transaction_hex)
        )
    )
    tasks.append(
        asyncio.create_task(
            broadcast_transaction_btctest_blockstream(raw_transaction_hex)
        )
    )
    tasks.append(
        asyncio.create_task(
            broadcast_transaction_btctest_mempool_space(raw_transaction_hex)
        )
    )
    for node in rpc_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_btctest_full_node(raw_transaction_hex, **node)
            )
        )
    for node in btctest_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_btctest_full_node(raw_transaction_hex, **node)
            )
        )
    for node in esplora_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_btctest_esplora(raw_transaction_hex, **node)
            )
        )
    for node in btctest_esplora_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_btctest_esplora(raw_transaction_hex, **node)
            )
        )

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        pass
