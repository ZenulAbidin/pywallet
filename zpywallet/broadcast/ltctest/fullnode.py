from Cryptodome import Random
import requests
from ...errors import NetworkException


async def broadcast_transaction_ltctest_full_node(raw_transaction_hex, **kwargs):
    """Broadcast a Litecoin testnet transaction using a full node.

    If the node requires authentication, both username and password must be passed.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
        url (str): The JSON-RPC URL of the node. Include the port if necessary.
        username (str): The RPC username.
        password (str): The RPC password.
    """

    user = kwargs.get("user")
    password = kwargs.get("password")
    url = kwargs.get("url")
    if user and password:
        rpc_url = f"http://{user}:{password}@{url}"
    else:
        rpc_url = url

    payload = {
        "jsonrpc": "2.0",
        "id": f"{int.from_bytes(Random.new().read(4), byteorder='big')}",
        "method": "sendrawtransaction",
        "params": [raw_transaction_hex],
    }

    try:
        response = requests.post(rpc_url, json=payload, timeout=30)
    except Exception as e:
        raise NetworkException(f"Failed to connect to RPC interface: {str(e)}")

    result = response.json()

    if "error" in result:
        raise NetworkException(
            f"Failed to broadcast Litecoin testnet transaction using full node: {result['error']}"
        )

    return result["result"]
