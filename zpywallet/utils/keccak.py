"""
The keccak module provides an implementation of the Keccak hash function, including various parameter presets
such as Keccak224, Keccak256, Keccak384, and Keccak512. The module offers a hashlib-compatible interface for
easy integration into existing codebases.
"""

from math import log
from operator import xor
from copy import deepcopy
from functools import reduce
from binascii import hexlify

# The round constants used in the Keccak-f permutation.
RoundConstants = [
  0x0000000000000001,   0x0000000000008082,   0x800000000000808A,   0x8000000080008000,
  0x000000000000808B,   0x0000000080000001,   0x8000000080008081,   0x8000000000008009,
  0x000000000000008A,   0x0000000000000088,   0x0000000080008009,   0x000000008000000A,
  0x000000008000808B,   0x800000000000008B,   0x8000000000008089,   0x8000000000008003,
  0x8000000000008002,   0x8000000000000080,   0x000000000000800A,   0x800000008000000A,
  0x8000000080008081,   0x8000000000008080,   0x0000000080000001,   0x8000000080008008
]

# The rotation constants used in the Keccak-f permutation.
RotationConstants = [
  [  0,  1, 62, 28, 27, ],
  [ 36, 44,  6, 55, 20, ],
  [  3, 10, 43, 25, 39, ],
  [ 41, 45, 15, 21,  8, ],
  [ 18,  2, 61, 56, 14, ]
]

# Bit masks used for circular rotations in the Keccak-f permutation.
Masks = [(1 << i) - 1 for i in range(65)]

def bits2bytes(x):
    """Converts the given number of bits to the corresponding number of bytes, rounding up if necessary."""
    return (int(x) + 7) // 8

def rol(value, left, bits):
    """
    Circularly rotate 'value' to the left,
    treating it as a quantity of the given size in bits.
    """
    top = value >> (bits - left)
    bot = (value & Masks[bits - left]) << left
    return bot | top

def ror(value, right, bits):
    """
    Circularly rotate 'value' to the right,
    treating it as a quantity of the given size in bits.
    """
    top = value >> right
    bot = (value & Masks[right]) << (bits - right)
    return bot | top

def multirate_padding(used_bytes, align_bytes):
    """
     Generates padding bytes according to the Keccak padding scheme,
     ensuring alignment to the specified number of bytes.
    """
    padlen = align_bytes - used_bytes
    if padlen == 0:
        padlen = align_bytes
    # note: padding done in 'internal bit ordering', wherein LSB is leftmost
    if padlen == 1:
        return [0x81]
    else:
        return [0x01] + ([0x00] * (padlen - 2)) + [0x80]

def keccak_f(state):
    """
    Performs the Keccak-f permutation on the given Keccak state. It applies multiple
    rounds of theta, rho, pi, chi, and iota operations to mutate the state. It operates
    on and mutates the passed-in KeccakState.  It returns nothing.
    """
    def f_round(A, RC):
        W, H = state.W, state.H
        rangeW, rangeH = state.rangeW, state.rangeH
        lanew = state.lanew
        zero = state.zero
    
        # theta
        C = [reduce(xor, A[x]) for x in rangeW]
        D = [0] * W
        for x in rangeW:
            D[x] = C[(x - 1) % W] ^ rol(C[(x + 1) % W], 1, lanew)
            for y in rangeH:
                A[x][y] ^= D[x]
        
        # rho and pi
        B = zero()
        for x in rangeW:
            for y in rangeH:
                B[y % W][(2 * x + 3 * y) % H] = rol(A[x][y], RotationConstants[y][x], lanew)
                
        # chi
        for x in rangeW:
            for y in rangeH:
                A[x][y] = B[x][y] ^ ((~ B[(x + 1) % W][y]) & B[(x + 2) % W][y])
        
        # iota
        A[0][0] ^= RC

    l = int(log(state.lanew, 2))
    nr = 12 + 2 * l
    
    for ir in range(nr):
        f_round(state.s, RoundConstants[ir])

