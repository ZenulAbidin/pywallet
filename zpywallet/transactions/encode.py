import binascii
import hashlib
import web3
from web3.gas_strategies.time_based import fast_gas_price_strategy
from ..network import BitcoinSegwitMainNet
from ..utils.keys import PrivateKey

from ..utxo import UTXO
from ..destination import Destination

from ..utils.base58 import b58decode_check
from ..utils.bech32 import bech32_decode
from ..utils.keccak import to_checksum_address

# Should really use list[] annotation directly but we still support Python 3.8 which does not have such syntax yet.
from typing import List

SIGHASH_ALL = 1

# def address_is_p2pkh(address, network=BitcoinSegwitMainNet):
#     """Checks whether the address is P2PKH"""
#     if "BASE58" not in network.ADDRESS_MODE:
#         return False
#     try:
#         b = b58decode_check(address)
#         return b[0] == network.PUBKEY_ADDRESS
#     except KeyError:
#         return False
#     except ValueError:
#         return False

# def address_is_p2sh(address, network=BitcoinSegwitMainNet):
#     """Checks whether the address is P2SH"""
#     if "BASE58" not in network.ADDRESS_MODE:
#         return False
#     try:
#         b = b58decode_check(address)
#         return b[0] == network.SCRIPT_ADDRESS
#     except KeyError:
#         return False
#     except ValueError:
#         return False

# def address_is_p2wpkh(address, network=BitcoinSegwitMainNet):
#     """Checks whether the address is P2WPKH"""
#     if "BECH32" not in network.ADDRESS_MODE:
#         return False
#     try:
#         b = bech32_decode(network.BECH32_PREFIX, address)
#         return len(b[1]) == 20
#     except KeyError:
#         return False
#     except ValueError:
#         return False
    
# def address_is_p2wsh(address, network=BitcoinSegwitMainNet):
#     """Checks whether the address is P2WSH"""
#     if "BECH32" not in network.ADDRESS_MODE:
#         return False
#     try:
#         b = bech32_decode(network.BECH32_PREFIX, address)
#         return len(b[1]) == 32
#     except KeyError:
#         return False
#     except ValueError:
#         return False

def script_is_p2pkh(script):
    return len(script) == 25 and script[0:3] == b"\x76\xa9\x14" and script[23:25] == b"\x88\xac"

def script_is_p2sh(script):
    return len(script) == 23 and script[0:2] == b"\xa9\x14" and script[24] == b"\x87"

def script_is_p2wpkh(script):
    return len(script) == 22 and script[0:2] == b"\x00\x14"

def script_is_p2wsh(script):
    return len(script) == 34 and script[0:2] == b"\x00\x20"


