import requests
import hashlib

from ...errors import NetworkException

async def broadcast_transaction_eth_blockcypher(raw_transaction_hex):
    api_url = "https://api.blockcypher.com/v1/eth/main/txs/push"
    payload = {"tx": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload, timeout=30)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code == 201:
        return hashlib.sha256(hashlib.sha256(raw_transaction_hex.encode()).digest()).digest()  # Transaction ID
    else:
        raise NetworkException("Failed to broadcast Ethereum transaction using BlockCypher API: {}".format(response.text))
