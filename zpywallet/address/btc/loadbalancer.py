from .blockchain_info import BlockchainInfoAddress
from .blockcypher import BlockcypherAddress
from .blockstream import BlockstreamAddress
from .btcdotcom import BTCDotComAddress
from .esplora import EsploraAddress
from .fullnode import BitcoinRPCClient
from .mempoolspace import MempoolSpaceAddress
from ...generated import wallet_pb2
from ...errors import NetworkException
from ...nodes.btc import btc_nodes, btc_esplora_nodes

class BitcoinAddress:
    """ Load balancer for all BTC address providers provided to an instance of this class,
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
        esplora_endpoints = kwargs.get('esplora_endpoints')
        blockcypher_tokens = kwargs.get('blockcypher_tokens')


        # Set everything to an empty list so that providers do not immediately start fetching
        # transactions and to avoid exceptions in loops later in this method.
        if not transactions:
            transactions = []
        if not esplora_endpoints:
            esplora_endpoints = [] + btc_esplora_nodes
        if not fullnode_endpoints:
            fullnode_endpoints = [] + btc_nodes

        self.transactions = transactions

        #if provider_bitmask & 1 << wallet_pb2.BTC_BLOCKCHAIN_INFO + 1:
        #    self.provider_list.append(BlockchainInfoAddress(addresses, transactions=transactions))
        if provider_bitmask & 1 << wallet_pb2.BTC_BLOCKCYPHER + 1:
            tokens = blockcypher_tokens
            if not tokens:
                tokens = []
            for token in tokens:
                self.provider_list.append(BlockcypherAddress(addresses, transactions=transactions, api_key=token))
            self.provider_list.append(BlockcypherAddress(addresses, transactions=transactions)) # No token (free) version
        if provider_bitmask & 1 << wallet_pb2.BTC_BLOCKSTREAM + 1:
            self.provider_list.append(BlockstreamAddress(addresses, transactions=transactions))
        if provider_bitmask & 1 << wallet_pb2.BTC_BTCDOTCOM + 1:
            self.provider_list.append(BTCDotComAddress(addresses, transactions=transactions))
        if provider_bitmask & 1 << wallet_pb2.BTC_ESPLORA + 1:
            for endpoint in esplora_endpoints:
                self.provider_list.append(EsploraAddress(addresses, transactions=transactions, **endpoint))
        if provider_bitmask & 1 << wallet_pb2.BTC_FULLNODE + 1:
            for endpoint in fullnode_endpoints:
                self.provider_list.append(BitcoinRPCClient(addresses, transactions=transactions, **endpoint))
        if provider_bitmask & 1 << wallet_pb2.BTC_MEMPOOLSPACE + 1:
            self.provider_list.append(MempoolSpaceAddress(addresses, transactions=transactions))

    def sync(self): 
       for provider in self.provider_list:
            try:
                provider.sync()
            except NetworkException:
                pass

    def get_balance(self):
        """
        Retrieves the balance of the Bitcoin address.

        Returns:
            float: The balance of the Bitcoin address in BTC.

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