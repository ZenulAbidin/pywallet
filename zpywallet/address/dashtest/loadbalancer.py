from .fullnode import DashRPCClient
from ...generated import wallet_pb2
from ...errors import NetworkException


class DashTestAddress:
    """Represents a list of Dash testnet addresses.

    Developers should use this class, because it autoselects the most stable
    providers to fetch data from.
    """

    def __init__(
        self,
        addresses,
        providers: bytes = b"\xff\xff",
        max_cycles=100,
        transactions=None,
        **kwargs,
    ):
        provider_bitmask = int.from_bytes(providers, "big")
        self.provider_list = []
        self.current_index = 0
        self.addresses = addresses
        self.max_cycles = max_cycles
        self.fast_mode = kwargs.get("fast_mode") or True
        fullnode_endpoints = kwargs.get("fullnode_endpoints")

        # Set everything to an empty list so that providers do not immediately start fetching
        # transactions and to avoid exceptions in loops later in this method.
        if not transactions:
            transactions = []
        if not fullnode_endpoints:
            fullnode_endpoints = []

        self.transactions = transactions

        if provider_bitmask & 1 << wallet_pb2.DASH_FULLNODE + 1:
            for endpoint in fullnode_endpoints:
                self.provider_list.append(
                    DashRPCClient(
                        addresses,
                        transactions=transactions,
                        fast_mode=self.fast_mode,
                        **endpoint,
                    )
                )

        if kwargs.get("min_height") is not None:
            self.min_height = kwargs.get("min_height")
        else:
            self.min_height = self.get_block_height()

        for i in range(len(self.provider_list)):
            self.provider_list[i].min_height = self.min_height

    def get_balance(self):
        """
        Retrieves the balance of the Dash address.

        Returns:
            float: The balance of the Dash address in DASH.

        Raises:
            Network Exception: If the API request fails or the address balance
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

    def get_block_height(self):
        """
        Retrieves the current block height.

        Returns:
            int: The current block height.

        Raises:
            NetworkException: If the API request fails or the block height
                cannot be retrieved.
        """
        cycle = 1
        while cycle <= self.max_cycles:
            self.provider_list[self.current_index].transactions = self.transactions
            try:
                h = self.provider_list[self.current_index].get_block_height()
                if h > 0:
                    return h
            except NetworkException:
                self.transactions = self.provider_list[self.current_index].transactions
                self._advance_to_next_provider()
                cycle += 1
        raise NetworkException(
            f"None of the address providers are working after {self.max_cycles} tries"
        )

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Dash address from cached data
        augmented with network data.

        Returns:
            list: A list of transaction objects.

        Raises:
            NetworkException: If the API request fails or the transaction
                history cannot be retrieved.
        """

        for address in self.addresses:
            txs = []
            ntransactions = -1  # Set to invalid value for the first iteration
            cycle = 1
            while ntransactions != len(self.transactions):
                if cycle > self.max_cycles:
                    raise NetworkException(
                        f"None of the address providers are working after {self.max_cycles} tries"
                    )
                self.provider_list[self.current_index].transactions = txs
                self.provider_list[self.current_index].addresses = [address]
                try:
                    self.provider_list[self.current_index].get_transaction_history()
                    ntransactions = len(self.transactions)
                    txs = self.provider_list[self.current_index].transactions
                    break
                except NetworkException:
                    txs = self.provider_list[self.current_index].transactions
                    self._advance_to_next_provider()
                    cycle += 1
            self.transactions.extend(txs)
        return self.transactions
