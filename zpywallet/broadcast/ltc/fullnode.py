import requests
from ...errors import NetworkException

def broadcast_transaction_ltc_full_node(raw_transaction_hex, rpc_user, rpc_password, rpc_host, rpc_port):
    rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "sendrawtransaction",
        "params": [raw_transaction_hex],
    }

    try:
        response = requests.post(rpc_url, json=payload)
    except Exception as e:
        raise NetworkException(f"Failed to connect to RPC interface: {str(e)}")

    result = response.json()

    if "error" in result:
        raise NetworkException(f"Failed to broadcast Litecoin transaction using full node: {result['error']}")
    
    return result["result"]
