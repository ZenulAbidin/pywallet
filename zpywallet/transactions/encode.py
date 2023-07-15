
class TransactionInput:
    def __init__(self, txid, index, private_key):
        self.txid = txid
        self.index = index
        self.private_key = private_key

class  TransactionOutput:
    def __init__(self, address, value):
        """The address prefix determines the kind of script created (P2PKH or P2WPKH)"""
        self.address = address
        self.value = value

def create_transaction(inputs, outputs, segwit=True):
    """
    Creates an unsigned raw transaction, given an inputs array and an outputs array.
    By default, it creates Segwit transactions, but it can also send legacy transactions
    if you want.
    """
    pass