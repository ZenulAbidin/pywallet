import unittest
import struct
from zpywallet.utils.ripemd160 import (
    ripemd160,
    RMDContext,
    rmd160_transform,
    rmd160_update,
    rmd160_final,
)

CASE_HELLO_WORLD = b"hello world"


class TestRIPEMD160(unittest.TestCase):
    def test_ripemd160(self):
        expected_digest = b"98c615784ccb5fe5936fbc0cbe9dfdb408d92f0f"
        digest = ripemd160(CASE_HELLO_WORLD)
        self.assertEqual(digest.hex(), expected_digest.decode())

    def test_rmd_context(self):
        ctx = RMDContext()
        self.assertEqual(
            ctx.state, [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]
        )
        self.assertEqual(ctx.count, 0)
        self.assertEqual(ctx.buffer, [0] * 64)

    def test_rmd160_update(self):
        ctx = RMDContext()
        rmd160_update(ctx, CASE_HELLO_WORLD, len(CASE_HELLO_WORLD))
        self.assertEqual(ctx.count, 88)

    def test_rmd160_final(self):
        ctx = RMDContext()
        rmd160_update(ctx, CASE_HELLO_WORLD, len(CASE_HELLO_WORLD))
        digest = rmd160_final(ctx)
        self.assertIsInstance(digest, bytes)

    def test_rmd160_transform(self):
        state = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]
        block = bytearray(CASE_HELLO_WORLD + b"\x00" * 53)
        rmd160_transform(state, block)
        expected_digest = "7398996ebc4e156f3906a70144a72a7a26d621af"
        digest = struct.pack("<5L", *state).hex()
        self.assertEqual(digest, expected_digest)
