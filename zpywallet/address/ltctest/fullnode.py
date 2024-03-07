import random
import requests

from ...errors import NetworkException
from ...generated import wallet_pb2


class LitecoinRPCClient:
    """Address querying class for Litecoin full nodes utilizing descriptors.
    Requires node running with -txindex.
    """

    # Not static because we need to make calls to fetch input transactions.
    def _clean_tx(self, element, block_height, is_mine=False, _recursive=False):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element["txid"]
        if block_height:
            new_element.confirmed = True
            new_element.height = block_height
        else:
            new_element.confirmed = False

        if "blocktime" in element.keys():
            new_element.timestamp = element["blocktime"]

        isCoinbase = False
        for vin in element["vin"]:
            txinput = new_element.btclike_transaction.inputs.add()
            if "txid" in vin.keys():
                # If there is a vin txid then it's not e.g. a coinbase transaction input
                txinput.txid = vin["txid"]
                txinput.index = vin["vout"]
                # To fill in the amount, we have to get the other transaction id
                # But only if we're not parsing a coinbase transaction
                if txinput.txid in [t.txid for t in self.txset] or is_mine:
                    res = self._send_rpc_request(
                        "getrawtransaction", params=[vin["txid"], True]
                    )
                    fine_rawtx = res["result"]
                    txinput.amount = int(
                        fine_rawtx["vout"][txinput.index]["value"] * 1e8
                    )
                    if (
                        "address"
                        in fine_rawtx["vout"][txinput.index]["scriptPubKey"].keys()
                    ):
                        address = fine_rawtx["vout"][txinput.index]["scriptPubKey"][
                            "address"
                        ]
                    elif (
                        "addresses"
                        in fine_rawtx["vout"][txinput.index]["scriptPubKey"].keys()
                    ):
                        address = fine_rawtx["vout"][txinput.index]["scriptPubKey"][
                            "addresses"
                        ][0]
                    is_mine = is_mine or address in self.addresses
            else:
                isCoinbase = True

        for vout in element["vout"]:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(vout["value"] * 1e8)
            txoutput.index = vout["n"]
            if "address" in vout["scriptPubKey"].keys():
                txoutput.address = vout["scriptPubKey"]["address"]
            elif "addresses" in vout["scriptPubKey"].keys():
                txoutput.address = vout["scriptPubKey"]["addresses"][0]
            is_mine = is_mine or txoutput.address in self.addresses

        if not isCoinbase and (not self.fast_mode or (_recursive and is_mine)):
            # Now we must calculate the total fee
            total_inputs = sum(
                [a.amount for a in new_element.btclike_transaction.inputs]
            )
            total_outputs = sum(
                [a.amount for a in new_element.btclike_transaction.outputs]
            )

            new_element.total_fee = total_inputs - total_outputs

            new_element.btclike_transaction.fee = int(
                (total_inputs - total_outputs) // element["vsize"]
            )
        new_element.fee_metric = wallet_pb2.VBYTE

        if is_mine:
            if not _recursive:
                new_element = self._clean_tx(
                    element, block_height, is_mine=True, _recursive=True
                )
                self.txset.append(new_element)
        else:
            return None
        return new_element

    def __init__(self, addresses, transactions=None, **kwargs):
        self.rpc_url = kwargs.get("url")
        self.rpc_user = kwargs.get("user")
        self.rpc_password = kwargs.get("password")
        self.max_tx_at_once = kwargs.get("max_tx_at_once") or 1000
        self.min_height = kwargs.get("min_height") or 0
        self.fast_mode = kwargs.get("fast_mode") or True
        self.transactions = []
        self.addresses = addresses
        if transactions is not None and isinstance(transactions, list):
            self.transactions = transactions
        else:
            self.transactions = []

        if kwargs.get("min_height") is not None:
            self.min_height = kwargs.get("min_height")
        else:
            try:
                self.min_height = self.get_block_height() + 1
            except NetworkException:
                self.min_height = 0

    def _send_rpc_request(self, method, params=None, as_wallet=False):
        payload = {
            "method": method,
            "params": params or [],
            "jsonrpc": "2.0",
            "id": random.randint(1, 999999),
        }
        try:
            response = requests.post(
                self.rpc_url,
                auth=(
                    (self.rpc_user, self.rpc_password)
                    if self.rpc_user and self.rpc_password
                    else None
                ),
                json=payload,
                timeout=86400,
            )
            j = response.json()
            if "result" not in j.keys():
                raise NetworkException("Failed to get result")
            return j
        except Exception as e:
            raise NetworkException(f"RPC call failed: {str(e)}")

    def get_block_height(self):
        response = self._send_rpc_request("getblockchaininfo")
        try:
            self.height = response["result"]["blocks"]
            return self.height
        except Exception as e:
            raise NetworkException(f"Failed to make RPC Call: {str(e)}")

    def get_balance(self):
        """
        Retrieves the balance of the Bitcoin address.

        Returns:
            float: The balance of the Bitcoin address in BTC.

        Raises:
            NetworkException: If the API request fails or the address balance cannot be retrieved.
        """
        utxos = self.get_utxos()
        total_balance = 0
        confirmed_balance = 0
        for utxo in utxos:
            total_balance += utxo.amount
            # Careful: Block height #0 is the Genesis block - don't want to exclude that.
            # (Not that it returns it ever though!)
            if utxo.confirmed:
                confirmed_balance += utxo.amount
        return total_balance, confirmed_balance

    def get_utxos(self):
        """Fetches the UTXO set for the addresses.

        Returns:
            list: A list of UTXOs
        """

        # Transactions are generated in reverse order
        utxos = []
        for i in range(len(self.transactions) - 1, -1, -1):
            for utxo in [u for u in utxos]:
                # Check if any utxo has been spent in this transaction
                for vin in self.transactions[i].btcllike_transaction.inputs:
                    if vin.spent or (
                        vin.txid == utxo["txid"] and vin["index"] == utxo.index
                    ):
                        # Spent
                        utxos.remove(utxo)
            for out in self.transactions[i].btclike_transaction.outputs:
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
        Retrieves the transaction history of the Dash address from cached data augmented with network data.
        Does not include Genesis blocks.

        Returns:
            list: A list of transaction objects.

        Raises:
            NetworkException: If the RPC request fails or the transaction history cannot be retrieved.
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
        self.get_block_height()
        self.txset = []  # Stores all of the output transactions in a temporary place
        found_it = txhash is None
        if not [*range(self.min_height, self.height + 1)]:
            return
        try:
            # Get the blockchain info to determine the best block height
            block_hash = self._send_rpc_request(
                "getblockhash", params=[self.min_height]
            )["result"]

            # Iterate through blocks to fetch transactions
            for block_height in range(self.min_height, self.height + 1):
                if not block_hash:
                    break
                block = self._send_rpc_request("getblock", params=[block_hash, True])[
                    "result"
                ]
                block_hash = block.get("nextblockhash")

                # Iterate through transactions in the block
                for tx in block["tx"]:
                    if tx != txhash and not found_it:
                        continue  # Don't process until we reach the specified transaction hash
                    else:
                        found_it = True

                    # raw_transaction = self._send_rpc_request('getrawtransaction', params=[tx, True])['result']
                    raw_transaction = tx  # Verbosity=2 in bitcoin gives us the getrawtransaction output
                    parsed_transaction = self._clean_tx(raw_transaction, block_height)
                    if parsed_transaction is not None:
                        yield parsed_transaction

            self.txset = []
            self.min_height = self.height + 1
        except Exception as e:
            self.txset = []
            raise NetworkException(f"Failed to get transaction history: {str(e)}")
