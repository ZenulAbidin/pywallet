import hashlib
import web3
from ..network import BitcoinSegwitMainNet
from ..utils.keys import PrivateKey


from ..utils.base58 import b58decode_check
from ..utils.bech32 import bech32_decode

def address_is_p2pkh(address, network=BitcoinSegwitMainNet):
    """Checks whether the address is P2PKH"""
    if "BASE58" not in network.ADDRESS_MODE:
        return False
    try:
        b = b58decode_check(address)
        return b[0] == network.PUBKEY_ADDRESS
    except KeyError:
        return False
    except ValueError:
        return False

def address_is_p2sh(address, network=BitcoinSegwitMainNet):
    """Checks whether the address is P2SH"""
    if "BASE58" not in network.ADDRESS_MODE:
        return False
    try:
        b = b58decode_check(address)
        return b[0] == network.SCRIPT_ADDRESS
    except KeyError:
        return False
    except ValueError:
        return False

def address_is_p2wpkh(address, network=BitcoinSegwitMainNet):
    """Checks whether the address is P2WPKH"""
    if "BECH32" not in network.ADDRESS_MODE:
        return False
    try:
        b = bech32_decode(network.BECH32_PREFIX, address)
        return len(b[1]) == 20
    except KeyError:
        return False
    except ValueError:
        return False
    
def address_is_p2wsh(address, network=BitcoinSegwitMainNet):
    """Checks whether the address is P2WSH"""
    if "BECH32" not in network.ADDRESS_MODE:
        return False
    try:
        b = bech32_decode(network.BECH32_PREFIX, address)
        return len(b[1]) == 32
    except KeyError:
        return False
    except ValueError:
        return False

def script_is_p2pkh(script):
    return len(script) == 25 and script[0:3] == b"\x76\xa9\x14" and script[23:25] == b"\x88\xac"

def script_is_p2sh(script):
    return len(script) == 23 and script[0:2] == b"\xa9\x14" and script[24] == b"\x87"

def script_is_p2wpkh(script):
    return len(script) == 22 and script[0:2] == b"\x00\x14"

def script_is_p2wsh(script):
    return len(script) == 34 and script[0:2] == b"\x00\x20"


