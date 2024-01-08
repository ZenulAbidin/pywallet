import requests

from ...errors import NetworkException

async def broadcast_transaction_btc_coinify(raw_transaction_hex):
    api_url = "https://coinify.com/api/broadcast-transaction/"
    payload = {"hex": raw_transaction_hex}

    try:
        response = requests.post(api_url, data=payload, timeout=30)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code >= 300:
        raise NetworkException("Failed to broadcast transaction using Coinify API: {}".format(response.text))
