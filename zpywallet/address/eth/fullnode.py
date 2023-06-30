import requests

from ...errors import NetworkException

class EthereumRPCClient:
    def __init__(self, rpc_url):
        self.rpc_url = rpc_url
    
    def get_balance(self, address):
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1
        }
        response = requests.post(self.rpc_url, json=payload)
        balance = int(response.json()["result"], 16)
        return balance
    
    def get_transaction_history(self, address):
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionCount",
            "params": [address, "latest"],
            "id": 1
        }
        response = requests.post(self.rpc_url, json=payload)
        transaction_count = int(response.json()["result"], 16)