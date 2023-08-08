from hashlib import sha256
import re
import datetime

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from .ripemd160 import ripemd160
from .keccak import Keccak256



def ensure_bytes(data):
    if not isinstance(data, bytes):
        return data.encode('utf-8')
    return data


def ensure_str(data):
    if isinstance(data, bytes):
        return data.decode('utf-8')
    elif not isinstance(data, str):
        raise ValueError("Invalid value for string")
    return data


def hash160(data):
    """Return ripemd160(sha256(data))"""
    return ripemd160(sha256(data).digest())

def is_hex_string(string):
    """Check if the string is only composed of hex characters."""
    pattern = re.compile(r'[A-Fa-f0-9]+')
    if isinstance(string, bytes):
        string = str(string)
    return pattern.match(string) is not None


def long_to_hex(l, size):
    """Encode a long value as a hex string, 0-padding to size.

    Note that size is the size of the resulting hex string. So, for a 32Byte
    long size should be 64 (two hex characters per byte"."""
    f_str = "{0:0%sx}" % size
    return ensure_bytes(f_str.format(l).lower())

def encrypt(raw, passphrase):
    """
    Encrypt text with the passphrase
    @param raw: string Text to encrypt
    @param passphrase: string Passphrase
    @type raw: string
    @type passphrase: string
    @rtype: bytes
    """
    backend = default_backend()
    cipher = Cipher(algorithms.AES(passphrase), modes.CBC(b'\x00'*16), backend=backend)
    encryptor = cipher.encryptor()
    return encryptor.update(raw) + encryptor.finalize()

def decrypt(enc, passphrase):
    """
    Decrypt encrypted text with the passphrase
    @param enc: bytes Text to decrypt
    @param passphrase: string Passphrase
    @type enc: bytes
    @type passphrase: string
    @rtype: bytes
    """
    backend = default_backend()
    cipher = Cipher(algorithms.AES(passphrase), modes.CBC(b'\x00'*16), backend=backend)
    decryptor = cipher.decryptor()
    return decryptor.update(enc) + decryptor.finalize()

def convert_to_utc_timestamp(date_string, format_string="%Y-%m-%dT%H:%M:%SZ"):
    # Create a datetime object from the input string
    # I think we have to check what value the format_string is supposed to be.
    date_object = datetime.datetime.strptime(date_string, format_string)

    # Convert the datetime object to UTC timezone
    utc_date = date_object.astimezone(datetime.timezone.utc)

    # Calculate the timestamp
    timestamp = int(utc_date.timestamp())
    
    return timestamp


def eth_transaction_hash(address: str, nonce: int) -> str:
    """Constructs an Ethereum transaction hash from an address and a transaction number"""
    # Combine the address and nonce as a string
    data_to_hash = address.lower() + format(nonce, 'x')
    
    # Calculate the hash using keccak256
    transaction_hash = Keccak256(bytes.fromhex(data_to_hash)).digest().hex()
    return transaction_hash