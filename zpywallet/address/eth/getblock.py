from .fullnode import EthereumRPCClient

class GetBlockRPCClient(EthereumRPCClient):
    def __init__(self, addresses, rpc_token, transactions=None):
        super().__init__(addresses, f"https://eth.getblock.io/{rpc_token}/mainnet/", transactions=transactions)