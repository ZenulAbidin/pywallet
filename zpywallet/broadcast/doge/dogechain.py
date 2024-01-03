import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_doge_dogechain(raw_transaction_hex):
    api_url = "https://dogechain.info/api/v1/pushtx"
    payload = {"tx": raw_transaction_hex}

    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException("Failed to broadcast Dogecoin transaction using DogeChain API: {}".format(response.text))
