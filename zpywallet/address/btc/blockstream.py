from .esplora import EsploraAddress

class BlockstreamAddress(EsploraAddress):
    def __init__(self, addresses, request_interval=(3,1), transactions=None):
        super().__init__(addresses, "https://blockstream.info/api", request_interval=request_interval, transactions=transactions)