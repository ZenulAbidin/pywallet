import requests

from ...errors import NetworkException

async def broadcast_transaction_btctest_bitaps(raw_transaction_hex):
    api_url = "https://api.bitaps.com/btc/testnet/v1/create/tx/push"
    payload = {"hex": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload, timeout=30)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code >= 300:
        raise NetworkException("Failed to broadcast testnet transaction using Bitaps API: {}".format(response.text))
