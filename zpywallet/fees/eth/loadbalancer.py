from .fullnode import EthereumWeb3FeeEstimator
from ...errors import NetworkException
from ...nodes.eth import eth_nodes

class EthereumFeeEstimator:
    """ Load balancer for all ETH gas providers provided to an instance of this class,
        using the round robin scheduling algorithm.
    """

    def __init__(self, max_cycles=100, **kwargs):
        self.provider_list = []
        self.current_index = 0
        self.max_cycles = max_cycles
        fullnode_endpoints = kwargs.get('fullnode_endpoints')

        if not fullnode_endpoints:
            fullnode_endpoints = [] + eth_nodes

        for endpoint in fullnode_endpoints:
            self.provider_list.append(EthereumWeb3FeeEstimator(**endpoint))

    def sync(self):
        # There is nothing to sync on EVM chains
        return

    def estimate_gas(self, transaction_obj):
        """
        Gets the gas required for a particular transaction.

        Returns:
            int: The gas required for the transaction.

        Raises:
            Exception: If the API request fails or the gas cannot be retrieved.
        """
        cycle = 1
        while cycle <= self.max_cycles:
            try:
                return self.provider_list[self.current_index].estimate_gas(transaction_obj)
            except NetworkException:
                self.advance_to_next_provider()
                cycle += 1
        raise NetworkException(f"None of the fee providers are working after {self.max_cycles} tries")

        

    def advance_to_next_provider(self):
        if not self.provider_list:
            return
        
        newindex = (self.current_index + 1) % len(self.provider_list)
        self.current_index = newindex


    def estimate_gas_price(self):
        """
        Gets the gas price for the network.

        Returns:
            int: The gas price for the network.

        Raises:
            Exception: If the API request fails or the gas cannot be retrieved.
        """
        cycle = 1
        while cycle <= self.max_cycles:
            try:
                return self.provider_list[self.current_index].estimate_gas_price()
            except NetworkException:
                self.advance_to_next_provider()
                cycle += 1
        raise NetworkException(f"None of the fee providers are working after {self.max_cycles} tries")