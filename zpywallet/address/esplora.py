from functools import reduce
import requests

from urllib3 import Retry
from requests.adapters import HTTPAdapter

from ..errors import NetworkException
from ..generated import wallet_pb2

from .provider import AddressProvider


class EsploraClient(AddressProvider):
    """
    A class representing a list of crypto addresses.

    This class allows you to retrieve the balance, UTXO set, and transaction
    history of a crypto address using an Esplora instance.

    Esplora is a block explorer software used by a few websites,
    including mempool.space (rate limited) and blockstream.info.

    Note: Esplora has a built-in limitation of returning up to 50 unconfirmed
    transactions per address.

    Note 2: This API will not return the transaction inside the Genesis block.
    This will affect balance displayed for Satoshi's first address
    1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa - but that output is unspendable
    for unrelated reasons.
    """

    # XXX Esplora does have a "get all the transactions in the mempool"
    # endpoint but its situation is similar to the full node provider in
    # that an external database would be required to store all that data,
    # since its not filtered by address. However, using the REST API
    # to get all those transactions in conjunction with rate limits is
    # prohibitively slow.

    def _clean_tx(self, element):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element["txid"]
        if "block_height" in element["status"].keys():
            new_element.confirmed = True
            new_element.height = element["status"]["block_height"]
        else:
            new_element.confirmed = False

        if new_element.confirmed:
            new_element.timestamp = element["status"]["block_time"]

        for vin in element["vin"]:
            txinput = new_element.btclike_transaction.inputs.add()
            txinput.txid = vin["txid"]
            txinput.index = vin["vout"]
            txinput.amount = int(vin["prevout"]["value"])
            txinput.address = vin["prevout"]["scriptpubkey_address"]

        i = 0
        for vout in element["vout"]:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(vout["value"])
            txoutput.index = i
            txoutput.address = vout["scriptpubkey_address"]
            i += 1

        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])

        new_element.total_fee = total_inputs - total_outputs

        new_element.btclike_transaction.fee = int(element["fee"])
        new_element.fee_metric = wallet_pb2.VBYTE
        return new_element

    def _chain_is_correct(self, chain):
        # Esplora APIs do not export chain information directly but they do have
        # a function for scanning for address prefixes which can be used as a
        # solution for verifying that the API indeed matches up with the
        # user-supplied chain parameter.
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=self.interval_sec / self.requests,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods={"GET"},
        )
        session.mount(self.HTTPS_ADAPTER, HTTPAdapter(max_retries=retries))

        url = f"{self.endpoint}/addres-prefix/{'bc' if chain else 'tb'}"
        try:
            response = session.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            return len(data) > 0
        except requests.exceptions.RetryError:
            raise NetworkException("Failed to verify chain type (max retries failed)")
        except requests.exceptions.JSONDecodeError:
            raise NetworkException(
                "Failed to verify chain type (response body is not JSON)"
            )

    def __init__(
        self,
        addresses,
        coin="BTC",
        chain="main",
        request_interval=(3, 1),
        transactions=None,
        **kwargs,
    ):
        """
        Initializes an instance of the EsploraClient class.

        Args:
            addresses (list): A list of human-readable crypto addresses.
            endpoint (str): The Esplora endpoint to use.
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0,N) for no rate limiting, where N>0.
        """
        # Blockstream.info's rate limits are unknown.
        # Ostensibly there are no limits for that site, but I got 429 errors when testing with (1000,1), so
        # the default limit will be the same as for mempool.space - 3 requests per second.

        super().__init__(
            addresses, request_interval=request_interval, transactions=transactions
        )

        self.db_connection_parameters = kwargs.get("db_connection_parameters")

        self.height = -1
        coin_map = {"BTC": "btc"}
        self.coin = coin_map.get(coin.upper())
        if not self.coin:
            raise ValueError(f"Unsupported coin '{coin}'")
        self.endpoint = kwargs.get("url")

        chain_map = {"main": "main", "test": "test"}
        self.chain = chain_map.get(chain)
        if not self.chain:
            raise ValueError(f"Unsupported chain '{chain}'")
        assert self._chain_is_correct(self.chain)

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
        session.mount(self.HTTPS_ADAPTER, HTTPAdapter(max_retries=retries))

        url = f"{self.endpoint}/blocks/tip/height"
        try:
            response = session.get(url, timeout=60)
            response.raise_for_status()
            return int(response.text)
        except requests.exceptions.RetryError:
            raise NetworkException(
                "Failed to retrieve block height (max retries failed)"
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
            self.transactions = self.deduplicate(self.transactions)
        self.height = block_height
        return self.transactions

    def _get_one_transaction_history(self, address):
        # This gets up to 50 mempool transactions + up to 25 confirmed transactions
        last_tx = ""
        data = [1]

        while len(data) > 0:
            url = f"{self.endpoint}/address/{address}/txs{last_tx}"
            session = requests.Session()
            retries = Retry(
                total=3,
                backoff_factor=self.interval_sec / self.requests,
                status_forcelist=[429, 502, 503, 504],
                allowed_methods={"GET"},
            )
            session.mount(self.HTTPS_ADAPTER, HTTPAdapter(max_retries=retries))

            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                data = response.json()
                for tx in data:
                    ctx = self._clean_tx(tx)
                    if ctx.confirmed and ctx.height < self.height:
                        return
                    ctx = self._clean_tx(tx)
                    yield ctx
                    last_tx = "/chain/" + ctx.txid

            except requests.exceptions.RetryError:
                raise NetworkException(
                    "Failed to retrieve transactions (max retries failed)"
                )
            except requests.exceptions.JSONDecodeError:
                raise NetworkException(
                    "Failed to retrieve transactions (response body is not JSON)"
                )
