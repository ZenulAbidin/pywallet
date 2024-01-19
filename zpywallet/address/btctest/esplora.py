import time
import requests

from ...errors import NetworkException
from ...generated import wallet_pb2

class EsploraAddress:
    """
    A class representing a Bitcoin address.

    This class allows you to retrieve the balance and transaction history of a Bitcoin address using the Esplora API.
    Esplora is deployed on many popular websites, including mempool.space (Rate limited) and blockstream.info.

    Note: Esplora has a built-in limitation of returning up to 50 unconfirmed transactions per address. While this should be
    large enough for most use cases, if you run into problems, try using a different address provider.

    Note 2: This API will not return the Genesis block in transactions, unlike the other balances. This will affect
    balance displayed for Satoshi's first address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa - but that output is unspendable anyway.

    Args:
        address (str): The human-readable Bitcoin address.

    Attributes:
        address (str): The human-readable Bitcoin address.
        endpoint (str): The Esplora endpoint to use. Defaults to Blockstream's endpoint.
        transaction_history (list): The cached list of transactions.
        height (int): The last known block height.

    Methods:
        get_balance(): Retrieves the total and confirmed balances of the Bitcoin address.
        get_utxos(): Retrieves the UTXO set for this address
        get_block_height(): Retrieves the current block height.
        get_transaction_history(): Retrieves the transaction history of the Bitcoin address.

    Raises:
        Exception: If the API request fails or the address balance/transaction history cannot be retrieved.
    """

    def _clean_tx(self, element):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element['txid']
        if 'block_height' in element['status'].keys():
            new_element.confirmed = True
            new_element.height = element['status']['block_height']
        else:
            new_element.confirmed = False
            
        if new_element.confirmed:
            new_element.timestamp = element['status']['block_time']

        for vin in element['vin']:
            txinput = new_element.btclike_transaction.inputs.add()
            txinput.txid = vin['txid']
            txinput.index = vin['vout']
            if vin['prevout'] is not None:
                txinput.amount = int(vin['prevout']['value'])
            else:
                txinput.amount = int(0)

        i = 0
        for vout in element['vout']:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(vout['value'])
            txoutput.index = i
            i += 1
            if 'scriptpubkey_address' in vout.keys():
                txoutput.address = vout['scriptpubkey_address']

        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])

        new_element.total_fee = (total_inputs - total_outputs)

        new_element.btclike_transaction.fee = int(element['fee'])
        new_element.fee_metric = wallet_pb2.VBYTE
        return new_element

    def __init__(self, addresses, request_interval=(3,1), transactions=None, **kwargs):
        """
        Initializes an instance of the EsploraAddress class.

        Args:
            addresses (list): A list of human-readable Bitcoin addresses.
            endpoint (str): The Esplora endpoint to use.
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0,N) for no rate limiting, where N>0.
        """
        # Blockstream.info's rate limits are unknown.
        # Ostensibly there are no limits for that site, but I got 429 errors when testing with (1000,1), so
        # the default limit will be the same as for mempool.space - 3 requests per second.
        self.requests, self.interval_sec = request_interval
        self.addresses = addresses
        self.endpoint = kwargs.get('url')
        if transactions is not None and isinstance(transactions, list):
            self.transactions = transactions
        else:
            self.transactions = []

    def sync(self):
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
        # Get the current block height now:
        url = f"{self.endpoint}/blocks/tip/height"
        for attempt in range(3, -1, -1):
            if attempt == 0:
                raise NetworkException("Network request failure")
            try:
                response = requests.get(url, timeout=60)
                break
            except requests.RequestException:
                pass
            except requests.exceptions.JSONDecodeError:
                pass
        
        if response.status_code == 200:
            self.height = int(response.text)
            return self.height
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
            self.transactions = [*self._get_transaction_history()]
        else:
            # First element is the most recent transactions
            txhash = self.transactions[0].txid
            txs = [*self._get_transaction_history(txhash)]
            txs.extend(self.transactions)
            self.transactions = txs
                    
        return self.transactions

    def _get_transaction_history(self, txhash=None):
        """
        Retrieves the transaction history of the Bitcoin address.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        for address in self.addresses:
            # This gets up to 50 mempool transactions + up to 25 confirmed transactions
            url = f"{self.endpoint}/address/{address}/txs"
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

            for tx in data:
                time.sleep(self.interval_sec/(self.requests*len(data)))
                if txhash and tx["txid"] == txhash:
                    return
                yield self._clean_tx(tx)
            
            if len(data) > 0:
                last_tx = data[-1]["txid"]
            else:
                break
            
            while len(data) > 0:
                url = f"{self.endpoint}/address/{address}/txs/chain/{last_tx}"
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
                    for tx in data:
                        time.sleep(self.interval_sec/(self.requests*len(data)))
                        if txhash and tx["hash"] == txhash:
                            return
                        yield self._clean_tx(tx)
                    if len(data) > 0:
                        last_tx = data[-1]["txid"]
                else:
                    raise NetworkException("Failed to retrieve transaction history")

