import subprocess
import json

from ...errors import NetworkException
from ...transactions.decode import transaction_size_simple

class ElectrumAddress:
    """
    A class representing a Bitcoin address.

    This class allows you to retrieve the balance and transaction history of a Bitcoin address using the Electrum local binary.

    Note: This class is only suitable for querying a locally-running Electrum daemon. If you want to query electrum over the
    network, see electrum_network instead.

    Args:
        address (str): The Bitcoin address.

    Attributes:
        address (str): The Bitcoin address.
        server_ip (str): The IP address of the Electrum server.
        server_port (int): The port number of the Electrum server.

    Methods:
        get_balance(): Retrieves the balance of the Bitcoin address.
        get_block_height(): Returns the current block height.
        get_utxos(): Retrieves the unspent transaction outputs (UTXOs) of the Bitcoin address.
        get_transaction_history(): Retrieves the transaction history of the Bitcoin address.

    Raises:
        Exception: If the command execution fails or the address balance/transaction history cannot be retrieved.
    """
    
    def _clean_tx(self, element, raw_transaction_hex):
        if element['height'] == -1:
            raise ValueError("We don't process RBF-overridden transactions")
        new_element = {}
        new_element['txid'] = element['txid']
        new_element['height'] = element['height']
        new_element['timestamp'] = None

        new_element['inputs'] = []
        new_element['outputs'] = []
        for vin in element['inputs']:
            txinput = {}
            txinput['txid'] = vin['prevout_hash']
            txinput['index'] = vin['prevout_n']

            # Get the previous transaction to as value is not directly accessible
            rawtx = self._run_electrum_command('gettransaction', txinput['txid'])
            fine_rawtx = self._run_electrum_command('deserialize', rawtx)
            
            txinput['amount'] = fine_rawtx["outputs"][txinput['index']]["value"] / 1e8
            new_element['inputs'].append(txinput)

        i = 0
        for vout in element['outputs']:
            txoutput = {}
            txoutput['amount'] = vout['value'] / 1e8
            txoutput['index'] = i
            i += 1
            txoutput['address'] = vout['address']
            txoutput['spent'] = vout['spent']
            new_element['outputs'].append(txoutput)

        total_inputs = sum([a['amount'] for a in new_element['inputs']])
        total_outputs = sum([a['amount'] for a in new_element['outputs']])
        new_element['total_fee'] = total_inputs - total_outputs

        # We must calculate the transaction size ourselves. Electrum doesn't provide tx size or fee info.
        size_element = transaction_size_simple(raw_transaction_hex)
        new_element['fee'] = new_element['total_fee'] / size_element
        new_element['fee_unit'] = 'vbyte'

        return new_element


    def __init__(self, address):
        """
        Initializes an instance of the ElectrumAddress class.

        Args:
            address (str): The Bitcoin address.
        """
        self.address = address
        self.transactions = [*self._get_transaction_history()]
        self.height = self.get_block_height()

    def _run_electrum_command(self, command, *args):
        """
        Runs the provided Electrum command using the local binary.

        Args:
            command (str): The Electrum command to execute.

        Returns:
            dict: The parsed JSON response.

        Raises:
            Exception: If the command execution fails or the JSON response cannot be parsed.
        """
        try:
            process = subprocess.Popen(
                ['electrum', command, *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            output, error = process.communicate()
            if error:
                raise NetworkException(f"Command execution failed: {error}")
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return output
        except Exception as e:
            raise NetworkException(f"Command execution failed: {e}") from e
        
    def get_block_height(self):
        """Returns the current block height."""
        response = self._run_electrum_command('getinfo')
        self.block_height = response.get('blockchain_height')
        return self.block_height

    def get_balance(self):
        """
        Retrieves the balance of the Bitcoin address.

        Returns:
            tuple: A tuple containing the total balance and confirmed balance of the Bitcoin address in BTC.

        Raises:
            Exception: If the command execution fails or the address balance cannot be retrieved.
        """
        try:
            response = self._run_electrum_command('getaddressbalance')
            total_balance = response.get('confirmed') + response.get('unconfirmed')
            confirmed_balance = response.get('confirmed')
            return total_balance, confirmed_balance
        except Exception as e:
            raise NetworkException(f"Failed to retrieve address balance: {e}") from e
        
    def get_utxos(self):
        """
        Retrieves the unspent transaction outputs (UTXOs) of the Bitcoin address.

        Returns:
            list: A list of dictionaries representing the UTXOs.

        Raises:
            Exception: If the connection to the Electrum server fails or the UTXOs cannot be retrieved.
        """
        utxos = []
        block_height = self.get_block_height()
        for tx in self._run_electrum_command("getaddressunspent"):
            for output in tx["outputs"]:
                if output['spent']:
                    continue
                if output["address"] == self.address:
                    utxo = {
                        "address": self.address,
                        "txid": tx["tx_hash"],
                        "index": output["tx_pos"],
                        "amount": output["value"] / 1e8,
                        "height": block_height
                    }
                    utxos.append(utxo)
        return utxos

    def get_transaction_history(self):
        """
        Retrieves the transaction history of the Bitcoin address.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the command execution fails or the transaction history cannot be retrieved.
        """
        if len(self.transactions) == 0:
            self.transactions = [*self.get_transaction_history()]
        else:
            # First element is the most recent transactions
            txhash = self.transactions[0]["txid"]
            txs = [*self._get_transaction_history(txhash)]
            txs.extend(self.transactions)
            self.transactions = txs
            del txs

    def _get_transaction_history(self, txhash=None):
        """
        Retrieves the transaction history of the Bitcoin address using the 'listtransactions' command.

        Returns:
            list: A list of dictionaries representing the transaction history.

        Raises:
            Exception: If the command execution fails or the transaction history cannot be retrieved.
        """
        try:
            response = self._run_electrum_command('getaddresshistory')
            for tx_height in response:
                height = max(tx_height["height"], 0)
                if height != 0 and height <= self.block_height:
                    continue
                tx = tx["transaction"]
                if txhash and tx == txhash:
                    return
                rawtx = self._run_electrum_command('gettransaction', tx)
                fine_rawtx = self._run_electrum_command('deserialize', rawtx)
                fine_rawtx["txid"] = tx
                fine_rawtx["height"] = height
                try:
                    yield self._clean_tx(fine_rawtx, rawtx)
                except ValueError:
                    pass


        except Exception as e:
            raise NetworkException(f"Failed to retrieve transaction history: {e}") from e

