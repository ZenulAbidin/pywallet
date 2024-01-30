import random
import requests

from ...errors import NetworkException
from ...transactions.decode import parse_transaction_simple
from ...generated import wallet_pb2


class BitcoinRPCClient:
    """Address querying class for Bitcoin full nodes utilizing descriptors.
       Requires a node running with -txindex.
    """
    
    # Not static because we need to make calls to fetch input transactions.
    def _clean_tx(self, element):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element['txid']
        if 'blockheight' in element.keys():
            new_element.confirmed = True
            new_element.height = element['blockheight']
        else:
            new_element.confirmed = False

        if 'blocktime' not in element.keys():
            new_element.timestamp = element['blocktime']

        element = element['decoded']

        for vin in element['vin']:
            txinput = new_element.btclike_transaction.inputs.add()
            if 'txid' in vin.keys():
                # If there is a vin txid then it's not e.g. a coinbase transaction input
                txinput.txid = vin['txid']
                txinput.index = vin['vout']
                # To fill in the amount, we have to get the other transaction id
                # But only if we're not parsing a coinbase transaction
                res = self._send_rpc_request('getrawtransaction', params=[vin['txid']])
                rawtx = res['result']
                fine_rawtx, _ = parse_transaction_simple(rawtx)
                txinput.amount = int(fine_rawtx["outputs"][txinput.index]["value"])

        for vout in element['vout']:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(vout['value'])
            txoutput.index = vout['n']
            if 'address' in vout['scriptPubKey']:
                txoutput.address = vout['scriptPubKey']['address']
        
        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])

        new_element.total_fee = (total_inputs - total_outputs)

        new_element.btclike_transaction.fee = int((total_inputs - total_outputs) // element['vsize'])
        new_element.fee_metric = wallet_pb2.VBYTE
        return new_element

    def __init__(self, addresses, last_update=0, transactions=None, **kwargs):
        self.rpc_url = kwargs.get('url')
        self.rpc_user = kwargs.get('user')
        self.rpc_password = kwargs.get('password')
        self.client_number = kwargs.get('client_number') or 0
        self.user_id = kwargs.get('user_id') or 0
        self.max_tx_at_once = kwargs.get('max_tx_at_once') or 1000
        
        self.min_height = kwargs.get('min_height') or 0
        self.transactions = []
        self.addresses = addresses
        self.last_update = last_update
        if transactions is not None and isinstance(transactions, list):
            self.transactions = transactions
        else:
            self.transactions = []
    
    def sync(self):
        self.height = self.get_block_height()
        self._load_addresses()
        self.transactions = [*self._get_transaction_history()]
    
    def _send_rpc_request(self, method, params=None, as_wallet=False):
        payload = {
            'method': method,
            'params': params or [],
            'jsonrpc': '2.0',
            'id': random.randint(1, 999999)
        }
        try:
            response = requests.post(self.rpc_url, auth=(self.rpc_user, self.rpc_password) if self.rpc_user and \
                                        self.rpc_password else None, json=payload, timeout=86400)
            j = response.json()
            if 'result' not in j.keys():
                raise NetworkException("Failed to get result")
        except Exception as e:
            raise NetworkException(f"RPC call failed: {str(e)}")
    
    def get_block_height(self):
        response = self._send_rpc_request('getblockchaininfo')
        try:
            return response['result']['blocks']
        except Exception as e:
            raise NetworkException(f"Failed to make RPC Call: {str(e)}")

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
            # (Not that it returns it ever though!)
            if utxo["confirmed"]:
                confirmed_balance += utxo["amount"]
        return total_balance, confirmed_balance
        
    def get_utxos(self):
        self.height = self.get_block_height()
        # Transactions are generated in reverse order
        utxos = []
        for i in range(len(self.transactions)-1, -1, -1):
            for utxo in [u for u in utxos]:
                # Check if any utxo has been spent in this transaction
                for vin in self.transactions[i].inputs:
                    if vin.spent or (vin.txid == utxo["txid"] and vin["index"] == utxo.index):
                        # Spent
                        utxos.remove(utxo)
            for out in self.transactions[i].outputs:
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
    
    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Bitcoin address from cached data augmented with network data.
        Does not include Genesis blocks.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the RPC request fails or the transaction history cannot be retrieved.
        """
        if len(self.transactions) == 0:
            self.transactions = [*self._get_transaction_history()]
        else:
            # First element is the most recent transactions
            txhash = self.transactions[0].txid
            txs = [*self._get_transaction_history(txhash)]
            txs.extend(self.transactions)
            self.transactions = txs
                
    def _get_transaction_history(self, txhash=None):
        try:
            # Get the blockchain info to determine the best block height
            blockchain_info = self._send_rpc_request('getblockchaininfo')
            best_block_height = blockchain_info['result']['blocks']

            # Iterate through blocks to fetch transactions
            for block_height in range(best_block_height , self.height-1, -1):
                block_hash = self._send_rpc_request('getblockhash', params=[block_height])['result']
                block = self._send_rpc_request('getblock', params=[block_hash, 2])['result']

                # Iterate through transactions in the block
                for tx in block['tx']:
                    if tx['txid'] == txhash:
                        return  # Stop if we reach the specified transaction hash

                    raw_transaction = block['tx'] # Verbosity=2 in bitcoin gives us the getrawtransaction output
                    raw_transaction = block['tx'] # Verbosity=2 in bitcoin gives us the getrawtransaction output
                    parsed_transaction = self._clean_tx(raw_transaction)
                    if not parsed_transaction.confirmed or parsed_transaction.height >= self.min_height:
                        yield parsed_transaction
                    else:
                        return

        except Exception as e:
            raise NetworkException(f"Failed to get transaction history: {str(e)}")

