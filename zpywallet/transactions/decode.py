class InvalidTransactionError(Exception):
    pass

def parse_transaction(raw_transaction_hex, segwit=False):
    transaction = {}
    witness_start = 0
    witness_end = 0
    witness_flag_size = 0

    try:
        # Version
        transaction['version'] = int(raw_transaction_hex[0:8], 16)
        index = 8

        # Marker & Flag (for SegWit)
        if segwit:
            flag = raw_transaction_hex[index:index+4]
            index += 4
            witness_flag_size = 2

            if int(flag, 16) != 1:
                raise InvalidTransactionError("Marker byte must be 0x00, flag byte immediately after it must be 0x01")

        # Input Count
        input_count, varint_length = parse_varint(raw_transaction_hex[index:])
        transaction['input_count'] = input_count
        index += varint_length

        if input_count == 0:
            raise InvalidTransactionError("Input count must not be zero (is this a segwit transaction?)")

        # Inputs
        transaction['inputs'] = []
        for _ in range(input_count):
            input_data = {}
            # Previous Transaction Hash
            input_data['prev_tx_hash'] = raw_transaction_hex[index:index+64]
            index += 64

            # Previous Transaction Output Index
            input_data['prev_tx_output_index'] = int(raw_transaction_hex[index:index+8], 16)
            index += 8

            # Script Length
            script_length, varint_length = parse_varint(raw_transaction_hex[index:])
            index += varint_length

            # Script Signature
            input_data['script_signature'] = raw_transaction_hex[index:index+(script_length*2)]
            index += script_length * 2

            # Sequence
            input_data['sequence'] = raw_transaction_hex[index:index+8]
            index += 8

            transaction['inputs'].append(input_data)

        # Output Count
        output_count, varint_length = parse_varint(raw_transaction_hex[index:])
        transaction['output_count'] = output_count
        index += varint_length

        if output_count == 0:
            raise InvalidTransactionError("Output count must not be zero")

        # Outputs
        transaction['outputs'] = []
        for _ in range(output_count):
            output_data = {}
            # Value
            output_data['value'] = int(raw_transaction_hex[index:index+16], 16)
            index += 16

            # Script Length
            script_length, varint_length = parse_varint(raw_transaction_hex[index:])
            index += varint_length

            # Script Public Key
            output_data['script_pubkey'] = raw_transaction_hex[index:index+(script_length*2)]
            index += script_length * 2

            transaction['outputs'].append(output_data)

        # Witness Data (for SegWit)
        # Ensure that the flag signals that witness data is present.
        if segwit and flag:
            witness_start = index
            transaction['witness_data'] = []
            witness_count, varint_length = parse_varint(raw_transaction_hex[index:])
            index += varint_length

            if witness_count == 0:
                raise InvalidTransactionError("Witness count must not be zero")

            for _ in range(witness_count):
                item_length, varint_length = parse_varint(raw_transaction_hex[index:])
                index += varint_length
                item = raw_transaction_hex[index:index+(item_length*2)]
                index += item_length * 2
                transaction['witness_data'].append(item)

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

def parse_varint(data):
    varint_type = int(data[0:2], 16)
    if varint_type < 0xfd:
        return varint_type, 1
    elif varint_type == 0xfd:
        return int(data[2:6], 16), 3
    elif varint_type == 0xfe:
        return int(data[2:10], 16), 5
    elif varint_type == 0xff:
        return int(data[2:18], 16), 9

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
