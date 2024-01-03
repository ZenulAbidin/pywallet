import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_btc_esplora(raw_transaction_hex, esplora_url):
    api_url = f"{esplora_url}/tx"
    payload = {"tx": raw_transaction_hex}

    response = requests.post(api_url, data=payload)

    if response.status_code == 200:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException(f"Failed to broadcast transaction using Esplora API: {response.text}")
