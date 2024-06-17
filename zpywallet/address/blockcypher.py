from functools import reduce
import requests
import datetime

from urllib3 import Retry
from requests.adapters import HTTPAdapter

from .provider import AddressProvider

from ..errors import NetworkException
from ..generated import wallet_pb2


# Note - the input date is assumed to be in UTC, even if you change the format string.
def convert_to_utc_timestamp(date_string, format_string="%Y-%m-%dT%H:%M:%SZ"):
    utc_timezone = datetime.timezone.utc
    date_object = datetime.datetime.strptime(date_string, format_string).replace(tzinfo=utc_timezone)
    return int(date_object.timestamp())


class BlockcypherClient(AddressProvider):
    """
    A class representing a list of crypto addresses.

    This class allows you to retrieve the balance, UTXO set, and transaction
    history of a crypto address using Blockcypher.
    """

    DEFAULT_URL = "https://api.blockcypher.com"

    def _clean_tx(self, element):
        new_element = wallet_pb2.Transaction()
        new_element.txid = element["hash"]

        if "block_height" not in element.keys():
            new_element.confirmed = False
        elif element["block_height"] == -1:
            new_element.confirmed = False
        elif element["block_index"] == 0:  # coinbase transaction
            new_element.confirmed = True
            new_element.height = 0
        else:
            new_element.confirmed = True
            new_element.height = element["block_height"]

        if "confirmed" in element.keys():
            new_element.timestamp = convert_to_utc_timestamp(
                element["confirmed"].split(".")[0].split("Z")[0], "%Y-%m-%dT%H:%M:%S"
            )

        for vin in element["inputs"]:
            txinput = new_element.btclike_transaction.inputs.add()
            txinput.txid = "" if "prev_hash" not in vin.keys() else vin["prev_hash"]
            txinput.index = vin["output_index"]
            txinput.amount = (
                0 if "output_value" not in vin.keys() else int(vin["output_value"])
            )

        i = 0
        for vout in element["outputs"]:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(vout["value"])
            txoutput.index = i
            i += 1
            if vout["addresses"]:
                txoutput.address = vout["addresses"][0]
            txoutput.spent = "spent_by" in vout.keys()

        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])
        new_element.total_fee = total_inputs - total_outputs

        size_element = (
            element["vsize"] if "vsize" in element.keys() else element["size"]
        )
        new_element.btclike_transaction.fee = int(new_element.total_fee // size_element)
        new_element.fee_metric = wallet_pb2.VBYTE

        return new_element

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
        Initializes an instance of the BlockcypherAddress class.

        Args:
            addresses (list): A list of human-readable crypto addresses.
            api_key (str): The API key for accessing the Blockcypher API.
            request_interval (tuple): A pair of integers indicating the number
                of requests allowed during a particular amount of seconds.
                Set to (0,N) for no rate limiting, where N>0.
        """
        super().__init__(
            addresses, request_interval=request_interval, transactions=transactions
        )
        self.api_key = kwargs.get("blockcypher_token")
        self.height = -1
        coin_map = {
            "BTC": "btc",
            "LTC": "ltc",
            "DOGE": "doge",
            "BCY": "bcy",
            "DASH": "dash",
        }
        self.coin = coin_map.get(coin.upper())
        if not self.coin:
            raise ValueError(f"Undefined coin '{coin}'")

        chain_map = {"main": "main", "test": "test"}
        self.chain = chain_map.get(chain)
        if not self.chain:
            raise ValueError(f"Undefined chain '{chain}'")

        self.base_url = kwargs.get("base_url", self.DEFAULT_URL)

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

        url = f"{self.base_url}/v1/{self.coin}/{self.chain}"
        try:
            params = None
            if self.api_key:
                params = {"token", self.api_key}
            response = session.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["height"]
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
            list: A list of transaction objects.

        Raises:
            NetworkException: If the API request fails or the transaction
                history cannot be retrieved.
        """
        block_height = self.get_block_height()
        for address in self.addresses:
            self.transactions.extend(self._get_one_transaction_history(address))
            self.transactions = self.deduplicate(self.transactions)
        # Ensure unconfirmed transactions are last.
        self.transactions.sort(key=lambda tx: tx.height if tx.confirmed else 1e100)
        self.height = block_height
        return self.transactions

    def _get_one_transaction_history(self, address):
        params = {"token", self.api_key} if self.api_key else None
        interval = 50

        # Set a very high UTXO limit for those rare address that have crazy high input/output counts.
        # This seems to work as of April 2024
        txlimit = 10000

        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=self.interval_sec / self.requests,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods={"GET"},
        )
        session.mount(self.HTTPS_ADAPTER, HTTPAdapter(max_retries=retries))

        data = {"hasMore": True}
        block_height = None

        try:
            while "hasMore" in data.keys() and data["hasMore"]:
                session = requests.Session()
                retries = Retry(
                    total=3,
                    backoff_factor=self.interval_sec / self.requests,
                    status_forcelist=[429, 502, 503, 504],
                    allowed_methods={"GET"},
                )
                session.mount(self.HTTPS_ADAPTER, HTTPAdapter(max_retries=retries))

                url = (
                    f"{self.base_url}/v1/{self.coin}/{self.chain}/addrs/{address}"
                    + f"/full?limit={interval}{'' if not block_height else f'&before={block_height}'}&txlimit={txlimit}"
                )
                response = session.get(url, params=params, timeout=60)
                response.raise_for_status()
                data = response.json()
                for tx in data["txs"]:
                    ctx = self._clean_tx(tx)
                    block_height = ctx.height
                    if ctx.confirmed and ctx.height < self.height:
                        # We already have those older transactions
                        # Strictly less-than allows for catching very large
                        # number of matches on the same block spanning
                        # multiple pages.
                        return
                    yield ctx
                if not data["txs"]:
                    return
                block_height = ctx.height
        except requests.exceptions.RetryError:
            raise NetworkException(
                "Failed to retrieve transactions (max retries failed)"
            )
        except requests.exceptions.JSONDecodeError:
            raise NetworkException(
                "Failed to retrieve transactions (response body is not JSON)"
            )
