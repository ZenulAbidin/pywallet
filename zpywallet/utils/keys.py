#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Code from:
https://github.com/michailbrynard/ethereum-bip44-python

This submodule provides the PublicKey, PrivateKey, and Signature classes.
It also provides HDPublicKey and HDPrivateKey classes for working with HD
wallets."""

import math
import base64
import binascii
from binascii import hexlify
import hashlib
from hashlib import sha256
import hmac
import random
import codecs
import os
from collections import namedtuple


from Crypto.Hash import keccak

import six

from .base58 import b58encode_check, b58decode_check
from ..mnemonic.mnemonic import Mnemonic
from .bech32 import encode as bech32_encode
from .ecdsa import Point
from .ecdsa import ECPointAffine
from .ecdsa import secp256k1
from .ripemd160 import ripemd160
from .utils import chr_py2
from .utils import ensure_bytes, ensure_str, long_or_int
from ..network import BitcoinMainNet



PublicPair = namedtuple("PublicPair", ["x", "y"])


class KeyParseError(Exception):
    pass


def incompatible_network_exception_factory(
        network_name, expected_prefix, given_prefix):
    return IncompatibleNetworkException(
        f"Incorrect network. {network_name} expects a byte prefix of "
        f"{expected_prefix}, but you supplied {given_prefix}")


class ChecksumException(Exception):
    pass


class IncompatibleNetworkException(Exception):
    pass


class InvalidChildException(Exception):
    pass

bitcoin_curve = secp256k1()

def sha3_256(x):
    """ Wrapper to quickly generate 256 digest bits of SHA3 Keccac. """
    return keccak.new(digest_bits=256, data=x)

Point = namedtuple('Point', ['x', 'y'])

def rand_bytes(n, secure=True):
    """ Returns n random bytes.
    Args:
        n (int): number of bytes to return.
        secure (bool): If True, uses os.urandom to generate
            cryptographically secure random bytes. Otherwise, uses
            random.randint() which generates pseudo-random numbers.
    Returns:
        b (bytes): n random bytes.
    """
    if secure:
        return os.urandom(n)
    else:
        return bytes([random.randint(0, 255) for i in range(n)])


def address_to_key_hash(s):
    """ Given a Bitcoin address decodes the version and
    RIPEMD-160 hash of the public key.
    Args:
        s (bytes): The Bitcoin address to decode
    Returns:
        (version, h160) (tuple): A tuple containing the version and
        RIPEMD-160 hash of the public key.
    """
    n = b58decode_check(s)
    version = n[0]
    h160 = n[1:]
    return version, h160


def sha3(seed):
    return sha3_256(seed).digest()


def get_bytes(s):
    """Returns the byte representation of a hex- or byte-string."""
    if isinstance(s, bytes):
        b = s
    elif isinstance(s, str):
        b = bytes.fromhex(s)
    else:
        raise TypeError("s must be either 'bytes' or 'str'!")

    return b


def bytes_to_str(b):
    """ Converts bytes into a hex-encoded string.
    Args:
        b (bytes): bytes to encode
    Returns:
        h (str): hex-encoded string corresponding to b.
    """
    return codecs.encode(b, 'hex_codec').decode('ascii')



class PrivateKeyBase(object):
    """ Base class for both PrivateKey and HDPrivateKey.

    As this class is a base class it should not be used directly.

    Args:
        k (int): The private key.

    Returns:
        PrivateKey: The object representing the private key.
    """

    @staticmethod
    def from_b58check(private_key):
        """ Decodes a Base58Check encoded private-key.

        Args:
            private_key (str): A Base58Check encoded private key.

        Returns:
            PrivateKey: A PrivateKey object
        """
        raise NotImplementedError

    def __init__(self, k):
        self.key = k
        self._public_key = None

    @property
    def public_key(self):
        """ Returns the public key associated with this private key.

        Returns:
            PublicKey:
                The PublicKey object that corresponds to this
                private key.
        """
        return self._public_key

    def raw_sign(self, message, do_hash=True):
        """ Signs message using this private key.

        Args:
            message (bytes): The message to be signed. If a string is
               provided it is assumed the encoding is 'ascii' and
               converted to bytes. If this is not the case, it is up
               to the caller to convert the string to bytes
               appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
               to signing, False if not. This should always be left as
               True except in special situations which require doing
               the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            ECPointAffine:
                a raw point (r = pt.x, s = pt.y) which is
                the signature.
        """
        raise NotImplementedError

    def sign(self, message, do_hash=True):
        """ Signs message using this private key.

        Note:
            This differs from `raw_sign()` since it returns a
            Signature object.

        Args:
            message (bytes or str): The message to be signed. If a
               string is provided it is assumed the encoding is
               'ascii' and converted to bytes. If this is not the
               case, it is up to the caller to convert the string to
               bytes appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
               to signing, False if not. This should always be left as
               True except in special situations which require doing
               the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            Signature: The signature corresponding to message.
        """
        raise NotImplementedError

    def sign_bitcoin(self, message, compressed=False):
        """ Signs a message using this private key such that it
        is compatible with bitcoind, bx, and other Bitcoin
        clients/nodes/utilities.

        Note:
            0x18 + b\"Bitcoin Signed Message:" + newline + len(message) is
            prepended to the message before signing.

        Args:
            message (bytes or str): Message to be signed.
            compressed (bool): True if the corresponding public key will be
              used in compressed format. False if the uncompressed version
              is used.

        Returns:
            bytes: A Base64-encoded byte string of the signed message.
            The first byte of the encoded message contains information
            about how to recover the public key. In bitcoind parlance,
            this is the magic number containing the recovery ID and
            whether or not the key was compressed or not. (This function
            always processes full, uncompressed public-keys, so the magic
            number will always be either 27 or 28).
        """
        raise NotImplementedError

    def to_b58check(self):
        """ Generates a Base58Check encoding of this private key."""
        raise NotImplementedError

    def to_hex(self):
        """ Generates a hex encoding of the serialized key.

        Returns:
           str: A hex encoded string representing the key.
        """
        return bytes_to_str(bytes(self))

    def __bytes__(self):
        raise NotImplementedError

    def __int__(self):
        raise NotImplementedError


class PublicKeyBase(object):
    """ Base class for both PublicKey and HDPublicKey.

    As this class is a base class it should not be used directly.

    Args:
        x (int): The x component of the public key point.
        y (int): The y component of the public key point.

    Returns:
        PublicKey: The object representing the public key.

    """

    @staticmethod
    def from_bytes(key_bytes):
        """ Generates a public key object from a byte (or hex) string.

        Args:
            key_bytes (bytes or str): A byte stream.

        Returns:
            PublicKey: A PublicKey object.
        """
        raise NotImplementedError

    @staticmethod
    def from_private_key(private_key):
        """ Generates a public key object from a PrivateKey object.

        Args:
            private_key (PrivateKey): The private key object from
               which to derive this object.

        Returns:
            PublicKey: A PublicKey object.
        """
        return private_key.public_key

    def __init__(self):
        pass

    def hash160(self, compressed=True):
        """ Return the RIPEMD-160 hash of the SHA-256 hash of the
        public key.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.
        Returns:
            bytes: RIPEMD-160 byte string.
        """
        raise NotImplementedError

    def base58_address(self, compressed=True):
        """ Address property that returns a base58 encoding of the public key.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.

        Returns:
            bytes: Address encoded in Base58Check.
        """
        raise NotImplementedError

    def bech32_address(self, compressed=True, witness_version=0):
        """ Address property that returns a bech32 encoding of the public key.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used. It is recommended to leave this value as true - Uncompressed segwit
               addresses are non-standard on most networks, preventing them from being broadcasted
               normally, and should be avoided.
            witness_version (int): Witness version to use for theBech32 address.
                Allowed values are 0 (segwit) and 1 (Taproot).

        Returns:
            bytes: Address encoded in Bech32.
        """
        raise NotImplementedError

    def hex_address(self):
        """ Address property that returns a hexadecimal encoding of the public key. """
        raise NotImplementedError

    def address(self, compressed=True, witness_version=0):
        """Returns the address genereated according to the first supported address format by the network."""
        raise NotImplementedError

    def verify(self, message, signature, do_hash=True):
        """ Verifies that message was appropriately signed.

        Args:
            message (bytes): The message to be verified.
            signature (Signature): A signature object.
            do_hash (bool): True if the message should be hashed prior
              to signing, False if not. This should always be left as
              True except in special situations which require doing
              the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            verified (bool): True if the signature is verified, False
            otherwise.
        """
        raise NotImplementedError

    def to_hex(self):
        """ Hex representation of the serialized byte stream.

        Returns:
            h (str): A hex-encoded string.
        """
        return bytes_to_str(bytes(self))

    def __bytes__(self):
        raise NotImplementedError

    def __int__(self):
        raise NotImplementedError

    @property
    def compressed_bytes(self):
        """ Byte string corresponding to a compressed representation
        of this public key.

        Returns:
            b (bytes): A 33-byte long byte string.
        """
        raise NotImplementedError


class PrivateKey(PrivateKeyBase):
    """ Encapsulation of a Bitcoin ECDSA private key.

    This class provides capability to generate private keys,
    obtain the corresponding public key, sign messages and
    serialize/deserialize into a variety of formats.

    Args:
        k (int): The private key.

    Returns:
        PrivateKey: The object representing the private key.
    """

    @staticmethod
    def from_bytes(b):
        """ Generates PrivateKey from the underlying bytes.

        Args:
            b (bytes): A byte stream containing a 256-bit (32-byte) integer.

        Returns:
            tuple(PrivateKey, bytes): A PrivateKey object and the remainder
            of the bytes.
        """
        if len(b) < 32:
            raise ValueError('b must contain at least 32 bytes')

        return PrivateKey(int.from_bytes(b[:32], 'big'))

    @staticmethod
    def from_hex(h):
        """ Generates PrivateKey from a hex-encoded string.

        Args:
            h (str): A hex-encoded string containing a 256-bit
                 (32-byte) integer.

        Returns:
            PrivateKey: A PrivateKey object.
        """
        return PrivateKey.from_bytes(bytes.fromhex(h))

    @staticmethod
    def from_int(i):
        """ Initializes a private key from an integer.

        Args:
            i (int): Integer that is the private key.

        Returns:
            PrivateKey: The object representing the private key.
        """
        return PrivateKey(i)

    @staticmethod
    def from_b58check(private_key, network=BitcoinMainNet):
        """ Decodes a Base58Check encoded private-key.

        Args:
            private_key (str): A Base58Check encoded private key.
            network: Network to work in. Default is Bitcoin mainnet.

        Returns:
            PrivateKey: A PrivateKey object
        """
        b58dec = b58decode_check(private_key)
        version = b58dec[0]
        assert version == network.SECRET_KEY

        return PrivateKey(int.from_bytes(b58dec[1:], 'big'))

    @staticmethod
    def from_random():
        """ Initializes a private key from a random integer.

        Returns:
            PrivateKey: The object representing the private key.
        """
        return PrivateKey(random.SystemRandom().randrange(1, bitcoin_curve.n))

    def __init__(self, k, network=BitcoinMainNet):
        PrivateKeyBase.__init__(self, k)
        self.key = k
        self._public_key = None
        self.network = network

    @classmethod
    def from_brainwallet(cls, password, salt="zpywallet"):
        """Generate a new key from a master password, and an optional salt.

        This password is hashed via a single round of sha256 and is highly
        breakable, but it's the standard brainwallet approach.

        It is highly recommended to salt a password before hashing it to protect
        it from rainbow table attacks. You should not need to change it from the
        default value, though. WARNING: Either remember the salt, and add it after
        the end of the password, or always use this method to regenerate the
        brainwallet so you don't lose your private key.
        """
        password = ensure_bytes(password) + ensure_bytes(salt)
        key = sha256(password).hexdigest()
        return cls(long_or_int(key, 16))

    __hash__ = object.__hash__

    @property
    def public_key(self):
        """ Returns the public key associated with this private key.

        Returns:
            PublicKey:
                The PublicKey object that corresponds to this
                private key.
        """
        if self._public_key is None:
            self._public_key = PublicKey.from_point(
                bitcoin_curve.public_key(self.key))
        return self._public_key

    def raw_sign(self, message, do_hash=True):
        """ Signs message using this private key.

        Args:
            message (bytes): The message to be signed. If a string is
                provided it is assumed the encoding is 'ascii' and
                converted to bytes. If this is not the case, it is up
                to the caller to convert the string to bytes
                appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
                to signing, False if not. This should always be left as
                True except in special situations which require doing
                the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            ECPointAffine:
                a raw point (r = pt.x, s = pt.y) which is
                the signature.
        """
        if isinstance(message, str):
            msg = bytes(message, 'ascii')
        elif isinstance(message, bytes):
            msg = message
        else:
            raise TypeError("message must be either str or bytes!")

        sig_pt, rec_id = bitcoin_curve.sign(msg, self.key, do_hash)

        # Take care of large s:
        # Bitcoin deals with large s, by subtracting
        # s from the curve order. See:
        # https://bitcointalk.org/index.php?topic=285142.30;wap2
        if sig_pt.y >= (bitcoin_curve.n // 2):
            sig_pt = Point(sig_pt.x, bitcoin_curve.n - sig_pt.y)
            rec_id ^= 0x1

        return (sig_pt, rec_id)

    def sign(self, message, do_hash=True):
        """ Signs message using this private key.

        Note:
            This differs from `raw_sign()` since it returns a Signature object.

        Args:
            message (bytes or str): The message to be signed. If a
                string is provided it is assumed the encoding is
                'ascii' and converted to bytes. If this is not the
                case, it is up to the caller to convert the string to
                bytes appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
                to signing, False if not. This should always be left as
                True except in special situations which require doing
                the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            Signature: The signature corresponding to message.
        """
        # Some BTC things want to have the recovery id to extract the public
        # key, so we should figure that out.
        sig_pt, rec_id = self.raw_sign(message, do_hash)

        return Signature(sig_pt.x, sig_pt.y, rec_id)

    def sign_bitcoin(self, message, compressed=False):
        """ Signs a message using this private key such that it
        is compatible with bitcoind, bx, and other Bitcoin
        clients/nodes/utilities.

        Note:
            0x18 + b\"Bitcoin Signed Message:" + newline + len(message) is
            prepended to the message before signing.

        Args:
            message (bytes or str): Message to be signed.
            compressed (bool): True if the corresponding public key will be
              used in compressed format. False if the uncompressed version
              is used.

        Returns:
            bytes: A Base64-encoded byte string of the signed message.
            The first byte of the encoded message contains information
            about how to recover the public key. In bitcoind parlance,
            this is the magic number containing the recovery ID and
            whether or not the key was compressed or not.
        """
        if isinstance(message, str):
            msg_in = bytes(message, 'ascii')
        elif isinstance(message, bytes):
            msg_in = message
        else:
            raise TypeError("message must be either str or bytes!")

        msg = b"\x18Bitcoin Signed Message:\n" + bytes([len(msg_in)]) + msg_in
        msg_hash = hashlib.sha256(msg).digest()

        sig = self.sign(msg_hash)
        comp_adder = 4 if compressed else 0
        magic = 27 + sig.recovery_id + comp_adder

        return base64.b64encode(bytes([magic]) + bytes(sig))

    def export_to_wif(self, compressed=False):
        """Export a key to WIF.

        :param compressed: False if you want a standard WIF export (the most
            standard option). True if you want the compressed form (Note that
            not all clients will accept this form). Defaults to None, which
            in turn uses the self.compressed attribute.
        :type compressed: bool

        See https://en.bitcoin.it/wiki/Wallet_import_format for a full
        description.
        """
        # Add the network byte, creating the "extended key"
        extended_key_hex = self.get_extended_key(self.network)
        # BIP32 wallets have a trailing \01 byte
        extended_key_bytes = binascii.unhexlify(extended_key_hex)
        if compressed:
            extended_key_bytes += b'\01'
        # And return the base58-encoded result with a checksum
        return b58encode_check(extended_key_bytes)

    @classmethod
    def from_wif(cls, wif, network=BitcoinMainNet):
        """Import a key in WIF format.

        WIF is Wallet Import Format. It is a base58 encoded checksummed key.
        See https://en.bitcoin.it/wiki/Wallet_import_format for a full
        description.

        This supports compressed WIFs - see this for an explanation:
        https://bitcoin.stackexchange.com/q/7299/112589  # nopep8
        (specifically http://bitcoin.stackexchange.com/a/7958)
        """
        # Decode the base58 string and ensure the checksum is valid
        wif = ensure_str(wif)
        try:
            extended_key_bytes = b58decode_check(wif)
        except ValueError as e:
            # Invalid checksum!
            raise ChecksumException(e) from e

        # Verify we're on the right network
        network_bytes = extended_key_bytes[0]
        # py3k interprets network_byte as an int already
        if not isinstance(network_bytes, six.integer_types):
            network_bytes = ord(network_bytes)
        if network_bytes != network.SECRET_KEY:
            raise incompatible_network_exception_factory(
                network_name=network.NAME,
                expected_prefix=network.SECRET_KEY,
                given_prefix=network_bytes)

        # Drop the network bytes
        extended_key_bytes = extended_key_bytes[1:]

        # Check for comprssed public key
        # This only affects the way in which addresses are generated.
        #compressed = False
        #if len(extended_key_bytes) == 33:
        #    # We are supposed to use compressed form!
        #    extended_key_bytes = extended_key_bytes[:-1]

        # And we should finally have a valid key
        return cls(long_or_int(hexlify(extended_key_bytes), 16))

    def to_b58check(self, network=BitcoinMainNet):
        """ Generates a Base58Check encoding of this private key."""
        version = network.SECRET_KEY
        return b58encode_check(bytes([version]) + bytes(self))

    def get_extended_key(self, network):
        """Get the extended key.

        Extended keys contain the network bytes and the public or private
        key.
        """
        network_hex_chars = binascii.hexlify(
            chr_py2(network.SECRET_KEY))
        return ensure_bytes(network_hex_chars) + ensure_bytes(self.to_hex())

    def __bytes__(self):
        return self.key.to_bytes(32, 'big')

    def __int__(self):
        return self.key


class PublicKey(PublicKeyBase):
    """ Encapsulation of a Bitcoin ECDSA public key.

    This class provides a high-level API to using an ECDSA public
    key, specifically for Bitcoin (secp256k1) purposes.

    Args:
        x (int): The x component of the public key point.
        y (int): The y component of the public key point.

    Returns:
        PublicKey: The object representing the public key.
    """

    @staticmethod
    def from_point(p):
        """ Generates a public key object from any object
        containing x, y coordinates.

        Args:
            p (Point): An object containing a two-dimensional, affine
               representation of a point on the secp256k1 curve.

        Returns:
            PublicKey: A PublicKey object.
        """
        return PublicKey(p.x, p.y)

    @staticmethod
    def from_int(i):
        """ Generates a public key object from an integer.

        Note:
            This assumes that the upper 32 bytes of the integer
            are the x component of the public key point and the
            lower 32 bytes are the y component.

        Args:
            i (Bignum): A 512-bit integer representing the public
               key point on the secp256k1 curve.

        Returns:
            PublicKey: A PublicKey object.
        """
        point = ECPointAffine.from_int(bitcoin_curve, i)
        return PublicKey.from_point(point)

    @staticmethod
    def from_base64(b64str):
        """ Generates a public key object from a Base64 encoded string.

        Args:
            b64str (str): A Base64-encoded string.
        
        Returns:
            PublicKey: A PublicKey object.
        """
        return PublicKey.from_bytes(base64.b64decode(b64str))

    @staticmethod
    def from_bytes(key_bytes):
        """ Generates a public key object from a byte (or hex) string.

        The byte stream must be of the SEC variety
        (http://www.secg.org/): beginning with a single byte telling
        what key representation follows. A full, uncompressed key
        is represented by: 0x04 followed by 64 bytes containing
        the x and y components of the point. For compressed keys
        with an even y component, 0x02 is followed by 32 bytes
        containing the x component. For compressed keys with an
        odd y component, 0x03 is followed by 32 bytes containing
        the x component.

        Args:
            key_bytes (bytes or str): A byte stream that conforms to the above.

        Returns:
            PublicKey: A PublicKey object.
        """
        b = get_bytes(key_bytes)
        key_bytes_len = len(b)

        key_type = b[0]
        if key_type == 0x04:
            # Uncompressed
            if key_bytes_len != 65:
                raise ValueError("key_bytes must be exactly 65 bytes long when uncompressed.")

            x = int.from_bytes(b[1:33], 'big')
            y = int.from_bytes(b[33:65], 'big')
        elif key_type == 0x02 or key_type == 0x03:
            if key_bytes_len != 33:
                raise ValueError("key_bytes must be exactly 33 bytes long when compressed.")

            x = int.from_bytes(b[1:33], 'big')
            ys = bitcoin_curve.y_from_x(x)

            # Pick the one that corresponds to key_type
            last_bit = key_type - 0x2
            for y in ys:
                if y & 0x1 == last_bit:
                    break
        else:
            return None

        return PublicKey(x, y)

    @staticmethod
    def from_hex(h):
        """ Generates a public key object from a hex-encoded string.

        See from_bytes() for requirements of the hex string.

        Args:
            h (str): A hex-encoded string.

        Returns:
            PublicKey: A PublicKey object.
        """
        return PublicKey.from_bytes(h)

    @staticmethod
    def from_signature(message, signature):
        """ Attempts to create PublicKey object by deriving it
        from the message and signature.

        Args:
            message (bytes): The message to be verified.
            signature (Signature): The signature for message.
               The recovery_id must not be None!

        Returns:
            PublicKey:
                A PublicKey object derived from the
                signature, it it exists. None otherwise.
        """
        if signature.recovery_id is None:
            raise ValueError("The signature must have a recovery_id.")

        msg = get_bytes(message)
        pub_keys = bitcoin_curve.recover_public_key(msg,
                                                    signature,
                                                    signature.recovery_id)

        for k, recid in pub_keys:
            if signature.recovery_id is not None and recid == signature.recovery_id:
                return PublicKey(k.x, k.y)

        return None

    @staticmethod
    def verify_bitcoin(message, signature, address):
        """ Verifies a message signed using PrivateKey.sign_bitcoin()
        or any of the bitcoin utils (e.g. bitcoin-cli, bx, etc.)

        Args:
            message(bytes): The message that the signature corresponds to.
            signature (bytes or str): A Base64 encoded signature
            address (str): Base58Check encoded address.

        Returns:
            bool: True if the signature verified properly, False otherwise.
        """
        magic_sig = base64.b64decode(signature)

        magic = magic_sig[0]
        sig = Signature.from_bytes(magic_sig[1:])
        sig.recovery_id = (magic - 27) & 0x3
        compressed = ((magic - 27) & 0x4) != 0

        # Build the message that was signed
        msg = b"\x18Bitcoin Signed Message:\n" + bytes([len(message)]) + message
        msg_hash = hashlib.sha256(msg).digest()

        derived_public_key = PublicKey.from_signature(msg_hash, sig)
        if derived_public_key is None:
            raise ValueError("Could not recover public key from the provided signature.")

        _, h160 = address_to_key_hash(address)
        hash160 = derived_public_key.hash160(compressed)
        if hash160 != h160:
            return False

        return derived_public_key.verify(msg_hash, sig)

    def __init__(self, x, y, network=BitcoinMainNet):
        p = ECPointAffine(bitcoin_curve, x, y)
        if not bitcoin_curve.is_on_curve(p):
            raise ValueError("The provided (x, y) are not on the secp256k1 curve.")

        self.point = p
        self.network = network

        # RIPEMD-160 of SHA-256
        self.ripe = ripemd160(hashlib.sha256(bytes(self)).digest())
        self.ripe_compressed = ripemd160(hashlib.sha256(bytes(self.compressed_bytes)).digest())

        self.keccak = sha3(bytes(self)[1:])

    def to_compressed_hex(self):
        """Return the compressed public key in hexadecimal
        """
        return binascii.hexlify(self.compressed_bytes).decode()

    def to_public_pair(self):
        """ Return the public key points as a PublicPair.
        """
        return PublicPair(self.point.x, self.point.y)

    def to_point(self):
        """ Alias for `to_public_pair`.
        """
        return self.to_public_pair()

    def hash160(self, compressed=True):
        """ Return the RIPEMD-160 hash of the SHA-256 hash of the
        public key.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.
        Returns:
            bytes: RIPEMD-160 byte string.
        """
        return self.ripe_compressed if compressed else self.ripe

    def base58_address(self, compressed=True):
        """ Address property that returns a base58 encoding of the public key.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.

        Returns:
            bytes: Address encoded in Base58Check.
        """
        if not self.network or not self.network.ADDRESS_MODE:
            raise TypeError("Invalid network parameter")
        elif "BASE58" not in self.network.ADDRESS_MODE:
            raise TypeError("Base58 addresses are not supported for this network")

        # Put the version byte in front, 0x00 for Mainnet, 0x6F for testnet
        version = bytes([self.network.PUBKEY_ADDRESS])
        return b58encode_check(version + self.hash160(compressed))


    def bech32_address(self, compressed=True, witness_version=0):
        """ Address property that returns a bech32 encoding of the public key.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used. It is recommended to leave this value as true - Uncompressed segwit
               addresses are non-standard on most networks, preventing them from being broadcasted
               normally, and should be avoided.
            witness_version (int): Witness version to use for theBech32 address.
                Allowed values are 0 (segwit) and 1 (Taproot).

        Returns:
            bytes: Address encoded in Bech32.
        """

        if not self.network or not self.network.ADDRESS_MODE:
            raise TypeError("Invalid network parameter")
        elif "BECH32" not in self.network.ADDRESS_MODE:
            raise TypeError("Bech32 addresses are not supported for this network")

        if not self.network.BECH32_PREFIX:
            raise ValueError("Network does not support Bech32")
        return bech32_encode(self.network.BECH32_PREFIX, witness_version, self.hash160(compressed))


    def hex_address(self):
        """ Address property that returns a hexadecimal encoding of the public key. """

        if not self.network or not self.network.ADDRESS_MODE:
            raise TypeError("Invalid network parameter")
        elif "HEX" not in self.network.ADDRESS_MODE:
            raise TypeError("HExadecimal addresses are not supported for this network")

        version = '0x'
        return version + binascii.hexlify(self.keccak[12:]).decode('ascii')


    def address(self, compressed=True, witness_version=0):
        """Returns the address genereated according to the first supported address format by the network."""
        if self.network.ADDRESS_MODE[0] == "BASE58":
            return self.base58_address(compressed)
        elif self.network.ADDRESS_MODE[0] == "BECH32":
            return self.bech32_address(compressed, witness_version)
        elif self.network.ADDRESS_MODE[0] == "HEX":
            return self.hex_address()
        else:
            raise TypeError("Network does not support any addres type")

    def verify(self, message, signature, do_hash=True):
        """ Verifies that message was appropriately signed.

        Args:
            message (bytes): The message to be verified.
            signature (Signature): A signature object.
            do_hash (bool): True if the message should be hashed prior
              to signing, False if not. This should always be left as
              True except in special situations which require doing
              the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            verified (bool): True if the signature is verified, False
            otherwise.
        """
        msg = get_bytes(message)
        return bitcoin_curve.verify(msg, signature, self.point, do_hash)

    def to_base64(self):
        """ Hex representation of the serialized byte stream.

        Returns:
            b (str): A Base64-encoded string.
        """
        return base64.b64encode(bytes(self))

    def __int__(self):
        mask = 2 ** 256 - 1
        return ((self.point.x & mask) << bitcoin_curve.nlen) | (self.point.y & mask)

    def __bytes__(self):
        return bytes(self.point)

    @property
    def compressed_bytes(self):
        """ Byte string corresponding to a compressed representation
        of this public key.

        Returns:
            b (bytes): A 33-byte long byte string.
        """
        return self.point.compressed_bytes

    def get_key(self, compressed=False):
        """ Returns the compressed or uncompressed public key in bytes, accordingly.

        Args:
            compressed (bool): Whether to compress the key

        Returns:
            b (bytes): a 33-byte of 65-byte long byte string.
        """
        if compressed:
            return self.compressed_bytes
        else:
            return bytes(self)


class Signature(object):
    """ Encapsulation of a ECDSA signature for Bitcoin purposes.

    Args:
        r (Bignum): r component of the signature.
        s (Bignum): s component of the signature.
        recovery_id (int) (Optional): Must be between 0 and 3 specifying
           which of the public keys generated by the algorithm specified
           in http://www.secg.org/sec1-v2.pdf Section 4.1.6 (Public Key
           Recovery Operation) is the correct one for this signature.

    Returns:
        sig (Signature): A Signature object.
    """

    @staticmethod
    def from_der(der):
        """ Decodes a Signature that was DER-encoded.

        Args:
            der (bytes or str): The DER encoding to be decoded.

        Returns:
            Signature: The deserialized signature.
        """
        d = get_bytes(der)
        # d must conform to (from btcd):
        # [0 ] 0x30      - ASN.1 identifier for sequence
        # [1 ] <1-byte>  - total remaining length
        # [2 ] 0x02      - ASN.1 identifier to specify an integer follows
        # [3 ] <1-byte>  - length of R
        # [4.] <bytes>   - R
        # [..] 0x02      - ASN.1 identifier to specify an integer follows
        # [..] <1-byte>  - length of S
        # [..] <bytes>   - S

        # 6 bytes + R (min. 1 byte) + S (min. 1 byte)
        if len(d) < 8:
            raise ValueError("DER signature string is too short.")
        # 6 bytes + R (max. 33 bytes) + S (max. 33 bytes)
        if len(d) > 72:
            raise ValueError("DER signature string is too long.")
        if d[0] != 0x30:
            raise ValueError("DER signature does not start with 0x30.")
        if d[1] != len(d[2:]):
            raise ValueError("DER signature length incorrect.")

        total_length = d[1]

        if d[2] != 0x02:
            raise ValueError("DER signature no 1st int marker.")
        if d[3] <= 0 or d[3] > (total_length - 7):
            raise ValueError("DER signature incorrect R length.")

        # Grab R, check for errors
        rlen = d[3]
        s_magic_index = 4 + rlen
        rb = d[4:s_magic_index]

        if rb[0] & 0x80 != 0:
            raise ValueError("DER signature R is negative.")
        if len(rb) > 1 and rb[0] == 0 and rb[1] & 0x80 != 0x80:
            raise ValueError("DER signature R is excessively padded.")

        r = int.from_bytes(rb, 'big')

        # Grab S, check for errors
        if d[s_magic_index] != 0x02:
            raise ValueError("DER signature no 2nd int marker.")
        slen_index = s_magic_index + 1
        slen = d[slen_index]
        if slen <= 0 or slen > len(d) - (slen_index + 1):
            raise ValueError("DER signature incorrect S length.")

        sb = d[slen_index + 1:]

        if sb[0] & 0x80 != 0:
            raise ValueError("DER signature S is negative.")
        if len(sb) > 1 and sb[0] == 0 and sb[1] & 0x80 != 0x80:
            raise ValueError("DER signature S is excessively padded.")

        s = int.from_bytes(sb, 'big')

        if r < 1 or r >= bitcoin_curve.n:
            raise ValueError("DER signature R is not between 1 and N - 1.")
        if s < 1 or s >= bitcoin_curve.n:
            raise ValueError("DER signature S is not between 1 and N - 1.")

        return Signature(r, s)

    @staticmethod
    def from_base64(b64str):
        """ Generates a signature object from a Base64 encoded string.

        Args:
            b64str (str): A Base64-encoded string.

        Returns:
            Signature: A Signature object.
        """
        return Signature.from_bytes(base64.b64decode(b64str))

    @staticmethod
    def from_bytes(b):
        """ Extracts the r and s components from a byte string.

        Args:
            b (bytes): A 64-byte long string. The first 32 bytes are
               extracted as the r component and the second 32 bytes
               are extracted as the s component.

        Returns:
            Signature: A Signature object.

        Raises:
            ValueError: If signature is incorrect length
        """
        if len(b) != 64:
            raise ValueError("from_bytes: Signature length != 64.")
        r = int.from_bytes(b[0:32], 'big')
        s = int.from_bytes(b[32:64], 'big')
        return Signature(r, s)

    @staticmethod
    def from_hex(h):
        """ Extracts the r and s components from a hex-encoded string.

        Args:
            h (str): A 64-byte (128 character) long string. The first
               32 bytes are extracted as the r component and the
               second 32 bytes are extracted as the s component.

        Returns:
            Signature: A Signature object.
        """
        return Signature.from_bytes(bytes.fromhex(h))

    def __init__(self, r, s, recovery_id=None):
        self.r = r
        self.s = s
        self.recovery_id = recovery_id

    @property
    def x(self):
        """ Convenience property for any method that requires
            this object to provide a Point interface.
        """
        return self.r

    @property
    def y(self):
        """ Convenience property for any method that requires
            this object to provide a Point interface.
        """
        return self.s

    def _canonicalize(self):
        # Compute minimum bytes to represent integer
        bl = math.ceil(self.r.bit_length() / 8)
        # Make sure it's at least one byte in length
        if bl == 0:
            bl += 1
        r_bytes = self.r.to_bytes(bl, 'big')

        # make sure there's no way it could be interpreted
        # as a negative integer
        if r_bytes[0] & 0x80:
            r_bytes = bytes([0]) + r_bytes

        # Compute minimum bytes to represent integer
        bl = math.ceil(self.s.bit_length() / 8)
        # Make sure it's at least one byte in length
        if bl == 0:
            bl += 1
        s_bytes = self.s.to_bytes(bl, 'big')

        # make sure there's no way it could be interpreted
        # as a negative integer
        if s_bytes[0] & 0x80:
            s_bytes = bytes([0]) + s_bytes

        return (r_bytes, s_bytes)

    def to_der(self):
        """ Encodes this signature using DER

        Returns:
            bytes: The DER encoding of (self.r, self.s).
        """
        # Output should be:
        # 0x30 <length> 0x02 <length r> r 0x02 <length s> s
        r, s = self._canonicalize()

        total_length = 6 + len(r) + len(s)
        der = bytes([0x30, total_length - 2, 0x02, len(r)]) + r + bytes([0x02, len(s)]) + s
        return der

    def to_hex(self):
        """ Hex representation of the serialized byte stream.

        Returns:
            str: A hex-encoded string.
        """
        return bytes_to_str(bytes(self))

    def to_base64(self):
        """ Hex representation of the serialized byte stream.

        Returns:
            str: A Base64-encoded string.
        """
        return base64.b64encode(bytes(self))

    def __bytes__(self):
        nbytes = math.ceil(bitcoin_curve.nlen / 8)
        return self.r.to_bytes(nbytes, 'big') + self.s.to_bytes(nbytes, 'big')


class HDKey(object):
    """ Base class for HDPrivateKey and HDPublicKey.

    Args:
        key (PrivateKey or PublicKey): The underlying simple private or
           public key that is used to sign/verify.
        chain_code (bytes): The chain code associated with the HD key.
        depth (int): How many levels below the master node this key is. By
           definition, depth = 0 for the master node.
        index (int): A value between 0 and 0xffffffff indicating the child
           number. Values >= 0x80000000 are considered hardened children.
        parent_fingerprint (bytes): The fingerprint of the parent node. This
           is 0x00000000 for the master node.
        :param network: The network to use for things like defining key
            key paths and supported address formats. Defaults to Bitcoin mainnet.

    Returns:
        HDKey: An HDKey object.
    """
    @staticmethod
    def from_b58check(key):
        """ Decodes a Base58Check encoded key.

        The encoding must conform to the description in:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#serialization-format

        Args:
            key (str): A Base58Check encoded key.

        Returns:
            HDPrivateKey or HDPublicKey:
                Either an HD private or
                public key object, depending on what was serialized.
        """
        return HDKey.from_bytes(b58decode_check(key))

    @staticmethod
    def from_bytes(b, network=BitcoinMainNet):
        """ Generates either a HDPrivateKey or HDPublicKey from the underlying
        bytes.

        The serialization must conform to the description in:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#serialization-format

        Args:
            b (bytes): A byte stream conforming to the above.

        Returns:
            HDPrivateKey or HDPublicKey:
                Either an HD private or
                public key object, depending on what was serialized.
        """
        if len(b) < 78:
            raise ValueError("b must be at least 78 bytes long.")

        version = int.from_bytes(b[:4], 'big')
        depth = b[4]
        parent_fingerprint = b[5:9]
        index = int.from_bytes(b[9:13], 'big')
        chain_code = b[13:45]
        key_bytes = b[45:78]

        rv = None
        if version == network.EXT_PRIVATE_KEY or version == network.EXT_SEGWIT_PRIVATE_KEY:
            if key_bytes[0] != 0:
                raise ValueError("First byte of private key must be 0x00!")

            private_key = int.from_bytes(key_bytes[1:], 'big')
            rv = HDPrivateKey(key=private_key,
                              chain_code=chain_code,
                              index=index,
                              depth=depth,
                              parent_fingerprint=parent_fingerprint)
        elif version == network.EXT_PUBLIC_KEY or version == network.EXT_SEGWIT_PUBLIC_KEY:
            if key_bytes[0] != 0x02 and key_bytes[0] != 0x03:
                raise ValueError("First byte of public key must be 0x02 or 0x03!")

            public_key = PublicKey.from_bytes(key_bytes)
            rv = HDPublicKey(x=public_key.point.x,
                             y=public_key.point.y,
                             chain_code=chain_code,
                             index=index,
                             depth=depth,
                             parent_fingerprint=parent_fingerprint)
        else:
            raise ValueError("Provided private key does not match any of the network's extended version bytes")

        return rv

    @staticmethod
    def from_hex(h):
        """ Generates either a HDPrivateKey or HDPublicKey from the underlying
        hex-encoded string.

        The serialization must conform to the description in:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#serialization-format

        Args:
            h (str): A hex-encoded string conforming to the above.

        Returns:
            HDPrivateKey or HDPublicKey:
                Either an HD private or
                public key object, depending on what was serialized.
        """
        return HDKey.from_bytes(bytes.fromhex(h))

    @staticmethod
    def from_path(root_key, path):
        p = HDKey.parse_path(path)

        if p[0] == "m":
            if root_key.master:
                p = p[1:]
            else:
                raise ValueError("root_key must be a master key if 'm' is the first element of the path.")

        keys = [root_key]
        for i in p:
            if isinstance(i, str):
                hardened = i[-1] == "'"
                index = int(i[:-1], 0) | 0x80000000 if hardened else int(i, 0)
            else:
                index = i
            k = keys[-1]
            klass = k.__class__
            keys.append(klass.from_parent(k, index))

        return keys

    @staticmethod
    def parse_path(path):
        if isinstance(path, str):
            # Remove trailing "/"
            p = path.rstrip("/").split("/")
        elif isinstance(path, bytes):
            p = path.decode('utf-8').rstrip("/").split("/")
        else:
            p = list(path)

        return p

    @staticmethod
    def path_from_indices(l):
        p = []
        for n in l:
            if n == "m":
                p.append(n)
            else:
                if n & 0x80000000:
                    _n = n & 0x7fffffff
                    p.append(str(_n) + "'")
                else:
                    p.append(str(n))

        return "/".join(p)

    def __init__(self, key, chain_code, index, depth, parent_fingerprint, network):
        if index < 0 or index > 0xffffffff:
            raise ValueError("index is out of range: 0 <= index <= 2**32 - 1")

        if not isinstance(chain_code, bytes):
            raise TypeError("chain_code must be bytes")

        self._key = key
        self.chain_code = chain_code
        self.depth = depth
        self.index = index

        self.parent_fingerprint = get_bytes(parent_fingerprint)
        self.network = network

    @property
    def keydata(self):
        """
        Returns the public key object.
        """
        return self._key

    @property
    def master(self):
        """ Whether or not this is a master node.

        Returns:
            bool: True if this is a master node, False otherwise.
        """
        return self.depth == 0

    @property
    def hardened(self):
        """ Whether or not this is a hardened node.

        Hardened nodes are those with indices >= 0x80000000.

        Returns:
            bool: True if this is hardened, False otherwise.
        """
        # A hardened key is a key with index >= 2 ** 31, so
        # we check that the MSB of a uint32 is set.
        return self.index & 0x80000000

    @property
    def identifier(self):
        """ Returns the identifier for the key.

        A key's identifier and fingerprint are defined as:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#key-identifiers

        Returns:
            bytes: A 20-byte RIPEMD-160 hash.
        """
        raise NotImplementedError

    @property
    def fingerprint(self):
        """ Returns the key's fingerprint, which is the first 4 bytes
        of its identifier.

        A key's identifier and fingerprint are defined as:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#key-identifiers

        Returns:
            bytes: The first 4 bytes of the RIPEMD-160 hash.
        """
        return self.identifier[:4]

    def to_b58check(self):
        """ Generates a Base58Check encoding of this key.

        Returns:
            str: A Base58Check encoded string representing the key.
        """
        b = self.serialize()
        return b58encode_check(b)

    def segwit_serialize(self, private=True):
        """Returns the extended public or private key for Segwit addresses."""
        if self.network.BIP32_SEGWIT_PATH:
            if private:
                version = self.network.EXT_SEGWIT_PRIVATE_KEY
            else:
                version = self.network.EXT_SEGWIT_PUBLIC_KEY
        else:
            raise ValueError("Segwit P2WPKH is not supported for this network.")

        key_bytes = self._key.compressed_bytes if isinstance(self, HDPublicKey) else b'\x00' + bytes(self._key)
        return (version.to_bytes(length=4, byteorder='big') +
                bytes([self.depth]) +
                self.parent_fingerprint +
                self.index.to_bytes(length=4, byteorder='big') +
                self.chain_code +
                key_bytes)

    def serialize(self, private=True):
        """Returns the extended public or private key for legacy addresses."""
        if private:
            version = self.network.EXT_PRIVATE_KEY
        else:
            version = self.network.EXT_PUBLIC_KEY

        key_bytes = self._key.compressed_bytes if isinstance(self, HDPublicKey) else b'\x00' + bytes(self._key)
        return (version.to_bytes(length=4, byteorder='big') +
                bytes([self.depth]) +
                self.parent_fingerprint +
                self.index.to_bytes(length=4, byteorder='big') +
                self.chain_code +
                key_bytes)

    def __bytes__(self):
        return self.serialize()


class HDPrivateKey(HDKey, PrivateKeyBase):
    """ Implements an HD Private Key according to BIP-0032:
    https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki

    For the vast majority of use cases, the 3 static functions
    (HDPrivateKey.master_key_from_entropy,
    HDPrivateKey.master_key_from_seed and
    HDPrivateKey.from_parent) will be used rather than directly
    constructing an object.

    Args:
        key (PrivateKey or PublicKey): The underlying simple private or
           public key that is used to sign/verify.
        chain_code (bytes): The chain code associated with the HD key.
        depth (int): How many levels below the master node this key is. By
           definition, depth = 0 for the master node.
        index (int): A value between 0 and 0xffffffff indicating the child
           number. Values >= 0x80000000 are considered hardened children.
        parent_fingerprint (bytes): The fingerprint of the parent node. This
           is 0x00000000 for the master node.

    Returns:
        HDKey: An HDKey object.

    """

    @staticmethod
    def master_key_from_mnemonic(mnemonic, passphrase='', network=BitcoinMainNet):
        """ Generates a master key from a mnemonic.

        Args:
            :param mnemonic (str): The mnemonic sentence representing
               the seed from which to generate the master key.
            :param passphrase (str): Password if one was used.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            HDPrivateKey: the master private key.
        """
        return HDPrivateKey.master_key_from_seed(
            Mnemonic.to_seed(mnemonic, passphrase), network=network)

    @staticmethod
    def master_key_from_entropy(passphrase='', strength=128, network=BitcoinMainNet):
        """ Generates a master key from system entropy.

        Args:
            :param strength (int): Amount of entropy desired, in bits.
                This should be a multiple of 32 between 128 and 256.
                It directly affects the length of the mnemonic exported
                (each additional 32 bits adds an extra three words at the end).
            passphrase (str): An optional passphrase for the generated
               mnemonic string.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            HDPrivateKey, str:
                a tuple consisting of the master
                private key and a mnemonic string from which the seed
                can be recovered.
        """
        if strength % 32 != 0:
            raise ValueError("strength must be a multiple of 32")
        if strength < 128 or strength > 256:
            raise ValueError("strength should be >= 128 and <= 256")
        entropy = rand_bytes(strength // 8)
        m = Mnemonic(language='english')
        n = m.to_mnemonic(entropy)
        return HDPrivateKey.master_key_from_seed(
            Mnemonic.to_seed(n, passphrase), network=network), n

    @staticmethod
    def master_key_from_seed(seed, network=BitcoinMainNet):
        """ Generates a master key from a provided seed.

        Args:
            :param seed (bytes or str): a string of bytes or a hex string
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            HDPrivateKey: the master private key.
        """
        seed_bytes = get_bytes(seed)
        I = hmac.new(b"Bitcoin seed", seed_bytes, hashlib.sha512).digest()
        Il, Ir = I[:32], I[32:]
        parse_Il = int.from_bytes(Il, 'big')
        if parse_Il == 0 or parse_Il >= bitcoin_curve.n:
            raise ValueError("Bad seed, resulting in invalid key!")

        return HDPrivateKey(key=parse_Il, chain_code=Ir, index=0, depth=0, network=network)

    @staticmethod
    def from_parent(parent_key, i):
        """ Derives a child private key from a parent
        private key. It is not possible to derive a child
        private key from a public parent key.

        Args:
            parent_private_key (HDPrivateKey):
        """
        if not isinstance(parent_key, HDPrivateKey):
            raise TypeError("parent_key must be an HDPrivateKey object.")

        hmac_key = parent_key.chain_code
        if i & 0x80000000:
            hmac_data = b'\x00' + bytes(parent_key.keydata()) + i.to_bytes(length=4, byteorder='big')
        else:
            hmac_data = parent_key.public_key.compressed_bytes + i.to_bytes(length=4, byteorder='big')

        I = hmac.new(hmac_key, hmac_data, hashlib.sha512).digest()
        Il, Ir = I[:32], I[32:]

        parse_Il = int.from_bytes(Il, 'big')
        if parse_Il >= bitcoin_curve.n:
            return None

        child_key = (parse_Il + parent_key.keydata().key) % bitcoin_curve.n
        if child_key == 0:
            # Incredibly unlucky choice
            raise ValueError("Child with index {i} causes a private key at zero, choose another one.")

        child_depth = parent_key.depth + 1
        return HDPrivateKey(key=child_key,
                            chain_code=Ir,
                            index=i,
                            depth=child_depth,
                            parent_fingerprint=parent_key.fingerprint,
                            network=parent_key.network)

    def __init__(self, key, chain_code, index, depth,
                 parent_fingerprint=b'\x00\x00\x00\x00', network=BitcoinMainNet):
        if index < 0 or index > 0xffffffff:
            raise ValueError("index is out of range: 0 <= index <= 2**32 - 1")

        private_key = PrivateKey(key)
        PrivateKeyBase.__init__(self, key)
        HDKey.__init__(self, private_key, chain_code, index, depth,
                       parent_fingerprint, network)
        self._public_key = None

    @property
    def public_key(self):
        """ Returns the public key associated with this private key.

        Returns:
            HDPublicKey:
                The HDPublicKey object that corresponds to this
                private key.
        """
        if self._public_key is None:
            self._public_key = HDPublicKey(x=self._key.public_key.point.x,
                                           y=self._key.public_key.point.y,
                                           chain_code=self.chain_code,
                                           index=self.index,
                                           depth=self.depth,
                                           parent_fingerprint=self.parent_fingerprint,
                                           network=self.network)

        return self._public_key

    def raw_sign(self, message, do_hash=True):
        """ Signs message using the underlying non-extended private key.

        Args:
            message (bytes): The message to be signed. If a string is
                provided it is assumed the encoding is 'ascii' and
                converted to bytes. If this is not the case, it is up
                to the caller to convert the string to bytes
                appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
                to signing, False if not. This should always be left as
                True except in special situations which require doing
                the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            ECPointAffine:
                a raw point (r = pt.x, s = pt.y) which is
                the signature.
        """
        return self._key.raw_sign(message, do_hash)

    def sign(self, message, do_hash=True):
        """ Signs message using the underlying non-extended private key.

        Note:
            This differs from `raw_sign()` since it returns a Signature object.

        Args:
            message (bytes or str): The message to be signed. If a
                string is provided it is assumed the encoding is
                'ascii' and converted to bytes. If this is not the
                case, it is up to the caller to convert the string to
                bytes appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
                to signing, False if not. This should always be left as
                True except in special situations which require doing
                the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            Signature: The signature corresponding to message.
        """
        return self._key.sign(message, do_hash)

    def sign_bitcoin(self, message, compressed=False):
        """ Signs a message using the underlying non-extended private
        key such that it is compatible with bitcoind, bx, and other
        Bitcoin clients/nodes/utilities.

        Note:
            0x18 + b\"Bitcoin Signed Message:" + newline + len(message) is
            prepended to the message before signing.

        Args:
            message (bytes or str): Message to be signed.
            compressed (bool):
                True if the corresponding public key will be
                used in compressed format. False if the uncompressed version
                is used.

        Returns:
            bytes: A Base64-encoded byte string of the signed message.
            The first byte of the encoded message contains information
            about how to recover the public key. In bitcoind parlance,
            this is the magic number containing the recovery ID and
            whether or not the key was compressed or not. (This function
            always processes full, uncompressed public-keys, so the
            magic number will always be either 27 or 28).
        """

        return self._key.sign_bitcoin(message, compressed)

    @property
    def identifier(self):
        """ Returns the identifier for the key.

        A key's identifier and fingerprint are defined as:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#key-identifiers

        In this case, it will return the RIPEMD-160 hash of the
        corresponding public key.

        Returns:
            bytes: A 20-byte RIPEMD-160 hash.
        """
        return self.public_key.hash160()

    def __int__(self):
        return int(self.key)


class HDPublicKey(HDKey, PublicKeyBase):
    """ Implements an HD Public Key according to BIP-0032:
    https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki

    For the vast majority of use cases, the static function
    HDPublicKey.from_parent() will be used rather than directly
    constructing an object.

    Args:
        x (int): x component of the point representing the public key.
        y (int): y component of the point representing the public key.
        chain_code (bytes): The chain code associated with the HD key.
        depth (int): How many levels below the master node this key is. By
           definition, depth = 0 for the master node.
        index (int): A value between 0 and 0xffffffff indicating the child
           number. Values >= 0x80000000 are considered hardened children.
        parent_fingerprint (bytes): The fingerprint of the parent node. This
           is 0x00000000 for the master node.

    Returns:
        HDPublicKey: An HDPublicKey object.

    """

    @staticmethod
    def from_parent(parent_key, i):
        """
        Derives a child HD private key at the particular index.

        Args:
            parent_key (HDPrivateKey): The parent key to derive a child key from
            i (int): The index for deriving the child key
        
        Returns:
            HDPrivateKey: an extended private key child.
        """
        if isinstance(parent_key, HDPrivateKey):
            # Get child private key
            return HDPrivateKey.from_parent(parent_key, i).public_key
        elif isinstance(parent_key, HDPublicKey):
            if i & 0x80000000:
                raise ValueError("Can't generate a hardened child key from a parent public key.")
            else:
                I = hmac.new(parent_key.chain_code,
                             parent_key.compressed_bytes + i.to_bytes(length=4, byteorder='big'),
                             hashlib.sha512).digest()
                Il, Ir = I[:32], I[32:]
                parse_Il = int.from_bytes(Il, 'big')
                if parse_Il >= bitcoin_curve.n:
                    return None

                temp_priv_key = PrivateKey(parse_Il)
                Ki = temp_priv_key.public_key.point + parent_key.keydata().point
                if Ki.infinity:
                    return None

                child_depth = parent_key.depth + 1
                return HDPublicKey(x=Ki.x,
                                   y=Ki.y,
                                   chain_code=Ir,
                                   index=i,
                                   depth=child_depth,
                                   parent_fingerprint=parent_key.fingerprint,
                                   network=parent_key.network)
        else:
            raise TypeError("parent_key must be either a HDPrivateKey or HDPublicKey object")

    def __init__(self, x, y, chain_code, index, depth,
                 parent_fingerprint=b'\x00\x00\x00\x00', network=BitcoinMainNet):
        key = PublicKey(x, y)
        HDKey.__init__(self, key, chain_code, index, depth, parent_fingerprint, network)
        PublicKeyBase.__init__(self)

    @property
    def identifier(self):
        """ Returns the identifier for the key.

        A key's identifier and fingerprint are defined as:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#key-identifiers

        In this case, it will return the RIPEMD-160 hash of the
        non-extended public key.

        Returns:
            bytes: A 20-byte RIPEMD-160 hash.
        """
        return self.hash160()

    def hash160(self, compressed=True):
        """ Return the RIPEMD-160 hash of the SHA-256 hash of the
        non-extended public key.

        Note:
            This always returns the hash of the compressed version of
            the public key.

        Returns:
            bytes: RIPEMD-160 byte string.
        """
        return self._key.hash160(True)

    def base58_address(self, compressed=True):
        """ This is a wrapper around PublicKey.base58_address(). """
        return self._key.base58_address(compressed)

    def bech32_address(self, compressed=True, witness_version=0):
        """ This is a wrapper around PublicKey.bech32_address(). """
        return self._key.bech32_address(compressed, witness_version)

    def hex_address(self, compressed=True):
        """ This is a wrapper around PublicKey.hex_address(). """
        return self._key.bech32_address(compressed)

    def address(self, compressed=True, witness_version=0):
        """ This is a wrapper around PublicKey.address(). """
        return self._key.address(compressed, witness_version)

    def verify(self, message, signature, do_hash=True):
        """ Verifies that message was appropriately signed.

        Args:
            message (bytes): The message to be verified.
            signature (Signature): A signature object.
            do_hash (bool): True if the message should be hashed prior
                to signing, False if not. This should always be left as
                True except in special situations which require doing
                the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            verified (bool): True if the signature is verified, False
            otherwise.
        """
        return self._key.verify(message, signature, do_hash)

    @property
    def compressed_bytes(self):
        """ Byte string corresponding to a compressed representation
        of this public key.

        Returns:
            b (bytes): A 33-byte long byte string.
        """
        return self._key.compressed_bytes

    def __int__(self):
        return int(self._key)
