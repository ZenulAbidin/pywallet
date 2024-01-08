import random
import requests
from ...errors import NetworkException

async def broadcast_transaction_ltctest_full_node(raw_transaction_hex, **kwargs):
    user = kwargs.get('user')
    password = kwargs.get('password')
    url = kwargs.get('url')
    if user and password:
        rpc_url = f"http://{user}:{password}@{url}"
    else:
        rpc_url = url
        
    payload = {
        "jsonrpc": "2.0",
        "id": f"{random.randint(1, (2<<31) - 1)}",
        "method": "sendrawtransaction",
        "params": [raw_transaction_hex],
    }

    try:
        response = requests.post(rpc_url, json=payload, timeout=30)
    except Exception as e:
        raise NetworkException(f"Failed to connect to RPC interface: {str(e)}")

    result = response.json()

    if "error" in result:
        raise NetworkException(f"Failed to broadcast Litecoin testnet transaction using full node: {result['error']}")
    
    return result["result"]
