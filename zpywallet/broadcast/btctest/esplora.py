import requests

from ...errors import NetworkException

async def broadcast_transaction_btctest_esplora(raw_transaction_hex, esplora_url):
    api_url = f"{esplora_url}/api/tx"
    payload = {"tx": raw_transaction_hex}

    try:
        response = requests.post(api_url, data=payload)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code >= 300:
        raise NetworkException(f"Failed to broadcast transaction using Esplora API: {response.text}")
