from statistics import median


from .bitstamp import BitstampFeeEstimator
from .blockchain_info import BlockchainInfoFeeEstimator
from .blockchair import BlockchairFeeEstimator
from .blockcypher import BlockcypherFeeEstimator
from .blockstream import BlockstreamFeeEstimator
from .btcdotcom import BTCDotComFeeEstimator
from .earndotcom import EarnDotComFeeEstimator
from .esplora import EsploraFeeEstimator
from .fullnode import BitcoinRPCClient
from .mempoolspace import MempoolSpaceFeeEstimator
from ...errors import NetworkException
from ...nodes.btc import btc_nodes, btc_esplora_nodes

class BitcoinFeeEstimator:
    """ Load balancer for all BTC fee providers provided to an instance of this class,
        using the round robin scheduling algorithm.
    """

    def __init__(self, max_cycles=100, **kwargs):
        self.provider_list = []
        self.current_index = 0
        self.max_cycles = max_cycles
        fullnode_endpoints = kwargs.get('fullnode_endpoints')
        esplora_endpoints = kwargs.get('esplora_endpoints')
        blockcypher_tokens = kwargs.get('blockcypher_tokens')

        if not esplora_endpoints:
            esplora_endpoints = [] + btc_esplora_nodes
        if not fullnode_endpoints:
            fullnode_endpoints = [] + btc_nodes



        self.provider_list.append(BitstampFeeEstimator())
        self.provider_list.append(BlockchainInfoFeeEstimator())
        tokens = blockcypher_tokens
        if not tokens:
            tokens = []
        for token in tokens:
            self.provider_list.append(BlockcypherFeeEstimator(api_key=token))
        self.provider_list.append(BlockcypherFeeEstimator()) # No token (free) version
        self.provider_list.append(BlockchairFeeEstimator())
        self.provider_list.append(BlockstreamFeeEstimator())
        self.provider_list.append(BTCDotComFeeEstimator())
        self.provider_list.append(EarnDotComFeeEstimator())
        for endpoint in esplora_endpoints:
            self.provider_list.append(EsploraFeeEstimator(**endpoint))
        for endpoint in fullnode_endpoints:
            self.provider_list.append(BitcoinRPCClient(**endpoint))
        self.provider_list.append(MempoolSpaceFeeEstimator())

    def advance_to_next_provider(self):
        if not self.provider_list:
            return
        
        newindex = (self.current_index + 1) % len(self.provider_list)
        self.current_index = newindex
    
    def get_fee_rate(self):
        """
        Gets the network fee rate.

        Returns:
            int: The network fee rate.

        Raises:
            Exception: If none of the fee providers are working after the specified number of tries.
        """
        cycle = 1
        fee_rates = []

        while cycle <= self.max_cycles:
            try:
                fee_rate = self.provider_list[self.current_index].get_fee_rate()
                fee_rates.append(fee_rate)
            except NetworkException:
                self.advance_to_next_provider()

            cycle += 1

        if not fee_rates:
            raise NetworkException(f"None of the fee providers are working after {self.max_cycles} tries")

        # Return the median fee rate from all collected rates
        return median(fee_rates)