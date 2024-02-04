#!/usr/bin/env python
# flake8: noqa: C0301

"""Tests for `zpywallet` package."""

import binascii
import unittest
from zpywallet import wallet
from zpywallet.bip38 import Bip38PrivateKey
from zpywallet.network import BitcoinSegwitMainNet
from zpywallet.utils.bip32 import HDWallet
from zpywallet.errors import IncompatibleNetworkException
from zpywallet.utils.keys import PrivateKey


class TestZPyWallet(unittest.TestCase):
    """Tests for `zpywallet` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_create_wallet(self):
        """Test wallet creation."""
        mne = wallet.generate_mnemonic(strength=128)
        assert mne.count(' ') == 11

        hdw = wallet.create_wallet(mnemonic="nature story debris circle decrease post "
                                    "gesture cute burger chef silent grief",
                                    network=BitcoinSegwitMainNet)
        assert hdw.serialize_b58(private=True) == \
            "xprv9s21ZrQH143K26AwKW3o1D9uVbbYJp4RCLWCVQNfarQ59cgG8udwc5SVGxrTPNo2HXLNK8ZJoavsNYuExeMmdmmGVZZh5M77UV6qbMisVSm"

    def test_001_bip32(self):
        """Test BIP32 confirmance."""

        hdw = HDWallet.from_master_seed(binascii.unhexlify("000102030405060708090a0b0c0d0e0f"), network=BitcoinSegwitMainNet)
        assert hdw.serialize_b58(private=False) == "xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8"
        assert hdw.serialize_b58(private=True) == "xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi"

        child1 = hdw.get_child(0, is_prime=True)
        assert child1.serialize_b58(private=False) == "xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw"
        assert child1.serialize_b58(private=True) == "xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7"

        child2 = child1.get_child(1, is_prime=False)
        assert child2.serialize_b58(private=False) == "xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ"
        assert child2.serialize_b58(private=True) == "xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs"

        child3 = child2.get_child(2, is_prime=True)
        assert child3.serialize_b58(private=False) == "xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7DogT5Uv6fcLW5"
        assert child3.serialize_b58(private=True) == "xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM"

        child4 = child3.get_child(2, is_prime=False)
        assert child4.serialize_b58(private=False) == "xpub6FHa3pjLCk84BayeJxFW2SP4XRrFd1JYnxeLeU8EqN3vDfZmbqBqaGJAyiLjTAwm6ZLRQUMv1ZACTj37sR62cfN7fe5JnJ7dh8zL4fiyLHV"
        assert child4.serialize_b58(private=True) == "xprvA2JDeKCSNNZky6uBCviVfJSKyQ1mDYahRjijr5idH2WwLsEd4Hsb2Tyh8RfQMuPh7f7RtyzTtdrbdqqsunu5Mm3wDvUAKRHSC34sJ7in334"

        child5 = child4.get_child(1000000000, is_prime=False)
        assert child5.serialize_b58(private=False) == "xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy"
        assert child5.serialize_b58(private=True) == "xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREPSL39UNdE3BBDu76"

    def test_002_bip32(self):
        """Test BIP32 confirmance."""
        hdw = HDWallet.from_master_seed(binascii.unhexlify("fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542"),
                                        network=BitcoinSegwitMainNet)
        assert hdw.serialize_b58(private=False) == "xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJY47LJhkJ8UB7WEGuduB"
        assert hdw.serialize_b58(private=True) == "xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U"

        child1 = hdw.get_child(0, is_prime=False)
        assert child1.serialize_b58(private=False) == "xpub69H7F5d8KSRgmmdJg2KhpAK8SR3DjMwAdkxj3ZuxV27CprR9LgpeyGmXUbC6wb7ERfvrnKZjXoUmmDznezpbZb7ap6r1D3tgFxHmwMkQTPH"
        assert child1.serialize_b58(private=True) == "xprv9vHkqa6EV4sPZHYqZznhT2NPtPCjKuDKGY38FBWLvgaDx45zo9WQRUT3dKYnjwih2yJD9mkrocEZXo1ex8G81dwSM1fwqWpWkeS3v86pgKt"

        child2 = child1.get_child(2147483647, is_prime=True)
        assert child2.serialize_b58(private=False) == "xpub6ASAVgeehLbnwdqV6UKMHVzgqAG8Gr6riv3Fxxpj8ksbH9ebxaEyBLZ85ySDhKiLDBrQSARLq1uNRts8RuJiHjaDMBU4Zn9h8LZNnBC5y4a"
        assert child2.serialize_b58(private=True) == "xprv9wSp6B7kry3Vj9m1zSnLvN3xH8RdsPP1Mh7fAaR7aRLcQMKTR2vidYEeEg2mUCTAwCd6vnxVrcjfy2kRgVsFawNzmjuHc2YmYRmagcEPdU9"

        child3 = child2.get_child(1, is_prime=False)
        assert child3.serialize_b58(private=False) == "xpub6DF8uhdarytz3FWdA8TvFSvvAh8dP3283MY7p2V4SeE2wyWmG5mg5EwVvmdMVCQcoNJxGoWaU9DCWh89LojfZ537wTfunKau47EL2dhHKon"
        assert child3.serialize_b58(private=True) == "xprv9zFnWC6h2cLgpmSA46vutJzBcfJ8yaJGg8cX1e5StJh45BBciYTRXSd25UEPVuesF9yog62tGAQtHjXajPPdbRCHuWS6T8XA2ECKADdw4Ef"

        child4 = child3.get_child(2147483646, is_prime=True)
        assert child4.serialize_b58(private=False) == "xpub6ERApfZwUNrhLCkDtcHTcxd75RbzS1ed54G1LkBUHQVHQKqhMkhgbmJbZRkrgZw4koxb5JaHWkY4ALHY2grBGRjaDMzQLcgJvLJuZZvRcEL"
        assert child4.serialize_b58(private=True) == "xprvA1RpRA33e1JQ7ifknakTFpgNXPmW2YvmhqLQYMmrj4xJXXWYpDPS3xz7iAxn8L39njGVyuoseXzU6rcxFLJ8HFsTjSyQbLYnMpCqE2VbFWc"

        child5 = child4.get_child(2, is_prime=False)
        assert child5.serialize_b58(private=False) == "xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt"
        assert child5.serialize_b58(private=True) == "xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEcBYJUuekgW4BYPJcr9E7j"

    def test_003_bip32(self):
        """Test BIP32 confirmance - retention of leading zeroes."""
        hdw = HDWallet.from_master_seed(binascii.unhexlify("4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be"),
                                        network=BitcoinSegwitMainNet)
        assert hdw.serialize_b58(private=False) == "xpub661MyMwAqRbcEZVB4dScxMAdx6d4nFc9nvyvH3v4gJL378CSRZiYmhRoP7mBy6gSPSCYk6SzXPTf3ND1cZAceL7SfJ1Z3GC8vBgp2epUt13"
        assert hdw.serialize_b58(private=True) == "xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6"

        child1 = hdw.get_child(0, is_prime=True)
        assert child1.serialize_b58(private=False) == "xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y"
        assert child1.serialize_b58(private=True) == "xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L"

    def test_004_bip32(self):
        """Test BIP32 confirmance - retention of leading zeroes."""
        hdw = HDWallet.from_master_seed(binascii.unhexlify("3ddd5602285899a946114506157c7997e5444528f3003f6134712147db19b678"),
                                        network=BitcoinSegwitMainNet)
        assert hdw.serialize_b58(private=False) == "xpub661MyMwAqRbcGczjuMoRm6dXaLDEhW1u34gKenbeYqAix21mdUKJyuyu5F1rzYGVxyL6tmgBUAEPrEz92mBXjByMRiJdba9wpnN37RLLAXa"
        assert hdw.serialize_b58(private=True) == "xprv9s21ZrQH143K48vGoLGRPxgo2JNkJ3J3fqkirQC2zVdk5Dgd5w14S7fRDyHH4dWNHUgkvsvNDCkvAwcSHNAQwhwgNMgZhLtQC63zxwhQmRv"

        child1 = hdw.get_child(0, is_prime=True)
        assert child1.serialize_b58(private=False) == "xpub69AUMk3qDBi3uW1sXgjCmVjJ2G6WQoYSnNHyzkmdCHEhSZ4tBok37xfFEqHd2AddP56Tqp4o56AePAgCjYdvpW2PU2jbUPFKsav5ut6Ch1m"
        assert child1.serialize_b58(private=True) == "xprv9vB7xEWwNp9kh1wQRfCCQMnZUEG21LpbR9NPCNN1dwhiZkjjeGRnaALmPXCX7SgjFTiCTT6bXes17boXtjq3xLpcDjzEuGLQBM5ohqkao9G"

        child2 = child1.get_child(1, is_prime=True)
        assert child2.serialize_b58(private=False) == "xpub6BJA1jSqiukeaesWfxe6sNK9CCGaujFFSJLomWHprUL9DePQ4JDkM5d88n49sMGJxrhpjazuXYWdMf17C9T5XnxkopaeS7jGk1GyyVziaMt"
        assert child2.serialize_b58(private=True) == "xprv9xJocDuwtYCMNAo3Zw76WENQeAS6WGXQ55RCy7tDJ8oALr4FWkuVoHJeHVAcAqiZLE7Je3vZJHxspZdFHfnBEjHqU5hG1Jaj32dVoS6XLT1"

    def test_005_bip32(self):
        """Test BIP32 confirmance - invalid HD keys."""
        with self.assertRaises(IncompatibleNetworkException):
            HDWallet.deserialize("xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6LBpB85b3D2yc8sfvZU521AAwdZafEz7mnzBBsz4wKY5fTtTQBm")

        with self.assertRaises(IncompatibleNetworkException):
            HDWallet.deserialize("xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFGTQQD3dC4H2D5GBj7vWvSQaaBv5cxi9gafk7NF3pnBju6dwKvH")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6Txnt3siSujt9RCVYsx4qHZGc62TG4McvMGcAUjeuwZdduYEvFn")

        with self.assertRaises(IncompatibleNetworkException):
            HDWallet.deserialize("xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFGpWnsj83BHtEy5Zt8CcDr1UiRXuWCmTQLxEK9vbz5gPstX92JQ")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6N8ZMMXctdiCjxTNq964yKkwrkBJJwpzZS4HS2fxvyYUA4q2Xe4")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFAzHGBP2UuGCqWLTAPLcMtD9y5gkZ6Eq3Rjuahrv17fEQ3Qen6J")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xprv9s2SPatNQ9Vc6GTbVMFPFo7jsaZySyzk7L8n2uqKXJen3KUmvQNTuLh3fhZMBoG3G4ZW1N2kZuHEPY53qmbZzCHshoQnNf4GvELZfqTUrcv")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xpub661no6RGEX3uJkY4bNnPcw4URcQTrSibUZ4NqJEw5eBkv7ovTwgiT91XX27VbEXGENhYRCf7hyEbWrR3FewATdCEebj6znwMfQkhRYHRLpJ")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xprv9s21ZrQH4r4TsiLvyLXqM9P7k1K3EYhA1kkD6xuquB5i39AU8KF42acDyL3qsDbU9NmZn6MsGSUYZEsuoePmjzsB3eFKSUEh3Gu1N3cqVUN")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xpub661MyMwAuDcm6CRQ5N4qiHKrJ39Xe1R1NyfouMKTTWcguwVcfrZJaNvhpebzGerh7gucBvzEQWRugZDuDXjNDRmXzSZe4c7mnTK97pTvGS8")

        with self.assertRaises(IncompatibleNetworkException):
            HDWallet.deserialize("DMwo58pR1QLEFihHiXPVykYB6fJmsTeHvyTp7hRThAtCX8CvYzgPcn8XnmdfHGMQzT7ayAmfo4z3gY5KfbrZWZ6St24UVf2Qgo6oujFktLHdHY4")

        with self.assertRaises(IncompatibleNetworkException):
            HDWallet.deserialize("DMwo58pR1QLEFihHiXPVykYB6fJmsTeHvyTp7hRThAtCX8CvYzgPcn8XnmdfHPmHJiEDXkTiJTVV9rHEBUem2mwVbbNfvT2MTcAqj3nesx8uBf9")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzF93Y5wvzdUayhgkkFoicQZcP3y52uPPxFnfoLZB21Teqt1VvEHx")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFAzHGBP2UuGCqWLTAPLcMtD5SDKr24z3aiUvKr9bJpdrcLg1y3G")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6Q5JXayek4PRsn35jii4veMimro1xefsM58PgBMrvdYre8QyULY")

        with self.assertRaises(ValueError):
            HDWallet.deserialize("xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHL")

    def test_006_bip84(self):
        """Test BIP84 confirmance"""
        mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        hdw = HDWallet.from_mnemonic(mnemonic)
        assert hdw.serialize_b58(private=True, segwit=True) == \
            "zprvAWgYBBk7JR8Gjrh4UJQ2uJdG1r3WNRRfURiABBE3RvMXYSrRJL62XuezvGdPvG6GFBZduosCc1YP5wixPox7zhZLfiUm8aunE96BBa4Kei5"
        assert hdw.serialize_b58(private=False, segwit=True) == \
            "zpub6jftahH18ngZxLmXaKw3GSZzZsszmt9WqedkyZdezFtWRFBZqsQH5hyUmb4pCEeZGmVfQuP5bedXTB8is6fTv19U1GQRyQUKQGUTzyHACMF"

        # Account 0, root = m/84'/0'/0'
        hdw1 = hdw.get_child_for_path("m/84'/0'/0'")
        assert hdw1.serialize_b58(private=True, segwit=True) == \
            "zprvAdG4iTXWBoARxkkzNpNh8r6Qag3irQB8PzEMkAFeTRXxHpbF9z4QgEvBRmfvqWvGp42t42nvgGpNgYSJA9iefm1yYNZKEm7z6qUWCroSQnE"
        assert hdw1.serialize_b58(private=False, segwit=True) == \
            "zpub6rFR7y4Q2AijBEqTUquhVz398htDFrtymD9xYYfG1m4wAcvPhXNfE3EfH1r1ADqtfSdVCToUG868RvUUkgDKf31mGDtKsAYz2oz2AGutZYs"

        # Account 0, first receiving address = m/84'/0'/0'/0/0
        hdw2 = hdw.get_child_for_path("m/84'/0'/0'/0/0")
        assert hdw2.private_key.to_wif(compressed=True) == \
            "KyZpNDKnfs94vbrwhJneDi77V6jF64PWPF8x5cdJb8ifgg2DUc9d"
        assert hdw2.public_key.to_hex(compressed=True) == \
            "0330d54fd0dd420a6e5f8d3624f5f3482cae350f79d5f0753bf5beef9c2d91af3c"
        assert hdw2.public_key.bech32_address(compressed=True, witness_version=0) == \
            "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu"

        # Account 0, second receiving address = m/84'/0'/0'/0/1
        hdw3 = hdw.get_child_for_path("m/84'/0'/0'/0/1")
        assert hdw3.private_key.to_wif(compressed=True) == \
            "Kxpf5b8p3qX56DKEe5NqWbNUP9MnqoRFzZwHRtsFqhzuvUJsYZCy"
        assert hdw3.public_key.to_hex(compressed=True) == \
            "03e775fd51f0dfb8cd865d9ff1cca2a158cf651fe997fdc9fee9c1d3b5e995ea77"
        assert hdw3.public_key.bech32_address(compressed=True, witness_version=0) == \
            "bc1qnjg0jd8228aq7egyzacy8cys3knf9xvrerkf9g"

        # Account 0, first change address = m/84'/0'/0'/1/0
        hdw4 = hdw.get_child_for_path("m/84'/0'/0'/1/0")
        assert hdw4.private_key.to_wif(compressed=True) == \
            "KxuoxufJL5csa1Wieb2kp29VNdn92Us8CoaUG3aGtPtcF3AzeXvF"
        assert hdw4.public_key.to_hex(compressed=True) == \
            "03025324888e429ab8e3dbaf1f7802648b9cd01e9b418485c5fa4c1b9b5700e1a6"
        assert hdw4.public_key.bech32_address(compressed=True, witness_version=0) == \
            "bc1q8c6fshw2dlwun7ekn9qwf37cu2rn755upcp6el"

    def test_007_brainwallet(self):
        """Tests brainwallet generation."""
        w = HDWallet.from_brainwallet("crazy horse battery staple", network=BitcoinSegwitMainNet)
        assert w.private_key.to_wif(compressed=True) == "KzJp5B7mDpZ7kMHv67GowQRys9W9Hbaa5Rzj4PCoiyXfTk1fGAvH"

    def test_008_bip38(self):
        """Tests BIP38 key generation (non-ECC mode)"""
        key = PrivateKey.from_wif("5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR")
        bip38key = Bip38PrivateKey(key, "TestingOneTwoThree", compressed=False)
        assert bip38key.base58 == "6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg"
        assert bip38key.private_key("TestingOneTwoThree", compressed=False).to_wif(compressed=False) == "5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR"
