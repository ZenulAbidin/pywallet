import requests

from functools import reduce

from urllib3 import Retry
from requests.adapters import HTTPAdapter

from ..errors import NetworkException
from ..generated import wallet_pb2

from .provider import AddressProvider


class DogeChainClient(AddressProvider):
    """
    A class representing a list of crypto addresses.

    This class allows you to retrieve the balance and transaction history of a
    crypto address using DogeChain.
    """

    def _clean_tx(self, element):

        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=self.interval_sec / self.requests,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods={"GET"},
        )
        session.mount(self.HTTPS_ADAPTER, HTTPAdapter(max_retries=retries))

        url = f"https://dogechain.info/api/v1/transaction/{element['hash']}"
        response = session.get(url, timeout=60)
        response.raise_for_status()  # _get_one_transaction_history catches this
        element = response.json()["transaction"]

        new_element = wallet_pb2.Transaction()
        new_element.txid = element["hash"]

        if element["confirmations"] == 0:
            new_element.confirmed = False
            new_element.height = 0
        else:
            new_element.confirmed = True
            url = f"https://dogechain.info/api/v1/block/{element['block_hash']}"
            response = session.get(url, timeout=60)
            response.raise_for_status()
            new_element.height = response.json()["block"]["height"]

        new_element.timestamp = element["time"]

        for vin in element["inputs"]:
            txinput = new_element.btclike_transaction.inputs.add()
            txinput.txid = (
                ""
                if "previous_output" not in vin.keys()
                else vin["previous_output"].get("hash") or ""
            )
            txinput.index = (
                0
                if "previous_output" not in vin.keys()
                else vin["previous_output"].get("pos") or 0
            )
            txinput.amount = (
                0 if "value" not in vin.keys() else int(float(vin["value"]) * 1e8)
            )

        i = 0
        for vout in element["outputs"]:
            txoutput = new_element.btclike_transaction.outputs.add()
            txoutput.amount = int(float(vout["value"]) * 1e8)
            txoutput.index = i
            i += 1
            txoutput.address = vout["address"]
            txoutput.spent = vout["spent"] is not None

        # Now we must calculate the total fee
        total_inputs = sum([a.amount for a in new_element.btclike_transaction.inputs])
        total_outputs = sum([a.amount for a in new_element.btclike_transaction.outputs])
        new_element.total_fee = total_inputs - total_outputs

        new_element.btclike_transaction.fee = int(float(element["fee"]) * 1e8)
        new_element.fee_metric = wallet_pb2.BYTE

        return new_element

    def __init__(
        self,
        addresses,
        coin="DOGE",
        chain="main",
        request_interval=(3, 1),
        transactions=None,
    ):
        """
        Initializes an instance of the DogeChainClient class.

        Args:
            addresses (list): A list of human-readable crypto addresses.
            request_interval (tuple): A pair of integers indicating the number
                of requests allowed during a particular amount of seconds. Set
                to (0,N) for no rate limiting, where N>0.
        """
        super().__init__(
            addresses, request_interval=request_interval, transactions=transactions
        )
        coin_map = {
            "DOGE": "doge",
        }
        self.coin = coin_map.get(coin.upper())
        if not self.coin:
            raise ValueError(f"Undefined coin '{coin}'")

        # I don't think testnet is spported. But I'll have to check again.
        chain_map = {"main": "main", "test": "test"}
        self.chain = chain_map.get(chain)
        if not self.chain:
            raise ValueError(f"Undefined chain '{chain}'")

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

        base_url = "https://dogechain.info/api/v1/block/"
        try:
            best_block_hash_response = session.get(base_url + "besthash")

            # Any competent API will send an HTTP client error code
            # fi they also send an JSON error payload. So no need to worry.
            best_block_hash_response.raise_for_status()
            best_block_hash_data = best_block_hash_response.json()
            best_block_hash = best_block_hash_data["hash"]

            # Get block information using the best block hash
            block_info_response = session.get(base_url + best_block_hash)
            block_info_response.raise_for_status()
            block_info_data = block_info_response.json()

            return block_info_data["block"]["height"]
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
        self.height = block_height
        return self.transactions

    def _get_one_transaction_history(self, address):
        data = {"transactions": 1}
        i = 1

        while data["transactions"]:
            session = requests.Session()
            retries = Retry(
                total=3,
                backoff_factor=self.interval_sec / self.requests,
                status_forcelist=[429, 502, 503, 504],
                allowed_methods={"GET"},
            )
            session.mount(self.HTTPS_ADAPTER, HTTPAdapter(max_retries=retries))

            url = f"https://dogechain.info/api/v1/address/transactions/{address}/{i}"
            try:
                response = session.get(url, timeout=60)
                response.raise_for_status()
                data = response.json()
                for tx in data["transactions"]:
                    ctx = self._clean_tx(tx)
                    if ctx.confirmed and ctx.height < self.height:
                        # We already have those older transactions
                        # Strictly less-than allows for catching very large
                        # number of matches on the same block spanning
                        # multiple pages.
                        return
                    yield ctx
                    i += 1

            except requests.exceptions.RetryError:
                raise NetworkException(
                    "Failed to retrieve transactions (max retries failed)"
                )
            except requests.exceptions.JSONDecodeError:
                raise NetworkException(
                    "Failed to retrieve transactions (response body is not JSON)"
                )
