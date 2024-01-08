import requests

from ...errors import NetworkException

async def broadcast_transaction_btc_blockchain_info(raw_transaction_hex):
    api_url = "https://blockchain.info/pushtx"
    payload = {"tx": raw_transaction_hex}

    try:
        response = requests.post(api_url, data=payload, timeout=30)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code >= 300:
        raise NetworkException("Failed to broadcast transaction using Blockchain.info API: {}".format(response.text))
