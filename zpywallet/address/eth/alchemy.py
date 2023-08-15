from .fullnode import EthereumRPCClient

class AlchemyRPCClient(EthereumRPCClient):
    def __init__(self, addresses, rpc_token, transactions=None):
        super().__init__(addresses, f"https://eth-mainnet.g.alchemy.com/v2/{rpc_token}", transactions=transactions)