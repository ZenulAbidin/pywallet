import requests
from ...errors import NetworkException

async def broadcast_transaction_btc_blockchair(raw_transaction_hex):
    api_url = "https://api.blockchair.com/bitcoin/push/transaction"

    payload = {"data": raw_transaction_hex}

    try:
        response = requests.post(api_url, json=payload, timeout=30)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))
    
    result = response.json()

    if response.status_code >= 300:
        raise NetworkException(f"Failed to broadcast Bitcoin transaction using Blockchair API: {result.get('message')}")
