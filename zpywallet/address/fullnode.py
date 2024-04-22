from functools import reduce

import json
import multiprocessing
from Cryptodome import Random
import requests
from concurrent.futures import ThreadPoolExecutor

from ..errors import NetworkException
from ..generated import wallet_pb2
from .cache import SQLTransactionStorage, DatabaseError

from .provider import AddressProvider


def transform_and_sort_transactions(data):
    transformed_data = [
        {**value, "txid": txid} for txid, value in data["result"].items()
    ]
    sorted_data = sorted(
        transformed_data, key=lambda x: x["fees"]["modified"] / x["vsize"], reverse=True
    )
    return sorted_data


class RPCClient(AddressProvider):
    """
    A class indexing all transactions in bitcoin-like blockchains and mempools into
    a database for quick fetching. It also lets you query transactions by address.

    The performance of this class heavily depends on the network speed and CPU
    speed of the node as well as the number of threads available, the size of the RPC
    batch work queue specified in the constructor, and the amount of transactions in
    megabytes you are trying to fetch at once.

    Additionally, the number of transactions returned depends on the number of
    transactions in the mempool itself and how well-connected the node is to other
    nodes. The longer you run your node and the more peers it has, the faster
    the mempool fills up with thransactions.

    If you intend to use the mempool to track pending payments, it is recommended
    to update it once every 10 to 60 seconds for optimal user experience. However,
    if this mempool class is empty, it can take several minutes to fill it with the
    current mempool. As a result, you should do this while your app is initializing
    in order to avoid stuck processing workflows caused by slow mempool initialization.

    The mempool class caches existing unconfirmed tranasctions so that they do not have
    to be fetched a second time, which should greatly improve performance and reduce
    waiting times during status updates.

    This class does not work well with nodes running behind web servers that use
    rate limiting.

    Requires a node running with -txindex.
    """

    # Not static because we need to make calls to fetch input transactions.
    def _clean_tx(self, element, block_height, sql_transaction_storage):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element["txid"]
        new_element.confirmed = bool(block_height)
        new_element.block_height = block_height

        new_element.timestamp = (
            element.get("blocktime")
            if new_element.confirmed
            else element.get("mempooltime")
        )

        is_coinbase = any(["txid" not in vin.keys() for vin in element["vin"]])

        for vout in element["vout"]:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(vout["value"] * 1e8)
            txoutput.index = vout["n"]
            if "address" in vout["scriptPubKey"].keys():
                txoutput.address = vout["scriptPubKey"]["address"]
            elif "addresses" in vout["scriptPubKey"].keys():
                txoutput.address = vout["scriptPubKey"]["addresses"][0]

        for vin in element["vin"]:
            txinput = new_element.btclike_transaction.inputs.add()
            txinput.amount = int(vin["value"] * 1e8)
            if is_coinbase:
                continue
            txinput.txid = vin["txid"]
            txinput.index = vin["vout"]

            # raised DatabaseError is caught elsewhere
            intx = sql_transaction_storage.get_transaction_by_txid(txinput.txid)
            txinput.amount = intx.btclike_transaction.outputs[txinput.index].amount
            txinput.address = intx.btclike_transaction.outputs[txinput.index].address

        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])

        new_element.total_fee = total_inputs - total_outputs

        # The vsize was stored in the fee field.
        new_element.btclike_transaction.fee = int(
            (total_inputs - total_outputs) // new_element.btclike_transaction.fee
        )
        new_element.fee_metric = self.fee_metric

        return new_element

    def __init__(self, coin="BTC", chain="main", **kwargs):
        self.rpc_host = kwargs.get("host") or "127.0.0.1"
        self.rpc_protocol = kwargs.get("protocol") or "http"
        self.rpc_user = kwargs.get("user")
        self.rpc_password = kwargs.get("password")
        self.max_batch = kwargs.get("max_batch") or 150
        self.rpc_threads = kwargs.get("rpc_threads") or 4
        self.db_connection_parameters = kwargs.get("db_connection_parameters")
        self.transactions = []

        use_auth = self.rpc_user or self.rpc_password

        coin_map = {
            "BTC": 0,
            "LTC": 1,
            "DOGE": 2,
            "DASH": 3,
        }
        self.coin = coin_map.get(coin.upper())
        if self.coin is None:
            raise ValueError(f"Undefined coin '{coin}'")

        chain_map = {"main": 0, "test": 1}
        self.chain = chain_map.get(chain)
        if self.chain is None:
            raise ValueError(f"Undefined chain '{chain}'")

        port_map = [[8332, 18332], [9332, 19332], [22555, 445555], [9998, 19998]]

        self.rpc_port = kwargs.get("port") or port_map[self.coin][self.chain]
        self.rpc_url = (
            f"{self.rpc_host}://{'' if use_auth else self.rpc_user + ':' + self.rpc_password + '@'}"
            + f"{self.rpc_host}:{self.rpc_port}"
        )

        fee_metric_map = [
            wallet_pb2.VBYTE,
            wallet_pb2.VBYTE,
            wallet_pb2.BYTE,
            wallet_pb2.BYTE,
        ]

        self.fee_metric = fee_metric_map[self.coin]

    def _send_rpc_request(self, method, params=None):
        payload = {
            "method": method,
            "params": params or [],
            "jsonrpc": "2.0",
            "id": int.from_bytes(Random.new().read(4), byteorder="big"),
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
        except Exception as e:
            raise NetworkException(f"RPC call failed: {str(e)}")

        # Certain nodes which are placed behind web servers or Cloudflare will
        # configure rate limits and return some HTML error page if we go over that.
        # Zpywallet is not designed to handle such content so we check for it first.
        # If you are using the full node facilities, you are recommended to connect
        # to your own node and not to a public one, for this reason.
        try:
            j = response.json()
        except json.decoder.JSONDecodeError:
            raise NetworkException("Internal RPC node error - expected JSON output")

        if "result" not in j.keys():
            raise NetworkException("Failed to get result")
        return j

    def _send_batch_rpc_request(self, reqs):
        payload = []
        for method, params in reqs:
            payload.append(
                {
                    "method": method,
                    "params": params or [],
                    "jsonrpc": "2.0",
                    "id": int.from_bytes(Random.new().read(4), byteorder="big"),
                }
            )

        try:
            # Requests session is not needed for the full node but we can use it
            # for the other providers in the future.
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
        except Exception as e:
            raise NetworkException(f"RPC call failed: {str(e)}")

        # Certain nodes which are placed behind web servers or Cloudflare will
        # configure rate limits and return some HTML error page if we go over that.
        # Zpywallet is not designed to handle such content so we check for it first.
        # If you are using the full node facilities, ou are recommended to connect
        # to your own node and not to a public one, for this reason.
        try:
            jj = response.json()
        except json.decoder.JSONDecodeError:
            print(response.text)
            raise NetworkException("Internal RPC node error - expected JSON output")

        for j in jj:
            if "result" not in j.keys():
                # Silently ignore the error since it only occurs in the case
                # of bad requests, replaced transactions, and so on which
                # either do not happen in this code or (in the case of RBF
                # replacement) must be ignored.
                # If the workflow is correct then either all of the results
                # will be successful or they will all fail. No in-between.
                # raise NetworkException("Failed to get result")
                continue
            yield j

    def _get_block_height(self):
        response = self._send_rpc_request("getblockchaininfo")
        try:
            return response["result"]["blocks"]
        except Exception as e:
            raise NetworkException(f"Failed to make RPC Call: {str(e)}")

    # Internal methods are ran in a separate process which allows the OS
    # to properly garbage collect the memory, as Python leaves a large footprint
    # behind.
    def _internal_mempool_fetch(self):
        res = self._send_rpc_request("getrawmempool", [True])
        sorted_transactions = transform_and_sort_transactions(res)
        return [(tx["txid"], tx["time"]) for tx in sorted_transactions]

    def _add_mempool_transactions(self, transaction_batch):
        sql_transaction_storage = SQLTransactionStorage(self.db_connection_parameters)
        sql_transaction_storage.connect()
        sql_transaction_storage.delete_dropped_txids()
        try:
            txids = transaction_batch
            # Next we are going to yield new mempool transactions that we don't have
            # Confirmed mempool transactions are dropped by this method and the one above.
            txid_batches = [
                txids[i : i + self.max_batch]
                for i in range(0, len(txids), self.max_batch)
            ]

            # The max_batch heere is actually just the number of threads to spawn for the pool
            with ThreadPoolExecutor(max_batch=self.rpc_threads) as executor:
                futures = [
                    executor.submit(
                        self._process_transaction, txes, sql_transaction_storage
                    )
                    for txes in txid_batches
                ]

                # Do a thread join before committing
                for future in futures:
                    future.result()

                sql_transaction_storage.commit()
        except DatabaseError as e:
            sql_transaction_storage.rollback()
            raise e

    def read_mempool(self):
        with multiprocessing.Pool(1) as pool:
            transaction_batches = pool.apply(self._internal_mempool_fetch)

        for transaction_batch in transaction_batches:
            self._add_mempool_transactions(transaction_batch)

    def _process_transaction(
        self, txes, sql_transaction_storage: SQLTransactionStorage
    ):
        txes = [
            tx for tx in txes if not sql_transaction_storage.have_transaction(tx[0])
        ]
        if not txes:
            return
        raw_transactions = [
            r
            for r in self._send_batch_rpc_request(
                [("getrawtransaction", [tx[0], 1]) for tx in txes]
            )
        ]
        for raw_transaction in raw_transactions:
            raw_transaction = raw_transaction["result"]
            if not raw_transaction:
                # Perhaps it has been replaced
                continue

            # We need to manually match each mempool entry time with the
            # correct raw transaction object.
            raw_transaction["mempooltime"] = next(
                filter(lambda tx, raw=raw_transaction: tx[0] == raw["txid"], txes),
                (None, None),
            )[1]
            transaction = self._clean_tx(raw_transaction, None, sql_transaction_storage)
            sql_transaction_storage.store_transaction(transaction)

    def get_block_height(self):
        """
        Retrieves the current block height.

        Returns:
            int: The current block height.

        Raises:
            NetworkException: If the API request fails or the block height
                cannot be retrieved.
        """

        response = self._send_rpc_request("getblockchaininfo")
        try:
            self.height = response["result"]["blocks"]
            return self.height
        except Exception as e:
            raise NetworkException(f"Failed to make RPC Call: {str(e)}")

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the addresses from cached data.
        Does not include Genesis blocks.

        Returns:
            list: A list of transaction objects.

        Raises:
            NetworkException: If the RPC request fails or the transaction
                history cannot be retrieved.
        """
        sql_transaction_storage = SQLTransactionStorage(self.db_connection_parameters)

        try:
            transactions = []
            for address in self.addresses:
                transactions.extend(
                    sql_transaction_storage.get_transactions_by_address(address)
                )
            transactions = self.deduplicate(transactions)
            self.transactions = transactions
            return transactions

        except DatabaseError as e:
            raise NetworkException(f"Failed to get transaction history: {str(e)}")

    def read_transaction_history(self):
        sql_transaction_storage = SQLTransactionStorage(self.db_connection_parameters)

        try:
            self.height = sql_transaction_storage.get_block_height()

            max_height = self._send_rpc_request(
                "getblockhash", params=[self.min_height]
            )["result"]

            if not [*range(self.height, max_height + 1)]:
                return

            # Get the blockchain info to determine the best block height
            block_hash = self._send_rpc_request("getblockhash", params=[self.height])[
                "result"
            ]

            # Iterate through blocks to fetch transactions
            for block_height in range(self.height, max_height + 1):
                if not block_hash:
                    break

                # Verbosity=1 is portable on all blockchains but will cost an
                # extra RPC batch call to get the raw transactions.
                block = self._send_rpc_request("getblock", params=[block_hash, 1])[
                    "result"
                ]
                block_hash = block.get("nextblockhash")

                # Iterate through transactions in the block
                raw_transactions = [
                    r
                    for r in self._send_batch_rpc_request(
                        [("getrawtransaction", [tx[0], 1]) for tx in block["tx"]]
                    )
                ]
                for raw_transaction in raw_transactions:
                    parsed_transaction = self._clean_tx(
                        raw_transaction, block_height, sql_transaction_storage
                    )
                    sql_transaction_storage.store_transaction(parsed_transaction)

            sql_transaction_storage.set_block_height(max_height)
            sql_transaction_storage.commit()
            self.read_mempool()
        except DatabaseError as e:
            raise NetworkException(f"Failed to get transaction history: {str(e)}")
