from .fullnode import EthereumRPCClient

class InfuraRPCClient(EthereumRPCClient):
    def __init__(self, addresses, rpc_token, transactions=None):
        super().__init__(addresses, f"https://mainnet.infura.io/v3/{rpc_token}", transactions=transactions)