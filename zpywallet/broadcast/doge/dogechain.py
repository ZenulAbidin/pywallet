import requests

from ...errors import NetworkException

async def broadcast_transaction_doge_dogechain(raw_transaction_hex):
    api_url = "https://dogechain.info/api/v1/pushtx"
    payload = {"tx": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload, timeout=30)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code >= 300:
        raise NetworkException("Failed to broadcast Dogecoin transaction using DogeChain API: {}".format(response.text))
