import unittest
from hashlib import sha256
from zpywallet.network import BitcoinSegwitMainNet
from zpywallet.utils.keys import PrivateKey, PublicKey, Point
from zpywallet.errors import IncompatibleNetworkException


class TestKey(unittest.TestCase):

    def test_001_private_key(self):
        # Test case for generating PrivateKey from bytes
        p = PrivateKey.from_hex("00" * 31 + "01")
        self.assertEqual(int(p), 1)
        self.assertEqual(p.to_hex(), "00" * 31 + "01")
        self.assertEqual(bytes(p), b"\x00" * 31 + b"\x01")
        self.assertEqual(
            p.to_wif(compressed=False),
            "5HpHagT65TZzG1PH3CSu63k8DbpvD8s5ip4nEB3kEsreAnchuDf",
        )
        self.assertEqual(
            p.to_wif(compressed=True),
            "KwDiBf89QgGbjEhKnhXJuH7LrciVrZi3qYjgd9M7rFU73sVHnoWn",
        )
        q = PrivateKey.from_wif("KwDiBf89QgGbjEhKnhXJuH7LrciVrZi3qYjgd9M7rFU73sVHnoWn")
        self.assertEqual(int(q), 1)
        q = PrivateKey.from_wif("5HpHagT65TZzG1PH3CSu63k8DbpvD8s5ip4nEB3kEsreAnchuDf")
        self.assertEqual(int(q), 1)
        r = PrivateKey.from_bytes(b"\x00" * 31 + b"\x01")
        self.assertEqual(int(r), 1)
        r = PrivateKey.from_int(1)
        self.assertEqual(r.to_hex(), "00" * 31 + "01")
        s = PrivateKey.from_brainwallet(b"")
        self.assertEqual(
            bytes(s),
            b"\r\xb9D\xf1tfr(\x99\x95\xb6\x0cI\xfa\x90ny\xb6\xa2\xc0\xcb\x8d}\xe6\xbfR\xce\x92:\xd8\x8b\x0b",
        )

    def test_002_public_key(self):
        # Test case for generating PrivateKey from bytes
        p = PrivateKey.from_hex("00" * 31 + "01", network=BitcoinSegwitMainNet)
        pp = p.public_key
        point = Point(
            x=55066263022277343669578718895168534326250603453777594175500187360389116729240,
            y=32670510020758816978083085130507043184471273380659243275938904335757337482424,
        )
        self.assertEqual(pp.to_point(), point)
        self.assertEqual(
            pp.to_hex(compressed=True),
            "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
        )
        self.assertEqual(
            pp.to_hex(compressed=False),
            "0479be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8",  # noqa: E501
        )
        self.assertEqual(
            pp.to_bytes(compressed=True),
            b"\x02y\xbef~\xf9\xdc\xbb\xacU\xa0b\x95\xce\x87\x0b\x07\x02\x9b\xfc\xdb-\xce(\xd9Y\xf2\x81[\x16\xf8\x17\x98",  # noqa: E501
        )
        self.assertEqual(
            pp.to_bytes(compressed=False),
            b"\x04y\xbef~\xf9\xdc\xbb\xacU\xa0b\x95\xce\x87\x0b\x07\x02\x9b\xfc\xdb-\xce(\xd9Y\xf2\x81[\x16\xf8\x17\x98H:\xdaw&\xa3\xc4e]\xa4\xfb\xfc\x0e\x11\x08\xa8\xfd\x17\xb4H\xa6\x85T\x19\x9cG\xd0\x8f\xfb\x10\xd4\xb8",  # noqa: E501
        )
        self.assertEqual(
            pp.hash160(), b"u\x1ev\xe8\x19\x91\x96\xd4T\x94\x1cE\xd1\xb3\xa3#\xf1C;\xd6"
        )
        self.assertEqual(
            pp.p2pkh_script(),
            b"v\xa9\x14u\x1ev\xe8\x19\x91\x96\xd4T\x94\x1cE\xd1\xb3\xa3#\xf1C;\xd6\x88\xac",
        )
        self.assertEqual(
            pp.p2wpkh_script(),
            b"\x00\x14u\x1ev\xe8\x19\x91\x96\xd4T\x94\x1cE\xd1\xb3\xa3#\xf1C;\xd6",
        )
        self.assertEqual(
            pp.base58_address(compressed=True), "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
        )
        self.assertEqual(
            pp.base58_address(compressed=False), "1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm"
        )
        self.assertEqual(
            pp.bech32_address(), "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
        )
        self.assertEqual(pp.address(), pp.bech32_address())
        with self.assertRaises(IncompatibleNetworkException):
            pp.hex_address()

    def test_003_sign_message(self):
        # Test case for generating PrivateKey from bytes
        p = PrivateKey.from_hex("00" * 31 + "01")
        pp = p.public_key
        message = "hello world"
        signature = p.der_sign(message)
        self.assertTrue(pp.der_verify(message, signature, pp.base58_address()))
        signature = p.base64_sign(message)
        self.assertTrue(pp.base64_verify(message, signature, pp.base58_address()))
        signature = p.rfc2440_sign(message)
        self.assertTrue(pp.rfc2440_verify(signature))
        r, s, z = p.rsz_sign(message)
        self.assertTrue(pp.rsz_verify(message, r, s, z, pp.base58_address()))
