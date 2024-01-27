from statistics import median


from .blockchain_info import BlockchainInfoFeeEstimator
from .blockcypher import BlockcypherFeeEstimator
from .blockstream import BlockstreamFeeEstimator
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

    def __init__(self, **kwargs):
        self.provider_list = []
        fullnode_endpoints = kwargs.get('fullnode_endpoints')
        esplora_endpoints = kwargs.get('esplora_endpoints')
        blockcypher_tokens = kwargs.get('blockcypher_tokens')

        if not esplora_endpoints:
            esplora_endpoints = [] + btc_esplora_nodes
        if not fullnode_endpoints:
            fullnode_endpoints = [] + btc_nodes


        self.provider_list.append(BlockchainInfoFeeEstimator())
        tokens = blockcypher_tokens
        if not tokens:
            tokens = []
        for token in tokens:
            self.provider_list.append(BlockcypherFeeEstimator(api_key=token))
        self.provider_list.append(BlockcypherFeeEstimator()) # No token (free) version
        self.provider_list.append(BlockstreamFeeEstimator())
        self.provider_list.append(EarnDotComFeeEstimator())
        for endpoint in esplora_endpoints:
            self.provider_list.append(EsploraFeeEstimator(**endpoint))
        for endpoint in fullnode_endpoints:
            self.provider_list.append(BitcoinRPCClient(**endpoint))
        self.provider_list.append(MempoolSpaceFeeEstimator())

    
    def get_fee_rate(self):
        """
        Gets the network fee rate.

        Returns:
            int: The network fee rate.

        Raises:
            Exception: If none of the fee providers are working after the specified number of tries.
        """
        fee_rates = []

        for provider in self.provider_list:
            try:
                fee_rate = provider.get_fee_rate()
                fee_rates.append(fee_rate)
            except NetworkException:
                continue

        # Return the median fee rate from all collected rates
        return median(fee_rates)