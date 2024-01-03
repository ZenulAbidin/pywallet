import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_btc_viabtc(raw_transaction_hex):
    api_url = "https://www.viabtc.com/res/tx/send"
    payload = {"rawtx": raw_transaction_hex}

    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException("Failed to broadcast transaction using ViaBTC API: {}".format(response.text))
