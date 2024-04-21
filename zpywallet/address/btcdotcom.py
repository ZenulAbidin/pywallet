from functools import reduce
import requests

from urllib3 import Retry
from requests.adapters import HTTPAdapter

from ..errors import NetworkException
from ..generated import wallet_pb2


def deduplicate(elements):
    return reduce(lambda re, x: re + [x] if x not in re else re, elements, [])


HTTPS_ADAPTER = "https://"


class BTCDotComClient:
    """
    A class representing a list of crypto addresses.

    This class allows you to retrieve the balance, UTXO set, and transaction
    history of a crypto address using BTC.com.
    """

    def _clean_tx(self, element):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element["hash"]
        if "block_height" in element.keys() and element["block_height"] is not None:
            new_element.confirmed = True
            new_element.height = element["block_height"]
        else:
            new_element.confirmed = False

        if new_element.confirmed:
            new_element.timestamp = element["block_time"]

        for vin in element["inputs"]:
            txinput = new_element.btclike_transaction.inputs.add()
            txinput.txid = vin["prev_tx_hash"]
            txinput.index = vin["prev_position"]
            txinput.amount = int(vin["prev_value"])

        i = 0
        for vout in element["outputs"]:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(vout["value"])
            txoutput.index = i
            i += 1
            if "addresses" in vout.keys():
                txoutput.address = vout["addresses"][0]
            txoutput.spent = vout["spent_by_tx"] != ""

        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])
        new_element.total_fee = total_inputs - total_outputs

        new_element.btclike_transaction.fee = int(
            (total_inputs - total_outputs) // element["vsize"]
        )
        new_element.fee_metric = wallet_pb2.VBYTE
        return new_element

    # BTC.com's rate limits are unknown.
    def __init__(
        self,
        addresses,
        coin="BTC",
        chain="main",
        request_interval=(1000, 1),
        transactions=None,
    ):
        """
        Initializes an instance of the BTCDotComClient class.

        Args:
            addresses (list): A list of human-readable crypto addresses.
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0,N) for no rate limiting, where N>0.
        """
        self.requests, self.interval_sec = request_interval
        self.height = -1
        coin_map = {"BTC": "btc"}
        self.coin = coin_map.get(coin.upper())
        if not self.coin:
            raise ValueError(f"Undefined coin '{coin}'")

        chain_map = {"main": "main"}
        self.chain = chain_map.get(chain)
        if not self.chain:
            raise ValueError(f"Undefined chain '{chain}'")

        self.addresses = addresses
        if transactions is not None and isinstance(transactions, list):
            self.transactions = transactions
        else:
            self.transactions = []

    def get_balance(self):
        """
        Retrieves the balance of the crypto address.

        Returns:
            float: The balance of the crypto address whole units e.g. BTC.

        Raises:
            NetworkException: If the API request fails or the address balance
                cannot be retrieved.
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
        """Fetches the UTXO set for the addresses.

        Returns:
            list: A list of UTXOs
        """

        # Transactions are generated in reverse order
        utxos = []
        for i in range(len(self.transactions) - 1, -1, -1):
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
        """
        Retrieves the current block height.

        Returns:
            int: The current block height.

        Raises:
            NetworkException: If the API request fails or the block height
                cannot be retrieved.
        """

        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=self.interval_sec / self.requests,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods={"GET"},
        )
        session.mount(HTTPS_ADAPTER, HTTPAdapter(max_retries=retries))

        url = "https://chain.api.btc.com/v3/block/latest"
        try:
            response = session.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["data"]["height"]
        except requests.exceptions.RetryError:
            raise NetworkException(
                "Failed to retrieve block height (max retries failed)"
            )
        except requests.exceptions.JSONDecodeError:
            raise NetworkException(
                "Failed to retrieve block height (response body is not JSON)"
            )

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the crypto address from cached
        data augmented with network data.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            NetworkException: If the API request fails or the transaction
                history cannot be retrieved.
        """
        block_height = self.get_block_height()
        for address in self.addresses:
            self.transactions.extend(self._get_one_transaction_history(address))
            self.transactions = deduplicate(self.transactions)
        self.height = block_height
        return self.transactions

    def _get_one_transaction_history(self, address):
        page = 1
        pagesize = 50

        data = {"data": {"list": 1}}

        while data["data"]["list"] is not None:
            url = f"https://chain.api.btc.com/v3/address/{address}/tx?page={page}&pagesize={pagesize}"
            session = requests.Session()
            retries = Retry(
                total=3,
                backoff_factor=self.interval_sec / self.requests,
                status_forcelist=[429, 502, 503, 504],
                allowed_methods={"GET"},
            )
            session.mount(HTTPS_ADAPTER, HTTPAdapter(max_retries=retries))

            try:
                response = session.get(url, timeout=60)
                response.raise_for_status()
                data = response.json()
                for tx in data["data"]["list"]:
                    ctx = self._clean_tx(tx)
                    if ctx.confirmed and ctx.height < self.height:
                        # We already have those older transactions
                        # Strictly less-than allows for catching very large
                        # number of matches on the same block spanning
                        # multiple pages.
                        return
                    yield ctx
                page += 1

            except requests.exceptions.RetryError:
                raise NetworkException(
                    "Failed to retrieve transactions (max retries failed)"
                )
            except requests.exceptions.JSONDecodeError:
                raise NetworkException(
                    "Failed to retrieve transactions (response body is not JSON)"
                )
