from .fullnode import EthereumRPCClient

class QuickNodeRPCClient(EthereumRPCClient):
    def __init__(self, addresses, rpc_name, rpc_token, transactions=None):
        super().__init__(addresses, f"https://{rpc_name}.quiknode.pro/{rpc_token}/", transactions=transactions)