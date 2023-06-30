# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    CONFIG - Configuration settings
#    © 2022 - 2023 May - 1200 Web Development <http://1200wd.com/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

_opcodes = [
    ("OP_0", 0), ("OP_PUSHDATA1", 76), "OP_PUSHDATA2", "OP_PUSHDATA4", "OP_1NEGATE", "OP_RESERVED", "OP_1",
    "OP_2", "OP_3", "OP_4", "OP_5", "OP_6", "OP_7", "OP_8", "OP_9", "OP_10", "OP_11", "OP_12", "OP_13", "OP_14",
    "OP_15", "OP_16", "OP_NOP", "OP_VER", "OP_IF", "OP_NOTIF", "OP_VERIF", "OP_VERNOTIF", "OP_ELSE", "OP_ENDIF",
    "OP_VERIFY", "OP_RETURN", "OP_TOALTSTACK", "OP_FROMALTSTACK", "OP_2DROP", "OP_2DUP", "OP_3DUP", "OP_2OVER",
    "OP_2ROT", "OP_2SWAP", "OP_IFDUP", "OP_DEPTH", "OP_DROP", "OP_DUP", "OP_NIP", "OP_OVER", "OP_PICK", "OP_ROLL",
    "OP_ROT", "OP_SWAP", "OP_TUCK", "OP_CAT", "OP_SUBSTR", "OP_LEFT", "OP_RIGHT", "OP_SIZE", "OP_INVERT", "OP_AND",
    "OP_OR", "OP_XOR", "OP_EQUAL", "OP_EQUALVERIFY", "OP_RESERVED1", "OP_RESERVED2", "OP_1ADD", "OP_1SUB", "OP_2MUL",
    "OP_2DIV", "OP_NEGATE", "OP_ABS", "OP_NOT", "OP_0NOTEQUAL", "OP_ADD", "OP_SUB", "OP_MUL", "OP_DIV", "OP_MOD",
    "OP_LSHIFT", "OP_RSHIFT", "OP_BOOLAND", "OP_BOOLOR", "OP_NUMEQUAL", "OP_NUMEQUALVERIFY", "OP_NUMNOTEQUAL",
    "OP_LESSTHAN", "OP_GREATERTHAN", "OP_LESSTHANOREQUAL", "OP_GREATERTHANOREQUAL", "OP_MIN", "OP_MAX", "OP_WITHIN",
    "OP_RIPEMD160", "OP_SHA1", "OP_SHA256", "OP_HASH160", "OP_HASH256", "OP_CODESEPARATOR", "OP_CHECKSIG",
    "OP_CHECKSIGVERIFY", "OP_CHECKMULTISIG", "OP_CHECKMULTISIGVERIFY", "OP_NOP1", "OP_CHECKLOCKTIMEVERIFY",
    "OP_CHECKSEQUENCEVERIFY", "OP_NOP4", "OP_NOP5", "OP_NOP6", "OP_NOP7", "OP_NOP8", "OP_NOP9", "OP_NOP10",
    ("OP_INVALIDOPCODE", 0xFF)
]


def op():
    pass


def _set_opcodes():
    idx = 0
    opcodenames = {}
    for opcode in _opcodes:
        if isinstance(opcode, tuple):
            var, idx = opcode
        else:
            var = opcode
        opcodenames.update({idx: var})
        setattr(op, var.lower(), idx)
        idx += 1
    return opcodenames


opcodenames = _set_opcodes()

OP_N_CODES = range(op.op_1, op.op_16)

# Transactions
SCRIPT_TYPES_LOCKING = {
    # Locking scripts / scriptPubKey (Output)
    'p2pkh': ['OP_DUP', 'OP_HASH160', 'hash-20', 'OP_EQUALVERIFY', 'OP_CHECKSIG'],
    'p2sh': ['OP_HASH160', 'hash-20', 'OP_EQUAL'],
    'p2wpkh': ['OP_0', 'hash-20'],
    'p2wsh': ['OP_0', 'hash-32'],
    'p2tr': ['op_n', 'hash-32'],
    'multisig': ['op_m', 'multisig', 'op_n', 'OP_CHECKMULTISIG'],
    'p2pk': ['public_key', 'OP_CHECKSIG'],
    'nulldata': ['OP_RETURN', 'return_data'],
}

