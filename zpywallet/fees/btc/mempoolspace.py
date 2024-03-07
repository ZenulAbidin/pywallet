from .esplora import EsploraFeeEstimator


class MempoolSpaceFeeEstimator(EsploraFeeEstimator):
    """
    A class representing a Mempool.space Bitcoin fee rate estimator.
    """

    def __init__(self, request_interval=(3, 1), transactions=None):
        super().__init__(
            request_interval=request_interval,
            transactions=transactions,
            url="https://mempool.space/api/v1",
        )
