# -*- coding: utf-8 -*-
# aes256.py
# This file is part of AES-everywhere project (https://github.com/mervick/aes-everywhere)
#
# This is an implementation of the AES algorithm, specifically CBC mode,
# with 256 bits key length and PKCS7 padding.
#
# Copyright Andrey Izman (c) 2018-2019 <izmanw@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import hashlib
import sys
import base64
from Cryptodome import Random
from Cryptodome.Cipher import AES

__author__ = "Andrey Izman"
__email__ = "izmanw@gmail.com"
__copyright__ = "Copyright 2018-2019 Andrey Izman"
__license__ = "MIT"


py2 = sys.version_info[0] == 2

BLOCK_SIZE = 16
KEY_LEN = 32
IV_LEN = 16


def hash_password_pbkdf2(password, iterations=600000, key_length=128):
    # Hash the password using PBKDF2
    return hashlib.pbkdf2_hmac("sha256", password, b"Salted__", iterations, key_length)


def encrypt(raw: str, passphrase: str):
    """
    Encrypt text with the passphrase

    Args:
        raw (str): Text to encrypt
        passphrase (str): Encryption password. It is recommended to use a strong password.

    Returns:
        bytes: The encrypted text
    """
    salt = Random.new().read(8)
    key, iv = __derive_key_and_iv(passphrase, salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return base64.b64encode(b"Salted__" + salt + cipher.encrypt(__pkcs7_padding(raw)))


def decrypt(enc, passphrase):
    """
    Decrypt encrypted text with the passphrase


    Args:
        enc (bytes): Text to decrypt
        passphrase (str): Decryption password

    Returns:
        str: The original text
    """
    ct = base64.b64decode(enc)
    salted = ct[:8]
    if salted != b"Salted__":
        raise ValueError("Decryption failed")
    salt = ct[8:16]
    key, iv = __derive_key_and_iv(passphrase, salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    d = __pkcs7_trimming(cipher.decrypt(ct[16:]))
    if len(d) == 0:
        raise ValueError("Decryption failed")
    return d


def __pkcs7_padding(s):
    """
    Padding to blocksize according to PKCS #7.

    Calculates the number of missing characters to BLOCK_SIZE and pads with
    ord(number of missing characters).

    See: http://www.di-mgt.com.au/cryptopad.html

    Args:
        s (str): Text to pad.

    Returns:
        str: Padded text.
    """
    s_len = len(s if py2 else s.encode("utf-8"))
    s = s + (BLOCK_SIZE - s_len % BLOCK_SIZE) * chr(BLOCK_SIZE - s_len % BLOCK_SIZE)
    return s if py2 else bytes(s, "utf-8")


def __pkcs7_trimming(s):
    """
    Trims padding according to PKCS #7.

    Args:
        s (str): Text to unpad.

    Returns:
        str: Unpadded text.
    """
    if sys.version_info[0] == 2:
        return s[0 : -ord(s[-1])]
    return s[0 : -s[-1]].decode("utf-8")


def __derive_key_and_iv(password, salt):
    """
    Derives key and IV.

    Args:
        password (str): Password.
        salt (str): Salt.

    Returns:
        str: Derived key and IV.
    """
    d = d_i = b""
    enc_pass = password if py2 else password.encode("utf-8")
    while len(d) < KEY_LEN + IV_LEN:
        d_i = hash_password_pbkdf2(d_i + enc_pass + salt)
        d += d_i
    return d[:KEY_LEN], d[KEY_LEN : KEY_LEN + IV_LEN]


if __name__ == "__main__":  # code to execute if called from command-line
    print(decrypt(encrypt("text", "pass"), "pass"))
