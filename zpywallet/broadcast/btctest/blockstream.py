import requests
import hashlib

from ...errors import NetworkException

def broadcast_transaction_btctest_blockstream(raw_transaction_hex):
    api_url = "https://blockstream.info/testnet/api/tx"
    payload = {"tx": raw_transaction_hex}

    try:
        response = requests.post(api_url, data=payload)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))

    if response.status_code >= 300:
        raise NetworkException("Failed to broadcast testnet transaction using Blocksream API: {}".format(response.text))