def int_to_hex(i, min_bytes):
    return i.to_bytes(max(min_bytes, (i.bit_length() + 7) // 8), byteorder="little").hex().encode()

def create_varint(value):
    if value < 0xfd:
        return int_to_hex(value, min_bytes=1)
    elif value <= 0xffff:
        return b'\xfd' + int_to_hex(value, min_bytes=2)
    elif value <= 0xffffffff:
        return b'\xfe' + int_to_hex(value, min_bytes=4)
    else:
        return b'\xff' + int_to_hex(value, min_bytes=8)

class TransactionInput:
    def __init__(self, txid, index, script_pubkey, value, private_key, sighash, address=None):
        self.txid = txid
        self.index = index
        self.script_pubkey = script_pubkey
        self.value = value # Not used in legacy transactions
        # This only works with simple scripts (i.e. not Multisig, or Taproot)
        # and it does not check whether the private key is correct for the input pubkey.
        self.private_key = private_key
        self.sighash = sighash
        self.address = address

class  TransactionOutput:
    def __init__(self, address, value):
        """The address prefix determines the kind of script created (P2PKH or P2WPKH)"""
        self.address = address
        self.value = value

def create_signatures_legacy(bytes_1, bytes_2_inputs, bytes_3, bytes_4):
    """
    Signs the inputs of a legacy transaction. The parts are contained in bytes 1, 2, 3, 4.
    Bytes 2 contains the inputs broken up so that the signature is isolated. It also has
    the script pubkey, the private key, and sighash.
    Note that Segwit transactions use a different signing format (see BIP 143).
    """
    signatures = []
    # Note that only ONE INPUT IS FILLED AT A TIME DURING SIGNING
    for b2i in range(0, len(bytes_2_inputs)):
        b2 = bytes_2_inputs[b2i]
        script_pubkey = b2[3]
        private_key = b2[4]
        sighash = b2[5]
        partial_transaction = bytes_1
        for i in range(0, len(bytes_2_inputs)):
            partial_transaction += bytes_2_inputs[i][0]
            if i == b2i:
                partial_transaction += script_pubkey
            else:
                partial_transaction += bytes_2_inputs[i][1] # The empty scriptsig
            partial_transaction += bytes_2_inputs[i][2]
        partial_transaction += bytes_3
        partial_transaction += bytes_4
        # And last, the input's sighash must be placed AT THE END of the temporary transaction
        partial_transaction += int_to_hex(sighash, 4)

        # Sign it
        p = PrivateKey.from_wif(private_key)
        der = p.der_sign(partial_transaction) + sighash
        script = int_to_hex(len(der)) + der + int_to_hex(len(script_pubkey)) + script_pubkey
        signatures.append(int_to_hex(script) + script)

    # Now that we have all the signatures, we can assemble the signed transaction
    signed_transaction = bytes_1
    for i in range(0, len(bytes_2_inputs)):
        signed_transaction += bytes_2_inputs[i][0]
        signed_transaction += signatures[i]
        signed_transaction += bytes_2_inputs[i][2]
    signed_transaction += bytes_3
    signed_transaction += bytes_4

    return signed_transaction
    


def create_signatures_segwit(bytes_1, bytes_2_inputs, bytes_3, bytes_4):
    """
    Signs the inputs of a segwit transaction. The parts are contained in bytes 1, 2, 3, 4.
    Bytes 2 contains the inputs broken up so that the signature is isolated. It also has
    the script pubkey, the private key, and sighash.
    """
    # The partial transaction to sign is a double SHA256 of the serialization of:
    # 1.  nVersion of the transaction (4-byte little endian)
    # 2.  hashPrevouts (32-byte hash)
    # 3.  hashSequence (32-byte hash)
    # 4.  outpoint (32-byte hash + 4-byte little endian) 
    # 5.  scriptCode of the input (serialized as scripts inside CTxOuts)
    # 6.  value of the output spent by this input (8-byte little endian)
    # 7.  nSequence of the input (4-byte little endian)
    # 8.  hashOutputs (32-byte hash)
    # 9.  nLocktime of the transaction (4-byte little endian)
    # 10. sighash type of the signature (4-byte little endian)
    
    signatures = []
    witness_stack = []
    # Note that only ONE INPUT IS FILLED AT A TIME DURING SIGNING
    for b2i in range(0, len(bytes_2_inputs)):
        b2 = bytes_2_inputs[b2i]
        script_pubkey = b2[3]
        private_key = b2[4]
        sighash = b2[5]
        segwit_payload = hashlib.sha256(hashlib.sha256(b2[7]).digest()).digest()

        # Sign it
        p = PrivateKey.from_wif(private_key)
        if script_is_p2pkh(script_pubkey) or script_is_p2sh(script_pubkey):
            # Legacy inputs are signed the old way
            der = p.der_sign(segwit_payload) + sighash
            script = int_to_hex(len(der)) + der + int_to_hex(len(script_pubkey)) + script_pubkey
            signatures.append(int_to_hex(script) + script)
            witness_stack.append([])
        elif script_is_p2wpkh(script_pubkey) or script_is_p2wsh(script_pubkey):
            # Place data on the witness stack
            der = p.der_sign(segwit_payload)
            witness_stack.append([der, script_pubkey])
            signatures.append(b"\x00")
        else:
            raise ValueError("Unknown script type")
    
    # Now that we have all the signatures, we can assemble the signed transaction
    signed_transaction = bytes_1
    for i in range(0, len(bytes_2_inputs)):
        signed_transaction += bytes_2_inputs[i][0]
        signed_transaction += signatures[i]
        signed_transaction += bytes_2_inputs[i][2]
    signed_transaction += bytes_3

    # Assemble the witness stack, one per input
    # Note that for legacy inputs, their witness stack is just b'0x00'
    for w in witness_stack:
        signed_transaction += int_to_hex(len(w))
        witness_bytes = b""
        for w_elem in w:
            witness_bytes += int_to_hex(len(w_elem)) + w_elem
        signed_transaction += int_to_hex(len(witness_bytes)) + witness_bytes

    signed_transaction += bytes_4

    return signed_transaction
    

def create_transaction(inputs: list, outputs: list, rbf=True, network=BitcoinSegwitMainNet, rpc_params={}):
    """
    Creates a signed transaction, given a network an array of UTXOs, and an array of address/amount
    destination tuples.
    """

    # First, construct the raw transacation
    if network.SUPPORTS_EVM:
        return create_web3_transaction(inputs[0].address, outputs[0].address, outputs[0].amount, inputs[0].private_key, network, rpc_params)
    else:
        tx_bytes_1 = tx_bytes_2 = tx_bytes_3 = b""
        tx_bytes_1 += int_to_hex(1, 4) # Version 1 transaction
        if network.SUPPORTS_SEGWIT:
            tx_bytes_1 += b"\x00\x01" # Signal segwit support
        
        # We process the outputs before the inputs so that we can use it for segwit transactions.
        tx_bytes_3 += create_varint(len(outputs))
        for o in outputs:
            tx_bytes_3 += int_to_hex(o.amount, 8)
            
            # Now we must identify what the address type is
            if address_is_p2pkh(o.address, network):
                address_hash = b58decode_check(o.address)[1:] # Remove the version byte
                script = b"\x76\xa9\x14" + address_hash + b"\x88\xac"
                tx_bytes_3 += int_to_hex(len(script))
                tx_bytes_3 += script
            elif address_is_p2sh(o.address, network):
                address_hash = b58decode_check(o.address)[1:] # Remove the version byte
                script = b"\xa9\x14" + address_hash + b"\x87"
                tx_bytes_3 += int_to_hex(len(script))
                tx_bytes_3 += script
            elif address_is_p2wpkh(o.address, network):
                address_hash = bech32_decode(network.BECH32_PREFIX, o.address)
                script = b"\x00\x14" + address_hash
                tx_bytes_3 += int_to_hex(len(script))
                tx_bytes_3 += script
            elif address_is_p2wsh(o.address, network):
                address_hash = bech32_decode(network.BECH32_PREFIX, o.address)
                script = b"\x00\x20" + address_hash
                tx_bytes_3 += int_to_hex(len(script))
                tx_bytes_3 += script
            else:
                raise ValueError("Unknown address type")
            

        # Inputs
        tx_bytes_1 += create_varint(len(inputs))
        tx_bytes_2_inputs = []
        for i in inputs:
            input_bytes_1 = input_bytes_2 = input_bytes_3 = input_bytes_4 = b""
            input_bytes_1 += i.txid
            input_bytes_1 += int_to_hex(i.index)

            # The transacion cannot be signed until it is fully constructed.
            # To avoid a chicken-and-egg, we set the signature scripts to empty.
            # This is the prescribed behavior by the bitcoin protocol.
            input_bytes_2 = b"\x00"

            input_bytes_3 = int_to_hex(0x80000000 if rbf else 0xffffffff, 4) # disables timelock timelocks, see https://bitcointalk.org/index.php?topic=5479540.msg63401889#msg63401889

            segwit_payload = b""
            # It is easier to prepare the Segwit signing data here.
            if network.SUPPORTS_SEGWIT:
                # nVersion of the transaction (4-byte little endian)
                segwit_payload = int_to_hex(1, 4)
                
                # hashPrevouts (32-byte hash)
                hashPrevouts = b""
                for j in inputs:
                    hashPrevouts += j.txid + int_to_hex(j.index)
                segwit_payload += hashlib.sha256(hashlib.sha256(hashPrevouts).digest()).digest()

                # hashSequence (32-byte hash)
                hashSequence = b""
                for j in inputs:
                    hashSequence += input_bytes_3 # The timelock is the same for all inputs.
                segwit_payload += hashlib.sha256(hashSequence).digest()

                # outpoint (32-byte hash + 4-byte little endian)
                segwit_payload += i.txid + int_to_hex(i.index)

                # scriptCode of the input (serialized as scripts inside CTxOuts)
                segwit_payload += i.script_pubkey

                # value of the output spent by this input (8-byte little endian)
                segwit_payload += int_to_hex(o.amount, 8)

                # nSequence of the input (4-byte little endian)
                segwit_payload += input_bytes_3

                # hashOutputs (32-byte hash)
                segwit_payload += tx_bytes_3

                # nLocktime of the transaction (4-byte little endian)
                segwit_payload += int_to_hex(0, 4)

                # sighash type of the signature (4-byte little endian)
                segwit_payload += int_to_hex(i.sighash, 4)


            # If this is a segwit transaction these will need to go into witness data eventually.
            tx_bytes_2_inputs.append([input_bytes_1, input_bytes_2, input_bytes_3, i.script_pubkey, i.private_key, i.sighash, segwit_payload])
        
        # tx_bytes_3 should also contain the witness data

        tx_bytes_4 += int_to_hex(0, 4) # Disable locktime (redundant)

        if network.SUPPORTS_SEGWIT:
            return create_signatures_segwit(tx_bytes_1, tx_bytes_2_inputs, tx_bytes_3, tx_bytes_4)
        else:
            return create_signatures_legacy(tx_bytes_1, tx_bytes_2_inputs, tx_bytes_3, tx_bytes_4)


def create_web3_transaction(a_from, a_to, amount, network, private_key, rpc_params):    
    sender_address = a_from
    receiver_address = a_to
    # All amounts are in WEI not Ether

    # Check the nonce for the sender address
    nonce = web3.eth.getTransactionCount(sender_address)

    # Build the transaction dictionary
    transaction = {
        'nonce': nonce,
        'to': receiver_address,
        'value': web3.toWei(amount, 'ether'),  # Sending 1 ether, adjust as needed
        'gas': rpc_params['gas'],#21000,  # Gas limit
        'gasPrice': web3.toWei(rpc_params['gasPrice'], 'gwei'),  # Gas price in Gwei, adjust as needed
        'chainId': 1,  # Mainnet, change to 3 for Ropsten, 4 for Rinkeby, etc.
    }

    # Sign the transaction
    return web3.eth.account.signTransaction(transaction, private_key)
