import asyncio
import binascii
import hashlib
from .blockcypher import broadcast_transaction_bcy_blockcypher


def tx_hash_bcy(raw_transaction_hex):
    """Calculate the hash of a Blockcypher testnet transaction.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """
    return binascii.hexlify(
        hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest()
    )


async def broadcast_transaction_bcy(raw_transaction_hex):
    """Broadcast a Blockcypher testnet transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    tasks = []

    tasks.append(
        asyncio.create_task(broadcast_transaction_bcy_blockcypher(raw_transaction_hex))
    )

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        pass
