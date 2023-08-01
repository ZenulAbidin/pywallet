from ..network import BitcoinSegwitMainNet
from .script import Script

class InvalidTransactionError(Exception):
    pass

def hex_to_int(string):
    return int.from_bytes(bytes.fromhex(string), byteorder="little")


def parse_transaction(raw_transaction_hex, segwit=False):
    transaction = {}
    witness_start = 0
    witness_end = 0
    witness_flag_size = 0

    try:
        # Version
        transaction['version'] = hex_to_int(raw_transaction_hex[0:8])
        index = 8

        # Marker & Flag (for SegWit)
        if segwit:
            marker = raw_transaction_hex[index:index+2]
            index += 2
            flag = raw_transaction_hex[index:index+2]
            index += 2
            witness_flag_size = 2

            if hex_to_int(marker) == 0 and hex_to_int(flag) != 1:
                raise InvalidTransactionError("Marker byte must be 0x00, flag byte immediately after it must be 0x01")

        # Input Count
        input_count, varint_length = parse_varint_hex(raw_transaction_hex[index:])
        transaction['input_count'] = input_count
        index += varint_length * 2

        if input_count == 0:
            raise InvalidTransactionError("Input count must not be zero (is this a segwit transaction?)")

        # Inputs
        transaction['inputs'] = []
        for _ in range(input_count):
            input_data = {}
            # Previous Transaction Hash
            b = bytearray.fromhex(raw_transaction_hex[index:index+64])
            b.reverse()
            input_data['prev_tx_hash'] = b.hex()
            index += 64

            # Previous Transaction Output Index
            input_data['prev_tx_output_index'] = hex_to_int(raw_transaction_hex[index:index+8])
            index += 8

            # Script Length
            script_length, varint_length = parse_varint_hex(raw_transaction_hex[index:])
            index += varint_length * 2

            # Script Signature
            input_data['script_signature'] = raw_transaction_hex[index:index+(script_length*2)]
            index += script_length * 2

            # Sequence
            input_data['sequence'] = raw_transaction_hex[index:index+8]
            index += 8

            transaction['inputs'].append(input_data)

        # Output Count
        output_count, varint_length = parse_varint_hex(raw_transaction_hex[index:])
        transaction['output_count'] = output_count
        index += varint_length * 2

        if output_count == 0:
            raise InvalidTransactionError("Output count must not be zero "
                                          "(If this is a segwit transaction, pass segwit=True)")

        # Outputs
        transaction['outputs'] = []
        for _ in range(output_count):
            output_data = {}
            # Value
            output_data['value'] = hex_to_int(raw_transaction_hex[index:index+16])
            index += 16

            # Script Length
            script_length, varint_length = parse_varint_hex(raw_transaction_hex[index:])
            index += varint_length * 2

            # Script Public Key
            output_data['script_pubkey'] = raw_transaction_hex[index:index+(script_length*2)]

            
            index += script_length * 2

            transaction['outputs'].append(output_data)

        # Witness Data (for SegWit)
        # Ensure that the flag signals that witness data is present.
        if segwit and flag:
            for j in range(input_count):
                witness_start = index
                transaction["inputs"][j]['witness_data'] = []
                witness_count, varint_length = parse_varint_hex(raw_transaction_hex[index:])
                index += varint_length * 2

                for _ in range(witness_count):
                    item_length, varint_length = parse_varint_hex(raw_transaction_hex[index:])
                    index += varint_length * 2
                    item = raw_transaction_hex[index:index+(item_length*2)]
                    index += item_length * 2
                    transaction["inputs"][j]['witness_data'].append(item)

            witness_end = index
        # Lock Time
        transaction['lock_time'] = raw_transaction_hex[index:index+8]

        if index+8 != len(raw_transaction_hex):
            raise InvalidTransactionError("Junk bytes after the transaction "
                            "(If this is a segwit transaction, pass segwit=True)")

        # Don't forget thhe lengths are in hex characters
        witness_size = (witness_end - witness_start) // 2 + witness_flag_size
        
        return transaction, witness_size
    
    except IndexError as e:
        raise InvalidTransactionError("Transaction too short") from e
    except ValueError as e:
        raise InvalidTransactionError("Invalid hexadecimal") from e

def parse_varint_hex(data):
    varint_type = hex_to_int(data[0:2])
    if varint_type < 0xfd:
        return varint_type, 1
    elif varint_type == 0xfd:
        return hex_to_int(data[2:6]), 3
    elif varint_type == 0xfe:
        return hex_to_int(data[2:10]), 5
    elif varint_type == 0xff:
        return hex_to_int(data[2:18]), 9

def transaction_size(raw_transaction_hex, segwit=False):
    _, witness_size = parse_transaction(raw_transaction_hex, segwit)
    if not segwit:
        # Pre-segwit transaction is just the transaction length (in bytes).
        return len(raw_transaction_hex) // 2
    else:
        # Calculate the size in weight units first
        tx_full_size = len(raw_transaction_hex) // 2

        # Weight units are:
        # tx size without witness, times 3,
        # plus the entire transaction size
        weight_units = (tx_full_size - witness_size) * 3 + tx_full_size

        # Convert to vbytes
        return round(weight_units / 4)

def transaction_size_simple(raw_transaction_hex):
    """ Returns the transaction size without throwing exceptions for valid & modern Segwit transactions """
    try:
        return transaction_size(raw_transaction_hex, False)
    except InvalidTransactionError:
        return transaction_size(raw_transaction_hex, True)


def parse_transaction_simple(raw_transaction_hex):
    """ Returns the parsed raw transaction without throwing exceptions for valid & modern Segwit transactions """
    try:
        return parse_transaction(raw_transaction_hex, False)
    except InvalidTransactionError:
        return parse_transaction(raw_transaction_hex, True)

def insert_address_in_outputs(fine_rawtx, network=BitcoinSegwitMainNet):
    for i in range(len(fine_rawtx["outputs"])):
        out = fine_rawtx["outputs"][i]
        script = Script.from_raw(out["script_pubkey"], network=network) # I have no idea what to use the has_segwit flag for.
        fine_rawtx["outputs"][i]["address"] = script.to_p2pkh() or script.to_p2sh() or script.to_p2wpkh() \
                                            or script.to_p2wsh() or script.to_p2tr()
    return fine_rawtx

