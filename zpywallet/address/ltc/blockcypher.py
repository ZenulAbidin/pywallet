from functools import reduce
import time
import requests

from ...errors import NetworkException
from ...utils.utils import convert_to_utc_timestamp
from ...generated.wallet_pb2 import VBYTE

def deduplicate(elements):
    return reduce(lambda re, x: re+[x] if x not in re else re, elements, [])

class BlockcypherAddress:
    """
    A class representing a Litecoin address.

    This class allows you to retrieve the balance and transaction history of a Litecoin address using the Blockcypher API.

    Args:
        address (str): The human-readable Litecoin address.
        api_key (str): The API key for accessing the Blockcypher API.

    Attributes:
        address (str): The human-readable Litecoin address.
        api_key (str): The API key for accessing the Blockcypher API.

    Methods:
        get_balance(): Retrieves the balance of the Litecoin address.
        get_transaction_history(): Retrieves the transaction history of the Litecoin address.

    Raises:
        Exception: If the API request fails or the address balance/transaction history cannot be retrieved.
    """

    def _clean_tx(self, element):
        new_element = {}
        new_element['txid'] = element['hash']
        new_element['height'] = None if 'block_height' not in element.keys() else element['block_height']
        if element['block_index'] == 0:
            new_element['height'] = 0
        elif element['block_height'] == -1:
            new_element['height'] = None
        new_element['timestamp'] = None if not 'confirmed' in element.keys() else convert_to_utc_timestamp(element['confirmed'].split(".")[0].split('Z')[0], '%Y-%m-%dT%H:%M:%S')

        new_element['inputs'] = []
        new_element['outputs'] = []
        for vin in element['inputs']:
            txinput = {}
            txinput['txid'] = '' if 'prev_hash' not in vin.keys() else vin['prev_hash']
            txinput['index'] = vin['output_index']
            txinput['amount'] = 0 if 'output_value' not in vin.keys() else vin['output_value'] / 1e8
            new_element['inputs'].append(txinput)
        
        i = 0
        for vout in element['outputs']:
            txoutput = {}
            txoutput['amount'] = vout['value'] / 1e8
            txoutput['index'] = i
            i += 1
            txoutput['address'] = None if not vout['addresses'] else vout['addresses'][0]
            txoutput['spent'] = 'spent_by' in vout.keys()
            new_element['outputs'].append(txoutput)
        
        # Now we must calculate the total fee
        total_inputs = sum([a['amount'] for a in new_element['inputs']])
        total_outputs = sum([a['amount'] for a in new_element['outputs']])
        new_element['total_fee'] = total_inputs - total_outputs

        size_element = element['vsize'] if 'vsize' in element.keys() else element['size']
        new_element['fee'] = new_element['total_fee'] / size_element
        new_element['fee_metric'] = VBYTE
        
        return new_element

    def __init__(self, addresses, request_interval=(3,1), transactions=None):
        """
        Initializes an instance of the BlockcypherAddress class.

        Args:
            addresses (list): A list of human-readable Litecoin addresses.
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0,N) for no rate limiting, where N>0.
        """
        self.addresses = addresses
        self.requests, self.interval_sec = request_interval
        if transactions:
            self.transactions = transactions
        else:
            self.transactions = deduplicate([*self._get_transaction_history()])
        self.height = self.get_block_height()

    def get_balance(self):
        """
        Retrieves the balance of the Litecoin address.

        Returns:
            float: The balance of the Litecoin address in BTC.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        utxos = self.get_utxos()
        total_balance = 0
        confirmed_balance = 0
        for utxo in utxos:
            total_balance += utxo["amount"]
            # Careful: Block height #0 is the Genesis block - don't want to exclude that.
            if utxo["height"] is not None:
                confirmed_balance += utxo["amount"]
        return total_balance, confirmed_balance
        
    def get_utxos(self):
        # Transactions are generated in reverse order
        utxos = []
        for i in range(len(self.transactions)-1, -1, -1):
            for out in self.transactions[i]["outputs"]:
                if out['spent']:
                    continue
                if out["address"] in self.addresses:
                    utxo = {}
                    utxo["address"] = out["address"]
                    utxo["txid"] = self.transactions[i]["txid"]
                    utxo["index"] = out["index"]
                    utxo["amount"] = out["amount"]
                    utxo["height"] = self.transactions[i]["height"]
                    utxos.append(utxo)
        return utxos

    def get_block_height(self):
        """Returns the current block height."""

        url = "https://api.blockcypher.com/v1/ltc/main"
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
        Retrieves the transaction history of the Litecoin address from cached data augmented with network data.

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
        
        self.transactions = deduplicate(self.transactions)
        return self.transactions

    def _get_transaction_history(self, txhash=None):
        """
        Retrieves the transaction history of the Litecoin address. (internal method that makes the network query)

        Parameters:
            txhash (str): Get all transactions before (and not including) txhash.
                Defaults to None, which disables this behavior.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        for address in self.addresses:
            interval = 50
            block_height = 0

            # Set a very high UTXO limit for those rare address that have crazy high input/output counts.
            txlimit = 10000

            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/full?limit={interval}&txlimit={txlimit}"
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
                if 'hasMore' not in data.keys():
                    return
                else:
                    block_height = data["txs"][-1]["block_height"]
            else:
                raise NetworkException("Failed to retrieve transaction history")
            
            while 'hasMore' in data.keys() and data['hasMore']:
                url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/full?limit={interval}&before={block_height}&txlimit={txlimit}"
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
                    if 'hasMore' not in data.keys():
                        return
                    else:
                        block_height = data["txs"][-1]["block_height"]
                else:
                    raise NetworkException("Failed to retrieve transaction history")
