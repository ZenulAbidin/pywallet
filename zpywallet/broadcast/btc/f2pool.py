import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_btc_f2pool(raw_transaction_hex):
    api_url = "https://www.f2pool.com/api/v1/pushtx"
    payload = {"tx": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload)
    except ConnectionError as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code == 200:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException("Failed to broadcast Bitcoin transaction using F2Pool API: {}".format(response.text))
