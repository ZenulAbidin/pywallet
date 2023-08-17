import random
import requests

from ...errors import NetworkException
from ...utils.utils import eth_transaction_hash
from ...generated import wallet_pb2


class EthereumRPCClient:
    """ Address querying class for Ethereum full nodes and Web3 clients.
        Most 3rd party providers e.g. Infura, QuickNode will also work here.
 
        WARNING: Ethereum nodes have a --txlookuplimit and maintain the last N transactions only,
        unless this option is turned off. 3rd party providers should have this switched off, but
        ensure it is turned off if you are running your own node.
    """
    
    def _clean_tx(self, element):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element['hash']
        if 'blockNumber' in element.keys():
            new_element.confirmed = True
            new_element.height = element['blockNumber']
        else:
            new_element.confirmed = False

        new_element.ethlike_transaction.txfrom = element['from']
        new_element.ethlike_transaction.txto = element['to']
        new_element.ethlike_transaction.amount = element['value']
        

        block = self._send_rpc_request('eth_getBlockByHash', params=[element['blockHash'], False])
        new_element.timestamp = hex(block["result"]["timestamp"], 16)
        new_element.ethlike_transaction.data = element['input']

        gas = int(element['gas'], 16)
        new_element.ethlike_transaction.gas = gas
        if 'maxFeePerGas' in element.keys():
            new_element.total_fee = int(element['maxFeePerGas'], 16) * gas
        else:
            new_element.total_fee = int(element['gasPrice']) * gas

        new_element.fee_metric = wallet_pb2.WEI
        return new_element

    def __init__(self, addresses, rpc_url, transactions=None):
        self.rpc_url = rpc_url

        self.transactions = []
        self.addresses = addresses
        self.height = self.get_block_height()
        if transactions is not None and isinstance(transactions, list):
            self.transactions = transactions
        else:
            self.transactions = [*self._get_transaction_history()]
    
    def _send_rpc_request(self, method, params=None):
        payload = {
            'method': method,
            'params': params or [],
            'jsonrpc': '2.0',
            'id': random.randint(1, 999999)
        }
        # Full nodes wallet RPC requests are notoriously slow if there are many transactions in the node.
        response = requests.post(self.rpc_url, json=payload, timeout=86400)
        #response.raise_for_status()
        return response.json()
    
    def get_block_height(self):
        response = self._send_rpc_request('getblockchaininfo')
        return response['result']['blocks']
    
    def get_balance(self):
        """
        Retrieves the balance of the Ethereum address.

        Returns:
            float: The balance of the Ethereum address in BTC.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        txs = self.transactions
        total_balance = 0
        confirmed_balance = 0
        for tx in txs:
            total_balance += tx.amount
            # Careful: Block height #0 is the Genesis block - don't want to exclude that.
            if tx.height is not None:
                confirmed_balance += tx.amount
        return total_balance, confirmed_balance
    
    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Ethereum address from cached data augmented with network data.
        Does not include Genesis blocks.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the RPC request fails or the transaction history cannot be retrieved.
        """
        if len(self.transactions) == 0:
            self.transactions = [*self.get_transaction_history()]
        else:
            # First element is the most recent transactions
            txhash = self.transactions[0].txid
            txs = [*self._get_transaction_history(txhash)]
            txs.extend(self.transactions)
            self.transactions = txs
            del txs
    
    def _get_transaction_history(self, txhash=None):

        for address in self.addresses:
            # Get the number of transactions
            total_transactions = self._send_rpc_request('eth_getTransactionCount')
            try:
                total_transactions = int(total_transactions['result'], 16)
            except KeyError as e:
                raise NetworkException("Error while fetching address transaction count") from e

            
            for i in range(total_transactions):
                transaction_hash = eth_transaction_hash(address, i)
                # listtransactions by default return only 10 most recent transactions)
                result = self._send_rpc_request('eth_getTransactionByHash', params=["*", transaction_hash, "latest"])
                transactions = result['result']
                
                # Extract the transaction IDs so we can query them verbosely
                # because the tx doesn't include info on other addresses
                for tx in transactions:
                    txid = tx['txid']
                    if txid == txhash:
                        return
                    yield self._clean_tx(tx)
            
        
