import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_btc_smartbit(raw_transaction_hex):
    api_url = "https://api.smartbit.com.au/v1/blockchain/pushtx"
    payload = {"hex": raw_transaction_hex}

    response = requests.post(api_url, data=payload)

    if response.status_code == 200:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException("Failed to broadcast transaction using Smartbit API: {}".format(response.text))
