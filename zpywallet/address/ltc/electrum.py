import electrum_ltc
from ...errors import NetworkException

class ElectrumLitecoinClient:
    def __init__(self, server='electrumx.server.com', port=50001, protocol='ssl'):
        self.server = server
        self.port = port
        self.protocol = protocol
        self.connection = electrum_ltc.Electrum(self.server, self.port, self.protocol)
    
    def connect(self):
        self.connection.open()
    
    def disconnect(self):
        self.connection.close()
    
    def get_balance(self, address):
        result = self.connection.blockchain_address_listunspent(address)
        utxos = []
        confirmed_balance = 0
        unconfirmed_balance = 0
        for utxo in result:
            utxos.append({
                'tx_hash': utxo['tx_hash'],
                'tx_pos': utxo['tx_pos'],
                'value': utxo['value'],
                'height': utxo['height'],
            })
            if utxo['height'] > 0:
                confirmed_balance += utxo['value']
            else:
                unconfirmed_balance += utxo['value']
        return utxos, confirmed_balance, unconfirmed_balance
    
    def get_transaction_history(self, address):
        result = self.connection.blockchain_address_get_history(address)
        return result
