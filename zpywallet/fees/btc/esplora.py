import requests
from ...errors import NetworkException

class EsploraFeeEstimator:
    """
    A class representing a Bitcoin fee rate estimator using Esplora API.

    This class allows you to retrieve the current fee rate for Bitcoin transactions using the Esplora API.

    Args:
        request_interval (tuple): A pair of integers indicating the number of requests allowed during
            a particular amount of seconds. Set to (0, N) for no rate limiting, where N > 0.

    Attributes:
        requests (int): The number of requests allowed during a specific interval.
        interval_sec (int): The interval in seconds for the specified number of requests.

    Methods:
        get_fee_rate(): Retrieves the current fee rate for Bitcoin transactions.

    Raises:
        Exception: If the API request fails or the fee rate cannot be retrieved.
    """

    def __init__(self, request_interval=(3, 1), **kwargs):
        """
        Initializes an instance of the EsploraFeeEstimator class.

        Args:
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0, N) for no rate limiting, where N > 0.
        """
        self.requests, self.interval_sec = request_interval
        self.endpoint = kwargs.get('url')

    def get_fee_rate(self):
        # Define the default API URL within the method:
        api_url = f"{self.endpoint}/fee-estimates"

        # Get the current fee rate from the specified API:
        for attempt in range(3, -1, -1):
            if attempt == 0:
                raise NetworkException("Network request failure")
            try:
                response = requests.get(api_url, timeout=60)
                break
            except requests.RequestException:
                pass
            except requests.exceptions.JSONDecodeError:
                pass

        if response.status_code == 200:
            data = response.json()
            fee_rate = data["1"]
            return fee_rate
        else:
            raise NetworkException("Failed to retrieve current fee rate")
