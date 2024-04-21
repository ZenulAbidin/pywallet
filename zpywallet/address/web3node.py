from functools import reduce

import web3
from web3 import Web3, middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy

from zpywallet.address.cache import SQLTransactionStorage, DatabaseError

from ..errors import NetworkException
from ..generated import wallet_pb2
from ..utils.keccak import to_checksum_address


def deduplicate(elements):
    return reduce(lambda re, x: re + [x] if x not in re else re, elements, [])


class Web3Client:
    """
    A class indexing all transactions in ethereum-like blockchains into
    a database for quick fetching. It also lets you query transactions by address.

    The performance of this class heavily depends on the network speed and CPU
    speed of the node as well as the number of threads available, the size of the RPC
    batch work queue specified in the constructor, and the amount of transactions in
    megabytes you are trying to fetch at once.

    You can run a private node with many 3rd party providers such as Alchemy,
    Infura, QuickNode, and GetBlock.

    WARNING: Ethereum nodes have a --txlookuplimit and keep only recent transactions,
    unless this option is turned off. 3rd party providers should have this disabled,
    but ensure it is turned off if you are running your own node.
    """

    def _clean_tx(self, element, block):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element["hash"]
        if "blockNumber" in element.keys():
            new_element.confirmed = True
            new_element.height = element["blockNumber"]
        else:
            new_element.confirmed = False

        new_element.ethlike_transaction.txfrom = element["from"]
        new_element.ethlike_transaction.txto = element["to"]
        new_element.ethlike_transaction.amount = int(element["value"])

        new_element.timestamp = int(block["timestamp"], 16)
        new_element.ethlike_transaction.data = element["input"]

        gas = int(element["gas"], 16)
        new_element.ethlike_transaction.gas = gas
        if "maxFeePerGas" in element.keys():
            new_element.total_fee = int(element["maxFeePerGas"], 16) * gas
        else:
            new_element.total_fee = int(element["gasPrice"]) * gas

        new_element.fee_metric = wallet_pb2.WEI
        return new_element

    def __init__(
        self, addresses, coin="ETH", chain="main", transactions=None, **kwargs
    ):
        coin_map = {
            "ETH": 0,
        }
        self.coin = coin_map.get(coin.upper())
        if self.coin is None:
            raise ValueError(f"Undefined coin '{coin}'")

        chain_map = {"main": 0, "sepolia": 1}
        self.chain = chain_map.get(chain)
        if self.chain is None:
            raise ValueError(f"Undefined chain '{chain}'")

        self.web3 = Web3(Web3.HTTPProvider(kwargs.get("url")))
        # This makes it fetch max<priority>feepergas info faster
        self.web3.eth.set_gas_price_strategy(fast_gas_price_strategy)
        self.web3.middleware_onion.add(middleware.time_based_cache_middleware)
        self.web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
        self.web3.middleware_onion.add(middleware.simple_cache_middleware)

        self.db_connection_parameters = kwargs.get("db_connection_parameters")
        self.transactions = []
        self.addresses = [to_checksum_address(a) for a in addresses]
        if transactions is not None and isinstance(transactions, list):
            self.transactions = transactions
        else:
            self.transactions = []

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the addresses from cached data.

        Returns:
            list: A list of transaction objects.

        Raises:
            NetworkException: If the RPC request fails or the transaction
                history cannot be retrieved.
        """
        sql_transaction_storage = SQLTransactionStorage(self.db_connection_parameters)

        try:
            transactions = []
            for address in self.addresses:
                transactions.extend(
                    sql_transaction_storage.get_transactions_by_address(address)
                )
            transactions = deduplicate(transactions)
            self.transactions = transactions
            return transactions

        except DatabaseError as e:
            raise NetworkException(f"Failed to get transaction history: {str(e)}")

    def get_block_height(self):
        """
        Retrieves the current block height.

        Returns:
            int: The current block height.

        Raises:
            NetworkException: If the API request fails or the block height
                cannot be retrieved.
        """
        try:
            return self.web3.eth.block_number
        except Exception:
            raise NetworkException("Failed to get web3 block height")

    def get_balance(self):
        """
        Retrieves the balance of the Ethereum address.

        The ETH balance can be obtained without fetching the Ethereum
        transactions first.

        Returns:
            int: The balance of the Ethereum address in Gwei.

        Raises:
            NetworkException: If the API request fails or the address balance
                cannot be retrieved.
        """
        balance = 0
        for address in self.addresses:
            try:
                balance += self.web3.eth.get_balance(address)
            except Exception:
                raise NetworkException("Failed to get web3 balance")

        # Ethereum has no unconfirmed balances or transactions.
        # But for compatibility reasons, we still return it as a 2-tuple.
        return (balance, balance)

    # In Ethereum, only one transaction per account can be included in a block
    # at a time.
    def read_mempool(self):
        sql_transaction_storage = SQLTransactionStorage(self.db_connection_parameters)

        try:
            self.height = sql_transaction_storage.get_block_height()

            # Web3.py stores unconfirmed ETH transactions in "pending".
            max_height = self.get_block_height()
            for block_number in list(range(self.block_height, max_height + 1)) + [
                "pending"
            ]:
                block = self.web3.eth.getBlock(block_number, full_transactions=True)

                if not block or "transactions" not in block:
                    continue
                transactions = block["transactions"]

                for tx_hash in transactions:
                    transaction = self.web3.eth.getTransaction(tx_hash)

                    parsed_transaction = self._clean_tx(transaction, block)
                    sql_transaction_storage.store_transaction(parsed_transaction)
        except web3.exceptions.Web3Exception as e:
            raise NetworkException(
                f"Failed to invoke get web3 transaction history: {e}"
            )
        except DatabaseError as e:
            raise NetworkException(f"Failed to get transaction history: {str(e)}")

        sql_transaction_storage.set_block_height(max_height)
        sql_transaction_storage.commit()
