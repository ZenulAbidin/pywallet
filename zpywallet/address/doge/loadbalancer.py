from .blockcypher import BlockcypherAddress
from .dogechain import DogeChainAddress
from ...generated import wallet_pb2
from ...errors import NetworkException
from ...nodes.eth import eth_nodes

class DogecoinAddress:
    """ Load balancer for all DOGE address providers provided to an instance of this class,
        using the round robin scheduling algorithm.
    """

    def __init__(self, providers: bytes, addresses, max_cycles=100,
                 transactions=None, **kwargs):
        provider_bitmask = int.from_bytes(providers, 'big')
        self.provider_list = []
        self.current_index = 0
        self.addresses = addresses
        self.max_cycles = max_cycles
        blockcypher_tokens = kwargs.get('blockcypher_tokens')

        # Set everything to an empty list so that providers do not immediately start fetching
        # transactions and to avoid exceptions in loops later in this method.
        if not transactions:
            transactions = []

        self.transactions = transactions

        if provider_bitmask & 1 << wallet_pb2.DOGE_BLOCKCYPHER + 1:
            tokens = blockcypher_tokens
            if not tokens:
                tokens = []
            for token in tokens:
                self.provider_list.append(BlockcypherAddress(addresses, transactions=transactions, api_key=token))
            self.provider_list.append(BlockcypherAddress(addresses, transactions=transactions)) # No token (free) version
        if provider_bitmask & 1 << wallet_pb2.DOGE_DOGECHAIN + 1:
            self.provider_list.append(DogeChainAddress(addresses, transactions=transactions))

    def sync(self):
        working_provider_list = []
        for provider in self.provider_list:
            try:
                provider.sync()
                working_provider_list.append(provider)
            except NetworkException:
                pass
        # self.provider_list = working_provider_list
        self.get_transaction_history()

    def get_balance(self):
        """
        Retrieves the balance of the Dogecoin address.

        Returns:
            float: The balance of the Dogecoin address in DOGE.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        utxos = self.get_utxos()
        total_balance = 0
        confirmed_balance = 0
        for utxo in utxos:
            total_balance += utxo.amount
            if utxo.confirmed:
                confirmed_balance += utxo.amount
        return total_balance, confirmed_balance
        
    def get_utxos(self):
        # Transactions are generated in reverse order
        utxos = []
        for i in range(len(self.transactions)-1, -1, -1):
            for out in self.transactions[i].btclike_transaction.outputs:
                if out.spent:
                    continue
                if out.address in self.addresses:
                    utxo = wallet_pb2.UTXO()
                    utxo.address = out.address
                    utxo.txid = self.transactions[i].txid
                    utxo.index = out.index
                    utxo.amount = out.amount
                    utxo.height = self.transactions[i].height
                    utxo.confirmed = self.transactions[i].confirmed
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
            self.provider_list[self.current_index].transactions = self.transactions
            try:
                self.provider_list[self.current_index].get_transaction_history()
                ntransactions = len(self.transactions)
                self.transactions = self.provider_list[self.current_index].transactions
                break
            except NetworkException:
                self.transactions = self.provider_list[self.current_index].transactions
                self.advance_to_next_provider()
                cycle += 1
        return self.transactions
    