class KeccakState(object):
    """
    A keccak state container.
    
     Represents the internal state of the Keccak algorithm.
     It maintains the state as a 5x5 table of integers and provides methods for
     manipulating the state, converting between byte sequences and lanes, and
     formatting the state as a hexadecimal string.
    """
    W = 5
    H = 5
    
    rangeW = list(range(W))
    rangeH = list(range(H))
    
    @staticmethod
    def zero():
        """
        Returns an zero state table.
        """
        return [[0] * KeccakState.W for x in KeccakState.rangeH]
    
    @staticmethod
    def format(st):
        """
        Formats the given state as hex, in natural byte order.
        """
        rows = []
        def fmt(x): return '%016x' % x
        for y in KeccakState.rangeH:
            row = []
            for x in KeccakState.rangeW:
                row.append(fmt(st[x][y]))
            rows.append(' '.join(row))
        return '\n'.join(rows)
    
    @staticmethod
    def lane2bytes(s, w):
        """
        Converts the lane s to a sequence of byte values,
        assuming a lane is w bits.
        """
        o = []
        for b in range(0, w, 8):
            o.append((s >> b) & 0xff)
        return o
    
    @staticmethod
    def bytes2lane(bb):
        """
        Converts a sequence of byte values to a lane.
        """
        r = 0
        for b in reversed(bb):
            r = r << 8 | b
        return r
    
    def __init__(self, bitrate, b):
        self.bitrate = bitrate
        self.b = b
        
        # only byte-aligned
        assert self.bitrate % 8 == 0
        self.bitrate_bytes = bits2bytes(self.bitrate)
        
        assert self.b % 25 == 0
        self.lanew = self.b // 25
        
        self.s = KeccakState.zero()
    
    def __str__(self):
        return KeccakState.format(self.s)
    
    def absorb(self, bb):
        """
        Mixes in the given bitrate-length string to the state.
        """
        assert len(bb) == self.bitrate_bytes
        
        bb += [0] * bits2bytes(self.b - self.bitrate)
        i = 0
        
        for y in self.rangeH:
            for x in self.rangeW:
                self.s[x][y] ^= KeccakState.bytes2lane(bb[i:i + 8])
                i += 8
    
    def squeeze(self):
        """
        Returns the bitrate-length prefix of the state to be output.
        """
        return self.get_bytes()[:self.bitrate_bytes]
    
    def get_bytes(self):
        """
        Convert whole state to a byte string.
        """
        out = [0] * bits2bytes(self.b)
        i = 0
        for y in self.rangeH:
            for x in self.rangeW:
                v = KeccakState.lane2bytes(self.s[x][y], self.lanew)
                out[i:i+8] = v
                i += 8
        return out
    
    def set_bytes(self, bb):
        """
        Set whole state from byte string, which is assumed
        to be the correct length.
        """
        i = 0
        for y in self.rangeH:
            for x in self.rangeW:
                self.s[x][y] = KeccakState.bytes2lane(bb[i:i+8])
                i += 8

class KeccakSponge(object):
    """
    Implements the sponge construction of the Keccak algorithm. It absorbs
    input data, applies the Keccak-f permutation, and produces output data
    based on the specified bitrate and capacity.
    """
    def __init__(self, bitrate, width, padfn, permfn):
        self.state = KeccakState(bitrate, width)
        self.padfn = padfn
        self.permfn = permfn
        self.buffer = []
        
    def copy(self):
        """ Creates a deep copy of the KeccakHash object, including the internal state. """
        return deepcopy(self)
        
    def absorb_block(self, bb):
        """ Absorbs a block of data of the bitrate length into the sponge's internal state. """
        assert len(bb) == self.state.bitrate_bytes
        self.state.absorb(bb)
        self.permfn(self.state)
    
    def absorb(self, s):
        """Absorbs input strings or bytes as byte data. """
        if type(s) is str:
            self.buffer += bytes(s, 'latin1')
        elif type(s) is bytes:
            self.buffer += s
        else:
            raise TypeError("Expected bytes or str")
        
        while len(self.buffer) >= self.state.bitrate_bytes:
            self.absorb_block(self.buffer[:self.state.bitrate_bytes])
            self.buffer = self.buffer[self.state.bitrate_bytes:]
    
    def absorb_final(self):
        """
        Used to apply padding to the remaining input data and absorb it into
        the sponge's internal state.
        """
        padded = self.buffer + self.padfn(len(self.buffer), self.state.bitrate_bytes)
        self.absorb_block(padded)
        self.buffer = []
        
    def squeeze_once(self):
        """Generates a single block of squeezed output data from the sponge's internal state."""
        rc = self.state.squeeze()
        self.permfn(self.state)
        return rc
    
    def squeeze(self, l):
        """Generates squeezed output data of the specified length from the sponge's internal state.
        
        Args:
            l (int): Length of squeezed data to return."""
        Z = self.squeeze_once()
        while len(Z) < l:
            Z += self.squeeze_once()
        return Z[:l]

