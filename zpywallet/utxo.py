from .transaction import Transaction


class UTXO:
    """
    Represents an Unspent Transaction Output (UTXO) associated with a transaction.

    NOTE: Currently, UTXO can only detect compressed/uncompressed P2PKH
    (legacy "1") and compressed P2WPKH (bech32 "bc1q") addresses.
    """

    def __init__(
        self,
        transaction: Transaction,
        index: int,
        other_transactions=None,
        addresses=None,
        only_mine=False,
        _unsafe_internal_testing_only=None,
    ):
        """
        Initializes a UTXO object.

        Args:
            transaction (Transaction): The transaction associated with the UTXO.
            index (int): The index of the UTXO in the transaction outputs.
            other_transactions (list, optional): Other transactions related to the UTXO. Defaults to None.
            addresses (list, optional): Addresses associated with the UTXO. Defaults to None.
            only_mine (bool, optional): If True, only includes UTXOs belonging to the specified addresses. Defaults to False.
            _unsafe_internal_testing_only: For internal testing purposes only. Defaults to None.
        """
        if other_transactions is None:
            other_transactions = []
        if addresses is None:
            addresses = []
        if _unsafe_internal_testing_only:
            self._output = _unsafe_internal_testing_only
            return

        if transaction.network().SUPPORTS_EVM:
            raise ValueError("Blockchain does not support UTXOs")

        self._network = transaction.network()
        outputs = transaction.sat_outputs(only_unspent=True)
        try:
            output = outputs[index]
            output["txid"] = transaction.txid()
            output["height"] = transaction.height()

            for ot in other_transactions:
                for i in ot.sat_inputs():
                    if i["txid"] == transaction.txid() and i["index"] == index:
                        raise ValueError("UTXO has already been spent")

            if not only_mine or output["address"] in addresses:
                self._output = output
            else:
                raise ValueError("UTXO does not belong to this wallet")
        except IndexError:
            raise IndexError(f"Transaction output {index} does not exist")

    def network(self):
        """
        Returns the network associated with the UTXO.
        """
        return self._network

    def txid(self):
        """
        Returns the transaction ID of the UTXO.
        """
        return self._output["txid"]

    def index(self):
        """
        Returns the index of the UTXO.
        """
        return self._output["index"]

    def amount(self, in_standard_units=True):
        """
        Returns the amount of the UTXO.

        Args:
            in_standard_units (bool, optional): If True, returns the amount in standard units. If False, returns the amount in the lowest denomination. Defaults to True.
        """
        if in_standard_units:
            return self._output["amount"] / 1e8
        else:
            return int(self._output["amount"])

    def address(self):
        """
        Returns the address associated with the UTXO.
        """
        return self._output["address"]

    def height(self):
        """
        Returns the block height of the UTXO.
        """
        return self._output["height"]

    # Private methods, do not use in user programs.
    def _private_key(self):
        """
        Returns the private key associated with the UTXO (for internal use only).
        """
        return self._output["private_key"]

    def _script_pubkey(self):
        """
        Returns the script pubkey associated with the UTXO (for internal use only).
        """
        return self._output["script_pubkey"]
