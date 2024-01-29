from enum import Enum
from .utils.keys import PublicKey


class FeePolicy(Enum):
    NONE = 0
    PROPORTIONAL = 1

# Amounts are always described internally in the lowest possible denomination
# to make them integers.
class Destination:
    def __init__(self, address, amount, network, fee_policy=FeePolicy.NONE):
        self._network = network
        self._address = address
        self._amount = amount
        self._fee_policy = fee_policy
        self._script_pubkey = PublicKey.script(address, network)
                

    def address(self):
        return self._address
    
    def amount(self, in_standard_units=True):
        if not in_standard_units:
            if self._network.SUPPORTS_EVM:
                return int(self._amount * 1e18)
            else:
                return int(self._amount * 1e8)
        else:
            return self._amount
    
    def script_pubkey(self):
        return self._script_pubkey
