import requests

from zpywallet.errors import NetworkException

class BlockchainInfoAddress:
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
        
    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Bitcoin address.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        interval = 50
        offset = 0

        url = f"https://blockchain.info/rawaddr/{self.address}?limit={interval}&offset={offset}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            # The rate limit is 1 request every 10 seconds, so we will amortize the speed bump by sleeping every 200 milliseconds.
            # Since we have max 50 transactions, total execution time will be at least 10 seconds incuding the sleep time and user
            # code execution time, and if there are less than 50 transactions, we are finished fetching transactions anyway.
            for tx in data["txs"]:
                time.sleep(0.2)
                yield tx
            n_tx = data["n_tx"]
            offset += min(interval, n_tx)
        else:
            raise Exception("Failed to retrieve transaction history")
        
        while offset < n_tx:
            # WARNING: RATE LIMIT IS 1 REQUEST PER 10 SECONDS.
            url = f"https://blockchain.info/rawaddr/{self.address}?limit={interval}&offset={offset}"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                for tx in data["txs"]:
                    time.sleep(0.2)
                    yield tx
                offset += interval
            else:
                raise Exception("Failed to retrieve transaction history")

class BlockcypherAddress:
    """
    A class representing a Bitcoin address.

    This class allows you to retrieve the balance and transaction history of a Bitcoin address using the Blockcypher API.

    Args:
        address (str): The human-readable Bitcoin address.
        api_key (str): The API key for accessing the Blockcypher API.

    Attributes:
        address (str): The human-readable Bitcoin address.
        api_key (str): The API key for accessing the Blockcypher API.

    Methods:
        get_balance(): Retrieves the balance of the Bitcoin address.
        get_transaction_history(): Retrieves the transaction history of the Bitcoin address.

    Raises:
        Exception: If the API request fails or the address balance/transaction history cannot be retrieved.
    """

    def __init__(self, address, api_key):
        """
        Initializes an instance of the BlockcypherAddress class.

        Args:
            address (str): The human-readable Bitcoin address.
            api_key (str): The API key for accessing the Blockcypher API.
        """
        self.address = address
        self.api_key = api_key

    def get_balance(self):
        """
        Retrieves the balance of the Bitcoin address.

        Returns:
            float: The balance of the Bitcoin address in BTC.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        url = f"https://api.blockcypher.com/v1/btc/main/addrs/{self.address}/balance"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            balance = data["balance"] / 10**8  # Balance in BTC
            return balance
        else:
            raise Exception("Failed to retrieve address balance")

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Bitcoin address.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        url = f"https://api.blockcypher.com/v1/btc/main/addrs/{self.address}/full"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return data["txs"]
        else:
            raise Exception("Failed to retrieve transaction history")

class BlockchairAddress:
    """
    A class representing a Bitcoin address.

    This class allows you to retrieve the balance and transaction history of a Bitcoin address using the Blockchair API.

    Note: Blockchair proactively bans IP addresses so if this doesn't work for you, try another provider.

    Args:
        address (str): The human-readable Bitcoin address.

    Attributes:
        address (str): The human-readable Bitcoin address.

    Methods:
        get_balance(): Retrieves the balance of the Bitcoin address.
        get_transaction_history(): Retrieves the transaction history of the Bitcoin address.

    Raises:
        Exception: If the API request fails or the address balance/transaction history cannot be retrieved.
    """

    def __init__(self, address):
        """
        Initializes an instance of the BlockchairAddress class.

        Args:
            address (str): The human-readable Bitcoin address.
        """
        self.address = address

    def get_balance(self):
        """
        Retrieves the balance of the Bitcoin address.

        Returns:
            float: The balance of the Bitcoin address in BTC.

        Raises:
            Exception: If the API request fails or the address balance cannot be retrieved.
        """
        url = f"https://api.blockchair.com/bitcoin/dashboards/address/{self.address}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            balance = data["data"][self.address]["address"]["balance"] / 10**8  # Balance in BTC
            return balance
        else:
            raise Exception("Failed to retrieve address balance")

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Bitcoin address.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the API request fails or the transaction history cannot be retrieved.
        """
        url = f"https://api.blockchair.com/bitcoin/dashboards/address/{self.address}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return data["data"][self.address]["transactions"]
        else:
            raise Exception("Failed to retrieve transaction history")

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


# Usage example
#api_key = "YOUR_BLOCKCHAIR_API_KEY"  # Replace with your Blockchair API key
#getblock_explorer = BlockchairExplorer(api_key)
#address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Example address

#address_data = getblock_explorer.get_address(address)
#transactions = getblock_explorer.get_transactions(address)