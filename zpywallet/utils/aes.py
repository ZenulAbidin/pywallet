# -*- coding: utf-8 -*-
#
# This is an implementation of the AES algorithm, specifically GCM-SIV mode,
# as defined in RFC 5297, with 256 bits key length and PKCS7 padding.
# Note that this is *not* AES-GCM-SIV!
#
#
# Copyright (c) Ali Sherief 2023-2024 <ali@notatether.com>
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
import base64
from Cryptodome import Random
from Cryptodome.Cipher import AES

BLOCK_SIZE = 16
KEY_LEN = 32
NONCE_LEN = 12


def hash_password_pbkdf2(
    password: bytes, salt: bytes, iterations=600000, key_length=128
):
    # Hash the password using PBKDF2 with OWASP-recommended rounds
    return hashlib.pbkdf2_hmac("sha256", password + salt, salt, iterations, key_length)


def encrypt(raw: bytes, passphrase: bytes) -> bytes:
    """
    Encrypt binary data with the passphrase

    Args:
        raw (bytes): data to encrypt
        passphrase (bytes): Encryption password. It is recommended to use a strong password.

    Returns:
        bytes: The encrypted text
    """
    salt = Random.new().read(8)
    key, nonce = __derive_key_and_nonce(passphrase, salt)
    cipher = AES.new(key, AES.MODE_SIV, nonce)
    text, mac = cipher.encrypt_and_digest(__pkcs7_padding(raw))
    return base64.b64encode(b"Salted__" + salt + mac + text)


def encrypt_str(raw: str, passphrase: str) -> str:
    """A wrapper around encyrpt() for str objects"""
    return encrypt(raw.encode("utf-8"), passphrase.encode("utf-8"))


def decrypt(enc: bytes, passphrase: bytes) -> bytes:
    """
    Decrypt encrypted binary data with the passphrase


    Args:
        enc (bytes): data to decrypt
        passphrase (bytes): Decryption password

    Returns:
        bytes: The original text
    """
    ct = base64.b64decode(enc)
    salted = ct[:8]
    if salted != b"Salted__":
        raise ValueError("Decryption failed")
    salt = ct[8:16]
    key, nonce = __derive_key_and_nonce(passphrase, salt)
    cipher = AES.new(key, AES.MODE_SIV, nonce)

    mac = ct[16:32]
    text = ct[32:]

    # Will throw ValueError if the authentication tag was tampered with
    d = __pkcs7_trimming(cipher.decrypt_and_verify(text, mac))

    if len(d) == 0:
        raise ValueError("Decryption failed")
    return d


def decrypt_str(enc: bytes, passphrase: str) -> str:
    """A wrapper around decrypt() for str objects"""
    return decrypt(enc, passphrase.encode("utf-8")).decode("utf-8")


def __pkcs7_padding(s):
    # Padding to blocksize according to PKCS #7.
    #
    # Calculates the number of missing characters to BLOCK_SIZE and pads with
    # ord(number of missing characters).
    #
    # See: http://www.di-mgt.com.au/cryptopad.html
    s_len = len(s)
    s = s + (BLOCK_SIZE - s_len % BLOCK_SIZE) * bytes(
        chr(BLOCK_SIZE - s_len % BLOCK_SIZE), "utf-8"
    )
    return s


def __pkcs7_trimming(s):
    # Trims padding (unpads) according to PKCS #7.
    return s[0 : -s[-1]]


def __derive_key_and_nonce(password, salt):
    d = d_i = b""
    enc_pass = password
    while len(d) < KEY_LEN + NONCE_LEN:
        d_i = hash_password_pbkdf2(d_i + enc_pass, salt)
        d += d_i
    return d[:KEY_LEN], d[KEY_LEN : KEY_LEN + NONCE_LEN]
