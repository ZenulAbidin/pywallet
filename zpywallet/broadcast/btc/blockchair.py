import requests
from ...errors import NetworkException

def broadcast_transaction_btc_blockchair(raw_transaction_hex):
    blockchair_url = "https://api.blockchair.com/bitcoin/push/transaction"

    payload = {"data": raw_transaction_hex}

    try:
        response = requests.post(blockchair_url, json=payload)
        result = response.json()

        if response.status_code == 200 and result.get("status") == "success":
            return result.get("data").get("transaction_hash")
        else:
            raise NetworkException(f"Failed to broadcast Bitcoin transaction using Blockchair API: {result.get('message')}")
    except Exception as e:
        raise NetworkException(f"Failed to broadcast Bitcoin transaction using Blockchair API: {e}")
