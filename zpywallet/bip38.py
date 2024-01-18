import hashlib
import binascii
import scrypt

from .utils.keys import PrivateKey
from .utils.utils import encrypt, decrypt
from .utils import base58

class Bip38PrivateKey:
    BLOCK_SIZE = 16
    KEY_LEN = 32
    IV_LEN = 16

    def __init__(self, privkey: PrivateKey, passphrase, compressed=True, segwit=False, witness_version=0):
        '''BIP0038 non-ec-multiply encryption. Returns BIP0038 encrypted privkey.'''
        if "BASE58" not in privkey.network.ADDRESS_MODE and "BECH32" not in privkey.network.ADDRESS_MODE:
            raise ValueError("BIP38 requires Base58 or Bech32 addresses")
        flagbyte = b'\xe0' if compressed else b'\xc0'
        addr = privkey.public_key.bech32_address(compressed, witness_version) if segwit else privkey.public_key.base58_address(compressed)
        addresshash = hashlib.sha256(hashlib.sha256(addr.encode()).digest()).digest()[0:4]
        key = scrypt.hash(passphrase, addresshash, 16384, 8, 8)
        derivedhalf1 = key[0:32]
        derivedhalf2 = key[32:64]
        encryptedhalf1 = encrypt(binascii.unhexlify('%0.32x' % (int(binascii.hexlify(bytes(privkey)[0:16]), 16) ^ int(binascii.hexlify(derivedhalf1[0:16]), 16))), derivedhalf2)
        encryptedhalf2 = encrypt(binascii.unhexlify('%0.32x' % (int(binascii.hexlify(bytes(privkey)[16:32]), 16) ^ int(binascii.hexlify(derivedhalf1[16:32]), 16))), derivedhalf2)
        self.flagbyte = flagbyte
        self.addresshash = addresshash
        self.encryptedhalf1 = encryptedhalf1
        self.encryptedhalf2 = encryptedhalf2
        encrypted_privkey = b'\x01\x42' + self.flagbyte + self.addresshash + self.encryptedhalf1 + self.encryptedhalf2
        encrypted_privkey += hashlib.sha256(hashlib.sha256(encrypted_privkey).digest()).digest()[:4] # b58check for encrypted privkey
        self._encrypted_privkey = base58.b58encode(encrypted_privkey)

    @property
    def base58(self):
        return self._encrypted_privkey.decode()
        

    def private_key(self, passphrase, compressed=True, segwit=False, witness_version=0):
        '''BIP0038 non-ec-multiply decryption. Returns WIF privkey.'''
        d = base58.b58decode(self._encrypted_privkey)
        d = d[2:]
        #flagbyte = d[0:1]
        d = d[1:]
        #WIF compression
        #if flagbyte == b'\xc0':
        #    compressed = False
        #if flagbyte == b'\xe0':
        #    compressed = True
        addresshash = d[0:4]
        d = d[4:-4]
        key = scrypt.hash(passphrase,addresshash, 16384, 8, 8)
        derivedhalf1 = key[0:32]
        derivedhalf2 = key[32:64]
        encryptedhalf1 = d[0:16]
        encryptedhalf2 = d[16:32]
        decryptedhalf2 = decrypt(encryptedhalf2, derivedhalf2)
        decryptedhalf1 = decrypt(encryptedhalf1, derivedhalf2)
        priv = decryptedhalf1 + decryptedhalf2
        priv = PrivateKey.from_bytes(binascii.unhexlify('%064x' % (int(binascii.hexlify(priv), 16) ^ int(binascii.hexlify(derivedhalf1), 16))))
        pub = priv.public_key

        addr = pub.bech32_address(compressed, witness_version) if segwit else pub.base58_address(compressed)
        if hashlib.sha256(hashlib.sha256(addr.encode()).digest()).digest()[0:4] != addresshash:
            raise ValueError('Verification failed. Password is incorrect.')
        else:
            return priv
