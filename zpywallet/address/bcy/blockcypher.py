import requests
import time

from ...errors import NetworkException
from ...utils.utils import convert_to_utc_timestamp

class BlockcypherAddress:
    """
    A class representing a Bitcoin address.

    This class allows you to retrieve the balance and transaction history of a Bitcoin address using the Blockcypher API.

    Args:
        address (str): The human-readable Bitcoin address.
        api_key (str): The API key for accessing the Blockcypher API.

    Attributes:
        address (str): The human-readable Bitcoin address.
        api_key (str): The API key for accessing the Blockcypher API.

    Methods:
        get_balance(): Retrieves the balance of the Bitcoin address.
        get_transaction_history(): Retrieves the transaction history of the Bitcoin address.

    Raises:
        Exception: If the API request fails or the address balance/transaction history cannot be retrieved.
    """

    def _clean_tx(self, element):
        new_element = {}
        new_element['txid'] = element['txid']
        new_element['height'] = element['block_height']
        new_element['timestamp'] = convert_to_utc_timestamp(element['received'])

        new_element['inputs'] = []
        new_element['outputs'] = []
        for vin in element['inputs']:
            txinput = {}
            txinput['txid'] = vin['prev_hash']
            txinput['index'] = vin['output_index']
            txinput['amount'] = vin['output_value'] / 1e8
            new_element['inputs'].append(txinput)
        
        i = 0
        for vout in element['vout']:
            txoutput = {}
            txoutput['amount'] = vout['value'] / 1e8
            txoutput['index'] = i
            i += 1
            txoutput['address'] = vout['addresses'][0]
            txoutput['spent'] = 'spent_by' in vout.keys()
            new_element['outputs'].append(txoutput)
        
        # Now we must calculate the total fee
        total_inputs = sum([a['amount'] for a in new_element['inputs']])
        total_outputs = sum([a['amount'] for a in new_element['outputs']])
        new_element['total_fee'] = total_inputs - total_outputs

        size_element = element['vsize'] if 'vsize' in element.keys() else element['size']
        new_element['fee'] = new_element['total_fee'] / size_element
        new_element['fee'] = 'byte'
        
        return new_element

    def __init__(self, address, request_interval=(3,1)):
        """
        Initializes an instance of the BlockcypherAddress class.

        Args:
            address (str): The human-readable Bitcoin address.
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0,N) for no rate limiting, where N>0.
        """
        self.address = address
        self.requests, self.interval_sec = request_interval
        self.transactions = [*self._get_transaction_history()]
        self.height = self.get_block_height()

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
            total_balance += utxo["amount"]
            if utxo["height"] > 0:
                confirmed_balance += utxo["amount"]
        return total_balance, confirmed_balance
        
    def get_utxos(self):
        # Transactions are generated in reverse order
        utxos = []
        for i in range(len(self.transactions)-1, -1, -1):
            for out in self.transactions[i]["outputs"]:
                if out['spent']:
                    continue
                if out["addr"] == self.address:
                    utxo = {}
                    utxo["address"] = self.address
                    utxo["txid"] = self.transactions[i]["txid"]
                    utxo["index"] = out["index"]
                    utxo["amount"] = out["amount"]
                    utxo["height"] = self.transactions[i]["height"]
                    utxos.append(utxo)
        return utxos

    def get_block_height(self):
        """Returns the current block height."""

        url = "https://api.blockcypher.com/v1/bcy/test"
        for attempt in range(3, -1, -1):
            if attempt == 0:
                raise NetworkException("Network request failure")
            try:
                response = requests.get(url, timeout=60)
                break
            except requests.RequestException:
                pass

        if response.status_code == 200:
            data = response.json()
            self.height = data["height"]
            return self.height
        else:
            raise NetworkException("Failed to retrieve block height")

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Bitcoin address from cached data augmented with network data.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        if len(self.transactions) == 0:
            self.transactions = [*self.get_transaction_history()]
        else:
            # First element is the most recent transactions
            txhash = self.transactions[0]["txid"]
            txs = [*self._get_transaction_history(txhash)]
            txs.extend(self.transactions)
            self.transactions = txs
            del txs
        
        return self.transactions

    def _get_transaction_history(self, txhash=None):
        """
        Retrieves the transaction history of the Bitcoin address. (internal method that makes the network query)

        Parameters:
            txhash (str): Get all transactions before (and not including) txhash.
                Defaults to None, which disables this behavior.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        interval = 50
        block_height = 0

        url = f"https://api.blockcypher.com/v1/bcy/test/addrs/{self.address}/full?limit={interval}"
        for attempt in range(3, -1, -1):
            if attempt == 0:
                raise NetworkException("Network request failure")
            try:
                response = requests.get(url, timeout=60)
                break
            except requests.RequestException:
                pass

        if response.status_code == 200:
            data = response.json()
            for tx in data["txs"]:
                time.sleep(self.interval_sec/(self.requests*len(data["txs"])))
                if txhash and tx["hash"] == txhash:
                    return
                yield self._clean_tx(tx)
            block_height = data["txs"][-1]["block_height"]
        else:
            raise NetworkException("Failed to retrieve transaction history")
        
        while len(data["txs"]) > 0:
            url = f"https://api.blockcypher.com/v1/bcy/test/addrs/{self.address}/full?limit={interval}&before={block_height}"
            for attempt in range(3, -1, -1):
                if attempt == 0:
                    raise NetworkException("Network request failure")
                try:
                    response = requests.get(url, timeout=60)
                    break
                except requests.RequestException:
                    pass

            if response.status_code == 200:
                data = response.json()
                for tx in data["txs"]:
                    time.sleep(self.interval_sec/(self.requests*len(data["txs"])))
                    if txhash and tx["hash"] == txhash:
                        return
                    yield self._clean_tx(tx)
                block_height = data["txs"][-1]["block_height"]
            else:
                raise NetworkException("Failed to retrieve transaction history")
