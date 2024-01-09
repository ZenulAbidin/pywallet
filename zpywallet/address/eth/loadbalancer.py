from .fullnode import EthereumWeb3Client
from ...generated import wallet_pb2
from ...errors import NetworkException
from ...nodes.eth import eth_nodes

class EthereumAddress:
    """ Load balancer for all LTC address providers provided to an instance of this class,
        using the round robin scheduling algorithm.
    """

    def __init__(self, providers: bytes, addresses, max_cycles=100,
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
        working_provider_list = []
        for provider in self.provider_list:
            try:
                provider.sync()
                working_provider_list.append(provider)
            except NetworkException:
                pass
        self.provider_list = working_provider_list
        self.get_transaction_history()

    def get_balance(self):
        """
        Retrieves the balance of the Ethereum address.

        Returns:
            float: The balance of the Ethereum address in LTC.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        utxos = self.get_utxos()
        total_balance = 0
        confirmed_balance = 0
        for utxo in utxos:
            total_balance += utxo["amount"]
            # Careful: Block height #0 is the Genesis block - don't want to exclude that.
            if utxo["confirmed"]:
                confirmed_balance += utxo["amount"]
        return total_balance, confirmed_balance
        
    def get_utxos(self):
        # Transactions are generated in reverse order
        #XXX I expect this to fail, because ETH does not use UTXOs!
        utxos = []
        for i in range(len(self.transactions)-1, -1, -1):
            for out in self.transactions[i].btclike_transaction.outputs:
                if out.spent:
                    continue
                if out.address in self.addresses:
                    utxo = {}
                    utxo["address"] = out.address
                    utxo["txid"] = self.transactions[i].txid
                    utxo["index"] = out.index
                    utxo["amount"] = out.amount
                    utxo["height"] = self.transactions[i].height
                    utxo["confirmed"] = self.transactions[i].confirmed
                    utxos.append(utxo)
        return utxos


    def advance_to_next_provider(self):
        if not self.provider_list:
            return
        
        newindex = (self.current_index + 1) % len(self.provider_list)
        self.provider_list[newindex].transactions = self.provider_list[self.current_index].transactions
        self.current_index = newindex
    
    def get_transaction_history(self):
        ntransactions = -1  # Set to invalid value for the first iteration
        cycle = 1
        while ntransactions != len(self.transactions):
            if cycle > self.max_cycles:
                raise NetworkException(f"None of the address providers are working after f{self.max_cycles} tries")
            ntransactions = len(self.transactions)
            self.provider_list[self.current_index].transactions = self.transactions
            try:
                self.provider_list[self.current_index].get_transaction_history()
                self.transactions = self.provider_list[self.current_index].transactions
                break
            except NetworkException:
                self.transactions = self.provider_list[self.current_index].transactions
                self.advance_to_next_provider()
                cycle += 1
        return self.transactions