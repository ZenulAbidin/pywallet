#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Code from:
https://github.com/michailbrynard/ethereum-bip44-python

This submodule provides the PublicKey, PrivateKey, and Signature classes.
It also provides HDPublicKey and HDPrivateKey classes for working with HD
wallets."""

import base64
import binascii
import hashlib
from hashlib import sha256
import random
from collections import namedtuple

import coincurve

from .keccak import Keccak256
from .base58 import b58encode_check, b58decode_check
from .bech32 import bech32_decode, bech32_encode
from .ripemd160 import ripemd160
from .utils import ensure_bytes, ensure_str
from ..network import BitcoinSegwitMainNet
from ..errors import incompatible_network_bytes_exception_factory, ChecksumException, unsupported_feature_exception_factory


Point = namedtuple('Point', ['x', 'y'])

class secp256k1():
    """ Elliptic curve used in Bitcoin, Ethereum, and their derivatives.
    """
    P = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
    A = 0
    B = 7
    N = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
    Gx = 0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
    Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
    G = Point(Gx, Gy)
    H = 1

def decode_der_signature(signature):
    """ Returns the R and S values of a DER signature. """
    # Check if the signature is in DER format
    if signature[0] != 0x30:
        raise ValueError("Invalid DER signature format")

    # Extract the length of the signature
    length = signature[1]

    assert len(signature[2:]) == length

    # Find the start and end positions of the R component
    r_start = 4
    r_length = signature[3]
    r_end = r_start + r_length

    # Find the start and end positions of the S component
    s_start = r_end + 2
    s_length = signature[r_end + 1]
    s_end = s_start + s_length

    # Extract the R and S components as bytes
    r = signature[r_start:r_end]
    s = signature[s_start:s_end]

    return r, s


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


class PrivateKey:
    """ Encapsulation of a private key on the secp256k1 curve.

    This class provides capability to generate private keys,
    obtain the corresponding public key, sign messages and
    serialize/deserialize into a variety of formats.

    Args:
        k (int): The private key.

    Returns:
        PrivateKey: The object representing the private key.
    """

    __hash__ = object.__hash__

    @staticmethod
    def from_bytes(b, network=BitcoinSegwitMainNet):
        """ Generates PrivateKey from the underlying bytes.

        Args:
            :param b (bytes): A byte stream containing a 256-bit (32-byte) integer.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            tuple(PrivateKey, bytes): A PrivateKey object and the remainder
            of the bytes.
        """
        if len(b) < 32:
            raise ValueError('b must contain at least 32 bytes')

        ckey = coincurve.PrivateKey(b)
        return PrivateKey(ckey, network)

    @staticmethod
    def from_hex(h, network=BitcoinSegwitMainNet):
        """ Generates PrivateKey from a hex-encoded string.

        Args:
            :param h (str): A hex-encoded string containing a 256-bit
                 (32-byte) integer.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            PrivateKey: A PrivateKey object.
        """
        return PrivateKey.from_bytes(bytes.fromhex(h), network)

    @staticmethod
    def from_int(i, network=BitcoinSegwitMainNet):
        """ Initializes a private key from an integer.

        Args:
            :param i (int): Integer that is the private key.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            PrivateKey: The object representing the private key.
        """
        ckey = coincurve.PrivateKey.from_int(i)
        return PrivateKey(ckey, network)

    @staticmethod
    def from_b58check(private_key, network=BitcoinSegwitMainNet):
        """ Decodes a Base58Check encoded private-key.

        Args:
            :param private_key (str): A Base58Check encoded private key.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            PrivateKey: A PrivateKey object
        """
        b58dec = b58decode_check(private_key)
        version = b58dec[0]
        assert version == network.SECRET_KEY

        return PrivateKey.from_bytes(b58dec[1:], network)

    @staticmethod
    def from_random(network=BitcoinSegwitMainNet):
        """ Initializes a private key from a random integer.

        Args:
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            PrivateKey: The object representing the private key.
        """
        return PrivateKey.from_int(random.SystemRandom().randrange(1, secp256k1.N), network)

    @classmethod
    def from_brainwallet(cls, password, salt="zpywallet", network=BitcoinSegwitMainNet):
        """Generate a new key from a master password, and an optional salt.

        This password is hashed via a single round of sha256 and is highly
        breakable, but it's the standard brainwallet approach.

        It is highly recommended to salt a password before hashing it to protect
        it from rainbow table attacks. You should not need to change it from the
        default value, though. WARNING: Either remember the salt, and add it after
        the end of the password, or always use this method to regenerate the
        brainwallet so you don't lose your private key.

        Args:
            :param password(str): The password to generate a private key from.
            :param salt(str): The salt to use. Unless you know what you're doing,
                leave this as the default value.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            PrivateKey: The object representing the private key.
        """
        password = ensure_bytes(password) + ensure_bytes(salt)
        key = sha256(password).hexdigest()
        return PrivateKey.from_int(int(key, 16), network)

    @classmethod
    def from_wif(cls, wif, network=BitcoinSegwitMainNet):
        """Import a key in WIF format.

        WIF is Wallet Import Format. It is a base58 encoded checksummed key.
        See https://en.bitcoin.it/wiki/Wallet_import_format for a full
        description.

        This supports compressed WIFs - see this for an explanation:
        https://bitcoin.stackexchange.com/q/7299/112589 
        (specifically http://bitcoin.stackexchange.com/a/7958)

        Args:
            :param wif (str): A base58-encoded string representing a private key.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Return:
            PrivateKey: An object representing a private key.
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
        if not isinstance(network_bytes, int):
            network_bytes = ord(network_bytes)
        if network_bytes != network.SECRET_KEY:
            raise incompatible_network_bytes_exception_factory(
                network_name=network.NAME,
                expected_prefix=network.SECRET_KEY,
                given_prefix=network_bytes)

        # Drop the network bytes
        extended_key_bytes = extended_key_bytes[1:]

        # And we should finally have a valid key
        return PrivateKey.from_bytes(extended_key_bytes, network)

    def __init__(self, ckey, network=BitcoinSegwitMainNet):
        self._key = ckey
        self._public_key = PublicKey(coincurve.PublicKey.from_secret(binascii.unhexlify(ckey.to_hex())), network=network)
        self._network = network

    @property
    def network(self):
        """Returns the network for this private key."""
        return self._network

    @property
    def public_key(self):
        """ Returns the public key associated with this private key.

        Returns:
            PublicKey:
                The PublicKey object that corresponds to this
                private key.
        """
        return self._public_key

    def der_sign(self, message):
        """ Signs message using this private key. The message is encoded in UTF-8.
        
        Avoid using any non-printable characters or whitespace (except for 0x20
        space and 0x0a newline) inside the signature.

        Args:
            message (bytes): The message to be signed. If a string is
                provided it is assumed the encoding is 'ascii' and
                converted to bytes. If this is not the case, it is up
                to the caller to convert the string to bytes
                appropriately and pass in the bytes.

        Returns:
            bytes: The signature encoded in DER form.
        """
        if isinstance(message, str):
            msg = bytes(message, 'utf-8')
        elif isinstance(message, bytes):
            msg = message
        else:
            raise TypeError("message must be either str or bytes")

        return self._key.sign(msg)

    def base64_sign(self, message):
        """ Signs message using this private key. The message is encoded in UTF-8.
        
        Avoid using any non-printable characters or whitespace (except for 0x20
        space and 0x0a newline) inside the signature.

        Args:
            message (bytes): The message to be signed. If a string is
                provided it is assumed the encoding is 'ascii' and
                converted to bytes. If this is not the case, it is up
                to the caller to convert the string to bytes
                appropriately and pass in the bytes.

        Returns:
            str: The signature encoded in DER form, which is again encoded in Base64.
        """
        if isinstance(message, str):
            msg = bytes(message, 'utf-8')
        elif isinstance(message, bytes):
            msg = message
        else:
            raise TypeError("message must be either str or bytes")

        return base64.b64encode(self._key.sign(msg)).decode() # decode is to convert from bytes to str

    def rfc2440_sign(self, message):
        """ Signs message using this private key. The message is encoded in UTF-8.
        
        Avoid using any non-printable characters or whitespace (except for 0x20
        space and 0x0a newline) inside the signature.

        This function returns a signature of this form:

        -----BEGIN {{network.NAME.upper()}} SIGNED MESSAGE-----
        Message
        -----BEGIN {{network.NAME.upper()}} SIGNATURE-----
        Address
        Signature
        -----END {{network.NAME.upper()}} SIGNATURE-----

        The message is printed as a UTF-8 string, whereas the address used is the
        default address for the mainnet. Address signatures are treated as if they
        are legacy P2PKH Base58-encoded addresses, for the purpose of the Bitcoin
        message signing algorithm, which was invented before any of the other
        address types existed. This is forced by the coincurve dependency which we
        use to calculate the signature. On the upside, coincurve calculates the
        signatures in an extremely robust and secure way.

        Args:
            message (bytes): The message to be signed. If a string is
                provided it is assumed the encoding is 'ascii' and
                converted to bytes. If this is not the case, it is up
                to the caller to convert the string to bytes
                appropriately and pass in the bytes.

        Returns:
            str: A text string in the form of RFC2440, in a similar form to Electrum.
        """
        if isinstance(message, str):
            msg = bytes(message, 'utf-8')
        elif isinstance(message, bytes):
            msg = message
        else:
            raise TypeError("message must be either str or bytes")

        sig = base64.b64encode(self._key.sign(msg)).decode()
        address = self._public_key.address()
        rfc2440 = f"-----BEGIN {self.network.NAME.upper()} SIGNED MESSAGE-----\n"
        rfc2440 += message
        rfc2440 += f"-----BEGIN {self.network.NAME.upper()} SIGNATURE-----\n"
        rfc2440 += address
        rfc2440 += sig
        rfc2440 += f"-----END {self.network.NAME.upper()} SIGNATURE-----\n"
        return rfc2440


    def rsz_sign(self, message):
        """ Signs message using this private key. The message is encoded in UTF-8.

        Avoid using any non-printable characters or whitespace (except for 0x20
        space and 0x0a newline) inside the signature.

        Args:
            message (bytes): The message to be signed. If a string is
                provided it is assumed the encoding is 'ascii' and
                converted to bytes. If this is not the case, it is up
                to the caller to convert the string to bytes
                appropriately and pass in the bytes.

        Returns:
                A tuple or R, S, and Z (message hash) values.
        """
        if isinstance(message, str):
            msg = bytes(message, 'utf-8')
        elif isinstance(message, bytes):
            msg = message
        else:
            raise TypeError("message must be either str or bytes")

        der = self._key.sign(msg)
        z = sha256(msg).digest()
        r, s = decode_der_signature(der)
        r = int(binascii.hexlify(r), 16)
        s = int(binascii.hexlify(s), 16)
        z = int(binascii.hexlify(z), 16)
        return r,s,z

    def to_wif(self, compressed=False):
        """Export a key to WIF.

        Args:
            :param compressed: False if you want a standard WIF export (the most
                standard option). True if you want the compressed form (Note that
                not all clients will accept this form). Defaults to None, which
                in turn uses the self.compressed attribute.
            :type compressed: bool

        Returns:
            str: THe WIF string

        See https://en.bitcoin.it/wiki/Wallet_import_format for a full
        description.
        """

        if "BASE58" not in self.network.ADDRESS_MODE:
            raise TypeError("Key network does not support Base58")

        # Add the network byte, creating the "extended key"
        extended_key_hex = self.get_extended_key(self.network)
        # BIP32 wallets have a trailing \01 byte
        extended_key_bytes = binascii.unhexlify(extended_key_hex)
        if compressed:
            extended_key_bytes += b'\01'
        # And return the base58-encoded result with a checksum
        return b58encode_check(extended_key_bytes).decode()


    def to_hex(self):
        "Returns the private key in hexadecimal form."
        return self._key.to_hex()

    def get_extended_key(self, network):
        """Get the extended key.

        Extended keys contain the network bytes and the public or private
        key.
        """
        network_hex_chars = binascii.hexlify(
            bytes([network.SECRET_KEY]))
        return ensure_bytes(network_hex_chars) + ensure_bytes(self.to_hex())

    def __bytes__(self):
        return binascii.unhexlify(self._key.to_hex())

    def __int__(self):
        return self._key.to_int()


class PublicKey:
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
    def from_point(p, network=BitcoinSegwitMainNet):
        """ Generates a public key object from any object
        containing x, y coordinates.

        Args:
            :param p (Point): An object containing a two-dimensional, affine
               representation of a point on the secp256k1 curve.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            PublicKey: A PublicKey object.
        """
        ckey = coincurve.PublicKey.from_point(p.x, p.y)
        return PublicKey(ckey, network)

    @staticmethod
    def from_bytes(key_bytes, network=BitcoinSegwitMainNet):
        """ Generates a public key object from a byte  string.

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
            :param key_bytes (bytes): A byte stream that conforms to the above.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.


        Returns:
            PublicKey: A PublicKey object.
        """
        ckey = coincurve.PublicKey(key_bytes)
        return PublicKey(ckey, network)

    @staticmethod
    def from_hex(h, network=BitcoinSegwitMainNet):
        """ Generates a public key object from a hex-encoded string.

        See from_bytes() for requirements of the hex string.

        Args:
            :param h (str): A hex-encoded string.
            :param network: The network to use for things like defining key
                key paths and supported address formats. Defaults to Bitcoin mainnet.

        Returns:
            PublicKey: A PublicKey object.
        """
        return PublicKey.from_bytes(binascii.unhexlify(h), network)

    def verify(self, message, signature, address):
        """ Verifies a signed message.

        Args:
            message(bytes or str): The message that the signature corresponds to.
            signature (bytes or str): A string Base64 encoded signature OR a bytes DER signature.
            address (str): Base58Check encoded address.

        Returns:
            bool: True if the signature is authentic, False otherwise.
        """
        if self.address(compressed=False) != address and self.address(compressed=True) != address:
            return False

        if isinstance(message, str):
            message = message.decode('utf-8')
        if isinstance(signature, str):
            signature = base64.b64decode(signature)
        return coincurve.verify_signature(signature, message, bytes(self))

    def rfc2440_verify(self, text):
        """ Verifies a signed message in the RFC2440 format.

        Args:
            text(str): The verfication message.

        Returns:
            bool: True if the signature is authentic, False otherwise.
        """

        text_lines = text.split('\n')
        if text_lines[0] != f"-----BEGIN {self.network.NAME.upper()} SIGNED MESSAGE-----":
            raise ValueError("Invalid RFC2440 signature")
        elif text_lines[-4] != f"-----BEGIN {self.network.NAME.upper()} SIGNATURE -----":
            raise ValueError("Invalid RFC2440 signature")
        elif text_lines[-4] != f"-----END {self.network.NAME.upper()} SIGNATURE -----":
            raise ValueError("Invalid RFC2440 signature")

        address = text_lines[-3]
        signature = text_lines[-2]
        # In case the newline is the first/last character of the message before it was signed,
        # this text_lines slice will have as its first/last element '' so a newline will still be inserted anyway.
        # If the newline is the only character in the message, then we have to check for that directly.
        if text_lines == ['']:
            message = '\n'
        else:
            message = '\n'.join(text_lines[1:-4])
        return self.verify(message, signature, address)

    def __init__(self, ckey, network=BitcoinSegwitMainNet):
        self._key = ckey
        self._network = network

        # RIPEMD-160 of SHA-256
        if "BASE58" in network.ADDRESS_MODE or "BECH32" in network.ADDRESS_MODE:
            self.ripe = ripemd160(hashlib.sha256(ckey.format(compressed=False)).digest())
            self.ripe_compressed = ripemd160(hashlib.sha256(ckey.format(compressed=True)).digest())
        else:
            self.ripe = None
            self.ripe_compressed = None

        # Keccak-256 for Ethereum
        if "HEX" in network.ADDRESS_MODE:
            self.keccak = Keccak256(ckey.format(compressed=False)[1:]).digest()
        else:
            self.keccak = None

    @property
    def network(self):
        """Returns the network for this public key."""
        return self._network

    def to_bytes(self, compressed=True):
        """ Converts the public key into bytes.

        Args:
            compressed (bool): Whether to return the compressed form. Default is true.
        Returns:
            b (bytes): A byte string.
        """
        return self._key.format(compressed)

    def to_hex(self, compressed=True):
        """ Converts the public key into a hex string.

        Args:
            compressed (bool): Whether to return the compressed form. Default is true.
        Returns:
            b (str): A hexadecimal string.
        """
        return ensure_str(binascii.hexlify(self.to_bytes(compressed)))

    def __bytes__(self):
        return self.to_bytes(compressed=True)

    def to_point(self):
        """ Return the public key points as a Point.
        """
        return Point(*self._key.point())

    def hash160(self, compressed=True):
        """ Return the RIPEMD-160 hash of the SHA-256 hash of the
        public key. Only defined if one of base58 or bech32 are supported
        by the network.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.
        Returns:
            bytes: RIPEMD-160 byte string.
        """
        return self.ripe_compressed if compressed else self.ripe

    def p2pkh_script(self, compressed=True):
        """ Return the P2PKH script bytes contianing the public key's hash.
        Undefined for EVM blockchains.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.
        Returns:
            bytes: A P2PKH script.
        """
        if (compressed and not self.ripe_compressed) or (not compressed and not self.ripe):
            return None
        # OP_DUP OP_HASH160 (OP_PUSH of pubkeyhash) OP_EQUALVERIFY OP_CHECKSIG
        return b"\x76\xa9\x14" + (self.ripe_compressed if compressed else self.ripe) + b"\x88\xac"
    

    @classmethod
    def p2pkh(cls, pubkey_hash):
        """ Return the P2PKH script bytes contianing the specified pubkey hash.
        Only applicable to Bitcoin-like blockchains.

        Args:
            pubkey_hash (bytes): The pubkey hash to use.
        Returns:
            bytes: A P2PKH script.
        """
        # OP_DUP OP_HASH160 (OP_PUSH of pubkeyhash) OP_EQUALVERIFY OP_CHECKSIG
        return b"\x76\xa9\x14" + pubkey_hash + b"\x88\xac"
    

    @classmethod
    def p2sh(cls, script_hash):
        """ Return the P2SH script bytes contianing the specified script hash.
        Only applicable to Bitcoin-like blockchains

        Args:
            script_hash (bytes): The script hash to use.
        Returns:
            bytes: A P2SH script.
        """
        # OP_HASH160 (OP_PUSH of scripthash) OP_EQUAL
        return b"\xa9\x14" + script_hash + b"\x87"
    
    # P2SH-P2WPKH is currently not supported
    def p2wpkh_script(self, compressed=True):
        """ Return the P2WPKH script bytes contianing the public key's hash.
        Undefined by EVM blockchains.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used. DO NOT change this value or you might make
                a non-standard transaction.
        Returns:
            bytes: A P2WPKH script.
        """
        if (compressed and not self.ripe_compressed) or (not compressed and not self.ripe):
            return None
        # OP_0 (OP_PUSH of pubkeyhash)
        return b"\x00\x14" + (self.ripe_compressed if compressed else self.ripe)
    

    @classmethod
    def p2wpkh(cls, pubkey_hash):
        """ Return the P2WPKH script bytes contianing the specified pubkey hash.
        Only applicable to Bitcoin-like blockchains.

        Args:
            pubkey_hash (bytes): The pubkey hash to use.
        Returns:
            bytes: A P2WPKH script.
        """
        # OP_DUP OP_HASH160 (OP_PUSH of pubkeyhash) OP_EQUALVERIFY OP_CHECKSIG
        return b"\x00\x14" + pubkey_hash

    @classmethod
    def p2wsh(cls, script_hash):
        """ Return the P2WSH script bytes contianing the specified script hash.
        Only applicable to Bitcoin-like blockchains.

        Args:
            script_hash (bytes): The script hash to use.
        Returns:
            bytes: A P2WSH script.
        """
        # OP_0 (OP_PUSH of scripthash)
        return b"\x00\x20" + script_hash
    
    @classmethod
    def script(cls, address, network):
        """ Returns the appropriate script depending on the address value.
        Only applicable to Bitcoin-like blockchains.

        Args:
            address (string) the address to get the script for.
            network (string) the network for this address
        Returns:
            bytes: the address script.
        """
        if network.SUPPORTS_EVM:
            return None # Undefined
        else:
            try:
                b = b58decode_check(address)
                if b[0] == network.PUBKEY_ADDRESS:
                    return b"\x76\xa9\x14" + b[1:] + b"\x88\xac"
                elif b[0] == network.SCRIPT_ADDRESS:
                    return b"\x76\xa9\x14" + b[1:] + b"\x88\xac"
                else:
                    raise ValueError("Unknown address type")
            except ValueError as e:
                b = bech32_decode(network.BECH32_PREFIX, address)[1]
                if len(b) == 20:
                    return b"\x00\x14" + bytes(b)
                elif len(b) == 32:
                    return b"\x00\x20" + bytes(b)
                else:
                    raise ValueError("Unknown address type")

    def keccak256(self):
        """ Return the Keccak-256 hash of the SHA-256 hash of the
        public key. Only defined if hex addresses are supported by
        the network.

        Returns:
            bytes: Keccak-256 byte string.
        """
        return self.keccak
    
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
            raise unsupported_feature_exception_factory(self.network.NAME, "base58 addresses")

        # Put the version byte in front, 0x00 for Mainnet, 0x6F for testnet
        version = bytes([self.network.PUBKEY_ADDRESS])
        return ensure_str(b58encode_check(version + self.hash160(compressed)))


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
            raise unsupported_feature_exception_factory(self.network.NAME, "bech32 addresses")

        if not self.network.BECH32_PREFIX:
            raise ValueError("Network does not support Bech32")
        return bech32_encode(self.network.BECH32_PREFIX, witness_version, self.hash160(compressed))


    def hex_address(self):
        """ Address property that returns a hexadecimal encoding of the public key. """

        if not self.network or not self.network.ADDRESS_MODE:
            raise TypeError("Invalid network parameter")
        elif "HEX" not in self.network.ADDRESS_MODE:
            raise unsupported_feature_exception_factory(self.network.NAME, "hexadecimal addresses")

        return '0x' + binascii.hexlify(self.keccak[12:]).decode('ascii')


    def address(self, compressed=True, witness_version=0):
        """Returns the address genereated according to the first supported address format by the network."""
        if self.network.ADDRESS_MODE[0] == "BASE58":
            return self.base58_address(compressed)
        elif self.network.ADDRESS_MODE[0] == "BECH32":
            return self.bech32_address(compressed, witness_version)
        elif self.network.ADDRESS_MODE[0] == "HEX":
            return self.hex_address()
        else:
            raise unsupported_feature_exception_factory(self.network.NAME, "addresses")
