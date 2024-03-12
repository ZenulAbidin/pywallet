import hashlib
import binascii

from hashlib import scrypt

from Cryptodome.Cipher import AES

from .utils.keys import PrivateKey
from .utils import base58


# We don't use our custom AES encryption functions because BIP38
# has specific requirements for the encryption.
def encrypt(raw, passphrase):
    """
    Encrypts data with a passphrase.

    This method should only be used for calculating BIP38 data.
    It uses AES settings that are not ideal for general-purpose use.

    Parameters:
        raw (str): The text to encrypt.
        passphrase (str): The passphrase used for encryption.

    Returns:
        bytes: The encrypted text.
    """
    cipher = AES.new(passphrase, AES.MODE_CBC, b"\x00" * 16)
    ciphertext = cipher.encrypt(raw)
    return ciphertext


def decrypt(enc, passphrase):
    """
    Decrypts encrypted data with a passphrase.

    This method should only be used for calculating BIP38 data.
    It uses AES settings that are not ideal for general-purpose use.

    Parameters:
        enc (bytes): The encrypted text to decrypt.
        passphrase (str): The passphrase used for decryption.

    Returns:
        bytes: The decrypted text.
    """
    ciphertext = enc
    cipher = AES.new(passphrase, AES.MODE_CBC, b"\x00" * 16)
    plaintext = cipher.decrypt(ciphertext)
    return plaintext.rstrip(b"\0")


class Bip38PrivateKey:
    """
    Represents a BIP38 encrypted private key for Bitcoin.
    """

    BLOCK_SIZE = 16
    KEY_LEN = 32
    IV_LEN = 16

    def __init__(
        self,
        privkey: PrivateKey,
        passphrase,
        compressed=True,
        segwit=False,
        witness_version=0,
    ):
        """Creates a BIP0038 private key with non-ec-multiply encryption.

        Args:
            privkey (PrivateKey): The private key.
            passphrase (_type_): The encryption passphrase
            compressed (bool, optional): Whether to use compressed public keys. Defaults to True.
            segwit (bool, optional): Whether to use segwit address. Defaults to False.
            witness_version (int, optional): The witness version for generating the segwit address. Defaults to 0.

        Raises:
            ValueError: If the private key object does not support Base58 or Bech32.
        """
        # BIP0038 non-ec-multiply encryption. Returns BIP0038 encrypted privkey.
        if (
            "BASE58" not in privkey.network.ADDRESS_MODE
            and "BECH32" not in privkey.network.ADDRESS_MODE
        ):
            raise ValueError("BIP38 requires Base58 or Bech32 addresses")
        flagbyte = b"\xe0" if compressed else b"\xc0"
        addr = (
            privkey.public_key.bech32_address(compressed, witness_version)
            if segwit
            else privkey.public_key.base58_address(compressed)
        )
        addresshash = hashlib.sha256(hashlib.sha256(addr.encode()).digest()).digest()[
            0:4
        ]
        key = scrypt(
            passphrase.encode("utf-8"), salt=addresshash, n=16384, r=8, p=8, dklen=64
        )
        derivedhalf1 = key[0:32]
        derivedhalf2 = key[32:64]
        encryptedhalf1 = encrypt(
            binascii.unhexlify(
                "%0.32x"
                % (
                    int(binascii.hexlify(bytes(privkey)[0:16]), 16)
                    ^ int(binascii.hexlify(derivedhalf1[0:16]), 16)
                )
            ),
            derivedhalf2,
        )
        encryptedhalf2 = encrypt(
            binascii.unhexlify(
                "%0.32x"
                % (
                    int(binascii.hexlify(bytes(privkey)[16:32]), 16)
                    ^ int(binascii.hexlify(derivedhalf1[16:32]), 16)
                )
            ),
            derivedhalf2,
        )
        self.flagbyte = flagbyte
        self.addresshash = addresshash
        self.encryptedhalf1 = encryptedhalf1
        self.encryptedhalf2 = encryptedhalf2
        encrypted_privkey = (
            b"\x01\x42"
            + self.flagbyte
            + self.addresshash
            + self.encryptedhalf1
            + self.encryptedhalf2
        )
        encrypted_privkey += hashlib.sha256(
            hashlib.sha256(encrypted_privkey).digest()
        ).digest()[
            :4
        ]  # b58check for encrypted privkey
        self._encrypted_privkey = base58.b58encode(encrypted_privkey)

    @property
    def base58(self):
        """Returns the Base58 representation of the encrypted private key."""
        return self._encrypted_privkey.decode()

    def private_key(self, passphrase, compressed=True, segwit=False, witness_version=0):
        """Decrypts the encrypted private key using the given passphrase and returns the corresponding WIF private key.

        Args:
            passphrase (_type_): The passphrase to decrypt the key.
            compressed (bool, optional): Whether to use compressed public keys. Defaults to True.
            segwit (bool, optional): Whether to use segwit address. Defaults to False.
            witness_version (int, optional): The witness version for generating the segwit address. Defaults to 0.


        Raises:
            ValueError: If the wrong decryption passphrase was supplied.

        Returns:
            PrivateKey: a Bitcoin private key.
        """
        # BIP0038 non-ec-multiply decryption. Returns WIF privkey.
        d = base58.b58decode(self._encrypted_privkey)
        d = d[2:]
        # flagbyte = d[0:1]
        d = d[1:]
        # WIF compression
        # if flagbyte == b'\xc0':
        #    compressed = False
        # if flagbyte == b'\xe0':
        #    compressed = True
        addresshash = d[0:4]
        d = d[4:-4]
        key = scrypt(
            passphrase.encode("utf-8"), salt=addresshash, n=16384, r=8, p=8, dklen=64
        )
        derivedhalf1 = key[0:32]
        derivedhalf2 = key[32:64]
        encryptedhalf1 = d[0:16]
        encryptedhalf2 = d[16:32]
        decryptedhalf2 = decrypt(encryptedhalf2, derivedhalf2)
        decryptedhalf1 = decrypt(encryptedhalf1, derivedhalf2)
        priv = decryptedhalf1 + decryptedhalf2
        priv = PrivateKey.from_bytes(
            binascii.unhexlify(
                "%064x"
                % (
                    int(binascii.hexlify(priv), 16)
                    ^ int(binascii.hexlify(derivedhalf1), 16)
                )
            )
        )
        pub = priv.public_key

        addr = (
            pub.bech32_address(compressed, witness_version)
            if segwit
            else pub.base58_address(compressed)
        )
        if (
            hashlib.sha256(hashlib.sha256(addr.encode()).digest()).digest()[0:4]
            != addresshash
        ):
            raise ValueError("Verification failed. Password is incorrect.")
        else:
            return priv
