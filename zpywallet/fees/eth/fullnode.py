from web3 import Web3

class EthereumWeb3FeeEstimator:
    """ Fee estimation class for Ethereum full nodes and Web3 clients.
        Most 3rd party providers e.g. Infura, QuickNode will also work here.

        Note: Ethereum calls fees "gas". So returned units are gas. There is
        also another function that returns the gas price
    """
    
    def __init__(self, **kwargs):
        self.web3 = Web3(Web3.HTTPProvider(kwargs.get('url')))

    def estimate_gas(self, transaction_obj):
        return self.web3.eth.estimate_gas(transaction_obj)
    
    def estimate_gas_price(self):
        return self.web3.eth.generate_gas_price()
