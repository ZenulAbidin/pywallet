import random
import requests

from ...errors import NetworkException
from ...utils.descriptors import descsum_create_only

def to_descriptor(address):
    ad = f"addr({address})"
    return f"{ad}#{descsum_create_only(ad)}"

def to_extpub_descriptor(expub, path):
    """
    Creates a descriptor out of the extended public key `expub`,
    and a path `path`.

    Parameters:
        expub (str): an extended public key. Can have any valid prefix, e.g. xpub, ypub, zpub, etc.
        path (str): a path string in the form of (for example) "m/0/0'/1". A non-hardened number
            can be replaced with '*' to fill in a range for a later RPC call. This can only be specified once.
             The path must start with 'm/'.
    
    Returns:
        str: A descriptor string.
    """
    if path[:2] != "m/":
        raise NetworkException("Path must start with 'm/")
    desc = expub + path[1:]
    return f"{desc}#{descsum_create_only(desc)}"

class BitcoinRPCClient:
    """Address querying class for Bitcoin full nodes utilizing descriptors.
       Requires node version v0.17.0 or later running with -txindex.
    """

    @staticmethod
    def _clean_utxos(element):
        new_element = {
            "txid": element["txid"],
            "index": element["vout"],
            "amount": element["amount"], # should be in the base value, eg. BTC, LTC, not sats or gwei
            "height": element["height"],
            "address": element["address"]
        }
        return new_element
    
    # Not static because we need to make calls to fetch input transactions.
    def _clean_tx(self, element):
        new_element = {}
        new_element['txid'] = element['txid']
        new_element['height'] = element['block_height']
        new_element['timestamp'] = element['time']
        element = element['decoded']

        new_element['inputs'] = []
        new_element['outputs'] = []
        for vin in element['vin']:
            txinput = {}
            txinput['txid'] = vin['txid']
            txinput['index'] = vin['vout']
            # To fill in the amount, we have to get the other transaction id
            res = self._send_rpc_request('gettransaction', params=[vin['txid'], True, True], as_wallet=True)
            txinput['amount'] = res['result']['decoded']['vout'][vin['vout']]['value']

            new_element['inputs'].append(txinput)
        for vout in element['vout']:
            txoutput = {}
            txoutput['amount'] = vout['value']
            txoutput['index'] = vout['n']
            txoutput['address'] = vout['scriptPubKey']['address']
            new_element['outputs'].append(txoutput)
        
        # Now we must calculate the total fee
        total_inputs = sum([a['amount'] for a in new_element['inputs']])
        total_outputs = sum([a['amount'] for a in new_element['outputs']])

        new_element['total_fee'] = (total_inputs - total_outputs) / 1e8

        new_element['fee'] = (total_inputs - total_outputs) / element['vsize']
        new_element['fee_metric'] = 'vbyte'
        return new_element

    def __init__(self, rpc_url, rpc_user, rpc_password, client_number=0, user_id=0, block_height=0, max_tx_at_once=1000):
        self.rpc_url = rpc_url
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.client_number = client_number
        self.user_id = user_id
        self.block_height = block_height
        self.max_tx_at_once = max_tx_at_once
    
    def _send_rpc_request(self, method, params=None, as_wallet=False):
        payload = {
            'method': method,
            'params': params or [],
            'jsonrpc': '2.0',
            'id': random.randint(1, 999999)
        }
        # Full nodes wallet RPC requests are notoriously slow if there are many transactions in the node.
        response = requests.post(f"{self.rpc_url}/wallet/zpywallet_{self.client_number}_{self.user_id}" if as_wallet \
                                 else self.rpc_url, auth=(self.rpc_user, self.rpc_password), json=payload, timeout=86400)
        #response.raise_for_status()
        return response.json()
    
    def get_block_height(self):
        # set self.block_height here
        response = self._send_rpc_request('getblockchaininfo')
        return response['result']['blocks']

    def load_addresses(self, addresses):
        # Create a new temporary wallet
        self._send_rpc_request('createwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])
        
        block_height = self.block_height
        block_height = min(block_height, self.get_block_height())


        params = [*map(lambda at: {"desc": to_descriptor(at), "timestamp": block_height}, addresses)]

        try:
            # Load the temporary wallet
            self._send_rpc_request('loadwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])
            
            # Import the address into the wallet
            self._send_rpc_request('importdescriptors', params=[params], as_wallet=True)
            self.block_height = self.get_block_height()
        
        finally:
            # Unload the temporary wallet
            self._send_rpc_request('unloadwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])
    
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
        try:
            # Load the temporary wallet
            self._send_rpc_request('loadwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])
            
                # Get UTXOs for the imported address
            result = self._send_rpc_request('listunspent', params=[0, 99999999], as_wallet=True)
            utxos = BitcoinRPCClient._clean_utxos(result['result'])
            return utxos
        
        finally:
            # Unload and delete the temporary wallet
            self._send_rpc_request('unloadwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])
    
    def get_transaction_history(self):
        try:
            # Load the temporary wallet
            self._send_rpc_request('loadwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])
            
             # Get the number of transactions
            total_transactions = self._send_rpc_request('getwalletinfo', as_wallet=True)['result']['txcount']

            skip_later_txs = total_transactions - self.max_tx_at_once
            while skip_later_txs > -self.max_tx_at_once:

                # If the subtraction gave us a negative skip offset, just make it zero to get the last most recent few transactions
                skip_later_txs = max(skip_later_txs, 0)
                # listtransactions by default return only 10 most recent transactions)
                # However, we cannot simply just make this a huge number, otherwise we will run out of memory if the wallet
                # has too many (in the hundreds of thousands) transactions.
                result = self._send_rpc_request('listtransactions', params=["*", self.max_tx_at_once, skip_later_txs, True], as_wallet=True)
                transactions = result['result']
                
                # Extract the transaction IDs so we can query them verbosely
                # because the tx doesn't include info on other addresses
                txids = []
                for tx in transactions:
                    txids.append(tx["txid"])

                # Call gettransaction for each txid (requires txindex=1 set by the
                transactions = []
                for txid in txids:
                    result = self._send_rpc_request('gettransaction', params=[txid, True, True], as_wallet=True)
                    txs = result['result']
                    
                    for tx in txs:
                        transactions.append(self._clean_tx(tx))
            
                # Get the number of transactions in case new, incoming txs arrived.
                total_transactions_new = self._send_rpc_request('getwalletinfo', as_wallet=True)['result']['txcount']
                if total_transactions_new > total_transactions:
                    # Transactions we haven't listed yet have been pushed into our current numerical range, so push
                    # the skipped later transactions count forward,
                    skip_later_txs += total_transactions_new - total_transactions
                    total_transactions = total_transactions_new

                # And finally prepare to process next most recent batch of transactions
                skip_later_txs -= self.max_tx_at_once

            return transactions
        
        finally:
            # Unload and delete the temporary wallet
            self._send_rpc_request('unloadwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])

