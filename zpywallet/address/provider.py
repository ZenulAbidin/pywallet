from functools import reduce
from ..generated import wallet_pb2


class AddressProvider(object):
    """
    A class representing a list of crypto addresses.

    This class allows you to retrieve the balance, UTXO set, and transaction
    history of a crypto address. It is the base class of all other providers.
    """

    HTTPS_ADAPTER = "https://"

    def deduplicate(self, elements):
        return reduce(lambda re, x: re + [x] if x not in re else re, elements, [])

    def __init__(
        self,
        addresses,
        request_interval=(3, 1),
        transactions=None,
    ):
        """
        Initializes an instance of the BlockcypherAddress class.

        Args:
            addresses (list): A list of human-readable crypto addresses.
            api_key (str): The API key for accessing the Blockcypher API.
            request_interval (tuple): A pair of integers indicating the number
                of requests allowed during a particular amount of seconds.
                Set to (0,N) for no rate limiting, where N>0.
        """
        self.addresses = addresses
        self.height = -1
        self.requests, self.interval_sec = request_interval
        if transactions is None:
            self.transactions = []
        else:
            self.transactions = transactions

    def get_balance(self):
        """
        Retrieves the balance of the crypto address.

        Returns:
            tuple: The total balance and the confirmed balance of the crypto address whole units e.g. BTC e.g. BTC.

        Raises:
            NetworkException: If the API request fails or the address balance cannot be retrieved.
        """

        utxos = self.get_utxos()
        total_balance = 0
        confirmed_balance = 0
        for utxo in utxos:
            total_balance += utxo.amount
            if utxo.confirmed:
                confirmed_balance += utxo.amount
        return total_balance, confirmed_balance

    def _manual_filter_utxos(self, utxos):
        # This method is for the benefit of providers which do not provide
        # data on spent outputs.
        for i in range(len(self.transactions)):
            for _in in self.transactions[i].btclike_transaction.inputs:
                for j in range(len(utxos) - 1, -1, -1):
                    if _in.txid == utxos[j].txid and _in.index == utxos[j].index:
                        del utxos[j]  # spent
        return utxos

    def get_utxos(self):
        """Fetches the UTXO set for the addresses.

        Returns:
            list: A list of UTXOs
        """

        # Transactions are generated in reverse order
        self.get_transaction_history()
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

        utxos = self._manual_filter_utxos(utxos)

        # Ensure unconfirmed UTXOs are last.
        utxos.sort(key=lambda u: u.height if u.confirmed else 1e100)
        return utxos

    def get_block_height(self):
        """
        Retrieves the current block height.

        Returns:
            int: The current block height.
        """

        raise NotImplementedError("Do not directly use the AddressProvider class")

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the crypto address from cached
        data augmented with network data.

        Returns:
            list: A list of transaction objects.
        """
        raise NotImplementedError("Do not directly use the AddressProvider class")
