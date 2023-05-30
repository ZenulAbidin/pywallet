from hashlib import sha256
import re

import six

from Cryptodome.Cipher import AES
from .ripemd160 import ripemd160


def ensure_bytes(data):
    if not isinstance(data, six.binary_type):
        return data.encode('utf-8')
    return data


def ensure_str(data):
    if isinstance(data, six.binary_type):
        return data.decode('utf-8')
    elif not isinstance(data, six.string_types):
        raise ValueError("Invalid value for string")
    return data


def chr_py2(num):
    """Ensures that python3's chr behavior matches python2."""
    if six.PY3:
        return bytes([num])
    return chr(num)


def hash160(data):
    """Return ripemd160(sha256(data))"""
    return ripemd160(sha256(data).digest())


def is_hex_string(string):
    """Check if the string is only composed of hex characters."""
    pattern = re.compile(r'[A-Fa-f0-9]+')
    if isinstance(string, six.binary_type):
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
    @rtype: string
    """
    cipher = AES.new(passphrase, AES.MODE_CBC, b'\x00'*16)
    return cipher.encrypt(raw)

def decrypt(enc, passphrase):
    """
    Decrypt encrypted text with the passphrase
    @param enc: string Text to decrypt
    @param passphrase: string Passphrase
    @type enc: string
    @type passphrase: string
    @rtype: string
    """
    cipher = AES.new(passphrase, AES.MODE_CBC, b'\x00'*16)
    return cipher.decrypt(enc)