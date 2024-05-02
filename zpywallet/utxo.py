from zpywallet.errors import PublicKeyHashException
from zpywallet.utils.base58 import is_b58check
from zpywallet.utils.keys import PublicKey
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
        _internal_param_do_not_use=None,
        _network=None,
    ):
        """
        Initializes a UTXO object.

        Args:
            transaction (Transaction): The transaction associated with the UTXO.
            index (int): The index of the UTXO in the transaction outputs.
            other_transactions (list, optional): Other transactions related to the UTXO. Defaults to None.
            addresses (list, optional): Addresses associated with the UTXO. Defaults to None.
            only_mine (bool, optional): If True, only includes UTXOs belonging to the specified addresses.
                Defaults to False.
        """
        if other_transactions is None:
            other_transactions = []
        if addresses is None:
            addresses = []
        if _internal_param_do_not_use:
            self._output = _internal_param_do_not_use
            self.network = _network
            return

        if transaction.network().SUPPORTS_EVM:
            raise ValueError("Blockchain does not support UTXOs")

        self._network = transaction.network()
        outputs = transaction.sat_outputs(only_unspent=True)
        try:
            output = outputs[index]
        except IndexError:
            raise IndexError(f"Transaction output {index} does not exist")

        output["txid"] = transaction.txid()
        output["height"] = transaction.height()
        try:
            output["address_hash"] = PublicKey.from_address(
                output["address"], self._network
            ).hash160()
        except PublicKeyHashException:
            output["address_hash"] = None

        for ot in other_transactions:
            for i in ot.sat_inputs():
                if i["txid"] == transaction.txid() and i["index"] == index:
                    raise ValueError("UTXO has already been spent")

        if only_mine and output["address"] not in addresses:
            raise ValueError("UTXO does not belong to this wallet")

        self._output = output

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
            in_standard_units (bool, optional): If True, returns the amount in standard units.
                If False, returns the amount in the lowest denomination. Defaults to True.
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

    def is_legacy(self):
        """Returns whether this UTXO is for a legacy input."""
        if not self.address() and self._addresshash():
            # P2PK
            return True
        return is_b58check(self.address())

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

    def _addresshash(self):
        """
        Returns the script pubkey associated with the UTXO (for internal use only).
        """
        return self._output["address_hash"]

    def _nsequence(self):
        """
        Returns the sequence number associated with the UTXO (for internal use only).
        """
        return self._output["nsequence"]
