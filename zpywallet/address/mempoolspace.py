from .esplora import EsploraClient


class MempoolSpaceClient(EsploraClient):
    """
    A class representing a list of crypto testnet addresses.

    This class allows you to retrieve the balance, UTXO set, and transaction
    history of a crypto testnet address using Mempool.space.
    """

    def __init__(
        self,
        addresses,
        coin="BTC",
        chain="main",
        request_interval=(3, 1),
        transactions=None,
        **kwargs,
    ):
        super().__init__(
            addresses,
            coin=coin,
            chain=chain,
            request_interval=request_interval,
            transactions=transactions,
            url=f"https://mempool.space/{'' if chain == 'main' else 'testnet/'}api",
            **kwargs,
        )
