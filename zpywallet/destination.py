from enum import Enum
from .utils.keys import PublicKey


class FeePolicy(Enum):
    """
    Enumeration representing fee policies.

    FeePolicy.NONE: Indicates no fee policy.
    FeePolicy.PROPORTIONAL: Indicates a proportional fee policy.
    """


class Destination:
    """
    Represents a destination address and amount to send.
    """

    def __init__(self, address, amount, network, fee_policy=FeePolicy.NONE):
        """
        Initializes a Destination object.

        Args:
            address (str): The destination address.
            amount (int): The amount of the destination in the lowest denomination.
            network: The network associated with the destination.
            fee_policy (FeePolicy, optional): The fee policy associated with the destination. Defaults to FeePolicy.NONE.
        """
        self._network = network
        self._address = address
        self._amount = amount
        self._fee_policy = fee_policy
        self._script_pubkey = PublicKey.script(address, network)

    def address(self):
        """
        Returns the destination address.
        """
        return self._address

    def amount(self, in_standard_units=True):
        """
        Returns the amount of the destination.

        Args:
            in_standard_units (bool, optional): If True, returns the amount in standard units. If False, returns the amount in the lowest denomination. Defaults to True.
        """
        if not in_standard_units:
            if self._network.SUPPORTS_EVM:
                return int(self._amount * 1e18)
            else:
                return int(self._amount * 1e8)
        else:
            return self._amount

    def script_pubkey(self):
        """
        Returns the script public key associated with the destination.
        """
        return self._script_pubkey
