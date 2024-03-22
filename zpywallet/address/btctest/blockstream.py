from .esplora import EsploraAddress


class BlockstreamAddress(EsploraAddress):
    """
    A class representing a list of Bitcoin testnet addresses.

    This class allows you to retrieve the balance, UTXO set, and transaction
    history of a Bitcoin testnet address using Blockstream.
    """

    def __init__(self, addresses, request_interval=(3, 1), transactions=None, **kwargs):
        super().__init__(
            addresses,
            request_interval=request_interval,
            transactions=transactions,
            url="https://blockstream.info/testnet/api",
            **kwargs
        )
