from .blockcypher import BlockcypherClient
from .blockstream import BlockstreamClient
from .btcdotcom import BTCDotComClient
from .dogechain import DogeChainClient
from .esplora import EsploraClient
from .fullnode import RPCClient
from .mempoolspace import MempoolSpaceClient
from .web3node import Web3Client
from ..generated import wallet_pb2
from ..errors import NetworkException
from contextlib import suppress

# TODO we currently have no easy way to update cache providers asynchronously.


class CryptoClient:
    """Represents a list of crypto addresses.

    Developers should use this class, because it autoselects the most stable
    providers to fetch data from.
    """

    def __init__(
        self,
        addresses,
        coin="BTC",
        chain="main",
        use_database=False,
        transactions=None,
        **kwargs,
    ):
        self.cache_provider_list = []
        self.provider_list = []
        self.current_index = 0
        self.addresses = addresses
        self.transactions = transactions or []
        fullnode_endpoints = kwargs.get("fullnode_endpoints") or []
        esplora_endpoints = kwargs.get("esplora_endpoints") or []
        blockcypher_tokens = kwargs.get("blockcypher_tokens") or []
        self.db_connection_parameters = (
            kwargs.get("db_connection_parameters") if use_database else None
        )
        self.transactions = transactions

        if use_database:
            for endpoint in fullnode_endpoints:
                with suppress(ValueError):
                    self.cache_provider_list.append(
                        RPCClient(
                            addresses,
                            coin,
                            chain,
                            transactions=self.transactions,
                            db_connection_parameters=self.db_connection_parameters,
                            **endpoint,
                        )
                    )

                with suppress(ValueError):
                    self.cache_provider_list.append(
                        Web3Client(
                            addresses,
                            coin,
                            chain,
                            transactions=self.transactions,
                            db_connection_parameters=self.db_connection_parameters,
                            **endpoint,
                        )
                    )

            for endpoint in esplora_endpoints:
                with suppress(ValueError):
                    self.cache_provider_list.append(
                        EsploraClient(
                            addresses,
                            coin,
                            chain,
                            transactions=self.transactions,
                            db_connection_parameters=self.db_connection_parameters,
                            **endpoint,
                        )
                    )

            with suppress(ValueError):
                self.cache_provider_list.append(
                    BlockstreamClient(
                        addresses,
                        coin,
                        chain,
                        transactions=self.transactions,
                        db_connection_parameters=self.db_connection_parameters,
                    )
                )

            with suppress(ValueError):
                self.cache_provider_list.append(
                    MempoolSpaceClient(
                        addresses,
                        coin,
                        chain,
                        transactions=self.transactions,
                        db_connection_parameters=self.db_connection_parameters,
                    )
                )

        for token in blockcypher_tokens:
            with suppress(ValueError):
                self.provider_list.append(
                    BlockcypherClient(
                        addresses,
                        coin,
                        chain,
                        transactions=self.transactions,
                        token=token,
                    )
                )

        # Blockcypher without any token
        with suppress(ValueError):
            self.provider_list.append(
                BlockcypherClient(
                    addresses,
                    coin,
                    chain,
                    transactions=self.transactions,
                )
            )

        with suppress(ValueError):
            self.provider_list.append(
                BTCDotComClient(
                    addresses,
                    coin,
                    chain,
                    transactions=self.transactions,
                )
            )

        with suppress(ValueError):
            self.provider_list.append(
                DogeChainClient(
                    addresses,
                    coin,
                    chain,
                    transactions=self.transactions,
                )
            )

        if not self.provider_list and not self.cache_provider_list:
            raise ValueError(f"No providers for coin '{coin}', chain '{chain}' found.")

    def get_balance(self):
        """
        Retrieves the balance of the Litecoin address.

        Returns:
            float: The balance of the Litecoin address in LTC.

        Raises:
            NetworkException: If the API request fails or the address balance
                cannot be retrieved.
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
        """Fetches the UTXO set for the addresses.

        Returns:
            list: A list of UTXOs
        """

        # Transactions are generated in reverse order
        utxos = []
        for i in range(len(self.transactions) - 1, -1, -1):
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

    def _advance_to_next_provider(self):
        if not self.provider_list:
            return

        newindex = (self.current_index + 1) % len(self.provider_list)
        self.provider_list[newindex].transactions = self.provider_list[
            self.current_index
        ].transactions
        self.current_index = newindex

    def initialize_database(self):
        for provider in self.cache_provider_list:
            # They all use the same database so we can just read the mempool
            # from the first one to populate the database.
            try:
                provider.read_mempool()
                return
            except NetworkException:
                pass

            raise NetworkException("Failed to populate database - all providers failed")

    def get_block_height(self):
        """
        Retrieves the current block height.

        Returns:
            int: The current block height.

        Raises:
            NetworkException: If the API request fails or the block height
                cannot be retrieved.
        """
        for provider in self.cache_provider_list:
            try:
                h = provider.get_block_height()
                if h > 0:
                    return h
            except NetworkException:
                continue

        for provider in self.provider_list:
            try:
                h = provider.get_block_height()
                if h > 0:
                    return h
            except NetworkException:
                continue

        raise NetworkException("All address providers failed to get block height")

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Litecoin address from cached
        data augmented with network data.

        Returns:
            list: A list of transaction objects.

        Raises:
            NetworkException: If the API request fails or the transaction
                history cannot be retrieved.
        """
        min_height = max([tx.height for tx in self.transactions] + [-1])

        for provider in self.provider_list:
            provider.transactions = self.transactions
            provider.height = min_height
            try:
                provider.get_transaction_history()
                self.transactions = provider.transactions
                break
            except NetworkException:
                continue
        return self.transactions
