import requests

from ...errors import NetworkException


async def broadcast_transaction_btctest_esplora(raw_transaction_hex, **kwargs):
    """Broadcast a Bitcoin testnet transaction using an Esplora node.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
        esplora_url (str): The Esplora endpoint URL.
    """

    esplora_url = kwargs.get("url")
    api_url = f"{esplora_url}/api/tx"
    payload = {"tx": raw_transaction_hex}

    try:
        response = requests.post(api_url, data=payload, timeout=30)
    except Exception as e:
        raise NetworkException(
            "Connection error while broadcasting transaction: {}".format(str(e))
        )

    if response.status_code >= 300:
        raise NetworkException(
            f"Failed to broadcast transaction using Esplora API: {response.text}"
        )
