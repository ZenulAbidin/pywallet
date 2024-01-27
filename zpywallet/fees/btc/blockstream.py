from .esplora import EsploraFeeEstimator

class BlockstreamFeeEstimator(EsploraFeeEstimator):
    def __init__(self, request_interval=(3,1), transactions=None):
        super().__init__(request_interval=request_interval, transactions=transactions, url="https://blockstream.info/api")