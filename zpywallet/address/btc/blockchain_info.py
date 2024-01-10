import requests
import time

from ...errors import NetworkException
from ...generated import wallet_pb2

class BlockchainInfoAddress:
    """
    A class representing a Bitcoin address.

    This class allows you to retrieve the balance and transaction history of a Bitcoin address using the Blockchain.info API.

    The rate limits are 1 request per 10 seconds.

    THIS CLASS IS NOT RECOMMENDED for fetching transaction lists, because there's no way to get the transaction ID of inputs,
    and also because it does not return transaction vsize which is the measurement unit used by segwit blockchains.
    And speaking of blockchains, this backend only supports the Bitcoin mainnet.

    As a side effect of this, it is impossible to determine which transactions are RBFs and/or double-spends and exclude them
    accordingly. This means total balance may be incorrect. However, confirmed balance will still be correct in any case.

    Args:
        address (str): The human-readable Bitcoin address.

    Attributes:
        address (str): The human-readable Bitcoin address.
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
    def __init__(self, addresses, request_interval=(1,10), transactions=None):
        """
        Initializes an instance of the Address class.

        Args:
            addresses (list): A list of human-readable Bitcoin addresses.
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
        self.transactions = [*self._get_transaction_history()]
        self.height = self.get_block_height()

    def _clean_tx(self, element):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element['hash']
        if 'block_height' in element.keys() and element['block_height'] is not None:
            new_element.confirmed = True
            new_element.height = element['block_height']
        else:
            new_element.confirmed = False

        if new_element.confirmed:
            new_element.timestamp = element['time']

        for vin in element['inputs']:
            txinput = new_element.btclike_transaction.inputs.add()
            # Blockchain.info is crazy!
            # It has no input txid, only the address
            # So for now, we will substitute the address for the txid,
            # and once we get a sane API, we can fill in the txid properly.
            # (It also only supports Bitcoin, so there's that.)
            txinput.index = vin['prev_out']['n']
            txinput.amount = int(vin['prev_out']['value'] * 1e8)
        
        for vout in element['out']:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(vout['value'] * 1e8)
            txoutput.index = vout['n']
            if 'addr' in vout.keys():
                txoutput.address = vout['addr']
            txoutput.spent = vout['spent']
        
        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])
        new_element.total_fee = total_inputs - total_outputs

        # Blockchain.info API does not support vbytes. It only returns bytes.
        new_element.btclike_transaction.fee = int(new_element.total_fee // element['size'])
        new_element.fee_metric = wallet_pb2.BYTE
        
        return new_element

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
        
        # Now we would've gone through the UTXOs *again* to eliminate the RBF-replaced UTXOs.
        # The issue we are going to have is, *any* of the inputs could be the identical
        # one, because it only takes one input to perform an RBF.

        # Unfortunately we CANNOT filter Blockchain.info UTXOs because they do not give us
        # the txids of inputs, and even the balance endpoint in the Blockchain Data API
        # returns the wrong total balance using exactly the same calculation.
        # Confirmed balances are not affected and still correct.


    def get_block_height(self):
        # Get the current block height now:
        url = "https://blockchain.info/latestblock"
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
            return response.json()["height"]
        else:
            raise NetworkException("Cannot get block height")


    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Bitcoin address from cached data augmented with network data.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        self.height = self.get_block_height()
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
            interval = 50
            offset = 0

            url = f"https://blockchain.info/rawaddr/{address}?limit={interval}&offset={offset}"
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

                # The rate limit is 1 request every 10 seconds, so we will amortize the speed bump by sleeping every 200 milliseconds.
                # Since we have max 50 transactions, total execution time will be at least 10 seconds incuding the sleep time and user
                # code execution time, and if there are less than 50 transactions, we are finished fetching transactions anyway.
                for tx in data["txs"]:
                    time.sleep(self.interval_sec/(self.requests*len(data["txs"])))
                    if txhash and tx["hash"] == txhash:
                        return
                    yield self._clean_tx(tx)
                n_tx = data["n_tx"]
                offset += min(interval, n_tx)
            else:
                raise NetworkException("Failed to retrieve transaction history")
            
            while offset < n_tx:
                # WARNING: RATE LIMIT IS 1 REQUEST PER 10 SECONDS.
                url = f"https://blockchain.info/rawaddr/{address}?limit={interval}&offset={offset}"
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
                    offset += interval
                else:
                    raise NetworkException("Failed to retrieve transaction history")
