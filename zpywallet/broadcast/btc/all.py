import asyncio
import binascii
import hashlib
from .bitaps import broadcast_transaction_btc_bitaps
from .blockchain_info import broadcast_transaction_btc_blockchain_info
from .blockchair import broadcast_transaction_btc_blockchair
from .blockcypher import broadcast_transaction_btc_blockcypher
from .blockstream import broadcast_transaction_btc_blockstream
from .esplora import broadcast_transaction_btc_esplora
from .fullnode import broadcast_transaction_btc_full_node
from .mempool_space import broadcast_transaction_btc_mempool_space
from .smartbit import broadcast_transaction_btc_smartbit
from .viabtc import broadcast_transaction_btc_viabtc
from ...nodes.btc import btc_nodes, btc_esplora_nodes


def tx_hash_btc(raw_transaction_hex):
    """Calculate the hash of a Bitcoin transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    return binascii.hexlify(
        hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest()
    )


async def broadcast_transaction_btc(raw_transaction_hex, **kwargs):
    """Broadcast a Bitcoin transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """
    rpc_nodes = kwargs.get("rpc_nodes") or []
    esplora_nodes = kwargs.get("esplora_nodes") or []

    tasks = []

    tasks.append(
        asyncio.create_task(broadcast_transaction_btc_bitaps(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(
            broadcast_transaction_btc_blockchain_info(raw_transaction_hex)
        )
    )
    tasks.append(
        asyncio.create_task(broadcast_transaction_btc_blockchair(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(broadcast_transaction_btc_blockcypher(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(broadcast_transaction_btc_blockstream(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(
            broadcast_transaction_btc_mempool_space(raw_transaction_hex)
        )
    )
    tasks.append(
        asyncio.create_task(broadcast_transaction_btc_smartbit(raw_transaction_hex))
    )
    tasks.append(
        asyncio.create_task(broadcast_transaction_btc_viabtc(raw_transaction_hex))
    )
    for node in rpc_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_btc_full_node(raw_transaction_hex, **node)
            )
        )
    for node in btc_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_btc_full_node(raw_transaction_hex, **node)
            )
        )
    for node in esplora_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_btc_esplora(raw_transaction_hex, **node)
            )
        )
    for node in btc_esplora_nodes:
        tasks.append(
            asyncio.create_task(
                broadcast_transaction_btc_esplora(raw_transaction_hex, **node)
            )
        )

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        pass