SCRIPT_TYPES_UNLOCKING = {
    # Unlocking scripts / scriptSig (Input)
    'sig_pubkey': ['signature', 'SIGHASH_ALL', 'public_key'],
    'p2sh_multisig': ['OP_0', 'multisig', 'redeemscript'],
    'p2sh_p2wpkh': ['OP_0', 'OP_HASH160', 'redeemscript', 'OP_EQUAL'],
    'p2sh_p2wsh': ['OP_0', 'push_size', 'redeemscript'],
    'locktime_cltv': ['locktime_cltv', 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP'],
    'locktime_csv': ['locktime_csv', 'OP_CHECKSEQUENCEVERIFY', 'OP_DROP'],
    'signature': ['signature']
}

SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
SIGHASH_ANYONECANPAY = 80

SEQUENCE_LOCKTIME_DISABLE_FLAG = (1 << 31)  # To enable sequence time locks
SEQUENCE_LOCKTIME_TYPE_FLAG = (1 << 22)  # If set use timestamp based lock otherwise use block height
SEQUENCE_LOCKTIME_GRANULARITY = 9
SEQUENCE_LOCKTIME_MASK = 0x0000FFFF
SEQUENCE_ENABLE_LOCKTIME = 0xFFFFFFFE
SEQUENCE_REPLACE_BY_FEE = 0xFFFFFFFD

SIGNATURE_VERSION_STANDARD = 0
SIGNATURE_VERSION_SEGWIT = 1

NETWORK_DENOMINATORS = {  # source: https://en.bitcoin.it/wiki/Units, https://en.wikipedia.org/wiki/Metric_prefix
    0.00000000000001: 'µsat',
    0.00000000001: 'msat',
    0.000000001: 'n',
    0.00000001: 'sat',
    0.0000001: 'fin',
    0.000001: 'µ',
    0.001: 'm',
    0.01: 'c',
    0.1: 'd',
    1: '',
    10: 'da',
    100: 'h',
    1000: 'k',
    1000000: 'M',
    1000000000: 'G',
    1000000000000: 'T',
    1000000000000000: 'P',
    1000000000000000000: 'E',
    1000000000000000000000: 'Z',
    1000000000000000000000000: 'Y',
}

DEFAULT_WITNESS_TYPE = 'legacy'

def varbyteint_to_int(byteint):
    """
    Convert CompactSize Variable length integer in byte format to integer.

    See https://en.bitcoin.it/wiki/Protocol_documentation#Variable_length_integer for specification

    >>> varbyteint_to_int(bytes.fromhex('fd1027'))
    (10000, 3)

    :param byteint: 1-9 byte representation
    :type byteint: bytes, list

    :return (int, int): tuple wit converted integer and size
    """
    if not isinstance(byteint, (bytes, list)):
        raise Exception("Byteint must be a list or defined as bytes")
    if byteint == b'':
        return 0, 0
    ni = byteint[0]
    if ni < 253:
        return ni, 1
    if ni == 253:  # integer of 2 bytes
        size = 2
    elif ni == 254:  # integer of 4 bytes
        size = 4
    else:  # integer of 8 bytes
        size = 8
    return int.from_bytes(byteint[1:1+size][::-1], 'big'), size + 1

def to_bytes(string, unhexlify=True):
    """
    Convert string, hexadecimal string to bytes

    :param string: String to convert
    :type string: str, bytes
    :param unhexlify: Try to unhexlify hexstring
    :type unhexlify: bool

    :return: Bytes var
    """
    if not string:
        return b''
    if unhexlify:
        try:
            if isinstance(string, bytes):
                string = string.decode()
            s = bytes.fromhex(string)
            return s
        except (TypeError, ValueError):
            pass
    if isinstance(string, bytes):
        return string
    else:
        return bytes(string, 'utf8')

def script_deserialize(script, script_types=None, locking_script=None, size_bytes_check=True):  # pragma: no cover
    """
    Deserialize a script: determine type, number of signatures and script data.
    
    :param script: Raw script
    :type script: str, bytes
    :param script_types: Limit script type determination to this list. Leave to default None to search in all script types.
    :type script_types: list
    :param locking_script: Only deserialize locking scripts. Specify False to only deserialize for unlocking scripts. Default is None for both
    :type locking_script: bool
    :param size_bytes_check: Check if script or signature starts with size bytes and remove size bytes before parsing. Default is True
    :type size_bytes_check: bool

    :return list: With this items: [script_type, data, number_of_sigs_n, number_of_sigs_m] 
    """

    def _parse_data(scr, max_items=None, redeemscript_expected=False, item_length=0):
        # scr = to_bytes(scr)
        items = []
        total_length = 0
        if 69 <= len(scr) <= 74 and scr[:1] == b'\x30':
            return [scr], len(scr)
        while len(scr) and (max_items is None or max_items > len(items)):
            itemlen, size = varbyteint_to_int(scr[0:9])
            if item_length and itemlen != item_length:
                break
            if not item_length and itemlen not in [20, 33, 65, 70, 71, 72, 73]:
                break
            if redeemscript_expected and len(scr[itemlen + 1:]) < 20:
                break
            items.append(scr[1:itemlen + 1])
            total_length += itemlen + size
            scr = scr[itemlen + 1:]
        return items, total_length

    def _get_empty_data():
        return {'script_type': '', 'keys': [], 'signatures': [], 'hashes': [], 'redeemscript': b'',
                'number_of_sigs_n': 1, 'number_of_sigs_m': 1, 'locktime_cltv': None, 'locktime_csv': None, 'result': ''}

    def _parse_script(script):
        found = False
        cur = 0
        data = _get_empty_data()
        for script_type in script_types:
            cur = 0
            try:
                ost = SCRIPT_TYPES_UNLOCKING[script_type]
            except KeyError:
                ost = SCRIPT_TYPES_LOCKING[script_type]
            data = _get_empty_data()
            data['script_type'] = script_type
            found = True
            for ch in ost:
                if cur >= len(script):
                    found = False
                    break
                cur_char = script[cur]
                if ch[:4] == 'hash':
                    hash_length = 0
                    if len(ch) > 5:
                        hash_length = int(ch.split("-")[1])
                    s, total_length = _parse_data(script[cur:], 1, item_length=hash_length)
                    if not s:
                        found = False
                        break
                    data['hashes'] += s
                    cur += total_length
                elif ch == 'signature':
                    signature_length = 0
                    s, total_length = _parse_data(script[cur:], 1, item_length=signature_length)
                    if not s:
                        found = False
                        break
                    data['signatures'] += s
                    cur += total_length
                elif ch == 'public_key':
                    pk_size, size = varbyteint_to_int(script[cur:cur + 9])
                    key = script[cur + size:cur + size + pk_size]
                    if not key:
                        found = False
                        break
                    data['keys'].append(key)
                    cur += size + pk_size
                elif ch == 'OP_RETURN':
                    if cur_char == op.op_return and cur == 0:
                        data.update({'op_return': script[cur + 1:]})
                        cur = len(script)
                        found = True
                        break
                    else:
                        found = False
                        break
                elif ch == 'multisig':  # one or more signatures
                    redeemscript_expected = False
                    if 'redeemscript' in ost:
                        redeemscript_expected = True
                    s, total_length = _parse_data(script[cur:], redeemscript_expected=redeemscript_expected)
                    if not s:
                        found = False
                        break
                    data['signatures'] += s
                    cur += total_length
                elif ch == 'redeemscript':
                    size_byte = 0
                    if script[cur:cur + 1] == b'\x4c':
                        size_byte = 1
                    elif script[cur:cur + 1] == b'\x4d':
                        size_byte = 2
                    elif script[cur:cur + 1] == b'\x4e':
                        size_byte = 3
                    data['redeemscript'] = script[cur + 1 + size_byte:]
                    data2 = script_deserialize(data['redeemscript'], locking_script=True)
                    if 'signatures' not in data2 or not data2['signatures']:
                        found = False
                        break
                    data['keys'] = data2['signatures']
                    data['number_of_sigs_m'] = data2['number_of_sigs_m']
                    data['number_of_sigs_n'] = data2['number_of_sigs_n']
                    cur = len(script)
                elif ch == 'push_size':
                    push_size, size = varbyteint_to_int(script[cur:cur + 9])
                    found = bool(len(script[cur:]) - size == push_size)
                    if not found:
                        break
                elif ch == 'op_m':
                    if cur_char in OP_N_CODES:
                        data['number_of_sigs_m'] = cur_char - op.op_1 + 1
                    else:
                        found = False
                        break
                    cur += 1
                elif ch == 'op_n':
                    if cur_char in OP_N_CODES:
                        data['number_of_sigs_n'] = cur_char - op.op_1 + 1
                    else:
                        found = False
                        break
                    if data['number_of_sigs_m'] > data['number_of_sigs_n']:
                        raise Exception("Number of signatures to sign (%s) is higher then actual "
                                               "amount of signatures (%s)" %
                                               (data['number_of_sigs_m'], data['number_of_sigs_n']))
                    if len(data['signatures']) > int(data['number_of_sigs_n']):
                        raise Exception("%d signatures found, but %s sigs expected" %
                                               (len(data['signatures']), data['number_of_sigs_n']))
                    cur += 1
                elif ch == 'SIGHASH_ALL':
                    pass
                    # if cur_char != SIGHASH_ALL:
                    #     found = False
                    #     break
                elif ch == 'locktime_cltv':
                    if len(script) < 4:
                        found = False
                        break
                    data['locktime_cltv'] = int.from_bytes(script[cur:cur + 4], 'little')
                    cur += 4
                elif ch == 'locktime_csv':
                    if len(script) < 4:
                        found = False
                        break
                    data['locktime_csv'] = int.from_bytes(script[cur:cur + 4], 'little')
                    cur += 4
                else:
                    try:
                        if opcodenames.get(cur_char) == ch:
                            cur += 1
                        else:
                            found = False
                            data = _get_empty_data()
                            break
                    except IndexError:
                        raise Exception("Opcode %s not found [type %s]" % (ch, script_type))
            if found and not len(script[cur:]):  # Found is True and no remaining script to parse
                break

        if found and not len(script[cur:]):
            return data, script[cur:]
        data = _get_empty_data()
        data['result'] = 'Script not recognised'
        return data, ''

    data = _get_empty_data()
    script = to_bytes(script)
    if not script:
        data.update({'result': 'Empty script'})
        return data

    # Check if script starts with size byte
    if size_bytes_check:
        script_size, size = varbyteint_to_int(script[0:9])
        if len(script[1:]) == script_size:
            data = script_deserialize(script[1:], script_types, locking_script, size_bytes_check=False)
            if 'result' in data and data['result'][:22] not in \
                    ['Script not recognised', 'Empty script', 'Could not parse script']:
                return data

    if script_types is None:
        if locking_script is None:
            script_types = dict(SCRIPT_TYPES_UNLOCKING, **SCRIPT_TYPES_LOCKING)
        elif locking_script:
            script_types = SCRIPT_TYPES_LOCKING
        else:
            script_types = SCRIPT_TYPES_UNLOCKING
    elif not isinstance(script_types, list):
        script_types = [script_types]

    locktime_cltv = 0
    locktime_csv = 0
    while len(script):
        begin_script = script
        data, script = _parse_script(script)
        if begin_script == script:
            break
        if script and data['script_type'] == 'locktime_cltv':
            locktime_cltv = data['locktime_cltv']
        if script and data['script_type'] == 'locktime_csv':
            locktime_csv = data['locktime_csv']
    if data and data['result'] != 'Script not recognised':
        data['locktime_cltv'] = locktime_cltv
        data['locktime_csv'] = locktime_csv
        return data

    wrn_msg = "Could not parse script, unrecognized script"
    # _logger.debug(wrn_msg)
    data = _get_empty_data()
    data['result'] = wrn_msg
    return data


def transaction_deserialize(rawtx):
    """
    Deserialize a raw transaction
    
    Returns a dictionary with list of input and output objects, locktime and version.
    
    Will raise an error if wrong number of inputs are found or if there are no output found.
    
    :param rawtx: Raw transaction as hexadecimal string or bytes
    :type rawtx: str, bytes

    :return Transaction:
    """

    rawtx = to_bytes(rawtx)
    coinbase = False
    flag = None
    witness_type = 'legacy'

    version = rawtx[0:4][::-1]
    cursor = 4
    if rawtx[4:5] == b'\0':
        flag = rawtx[5:6]
        if flag == b'\1':
            witness_type = 'segwit'
        cursor += 2
    n_inputs, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
    cursor += size
    inputs = []
    for n in range(0, n_inputs):
        inp_hash = rawtx[cursor:cursor + 32][::-1]
        if not len(inp_hash):
            raise TransactionError("Input transaction hash not found. Probably malformed raw transaction")
        if inp_hash == 32 * b'\0':
            coinbase = True
        output_n = rawtx[cursor + 32:cursor + 36][::-1]
        cursor += 36
        unlocking_script_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        unlocking_script = rawtx[cursor:cursor + unlocking_script_size]
        inp_type = 'legacy'
        if witness_type == 'segwit' and not unlocking_script_size:
            inp_type = 'segwit'
        cursor += unlocking_script_size
        sequence_number = rawtx[cursor:cursor + 4]
        cursor += 4
        inputs.append({'prev_txid':inp_hash, 'output_n':output_n, 'unlocking_script':unlocking_script,
                            'witness_type':inp_type, 'sequence':sequence_number, 'index_n':n})
    if len(inputs) != n_inputs:
        raise Exception("Error parsing inputs. Number of tx specified %d but %d found" % (n_inputs, len(inputs)))

    outputs = []
    n_outputs, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
    cursor += size
    output_total = 0
    for n in range(0, n_outputs):
        value = int.from_bytes(rawtx[cursor:cursor + 8][::-1], 'big')
        cursor += 8
        lock_script_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
        cursor += size
        lock_script = rawtx[cursor:cursor + lock_script_size]
        cursor += lock_script_size
        outputs.append({'value':value, 'lock_script':lock_script, 'output_n':n})
        output_total += value
    if not outputs:
        raise Exception("Error no outputs found in this transaction")

    if witness_type == 'segwit':
        for n in range(0, len(inputs)):
            n_items, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
            cursor += size
            witnesses = []
            for m in range(0, n_items):
                witness = b'\0'
                item_size, size = varbyteint_to_int(rawtx[cursor:cursor + 9])
                if item_size:
                    witness = rawtx[cursor + size:cursor + item_size + size]
                cursor += item_size + size
                witnesses.append(witness)
            if witnesses and not coinbase:
                script_type = inputs[n].script_type
                witness_script_type = 'sig_pubkey'
                signatures = []
                keys = []
                sigs_required = 1
                public_hash = b''
                for witness in witnesses:
                    if witness == b'\0':
                        continue
                    if 69 <= len(witness) <= 74 and witness[0:1] == b'\x30':  # witness is DER encoded signature
                        signatures.append(witness)
                    elif len(witness) == 33 and len(signatures) == 1:  # key from sig_pk
                        keys.append(witness)
                    else:
                        rsds = script_deserialize(witness, script_types=['multisig'])
                        if not rsds['script_type'] == 'multisig':
                            _logger.warning("Could not parse witnesses in transaction. Multisig redeemscript expected")
                            witness_script_type = 'unknown'
                            script_type = 'unknown'
                        else:
                            keys = rsds['signatures']
                            sigs_required = rsds['number_of_sigs_m']
                            witness_script_type = 'p2sh'
                            script_type = 'p2sh_multisig'

                inp_witness_type = inputs[n].witness_type
                usd = script_deserialize(inputs[n].unlocking_script, locking_script=True)

                if usd['script_type'] == "p2wpkh" and witness_script_type == 'sig_pubkey':
                    inp_witness_type = 'p2sh-segwit'
                    script_type = 'p2sh_p2wpkh'
                elif usd['script_type'] == "p2wsh" and witness_script_type == 'p2sh':
                    inp_witness_type = 'p2sh-segwit'
                    script_type = 'p2sh_p2wsh'
                inputs[n] = {'prev_txid':inputs[n].prev_txid, 'output_n':inputs[n].output_n, 'keys':keys,
                                  'unlocking_script_unsigned':inputs[n].unlocking_script_unsigned,
                                  'unlocking_script':inputs[n].unlocking_script, 'sigs_required':sigs_required,
                                  'signatures':signatures, 'witness_type':inp_witness_type, 'script_type':script_type,
                                  'sequence':inputs[n].sequence, 'index_n':inputs[n].index_n, 'public_hash':public_hash,
                                  'network':inputs[n].network, 'witnesses':witnesses}
    if len(rawtx[cursor:]) != 4:
        raise Exception("Error when deserializing raw transaction, bytes left for locktime must be 4 not %d" %
                               len(rawtx[cursor:]))
    locktime = int.from_bytes(rawtx[cursor:cursor + 4][::-1], 'big')

    return {'inputs':inputs, 'outputs':outputs, 'locktime':locktime, 'version':version, 'size':cursor + 4, 'output_total':output_total,
                       'coinbase':coinbase, 'flag':flag, 'witness_type':witness_type, 'rawtx':rawtx}
