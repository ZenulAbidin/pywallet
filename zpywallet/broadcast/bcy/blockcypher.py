import requests

from ...errors import NetworkException

async def broadcast_transaction_bcy_blockcypher(raw_transaction_hex, **kwargs):
    api_url = "https://api.blockcypher.com/v1/bcy/main/txs/push"
    payload = {"tx": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload, timeout=30)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code >= 300:
        raise NetworkException("Failed to broadcast BCY transaction using BlockCypher API: {}".format(response.text))
