import random
import requests
from datetime import datetime

from ...transactions.decode import parse_transaction_simple
from ...generated.wallet_pb2 import BYTE, VBYTE

class DashRPCClient:
    """Address querying class for Dash full nodes utilizing descriptors.
       Requires node with multi-wallet support and -txindex.
    """
    
    # Not static because we need to make calls to fetch input transactions.
    def _clean_tx(self, element):
        new_element = {}
        new_element['txid'] = element['txid']
        if 'blockheight' in element.keys():
            new_element['height'] = element['blockheight']
        else:
            new_element['height'] = None
        new_element['timestamp'] = None if 'blocktime' not in element.keys() else element['blocktime']
        element = element['decoded']

        new_element['inputs'] = []
        new_element['outputs'] = []
        for vin in element['vin']:
            txinput = {}
            if 'txid' in vin.keys():
                txinput['txid'] = vin['txid']
                txinput['index'] = vin['vout']
                # To fill in the amount, we have to get the other transaction id
                # But only if we're not parsing a coinbase transaction
                res = self._send_rpc_request('getrawtransaction', params=[vin['txid']])
                rawtx = res['result']
                fine_rawtx, _ = parse_transaction_simple(rawtx)
                txinput['amount'] = fine_rawtx["outputs"][txinput['index']]["value"] / 1e8
            else:
                txinput['txid'] = None
                txinput['index'] = None
                txinput['amount'] = 0

            new_element['inputs'].append(txinput)
        for vout in element['vout']:
            txoutput = {}
            txoutput['amount'] = vout['value']
            txoutput['index'] = vout['n']
            if 'address' in vout['scriptPubKey']:
                txoutput['address'] = vout['scriptPubKey']['address']
            else:
                txoutput['address'] = None
            new_element['outputs'].append(txoutput)
        
        # Now we must calculate the total fee
        total_inputs = sum([a['amount'] for a in new_element['inputs']])
        total_outputs = sum([a['amount'] for a in new_element['outputs']])

        new_element['total_fee'] = (total_inputs - total_outputs) / 1e8

        # vbytes will be the default transaction metric for networks that support segwit,
        # else, bytes.
        if 'vsize' in element.keys():
            new_element['fee'] = (total_inputs - total_outputs) / element['vsize']
            new_element['fee_metric'] = VBYTE
        else:
            new_element['fee'] = (total_inputs - total_outputs) / element['size']
            new_element['fee'] = BYTE

        return new_element

    def __init__(self, addresses, rpc_url, rpc_user, rpc_password, client_number=0, user_id=0, last_update=0, max_tx_at_once=1000, transactions=None):
        self.rpc_url = rpc_url
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.client_number = client_number
        self.user_id = user_id
        self.max_tx_at_once = max_tx_at_once
        
        self.transactions = []
        self.addresses = addresses
        self.last_update = last_update
        self.height = self.get_block_height()
        self._load_addresses()
        if transactions:
            self.transactions = transactions
        else:
            self.transactions = [*self._get_transaction_history()]
    
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
        response = self._send_rpc_request('getblockchaininfo')
        return response['result']['blocks']

    def _load_addresses(self):
        # Create a new temporary wallet
        self._send_rpc_request('createwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}", True])
        
        block_height = self.height
        block_height = min(block_height, self.get_block_height())


        params = [*map(lambda at: {"scriptPubKey": {"address": at}, "timestamp": self.last_update}, self.addresses)]

        try:
            # Load the temporary wallet
            self._send_rpc_request('loadwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])
            
            # Import the address into the wallet
            self._send_rpc_request('importmulti', params=[params], as_wallet=True)
            
            self.last_update = datetime.now().timestamp()
            
        finally:
            # Unload the temporary wallet
            self._send_rpc_request('unloadwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])
    
    def get_balance(self):
        """
        Retrieves the balance of the Dash address.

        Returns:
            float: The balance of the Dash address in BTC.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        utxos = self.get_utxos()
        total_balance = 0
        confirmed_balance = 0
        for utxo in utxos:
            total_balance += utxo["amount"]
            # Careful: Block height #0 is the Genesis block - don't want to exclude that.
            # (Not that it returns it ever though!)
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
    
    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Dash address from cached data augmented with network data.
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
            txhash = self.transactions[0]["txid"]
            txs = [*self._get_transaction_history(txhash)]
            txs.extend(self.transactions)
            self.transactions = txs
            del txs
    
    def _get_transaction_history(self, txhash=None):
        try:
            # Load the temporary wallet
            self._send_rpc_request('loadwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])
            
             # Get the number of transactions
            total_transactions = self._send_rpc_request('getwalletinfo', as_wallet=True)['result']['txcount']

            skip_later_txs = 0
            while skip_later_txs < total_transactions:

                # listtransactions by default return only 10 most recent transactions)
                result = self._send_rpc_request('listtransactions', params=["*", self.max_tx_at_once, skip_later_txs, True], as_wallet=True)
                transactions = result['result']
                
                # Extract the transaction IDs so we can query them verbosely
                # because the tx doesn't include info on other addresses
                for tx in transactions:
                    txid = tx['txid']
                    if txid == txhash:
                        return
                    result = self._send_rpc_request('gettransaction', params=[txid, True, True], as_wallet=True)
                    result_tx = result['result']
                    yield self._clean_tx(result_tx)
            

                # Get the number of transactions in case new, incoming txs arrived.
                # We will just skip those txs and they can be received in the next method invocation.
                total_transactions_new = self._send_rpc_request('getwalletinfo', as_wallet=True)['result']['txcount']
                if total_transactions_new > total_transactions:
                    skip_later_txs += total_transactions_new - total_transactions
                    total_transactions = total_transactions_new

                # And finally prepare to process next most recent batch of transactions
                skip_later_txs += self.max_tx_at_once
        
        finally:
            # Unload and delete the temporary wallet
            self._send_rpc_request('unloadwallet', params=[f"zpywallet_{self.client_number}_{self.user_id}"])

