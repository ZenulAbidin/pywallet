from web3 import Web3, middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy

class EthereumWeb3FeeEstimator:
    """ Fee estimation class for Ethereum full nodes and Web3 clients.
        Most 3rd party providers e.g. Infura, QuickNode will also work here.

        Note: Ethereum calls fees "gas". So returned units are gas. There is
        also another function that returns the gas price
    """
    
    def __init__(self, **kwargs):
        self.web3 = Web3(Web3.HTTPProvider(kwargs.get('url')))
        # This makes it fetch max<priority>feepergas info faster
        self.web3.eth.set_gas_price_strategy(fast_gas_price_strategy)
        self.web3.middleware_onion.add(middleware.time_based_cache_middleware)
        self.web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
        self.web3.middleware_onion.add(middleware.simple_cache_middleware)

    def estimate_gas(self, transaction_obj):
        return self.web3.eth.estimate_gas(transaction_obj)
    
    def estimate_gas_price(self):
        return self.web3.eth.generate_gas_price()
