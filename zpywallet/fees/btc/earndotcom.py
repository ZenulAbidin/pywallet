import requests
from ...errors import NetworkException

class EarnDotComFeeEstimator:
    """
    A class representing a Bitcoin fee rate estimator using Earn.com API.

    This class allows you to retrieve the current fee rate for Bitcoin transactions using the Earn.com API.

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

    def __init__(self, request_interval=(1000, 1)):
        """
        Initializes an instance of the EarnDotComFeeEstimator class.

        Args:
            request_interval (tuple): A pair of integers indicating the number of requests allowed during
                a particular amount of seconds. Set to (0, N) for no rate limiting, where N > 0.
        """
        self.requests, self.interval_sec = request_interval

    def get_fee_rate(self):
        # Define the default API URL within the method for Earn.com:
        api_url = "https://bitcoinfees.earn.com/api/v1/fees/recommended"

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
            fee_rate = data["fastestFee"]  # You can use other fee rate values available in the response
            return fee_rate
        else:
            raise NetworkException("Failed to retrieve current fee rate from Earn.com")
