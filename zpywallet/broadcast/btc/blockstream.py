import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_btc_blockstream(raw_transaction_hex):
    api_url = "https://blockstream.info/api/tx"
    payload = {"tx": raw_transaction_hex}

    response = requests.post(api_url, data=payload)

    if response.status_code == 200:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException("Failed to broadcast transaction using Blocksream API: {}".format(response.text))
