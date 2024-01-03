import requests
from ...errors import NetworkException

def broadcast_transaction_eth_mew(raw_transaction_hex):
    mew_url = "https://api.mewapi.io/v1/transaction/sendRaw"

    payload = {
        "rawTx": raw_transaction_hex,
    }

    try:
        response = requests.post(mew_url, json=payload)
        result = response.json()

        if response.status_code == 200 and result.get("status") == "1":
            return result.get("result")
        else:
            raise NetworkException(f"Failed to broadcast Ethereum transaction using MyEtherWallet: {result.get('message')}")
    except Exception as e:
        raise NetworkException(f"Failed to broadcast Ethereum transaction using MyEtherWallet: {e}")
