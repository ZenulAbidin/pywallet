import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_btctest_bitaps(raw_transaction_hex):
    api_url = "https://api.bitaps.com/btc/testnet/v1/create/tx/push"
    payload = {"hex": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code == 200:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException("Failed to broadcast testnet transaction using Bitaps API: {}".format(response.text))
