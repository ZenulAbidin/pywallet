import requests

from zpywallet.errors import NetworkException
from ...utils.utils import convert_to_utc_timestamp

class BTCcomExplorer:
    """
    A class representing a Bitcoin address.

    This class allows you to retrieve the balance and transaction history of a Bitcoin address using the BTC.com API.

    Args:
        api_key (str): The API key for accessing the BTC.com API.

    Attributes:
        api_key (str): The API key for accessing the BTC.com API.

    Methods:
        get_balance(): Retrieves the balance of the Bitcoin address.
        get_transaction_history(): Retrieves the transaction history of the Bitcoin address.

    Raises:
        Exception: If the API request fails or the address balance/transaction history cannot be retrieved.
    """

    def _clean_tx(self, element):
        new_element = {}
        new_element['txid'] = element['hash']
        new_element['height'] = element['block_height']
        new_element['timestamp'] = convert_to_utc_timestamp(element['received'])

        new_element['inputs'] = []
        new_element['outputs'] = []
        for vin in element['inputs']:
            txinput = {}
            txinput['txid'] = vin['prev_tx_hash']
            txinput['index'] = vin['prev_position']
            txinput['amount'] = vin['prev_value'] / 1e8
            new_element['inputs'].append(txinput)

        i = 0 
        for vout in element['vout']:
            txoutput = {}
            txoutput['amount'] = vout['value'] / 1e8
            txoutput['index'] = i
            i += 1
            txoutput['address'] = vout['scriptpubkey_address']

        # Now we must calculate the total fee
        total_inputs = sum([a['amount'] for a in new_element['inputs']])
        total_outputs = sum([a['amount'] for a in new_element['outputs']])
        new_element['total_fee'] = (total_inputs - total_outputs) / 1e8

        new_element['fee'] = (total_inputs - total_outputs) / element['vsize']
        new_element['fee'] = 'vbyte'

    def __init__(self, api_key):
        """
        Initializes an instance of the BTCcomExplorer class.

        Args:
            api_key (str): The API key for accessing the BTC.com API.
        """
        self.api_key = api_key

    def get_balance(self, address):
        """
        Retrieves the balance of a Bitcoin address.

        Args:
            address (str): The Bitcoin address.

        Returns:
            float: The balance of the Bitcoin address in BTC.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        url = f"https://chain.api.btc.com/v3/address/{address}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            balance = data.get("data", {}).get("balance") or 0
            return float(balance)
        else:
            raise Exception("Failed to retrieve address balance")

    def get_transaction_history(self, address):
        """
        Retrieves the transaction history of a Bitcoin address.

        Args:
            address (str): The Bitcoin address.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        url = f"https://chain.api.btc.com/v3/address/{address}/tx"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            raise Exception("Failed to retrieve transaction history")