class KeccakHash(object):
    """
    The Keccak hash function, with a hashlib-compatible interface.

    Represents a Keccak hash object with customizable bitrate, capacity, and output length.
    It provides methods for updating the hash state with input data and generating the
    final hash value.
    """
    def __init__(self, bitrate_bits, capacity_bits, output_bits):
        # our in-absorption sponge. this is never given padding
        assert bitrate_bits + capacity_bits in (25, 50, 100, 200, 400, 800, 1600)
        self.sponge = KeccakSponge(bitrate_bits, bitrate_bits + capacity_bits,
                                   multirate_padding,
                                   keccak_f)
        
        # hashlib interface members
        assert output_bits % 8 == 0
        self.digest_size = bits2bytes(output_bits)
        self.block_size = bits2bytes(bitrate_bits)
    
    def __repr__(self):
        inf = (self.sponge.state.bitrate,
               self.sponge.state.b - self.sponge.state.bitrate,
               self.digest_size * 8)
        return '<KeccakHash with r=%d, c=%d, image=%d>' % inf
    
    def copy(self):
        """ Creates a deep copy of the KeccakHash object, including the internal state. """
        return deepcopy(self)
    
    def update(self, s):
        """
        Updates the hash state by absorbing the input data `s`. The input data can be either a string or bytes object.

        Args:
            s (str or bytes): The input data to update the hash state with.
        """
        self.sponge.absorb(s)
    
    def digest(self):
        """
        Retrieves the final hash value as a bytes object. The hash state is finalized before generating the digest.

        Returns:
            bytes: The final hash value as a bytes object.
        """
        finalised = self.sponge.copy()
        finalised.absorb_final()
        digest = bytes(finalised.squeeze(self.digest_size))
        return digest
    
    def hexdigest(self):
        """
        Retrieves the final hash value as a hex string. The hash state is finalized before generating the digest.

        Returns:
            str: The final hash value as a hex string.
        """
        return hexlify(self.digest()).decode()
    
    @staticmethod
    def preset(bitrate_bits, capacity_bits, output_bits):
        """
        Returns a factory function for the given bitrate, sponge capacity and output length.
        The function accepts an optional initial input, ala hashlib.
        """
        def create(initial_input = None):
            h = KeccakHash(bitrate_bits, capacity_bits, output_bits)
            if initial_input is not None:
                h.update(initial_input)
            return h
        return create

# SHA3 parameter presets
# Keccak224: Creates a KeccakHash object with a bitrate of 1152 bits, a capacity of 448 bits, and an output length of 224 bits.
# Keccak256: Creates a KeccakHash object with a bitrate of 1088 bits, a capacity of 512 bits, and an output length of 256 bits.
# Keccak384: Creates a KeccakHash object with a bitrate of 832 bits, a capacity of 768 bits, and an output length of 384 bits.
# Keccak512: Creates a KeccakHash object with a bitrate of 576 bits, a capacity of 1024 bits, and an output length of 512 bits.
Keccak224 = KeccakHash.preset(1152, 448, 224)
Keccak256 = KeccakHash.preset(1088, 512, 256)
Keccak384 = KeccakHash.preset(832, 768, 384)
Keccak512 = KeccakHash.preset(576, 1024, 512)

def to_checksum_address(address):
    address = address.lower().replace('0x', '')
    keccak_hash = Keccak256(address.encode('utf-8')).hexdigest()
    checksum_address = '0x'
    
    for i in range(len(address)):
        if int(keccak_hash[i], 16) >= 8:
            checksum_address += address[i].upper()
        else:
            checksum_address += address[i]
    return checksum_address

def is_checksum_address(address):
    address = address.replace('0x', '')
    address_hash = Keccak256(address.lower().encode('utf-8')).hexdigest()
    
    for i in range(0, 40):
        # The nth letter should be uppercase if the nth digit of casemap is 1
        if ((int(address_hash[i], 16) > 7 and address[i].upper() != address[i]) or
                (int(address_hash[i], 16) <= 7 and address[i].lower() != address[i])):
            return False
    return True