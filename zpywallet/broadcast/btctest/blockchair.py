import requests

from ...errors import NetworkException


async def broadcast_transaction_btctest_blockchair(raw_transaction_hex):
    """Broadcast a Bitcoin testnet transaction using Blockchair.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    api_url = "https://api.blockchair.com/bitcoin/testnet/push/transaction"
    payload = {"data": raw_transaction_hex}

    try:
        response = requests.post(api_url, data=payload, timeout=30)
    except Exception as e:
        raise NetworkException(
            "Connection error while broadcasting transaction: {}".format(str(e))
        )

    if response.status_code >= 300:
        raise NetworkException(
            "Failed to broadcast testnet transaction using Blockchair API: {}".format(
                response.text
            )
        )