def int_to_hex(i, min_bytes=1):
    return i.to_bytes(max(min_bytes, (i.bit_length() + 7) // 8), byteorder="little")

def create_varint(value):
    if value < 0xfd:
        return int_to_hex(value, min_bytes=1)
    elif value <= 0xffff:
        return b'\xfd' + int_to_hex(value, min_bytes=2)
    elif value <= 0xffffffff:
        return b'\xfe' + int_to_hex(value, min_bytes=4)
    else:
        return b'\xff' + int_to_hex(value, min_bytes=8)


def create_signatures_legacy(bytes_1, bytes_2_inputs, bytes_3, bytes_4, network):
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
        address = b2[6]
        partial_transaction = bytes_1
        for i in range(0, len(bytes_2_inputs)):
            partial_transaction += bytes_2_inputs[i][0]
            if i == b2i:
                partial_transaction += create_varint(len(script_pubkey)) + script_pubkey
            else:
                partial_transaction += bytes_2_inputs[i][1] # The empty scriptsig
            partial_transaction += bytes_2_inputs[i][2]
        partial_transaction += bytes_3
        partial_transaction += bytes_4
        # And last, the input's sighash must be placed AT THE END of the temporary transaction
        partial_transaction += int_to_hex(sighash, 4)
        hashed_preimage = hashlib.sha256(partial_transaction).digest()

        # Sign it
        p = PrivateKey.from_wif(private_key, network=network)
        pubkey = p.public_key.to_bytes()
        if p.public_key.base58_address(compressed=False) == address:
            pubkey = p.public_key.to_bytes(False)
        der = p.der_sign(hashed_preimage) + bytes([sighash])
        # I would like to mention that this only works if the data being pushed is less than 76 bytes.
        # Otherwise we need to use OP_PUSHDATA<1/2/4>
        script = int_to_hex(len(der)) + der + int_to_hex(len(pubkey)) + pubkey
        signatures.append(create_varint(len(script)) + script)

    # Now that we have all the signatures, we can assemble the signed transaction
    signed_transaction = bytes_1
    for i in range(0, len(bytes_2_inputs)):
        signed_transaction += bytes_2_inputs[i][0]
        signed_transaction += signatures[i]
        signed_transaction += bytes_2_inputs[i][2]
    signed_transaction += bytes_3
    signed_transaction += bytes_4

    return signed_transaction.hex()
    


def create_signatures_segwit(bytes_1, bytes_2_inputs, bytes_3, bytes_4, network):
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
        address = b2[6]
        segwit_payload = hashlib.sha256(b2[7]).digest()

        # Sign it
        p = PrivateKey.from_wif(private_key, network=network)
        pubkey = p.public_key.to_bytes()
        if script_is_p2pkh(script_pubkey):
            if p.public_key.base58_address(compressed=False) == address:
                pubkey = p.public_key.to_bytes(False)
            # Legacy inputs are signed the old way
            der = p.der_sign(hashlib.sha256(segwit_payload).digest()) + bytes([sighash])
            script = int_to_hex(len(der)) + der + int_to_hex(len(pubkey)) + pubkey
            signatures.append(create_varint(len(script)) + script)
            witness_stack.append([])
        elif script_is_p2wpkh(script_pubkey):
            # Place data on the witness stack
            der = p.der_sign(segwit_payload) + bytes([sighash])
            witness_stack.append([der, pubkey])
            signatures.append(b"\x00")
        else:
            raise ValueError("Unsupported script type")
    
    # Now that we have all the signatures, we can assemble the signed transaction
    signed_transaction = bytes_1
    for i in range(0, len(bytes_2_inputs)):
        signed_transaction += bytes_2_inputs[i][0]
        signed_transaction += signatures[i]
        signed_transaction += bytes_2_inputs[i][2]
    signed_transaction += bytes_3

    # Assemble the witness stack, one per input, segwit inputs only
    for w in witness_stack:
        signed_transaction += create_varint(len(w))
        witness_bytes = b""
        for w_elem in w:
            witness_bytes += create_varint(len(w_elem)) + w_elem
        signed_transaction += witness_bytes

    signed_transaction += bytes_4

    return signed_transaction.hex()
    

def create_transaction(inputs: List[UTXO], outputs: List[Destination], rbf=True, network=BitcoinSegwitMainNet, full_nodes=[], **kwargs):
    """
    Creates a signed transaction, given a network an array of UTXOs, and an array of address/amount
    destination tuples.
    Never call this function directly, it does not automatically calculate change or fees. Instead, use Wallet.create_transaction().
    """
    
    # First, construct the raw transacation
    if network.SUPPORTS_EVM:
        try:
            return create_web3_transaction(inputs[0].address(), outputs[0].address(), outputs[0].amount(in_standard_units=False),
                                           inputs[0]._private_key(), full_nodes, kwargs.get('gas'), network.CHAIN_ID)
        finally:
            del(inputs)
    else:
        all_legacy = True
        for i in inputs:
            try:
                b58decode_check(i.address())
            except ValueError:
                all_legacy = False
                if not network.SUPPORTS_SEGWIT:
                    raise ValueError("You must use a segwit network to use bech32 inputs")
                break
        tx_bytes_1 = tx_bytes_2 = tx_bytes_3 = tx_bytes_4 = b""
        tx_bytes_1 += int_to_hex(1, 4) # Version 1 transaction
        if network.SUPPORTS_SEGWIT and not all_legacy:
            tx_bytes_1 += b"\x00\x01" # Signal segwit support
        
        # We process the outputs before the inputs so that we can use it for segwit transactions.
        tx_bytes_3 += create_varint(len(outputs))
        tx_bytes_3a = b''
        for o in outputs:
            tx_bytes_3b = b''
            tx_bytes_3b += int_to_hex(o.amount(in_standard_units=False), 8)
            #if network.SUPPORTS_SEGWIT and o.script_pubkey()[0] == 0:
            #    script =  b"\x76\xa9" + o.script_pubkey()[1:] + b"\x88\xac"
            #    tx_bytes_3b += create_varint(len(script)) + script
            #else:
            script = o.script_pubkey()
            tx_bytes_3b += create_varint(len(script))
            tx_bytes_3b += script            
            tx_bytes_3a += tx_bytes_3b
        tx_bytes_3 += tx_bytes_3a

        # Inputs
        tx_bytes_1 += create_varint(len(inputs))
        tx_bytes_2_inputs = []
        for i in inputs:
            input_bytes_1 = input_bytes_2 = input_bytes_3 = input_bytes_4 = b""
            input_bytes_1 += binascii.unhexlify(i.txid().encode())[::-1]
            input_bytes_1 += int_to_hex(i.index(), 4)

            # The transacion cannot be signed until it is fully constructed.
            # To avoid a chicken-and-egg, we set the signature scripts to empty.
            # This is the prescribed behavior by the bitcoin protocol.
            # EDIT I heard it's just the scriptpubkey
            input_bytes_2 = b"\x00" #create_varint(len(i._script_pubkey())) + i._script_pubkey()

            input_bytes_3 = int_to_hex(0xfffffffd if rbf else 0xffffffff, 4) # disables timelocks, see https://bitcointalk.org/index.php?topic=5479540.msg63401889#msg63401889

            segwit_payload = b""
            # It is easier to prepare the Segwit signing data here.
            if network.SUPPORTS_SEGWIT and not all_legacy:
                # nVersion of the transaction (4-byte little endian)
                segwit_payload = int_to_hex(1, 4)
                
                # hashPrevouts (32-byte hash)
                hashPrevouts = b""
                for j in inputs:
                    hashPrevouts += binascii.unhexlify(j.txid().encode())[::-1] + int_to_hex(j.index(), 4)
                segwit_payload += hashlib.sha256(hashlib.sha256(hashPrevouts).digest()).digest()

                # hashSequence (32-byte hash)
                hashSequence = b""
                for j in inputs:
                    hashSequence += input_bytes_3 # The timelock is the same for all inputs.
                segwit_payload += hashlib.sha256(hashlib.sha256(hashSequence).digest()).digest()

                # outpoint (32-byte hash + 4-byte little endian)
                segwit_payload += binascii.unhexlify(i.txid().encode())[::-1] + int_to_hex(i.index(), 4)

                # scriptCode of the input (serialized as scripts inside CTxOuts)
                # note: for p2wpkh this is actually the P2PKH script!!!
                script =  b"\x76\xa9" + i._script_pubkey()[1:] + b"\x88\xac"
                segwit_payload += create_varint(len(script)) + script
                #segwit_payload += create_varint(len(i._script_pubkey())) + i._script_pubkey()

                # value of the output spent by this input (8-byte little endian)
                segwit_payload += int_to_hex(i.amount(in_standard_units=False), 8)

                # nSequence of the input (4-byte little endian)
                segwit_payload += input_bytes_3

                # hashOutputs (32-byte hash)
                segwit_payload += hashlib.sha256(hashlib.sha256(tx_bytes_3a).digest()).digest()

                # nLocktime of the transaction (4-byte little endian)
                segwit_payload += int_to_hex(0, 4)

                # sighash type of the signature (4-byte little endian)
                segwit_payload += int_to_hex(SIGHASH_ALL, 4)


            # If this is a segwit transaction these will need to go into witness data eventually.
            tx_bytes_2_inputs.append([input_bytes_1, input_bytes_2, input_bytes_3, i._script_pubkey(), i._private_key(), SIGHASH_ALL, i.address(), segwit_payload])
        
        # tx_bytes_3 should also contain the witness data

        tx_bytes_4 += int_to_hex(0, 4) # Disable locktime (redundant)

        del(inputs)
        if network.SUPPORTS_SEGWIT and not all_legacy:
            return create_signatures_segwit(tx_bytes_1, tx_bytes_2_inputs, tx_bytes_3, tx_bytes_4, network)
        else:
            return create_signatures_legacy(tx_bytes_1, tx_bytes_2_inputs, tx_bytes_3, tx_bytes_4, network)


def create_web3_transaction(a_from, a_to, amount, private_key, fullnodes, gas, chainId):
    sender_address = a_from
    receiver_address = a_to
    # All amounts are in WEI not Ether

    # Check the nonce for the sender address
    for node in fullnodes:
        try:
            w3 = web3.Web3(web3.HTTPProvider(node['url']))
            # This makes it fetch max<priority>feepergas info faster
            w3.eth.set_gas_price_strategy(fast_gas_price_strategy)
            w3.middleware_onion.add(web3.middleware.time_based_cache_middleware)
            w3.middleware_onion.add(web3.middleware.latest_block_based_cache_middleware)
            w3.middleware_onion.add(web3.middleware.simple_cache_middleware)

            nonce = w3.eth.getTransactionCount(to_checksum_address(sender_address))

            # Build the transaction dictionary
            transaction = {
                'nonce': nonce,
                'to': to_checksum_address(receiver_address),
                'value': w3.toWei(amount, 'ether'),  # Sending 1 ether, adjust as needed
                #'gas': gas,#21000,  # Gas limit
                # Since the London hard work (EIP-1559), nobody uses gasPrice anymore. They use max<Priority>FeePerGas
                # Which is automatically specified (somehow) in Web3.
                #'gasPrice': w3.toWei(gasPrice, 'gwei'),  # Gas price in Gwei, adjust as needed
                'chainId': chainId,  # 1 for Mainnet, change to 3 for Ropsten, 4 for Rinkeby, etc.
            }

            # OK now calculate the gas
            if not gas:
                gas = w3.eth.estimate_gas(transaction)
            transaction['gas'] = gas

            # Sign the transaction
            return w3.eth.account.signTransaction(transaction, binascii.unhexlify(private_key[2:].encode()))
        except Exception:
            pass
    raise RuntimeError("Cannot sign web3 transaction (try specifying different nodes)")
