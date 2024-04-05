from .generated import wallet_pb2


class Transaction:
    """
    Represents a transaction with associated metadata.
    """

    def __init__(self, transaction: wallet_pb2.Transaction, network):
        """
        Initializes a Transaction object.

        Args:
            transaction (wallet_pb2.Transaction): The transaction protobuf message.
            network: The network associated with the transaction.
        """
        self._network = network
        self._txid = transaction.txid
        self._timestamp = transaction.timestamp
        self._confirmed = transaction.confirmed
        self._height = transaction.height
        self._total_fee = transaction.total_fee

        if transaction.fee_metric == wallet_pb2.FeeMetric.Value("BYTE"):
            self._fee_metric = "bytes"
        elif transaction.fee_metric == wallet_pb2.FeeMetric.Value("VBYTE"):
            self._fee_metric = "vbytes"
        elif transaction.fee_metric == wallet_pb2.FeeMetric.Value("WEI"):
            self._fee_metric = "wei"
        else:
            raise ValueError("Unknown fee metric")

        self._sat_metadata = {}
        self._evm_metadata = {}
        if network.SUPPORTS_EVM:
            self._evm_metadata["from"] = transaction.ethlike_transaction.txfrom
            self._evm_metadata["to"] = transaction.ethlike_transaction.txto
            self._evm_metadata["amount"] = transaction.ethlike_transaction.amount
            self._evm_metadata["gasUsed"] = transaction.ethlike_transaction.gas
            self._evm_metadata["data"] = transaction.ethlike_transaction.data
        else:
            self._sat_metadata["feeRate"] = transaction.btclike_transaction.fee
            self._sat_metadata["inputs"] = []
            self._sat_metadata["outputs"] = []
            for i in transaction.btclike_transaction.inputs:
                i_ = {}
                i_["txid"] = i.txid
                i_["index"] = i.index
                i_["amount"] = i.amount
                i_["witness"] = []
                for w in i.witness_data:
                    i_["witness"].append(w)
                self._sat_metadata["inputs"].append(i_)
            for o in transaction.btclike_transaction.outputs:
                o_ = {}
                o_["address"] = o.address
                o_["index"] = o.index
                o_["amount"] = o.amount
                o_["spent"] = o.spent
                self._sat_metadata["outputs"].append(o_)

    def network(self):
        """
        Returns the network associated with the transaction.
        """
        return self._network

    def txid(self):
        """
        Returns the transaction ID.
        """
        return self._txid

    def timestamp(self):
        """
        Returns the timestamp of the transaction.
        """
        return self._timestamp

    def confirmed(self):
        """
        Returns a boolean indicating if the transaction is confirmed.
        """
        return self._confirmed

    def height(self):
        """
        Returns the block height of the transaction.
        """
        return self._height

    def total_fee(self, in_standard_units=True):
        """
        Returns the total fee of the transaction.

        Args:
            in_standard_units (bool, optional): If True, returns the fee in standard units.
                If False, returns the fee in the lowest denomination. Defaults to True.
        """
        if in_standard_units:
            if self._network.SUPPORTS_EVM:
                fee = self._total_fee / 1e18
            else:
                fee = self._total_fee / 1e8
        else:
            fee = self._total_fee
        return (fee, self._fee_metric)

    def evm_from(self):
        """
        Returns the sender address of the transaction (EVM).
        """
        if not self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        return self._evm_metadata["from"]

    def evm_to(self):
        """
        Returns the recipient address of the transaction (EVM).
        """
        if not self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        return self._evm_metadata["to"]

    def evm_amount(self, in_standard_units=True):
        """
        Returns the amount transferred in the transaction (EVM).

        Args:
            in_standard_units (bool, optional): If True, returns the amount in standard units.
                If False, returns the amount in the lowest denomination. Defaults to True.
        """
        if not self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        if in_standard_units:
            return self._evm_metadata["amount"] / 1e18
        else:
            return self._evm_metadata["amount"]

    def evm_gas(self):
        """
        Returns the gas used in the transaction (EVM).
        """
        if not self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        return self._evm_metadata["gasUsed"]  # always in WEI

    def evm_data(self):
        """
        Returns the data associated with the transaction (EVM).
        """
        if not self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        return self._evm_metadata["data"]

    def sat_feerate(self):
        """
        Returns the fee rate of the transaction (Bitcoin-like).
        """
        if self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        return self._sat_metadata["feeRate"]  # always in sats per byte or vbyte

    def sat_inputs(self, include_witness=False):
        """
        Returns the inputs of the transaction (Bitcoin-like).

        Args:
            include_witness (bool, optional): If True, includes witness data. Defaults to False.
        """
        if self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        inputs = []
        for i in self._sat_metadata["inputs"]:
            if not include_witness and "witness" in i.keys():
                del i["witness"]
            inputs.append(i)
        return inputs

    def sat_outputs(self, only_unspent=False):
        """
        Returns the outputs of the transaction (Bitcoin-like).

        Args:
            only_unspent (bool, optional): If True, returns only unspent outputs. Defaults to False.
        """
        if self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        outputs = []
        for o in self._sat_metadata["outputs"]:
            if not only_unspent or not o["spent"]:
                outputs.append(o)
        return outputs
