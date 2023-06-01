import requests

from zpywallet.errors import NetworkException

class Address:
    """
    A class representing a Bitcoin address.

    This class allows you to retrieve the balance of a Bitcoin address using the Blockchain.info API.
    """

    def __init__(self, coin_address):
        """
        Initializes an instance of the Address class.

        Args:
            address (str): The human-readable Bitcoin address.
        """
        self.address = coin_address

    def get_balance(self):
        """
        Retrieves the balance of the Bitcoin address.

        Returns:
            float: The balance of the Bitcoin address in BTC.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        url = f"https://blockchain.info/q/addressbalance/{self.address}"
        response = requests.get(url)

        if response.status_code == 200:
            balance = int(response.text) / 100000000  # Convert satoshis to bitcoins
            return balance
        else:
            raise NetworkException("Failed to retrieve address balance")