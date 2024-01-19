from .fullnode import EthereumWeb3Client
from ...generated import wallet_pb2
from ...errors import NetworkException
from ...nodes.eth import eth_nodes

class EthereumAddress:
    """ Load balancer for all ETH address providers provided to an instance of this class,
        using the round robin scheduling algorithm.
    """

    def __init__(self, addresses, providers: bytes = b'\xff\xff', max_cycles=100,
                 transactions=None, **kwargs):
        provider_bitmask = int.from_bytes(providers, 'big')
        self.provider_list = []
        self.current_index = 0
        self.addresses = addresses
        self.max_cycles = max_cycles
        fullnode_endpoints = kwargs.get('fullnode_endpoints')

        # Set everything to an empty list so that providers do not immediately start fetching
        # transactions and to avoid exceptions in loops later in this method.
        if not transactions:
            transactions = []
        if not fullnode_endpoints:
            fullnode_endpoints = [] + eth_nodes

        self.transactions = transactions

        if provider_bitmask & 1 << wallet_pb2.ETH_FULLNODE + 1:
            for endpoint in fullnode_endpoints:
                self.provider_list.append(EthereumWeb3Client(addresses, transactions=transactions, **endpoint))

    def sync(self):
        # There is nothing to sync on EVM chains
        return

    def get_balance(self):
        """
        Retrieves the balance of the Ethereum address.

        Returns:
            float: The balance of the Ethereum address in ETH.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        cycle = 1
        while cycle <= self.max_cycles:
            self.provider_list[self.current_index].transactions = self.transactions
            try:
                return self.provider_list[self.current_index].get_balance()
            except NetworkException:
                self.transactions = self.provider_list[self.current_index].transactions
                self.advance_to_next_provider()
                cycle += 1
        raise NetworkException(f"None of the address providers are working after {self.max_cycles} tries")

        

    def advance_to_next_provider(self):
        if not self.provider_list:
            return
        
        newindex = (self.current_index + 1) % len(self.provider_list)
        self.provider_list[newindex].transactions = self.provider_list[self.current_index].transactions
        self.current_index = newindex
    
    def get_transaction_history(self):
        for address in self.addresses:
            txs = []
            ntransactions = -1  # Set to invalid value for the first iteration
            cycle = 1
            while ntransactions != len(self.transactions):
                if cycle > self.max_cycles:
                    raise NetworkException(f"None of the address providers are working after {self.max_cycles} tries")
                self.provider_list[self.current_index].transactions = txs
                self.provider_list[self.current_index].addresses = [address]
                try:
                    self.provider_list[self.current_index].get_transaction_history()
                    ntransactions = len(self.transactions)
                    txs = self.provider_list[self.current_index].transactions
                    break
                except NetworkException:
                    txs = self.provider_list[self.current_index].transactions
                    self.advance_to_next_provider()
                    cycle += 1
            self.transactions.extend(txs)
        return self.transactions