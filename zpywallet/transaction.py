from .generated import wallet_pb2

class Transaction:
    def __init__(self, transaction: wallet_pb2.Transaction, network):
        self._network = network
        self._txid = transaction.txid
        self._timestamp = transaction.timestamp
        self._confirmed = transaction.confirmed
        self._height = transaction.height
        self._total_fee = transaction.total_fee

        if transaction.fee_metric == wallet_pb2.FeeMetric.Value('BYTE'):
            self._fee_metric = "bytes"
        elif transaction.fee_metric == wallet_pb2.FeeMetric.Value('VBYTE'):
            self._fee_metric = "vbytes"
        elif transaction.fee_metric == wallet_pb2.FeeMetric.Value('WEI'):
            self._fee_metric = "wei"
        else:
            raise ValueError("Unknown fee metric")
        
        self._sat_metadata = {}
        self._evm_metadata =  {}
        if network.SUPPORTS_EVM:
            self._evm_metadata['from'] = transaction.ethlike_transaction.txfrom
            self._evm_metadata['to'] = transaction.ethlike_transaction.txto
            self._evm_metadata['amount'] = transaction.ethlike_transaction.amount
            self._evm_metadata['gasUsed'] = transaction.ethlike_transaction.gas
            self._evm_metadata['data'] = transaction.ethlike_transaction.data
        else:
            self._sat_metadata['feeRate'] = transaction.btclike_transaction.fee
            self._sat_metadata['inputs'] = []
            self._sat_metadata['outputs'] = []
            for i in transaction.btclike_transaction.inputs:
                i_ = {}
                i_['txid'] = i.txid
                i_['index'] = i.index
                i_['amount'] = i.amount
                i_['witness'] = []
                for w in i.witness_data:
                    i_['witness'].append(w)
                self._sat_metadata['inputs'].append(i_)
            for o in transaction.btclike_transaction.outputs:
                o_ = {}
                o_['address'] = o.address
                o_['index'] = o.index
                o_['amount'] = o.amount
                o_['spent'] = o.spent
                self._sat_metadata['outputs'].append(o_)
        
    def network(self):
        return self._network

    def txid(self):
        return self._txid
    
    def timestamp(self):
        return self._timestamp
    
    def confirmed(self):
        return self._confirmed

    def height(self):
        return self._height
    
    def total_fee(self, in_standard_units=True):
        if in_standard_units:
            if self._network.SUPPORTS_EVM:
                fee = self._total_fee / 1e18
            else:
                fee = self._total_fee / 1e8
        else:
            fee = self._total_fee
        return (fee, self._fee_metric)
        
    def evm_from(self):
        if not self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        return self._evm_metadata['from']
    
    def evm_to(self):
        if not self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        return self._evm_metadata['to']
    
    def evm_amount(self, in_standard_units=True):
        if not self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        if in_standard_units:
            return self._evm_metadata['amount'] / 1e18
        else:
            return self._evm_metadata['amount']
    
    def evm_gas(self):
        if not self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        return self._evm_metadata['gasUsed'] # always in WEI

    def evm_data(self):
        if not self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        return self._evm_metadata['data']
    
    def sat_feerate(self):
        if self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        return self._sat_metadata['feeRate'] # always in sats per byte or vbyte
    
    def sat_inputs(self, include_witness=False):
        if self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        inputs = []
        for i in self._sat_metadata['inputs']:
            if not include_witness and 'witness' in i.keys():
                del i['witness']
            inputs.append(i)
        return inputs
        
    def sat_outputs(self, only_unspent=False):
        if self._network.SUPPORTS_EVM:
            raise ValueError("Blockchain does not support this property")
        outputs = []
        for o in self._sat_metadata['outputs']:
            if not only_unspent or not o['spent']:
                outputs.append(o)
        return outputs


