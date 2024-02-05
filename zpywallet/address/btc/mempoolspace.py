from .esplora import EsploraAddress


class MempoolSpaceAddress(EsploraAddress):
    def __init__(self, addresses, request_interval=(3, 1), transactions=None, **kwargs):
        super().__init__(
            addresses,
            request_interval=request_interval,
            transactions=transactions,
            url="https://mempool.space/api/v1",
            **kwargs
        )
