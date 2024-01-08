import requests
from ...errors import NetworkException

async def broadcast_transaction_eth_etherscan(raw_transaction_hex, api_key):
    api_url = f"https://api.etherscan.io/api"
    payload = {
        "module": "proxy",
        "action": "eth_sendRawTransaction",
        "hex": raw_transaction_hex,
        "apikey": api_key,
    }

    try:
        response = requests.get(api_url, params=payload, timeout=30)
    except Exception as e:
        raise NetworkException("Connection error while broadcasting transaction: {}".format(str(e)))
    
    result = response.json()

    if response.status_code >= 300 and result.get("status") == "1":
        raise NetworkException(f"Failed to broadcast Ethereum transaction using Etherscan: {result.get('message')}")
