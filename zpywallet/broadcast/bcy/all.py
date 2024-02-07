import asyncio
import binascii
import hashlib
from .blockcypher import broadcast_transaction_bcy_blockcypher


def tx_hash_bcy(raw_transaction_hex):
    return binascii.hexlify(
        hashlib.sha256(hashlib.sha256(raw_transaction_hex.decode()).digest()).digest()
    )


async def broadcast_transaction_bcy(raw_transaction_hex):

    tasks = []

    tasks.append(
        asyncio.create_task(broadcast_transaction_bcy_blockcypher(raw_transaction_hex))
    )

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        pass
