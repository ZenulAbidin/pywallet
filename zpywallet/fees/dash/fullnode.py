import random
import requests

from ...errors import NetworkException

class DashRPCClient:
    """Fee estimation class using Dash full nodes.
    """
    
    def __init__(self, **kwargs):
        self.rpc_url = kwargs.get('url')
        self.rpc_user = kwargs.get('user')
        self.rpc_password = kwargs.get('password')

    
    def _send_rpc_request(self, method, params=None):
        payload = {
            'method': method,
            'params': params or [],
            'jsonrpc': '2.0',
            'id': random.randint(1, 999999)
        }
        try:
            response = requests.post(self.rpc_url, auth=(self.rpc_user, self.rpc_password) if self.rpc_user and \
                                        self.rpc_password else None, json=payload, timeout=86400)
            j = response.json()
            if 'result' not in j.keys():
                raise NetworkException("Failed to get result")
            return j  # Return the JSON response
        except Exception as e:
            raise NetworkException(f"RPC call failed: {str(e)}")
    
    def get_fee_rate(self, blocks=6):
        """
        Get fee rate estimate for a target number of blocks.
        
        Args:
            blocks (int): Target number of blocks for fee rate estimation.

        Returns:
            float: Fee rate in satoshis per virtual byte.
        """
        try:
            estimate_response = self._send_rpc_request('estimatesmartfee', [blocks])
            fee_rate = estimate_response['result']['feerate'] / 0.00001
            return fee_rate
        except Exception as e:
            raise NetworkException(f"Failed to get fee rate: {str(e)}")
