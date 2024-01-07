from .btc.all import broadcast_transaction_btc
from .btctest.all import broadcast_transaction_btctest
from .bcy.all import broadcast_transaction_bcy
from .eth.all import broadcast_transaction_eth
from .dash.all import broadcast_transaction_dash
from .dashtest.all import broadcast_transaction_dashtest
from .doge.all import broadcast_transaction_doge
from .dogetest.all import broadcast_transaction_dogetest
from .ltc.all import broadcast_transaction_ltc
from .ltctest.all import broadcast_transaction_ltctest
from ..network import *

def broadcast_transaction(transaction: str, network):
    if network.COIN == "BTC":
        if not network.TESTNET:
            broadcast_transaction_btc(transaction)
        else:
            broadcast_transaction_btctest(transaction)
    elif network.COIN == "LTC":
        if not network.TESTNET:
            broadcast_transaction_ltc(transaction)
        else:
            broadcast_transaction_ltctest(transaction)
    elif network.COIN == "DASH":
        if not network.TESTNET:
            broadcast_transaction_dash(transaction)
        else:
            broadcast_transaction_dashtest(transaction)
    elif network.COIN == "DOGE":
        if not network.TESTNET:
            broadcast_transaction_doge(transaction)
        else:
            broadcast_transaction_dogetest(transaction)
    elif network.COIN == "ETH":
        broadcast_transaction_eth(transaction)
    elif network.COIN == "BCY":
        broadcast_transaction_bcy(transaction)
    else:
        raise ValueError("Cannot broadcast transaction: Unsupported network")