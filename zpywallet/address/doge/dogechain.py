import requests
import time
import websocket
import json

from functools import reduce

from ...errors import NetworkException
from ...utils.utils import convert_to_utc_timestamp
from ...generated import wallet_pb2

def deduplicate(elements):
    return reduce(lambda re, x: re+[x] if x not in re else re, elements, [])

class DogeChainAddress:
    """
    A class representing a Dogecoin address.

    This class allows you to retrieve the balance and transaction history of a Dogecoin address using the DogeChain API.

    Args:
        address (str): The human-readable Dogecoin address.

    Attributes:
        address (str): The human-readable Dogecoin address.

    Methods:
        get_balance(): Retrieves the balance of the Dogecoin address.
        get_transaction_history(): Retrieves the transaction history of the Dogecoin address.

    Raises:
        Exception: If the API request fails or the address balance/transaction history cannot be retrieved.
    """

    def _clean_tx(self, element):
        url = f"https://dogechain.info/api/v1/transaction/{element['hash']}"
        for attempt in range(3, -1, -1):
            if attempt == 0:
                raise NetworkException("Network request failure")
            try:
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    data = element
                    element = response.json()['transaction']
                    break
                else:
                    raise NetworkException("Failed to retrieve transaction history")
            except requests.RequestException:
                pass

        new_element = wallet_pb2.Transaction()
        new_element.txid = element['hash']
        
        if element['confirmations'] == 0:
            new_element.confirmed = False
            new_element.height = 0
        else:
            new_element.confirmed = True
            url = f"https://dogechain.info/api/v1/block/{element['block_hash']}"
            for attempt in range(3, -1, -1):
                if attempt == 0:
                    raise NetworkException("Network request failure")
                try:
                    response = requests.get(url, timeout=60)
                    if response.status_code == 200:
                        new_element.height = response.json()['block']['height']
                        break
                    else:
                        raise NetworkException("Failed to retrieve transaction history")
                except requests.RequestException:
                    pass
        
        new_element.timestamp = element['time']
        
        for vin in element['inputs']:
            txinput = new_element.btclike_transaction.inputs.add()
            txinput.txid = '' if 'previous_output' not in vin.keys() else vin['previous_output'].get('hash') or ''
            txinput.index = 0 if 'previous_output' not in vin.keys() else vin['previous_output'].get('pos') or 0
            txinput.amount = 0 if 'value' not in vin.keys() else int(float(vin['value']) * 1e8)
        
        i = 0
        for vout in element['outputs']:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(float(vout['value']) * 1e8)
            txoutput.index = i
            i += 1
            txoutput.address = vout['address']
            txoutput.spent = vout['spent'] is not None
        
        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])
        new_element.total_fee = total_inputs - total_outputs

        new_element.btclike_transaction.fee = int(float(element['fee']) * 1e8)
        new_element.fee_metric = wallet_pb2.BYTE
        
        return new_element

    def __init__(self, addresses, request_interval=(3,1), transactions=None):
        """
        Initializes an instance of the DogeChainAddress class.

        Args:
            addresses (list): A list of human-readable Dogecoin addresses.
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0,N) for no rate limiting, where N>0.
        """
        self.addresses = addresses
        self.requests, self.interval_sec = request_interval
        if transactions is not None and isinstance(transactions, list):
            self.transactions = transactions
        else:
            self.transactions = []

    def sync(self):
        self.transactions = deduplicate([*self._get_transaction_history()])
        self.height = self.get_block_height()

    def get_balance(self):
        """
        Retrieves the balance of the Dogecoin address.

        Returns:
            float: The balance of the Dogecoin address in BTC.

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
            for out in self.transactions[i].outputs:
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

    def get_block_height(self):
        """Returns the current block height."""

        # Dogechain gives us the block height through a web socket
        # This only works because the block mining for Dogecoin is very fast.
        uri = "wss://ws.dogechain.info/inv"
        for attempt in range(3, -1, -1):
            if attempt == 0:
                                raise NetworkException("Network request failure")
            try:
                ws = websocket.create_connection(uri)
                message = {"op": "ping_block"}
                ws.send(json.dumps(message))

                # Ignore the pong response
                ws.recv()
                # And get the real response
                response = json.loads(ws.recv())
            except requests.RequestException:
                pass
            finally:
                try:
                    ws.close()
                except Exception:
                    pass
                break
        
        self.height = response['x']['height']
        return self.height
        

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Dogecoin address from cached data augmented with network data.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        if len(self.transactions) == 0:
            self.transactions = [*self._get_transaction_history()]
        else:
            # First element is the most recent transactions
            txhash = self.transactions[0].txid
            txs = [*self._get_transaction_history(txhash)]
            txs.extend(self.transactions)
            self.transactions = txs

        self.transactions = deduplicate(self.transactions)
        return self.transactions

    def _get_transaction_history(self, txhash=None):
        """
        Retrieves the transaction history of the Dogecoin address. (internal method that makes the network query)

        Parameters:
            txhash (str): Get all transactions before (and not including) txhash.
                Defaults to None, which disables this behavior.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        for address in self.addresses:
            i = 1
            url = f"https://dogechain.info/api/v1/address/transactions/{address}/{i}"
            for attempt in range(3, -1, -1):
                if attempt == 0:
                    raise NetworkException("Network request failure")
                try:
                    response = requests.get(url, timeout=60)
                    if response.status_code == 200:
                        data = response.json()
                        break
                    else:
                                                raise NetworkException("Failed to retrieve transaction history")
                except requests.RequestException:
                    pass

            for tx in data["transactions"]:
                time.sleep(self.interval_sec/(self.requests*len(data["transactions"])))
                if txhash and tx["hash"] == txhash:
                    return
                yield self._clean_tx(tx)
            if not data["transactions"]:
                return
            
            while data["transactions"]:
                i += 1
                url = f"https://dogechain.info/api/v1/address/transactions/{address}/{i}"
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
                    for tx in data["transactions"]:
                        time.sleep(self.interval_sec/(self.requests*len(data["transactions"])))
                        if txhash and tx["hash"] == txhash:
                            return
                        yield self._clean_tx(tx)
                    if not data["transactions"]:
                        return
                else:
                                        raise NetworkException("Failed to retrieve transaction history")
