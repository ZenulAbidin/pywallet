# Amounts are always described internally in the lowest possible denomination
# to make them integers.
class Destination:
    def __init__(self, network, address, amount, in_standard_units=False):
        self._network = network
        self._address = address
        if in_standard_units:
            if network.SUPPORTS_EVM:
                self._amount = amount / 1e18
            else:
                self._amount = amount / 1e8
        else:
            self._amount = amount

    def address(self):
        return self._address
    
    def amount(self):
        return self._amount
