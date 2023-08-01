import requests
import time

from ...errors import NetworkException

class BTCcomAddress:
    """
    A class representing a Bitcoin address.

    This class allows you to retrieve the balance and transaction history of a Bitcoin address using the BTC.com API.

    Args:
        api_key (str): The API key for accessing the BTC.com API.

    Attributes:
        api_key (str): The API key for accessing the BTC.com API.

    Methods:
        get_balance(): Retrieves the balance of the Bitcoin address.
        get_transaction_history(): Retrieves the transaction history of the Bitcoin address.

    Raises:
        Exception: If the API request fails or the address balance/transaction history cannot be retrieved.
    """

    def _clean_tx(self, element):
        new_element = {}
        new_element['txid'] = element['hash']
        new_element['height'] = element['block_height']
        new_element['timestamp'] = None

        new_element['inputs'] = []
        new_element['outputs'] = []
        for vin in element['inputs']:
            txinput = {}
            txinput['txid'] = vin['prev_tx_hash']
            txinput['index'] = vin['prev_position']
            txinput['amount'] = vin['prev_value'] / 1e8
            new_element['inputs'].append(txinput)

        i = 0 
        for vout in element['outputs']:
            txoutput = {}
            txoutput['amount'] = vout['value'] / 1e8
            txoutput['index'] = i
            i += 1
            if 'addresses' in vout.keys():
                txoutput['address'] = vout['addresses'][0]
            else:
                txoutput['address'] = ''
            txoutput['spent'] = vout['spent_by_tx'] != ""
            new_element['outputs'].append(txoutput)

        # Now we must calculate the total fee
        total_inputs = sum([a['amount'] for a in new_element['inputs']])
        total_outputs = sum([a['amount'] for a in new_element['outputs']])
        new_element['total_fee'] = (total_inputs - total_outputs) / 1e8

        new_element['fee'] = (total_inputs - total_outputs) / element['vsize']
        new_element['fee'] = 'vbyte'
        return new_element

    # BTC.com's rate limits are unknown.
    def __init__(self, addresses, request_interval=(1000,1), transactions=None):
        """
        Initializes an instance of the BTCcomAddress class.

        Args:
            addresses (list): A list of human-readable Bitcoin addresses.
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0,N) for no rate limiting, where N>0.
        """
        self.requests, self.interval_sec = request_interval
        self.addresses = addresses
        if transactions:
            self.transactions = transactions
        else:
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
            # Careful: Block height #0 is the Genesis block - don't want to exclude that.
            if utxo["height"] is not None:
                confirmed_balance += utxo["amount"]
        return total_balance, confirmed_balance
        
    def get_utxos(self):
        self.height = self.get_block_height()
        # Transactions are generated in reverse order
        utxos = []
        for i in range(len(self.transactions)-1, -1, -1):
            for utxo in [u for u in utxos]:
                # Check if any utxo has been spent in this transaction
                for vin in self.transactions[i]["inputs"]:
                    if vin["txid"] == utxo["txid"] and vin["index"] == utxo["index"]:
                        # Spent
                        utxos.remove(utxo)
            for out in self.transactions[i]["outputs"]:
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
        # Get the current block height now:
        url = "https://chain.api.btc.com/v3/block/latest"
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
            self.height = data["data"]["height"]
        else:
            try:
                return self.height
            except AttributeError as exc:
                raise NetworkException("Failed to retrieve current blockchain height") from exc

        
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
        for address in self.addresses:
            page = 1
            pagesize = 50

            url = f"https://chain.api.btc.com/v3/address/{address}/tx?page={page}&pagesize={pagesize}"
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
                if data["data"]["list"] is None:
                    return
                for tx in data["data"]["list"]:
                    time.sleep(self.interval_sec/(self.requests*len(data["data"]["list"])))
                    if txhash and tx["hash"] == txhash:
                        return
                    yield self._clean_tx(tx)
                page += 1
            else:
                raise NetworkException("Failed to retrieve transaction history")
            

            while data["data"]["list"] is not None: 
                url = f"https://chain.api.btc.com/v3/address/{address}/tx?page={page}&pagesize={pagesize}"
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
                    if data["data"]["list"] is None:
                        return
                    for tx in data["data"]["list"]:
                        time.sleep(self.interval_sec/(self.requests*len(data["data"]["list"])))
                        if txhash and tx["hash"] == txhash:
                            return
                        yield self._clean_tx(tx)
                    page += 1
                else:
                    raise NetworkException("Failed to retrieve transaction history")
