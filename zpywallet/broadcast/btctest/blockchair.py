import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_btctest_blockchair(raw_transaction_hex):
    api_url = "https://api.blockchair.com/bitcoin/testnet/push/transaction"
    payload = {"data": raw_transaction_hex}

    response = requests.post(api_url, data=payload)

    if response.status_code == 200:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException("Failed to broadcast testnet transaction using Blockchair API: {}".format(response.text))
