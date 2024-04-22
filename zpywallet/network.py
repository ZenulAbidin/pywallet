"""
This file contains parameters and constants for all supported networks.
"""

from .generated import wallet_pb2


# Internal base class: Do not use.
class CryptoNetwork(object):
    """Represents a cryptocurrency blockchain.

    Don't use this class - use one of the subclasses instead.
    """

    # All P2PKH testnet chains use this path.
    P2PKH_TESTNET_PATH = "m/44'/1'/0'"


class BitcoinCashMainNet(CryptoNetwork):
    """Bitcoin Cash MainNet version bytes."""

    NAME = "Bitcoin Cash"
    INTERNAL_NAME = wallet_pb2.Network.BITCOIN_CASH_MAINNET
    COIN = "BCH"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x28  # decimal 40
    PUBKEY_ADDRESS = 0x1C  # decimal 28
    SECRET_KEY = 0x80  # decimal 128
    # same as Bitcoin
    EXT_PUBLIC_KEY = 0x0488B21E  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x0488ADE4  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/145'/0'"

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None  # P2WPKH not supported
    BECH32_PREFIX = None  # Bech32 not supported


class DashMainNet(CryptoNetwork):
    """Dash MainNet version bytes.

    Dash's xpub/xprv were originally drkp/drkv. But somehow, they were swapped
    when inserted into the refernece client. So there are actually two possible
    combinations of addresses in Dash (3, if you also count Bitcoin's xpub/xprv)

    For more information, see the following link:
    https://www.dash.org/forum/index.php?threads/dash-bip32-serialization-values-dev-discussion-wont-apply-to-most.8092/
    """

    NAME = "Dash"
    INTERNAL_NAME = wallet_pb2.Network.DASH_MAINNET
    COIN = "DASH"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x10  # decimal 16
    PUBKEY_ADDRESS = 0x4C  # decimal 76
    SECRET_KEY = 0xCC  # decimal 204
    EXT_PUBLIC_KEY = 0x02FE52CC  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x02FE52F8  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/5'/0'"

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None  # P2WPKH not supported
    BECH32_PREFIX = None  # Bech32 not supported


class DashInvertedMainNet(DashMainNet):
    """Dash MainNet version bytes.

    This is the version that uses drkv/drkp as the public/private
    extended version bytes respectively. It intentionally has the same name
    and coin as the other Dash mainnets.
    """

    INTERNAL_NAME = wallet_pb2.Network.DASH_INVERTED_MAINNET
    EXT_PUBLIC_KEY = 0x02FE52F8  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x02FE52CC  # Used to serialize private BIP32 addresses


class DashBTCMainNet(CryptoNetwork):
    """Dash MainNet version bytes.

    Extended version bytes are the same as for Bitcoin, i.e. xpub/xprv,
    for maximum wallet compatibility.
    """

    NAME = "Dash"
    INTERNAL_NAME = wallet_pb2.Network.DASH_BTC_MAINNET
    COIN = "DASH"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x10  # decimal 16
    PUBKEY_ADDRESS = 0x4C  # decimal 76
    SECRET_KEY = 0xCC  # decimal 204
    EXT_PUBLIC_KEY = 0x0488B21E  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x0488ADE4  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/5'/0'"

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None  # P2WPKH not supported
    BECH32_PREFIX = None  # Bech32 not supported


class DashTestNet(CryptoNetwork):
    """Dash TestNet version bytes."""

    NAME = "Dash"
    INTERNAL_NAME = wallet_pb2.Network.DASH_TESTNET
    COIN = "DASH"
    TESTNET = True
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x13  # decimal 19
    PUBKEY_ADDRESS = 0x8C  # decimal 140
    SECRET_KEY = 0xEF  # decimal 239
    EXT_PUBLIC_KEY = 0x3A805837  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x3A8061A0  # Used to serialize private BIP32 addresses
    BIP32_PATH = CryptoNetwork.P2PKH_TESTNET_PATH

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None  # P2WPKH not supported
    BECH32_PREFIX = None  # Bech32 not supported


class DashInvertedTestNet(DashTestNet):
    """Dash TestNet version bytes with inverted extended version bytes."""

    INTERNAL_NAME = wallet_pb2.Network.DASH_INVERTED_TESTNET
    EXT_PUBLIC_KEY = 0x3A8061A0  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x3A805837  # Used to serialize private BIP32 addresses


class BitcoinMainNet(CryptoNetwork):
    """Bitcoin MainNet version bytes defaulting to legacy addresses.
    From https://github.com/bitcoin/bitcoin/blob/v0.9.0rc1/src/chainparams.cpp
    """

    NAME = "Bitcoin"
    INTERNAL_NAME = wallet_pb2.Network.BITCOIN_MAINNET
    COIN = "BTC"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x05  # decimal 5
    PUBKEY_ADDRESS = 0x00  # decimal 0
    SECRET_KEY = 0x80  # decimal 128

    EXT_PUBLIC_KEY = 0x0488B21E  # Used to serialize public keys in BIP32 legacy (P2PKH)
    EXT_SECRET_KEY = (
        0x0488ADE4  # Used to serialize private keys in BIP32 legacy (P2PKH)
    )
    BIP32_PATH = "m/44'/0'/0'"

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None
    BECH32_PREFIX = None


class BitcoinSegwitMainNet(BitcoinMainNet):
    """Bitcoin MainNet version bytes, defaulting to segwit addresses."""

    INTERNAL_NAME = wallet_pb2.Network.BITCOIN_SEGWIT_MAINNET
    ADDRESS_MODE = ["BECH32", "BASE58"]
    SUPPORTS_SEGWIT = True
    EXT_SEGWIT_PUBLIC_KEY = (
        0x04B24746  # Used to serialize public keys in BIP32 segwit (P2WPKH)
    )
    EXT_SEGWIT_SECRET_KEY = (
        0x04B2430C  # Used to serialize private keys in BIP32 segwit (P2WPKH)
    )
    BIP32_SEGWIT_PATH = "m/84'/0'/0'"
    BECH32_PREFIX = "bc"


class BitcoinTestNet(CryptoNetwork):
    """Bitcoin TestNet version bytes, defaulting to legacy addresses.
    From https://github.com/bitcoin/bitcoin/blob/v0.9.0rc1/src/chainparams.cpp
    """

    NAME = "Bitcoin"
    INTERNAL_NAME = wallet_pb2.Network.BITCOIN_TESTNET
    COIN = "BTC"
    TESTNET = True
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0xC4  # decimal 196
    PUBKEY_ADDRESS = 0x6F  # decimal 111
    SECRET_KEY = 0xEF  # decimal 239

    EXT_PUBLIC_KEY = 0x043587CF  # Used to serialize public keys in BIP32 legacy (P2PKH)
    EXT_SECRET_KEY = (
        0x04358394  # Used to serialize private keys in BIP32 legacy (P2PKH)
    )
    BIP32_PATH = CryptoNetwork.P2PKH_TESTNET_PATH

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None
    BECH32_PREFIX = None


class BitcoinSegwitTestNet(BitcoinTestNet):
    """Bitcoin TestNet version bytes, defaulting to segwit addresses."""

    INTERNAL_NAME = wallet_pb2.Network.BITCOIN_SEGWIT_TESTNET
    ADDRESS_MODE = ["BECH32", "BASE58"]
    SUPPORTS_SEGWIT = True
    EXT_SEGWIT_PUBLIC_KEY = (
        0x045F1CF6  # Used to serialize public keys in BIP32 segwit (P2WPKH)
    )
    EXT_SEGWIT_SECRET_KEY = (
        0x045F18BC  # Used to serialize private keys in BIP32 segwit (P2WPKH)
    )
    BIP32_SEGWIT_PATH = "m/84'/1'/0'"
    BECH32_PREFIX = "tb"


class LitecoinMainNet(CryptoNetwork):
    """Litecoin MainNet version bytes

    Primary version bytes from:
    https://github.com/litecoin-project/litecoin/blob/master-0.8/src/base58.h

    Extemded version bytes from https://bitcointalk.org/index.php?topic=453395.0
    """

    NAME = "Litecoin"
    INTERNAL_NAME = wallet_pb2.Network.LITECOIN_MAINNET
    COIN = "LTC"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x05  # decimal 5
    PUBKEY_ADDRESS = 0x30  # decimal 48
    SECRET_KEY = PUBKEY_ADDRESS + 128  # = decimal 176

    # Litecoin is using xpub/xpriv - same as Bitcoin
    # According to [1] and [2], Litecoin was supposed to use Lpub/Lprv
    # but Litecoin devs never got around to implementing that.
    # [1]: https://www.reddit.com/r/litecoin/comments/7rorqa/electrum_using_bitcoin_xpub_headers/dszq9d5/?context=3
    # [2]: https://github.com/ranaroussi/pywallet/issues/6
    EXT_PUBLIC_KEY = 0x019DA462
    EXT_SECRET_KEY = 0x019D9CFE
    BIP32_PATH = "m/44'/2'/0'"

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None
    BECH32_PREFIX = None


class LitecoinSegwitMainNet(LitecoinMainNet):
    """Litecoin MainNet version bytes, defaulting to segwit addresses."""

    INTERNAL_NAME = wallet_pb2.Network.LITECOIN_SEGWIT_MAINNET
    ADDRESS_MODE = ["BECH32", "BASE58"]
    SUPPORTS_SEGWIT = True
    EXT_SEGWIT_PUBLIC_KEY = (
        0x04B24746  # Used to serialize public keys in BIP32 segwit (P2WPKH)
    )
    EXT_SEGWIT_SECRET_KEY = (
        0x04B2430C  # Used to serialize private keys in BIP32 segwit (P2WPKH)
    )
    BIP32_SEGWIT_PATH = "m/84'/2'/0'"
    BECH32_PREFIX = "ltc"


class LitecoinBTCMainNet(CryptoNetwork):
    """Litecoin MainNet version bytes

    Primary version bytes from:
    https://github.com/litecoin-project/litecoin/blob/master-0.8/src/base58.h

    Extended version bytes same as bitcoin's
    """

    NAME = "Litecoin"
    INTERNAL_NAME = wallet_pb2.Network.LITECOIN_BTC_MAINNET
    COIN = "LTC"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x05  # decimal 5
    PUBKEY_ADDRESS = 0x30  # decimal 48
    SECRET_KEY = PUBKEY_ADDRESS + 128  # = decimal 176

    # Litecoin is using xpub/xpriv - same as Bitcoin
    # According to [1] and [2], Litecoin was supposed to use Lpub/Lprv
    # but Litecoin devs never got around to implementing that.
    # Although some wallets such as Trezor are still implementing Ltub/Ltpv
    # [1]: https://www.reddit.com/r/litecoin/comments/7rorqa/electrum_using_bitcoin_xpub_headers/dszq9d5/?context=3
    # [2]: https://github.com/ranaroussi/pywallet/issues/6
    EXT_PUBLIC_KEY = 0x0488B21E
    EXT_SECRET_KEY = 0x0488ADE4
    BIP32_PATH = "m/44'/2'/0'"

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None
    BECH32_PREFIX = None


class LitecoinBTCSegwitMainNet(LitecoinBTCMainNet):
    """Litecoin MainNet version bytes, defaulting to segwit addresses."""

    INTERNAL_NAME = wallet_pb2.Network.LITECOIN_BTC_SEGWIT_MAINNET
    ADDRESS_MODE = ["BECH32", "BASE58"]
    SUPPORTS_SEGWIT = True
    EXT_SEGWIT_PUBLIC_KEY = (
        0x04B24746  # Used to serialize public keys in BIP32 segwit (P2WPKH)
    )
    EXT_SEGWIT_SECRET_KEY = (
        0x04B2430C  # Used to serialize private keys in BIP32 segwit (P2WPKH)
    )
    BIP32_SEGWIT_PATH = "m/84'/2'/0'"
    BECH32_PREFIX = "ltc"


class LitecoinTestNet(CryptoNetwork):
    """Litecoin TestNet version bytes

    Primary version bytes from:
    https://github.com/litecoin-project/litecoin/blob/master-0.8/src/base58.h

    Litecoin testnet extended version bytes for legacy are the same as for Bitcoin testnet
    so we will just reuse the segwit for Bitcoin testnet as well. There is no official document
    I could find that supports this though.
    """

    NAME = "Litecoin"
    INTERNAL_NAME = wallet_pb2.Network.LITECOIN_MAINNET
    COIN = "LTC"
    TESTNET = True
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0xC4  # decimal 196
    PUBKEY_ADDRESS = 0x6F  # decimal 111
    SECRET_KEY = PUBKEY_ADDRESS + 128  # = decimal 239

    EXT_PUBLIC_KEY = 0x0436F6E1
    EXT_SECRET_KEY = 0x0436EF7D
    BIP32_PATH = CryptoNetwork.P2PKH_TESTNET_PATH

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None
    BECH32_PREFIX = None


class LitecoinSegwitTestNet(LitecoinTestNet):
    """Litecoin TestNet version bytes, defaulting to segwit addresses."""

    INTERNAL_NAME = wallet_pb2.Network.LITECOIN_MAINNET
    ADDRESS_MODE = ["BECH32", "BASE58"]
    SUPPORTS_SEGWIT = True
    EXT_SEGWIT_PUBLIC_KEY = (
        0x045F1CF6  # Used to serialize public keys in BIP32 segwit (P2WPKH)
    )
    EXT_SEGWIT_SECRET_KEY = (
        0x045F18BC  # Used to serialize private keys in BIP32 segwit (P2WPKH)
    )
    BIP32_SEGWIT_PATH = "m/84'/1'/0'"
    BECH32_PREFIX = "tltc"


class DogecoinMainNet(CryptoNetwork):
    """Dogecoin MainNet version bytes

    Primary version bytes from:
    https://github.com/dogecoin/dogecoin/blob/1.5.2/src/base58.h

    Unofficial extended version bytes from
    https://bitcointalk.org/index.php?topic=409731
    """

    NAME = "Dogecoin"
    INTERNAL_NAME = wallet_pb2.Network.DOGECOIN_MAINNET
    COIN = "DOGE"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x16  # decimal 22
    PUBKEY_ADDRESS = 0x1E  # decimal 30
    SECRET_KEY = PUBKEY_ADDRESS + 128  # decimal 158

    # Unofficial extended version bytes taken from
    # https://bitcointalk.org/index.php?topic=409731
    # and https://github.com/dogecoin/dogecoin/blob/3a29ba6d497cd1d0a32ecb039da0d35ea43c9c85/src/chainparams.cpp
    EXT_PUBLIC_KEY = 0x02FACAFD
    EXT_SECRET_KEY = 0x02FAC398
    BIP32_PATH = "m/44'/3'/0'"

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None  # P2WPKH not supported
    BECH32_PREFIX = None  # Bech32 not supported


class DogecoinBTCMainNet(CryptoNetwork):
    """Dogecoin MainNet version bytes

    Primary version bytes from:
    https://github.com/dogecoin/dogecoin/blob/1.5.2/src/base58.h

    Extended version bytes are the same as for Bitocin mainnet,
    i.e. xpub/xprv, for wallet compatibility.
    """

    NAME = "Dogecoin"
    INTERNAL_NAME = wallet_pb2.Network.DOGECOIN_BTC_MAINNET
    COIN = "DOGE"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x16  # decimal 22
    PUBKEY_ADDRESS = 0x1E  # decimal 30
    SECRET_KEY = PUBKEY_ADDRESS + 128  # decimal 158

    # Unofficial extended version bytes taken from
    # https://bitcointalk.org/index.php?topic=409731
    # and https://github.com/dogecoin/dogecoin/blob/3a29ba6d497cd1d0a32ecb039da0d35ea43c9c85/src/chainparams.cpp
    EXT_PUBLIC_KEY = 0x02FACAFD
    EXT_SECRET_KEY = 0x02FAC398
    BIP32_PATH = "m/44'/3'/0'"

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None  # P2WPKH not supported
    BECH32_PREFIX = None  # Bech32 not supported


class DogecoinTestNet(CryptoNetwork):
    """Dogecoin TestNet version bytes

    Primary version bytes from:
    https://github.com/dogecoin/dogecoin/blob/1.5.2/src/base58.h

    Unofficial extended version bytes from
    https://bitcointalk.org/index.php?topic=409731
    """

    NAME = "Dogecoin"
    INTERNAL_NAME = wallet_pb2.Network.DOGECOIN_TESTNET
    COIN = "DOGE"
    TESTNET = True
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0xC4  # decimal 196
    PUBKEY_ADDRESS = 0x71  # decimal 113
    SECRET_KEY = PUBKEY_ADDRESS + 128  # decimal 241

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    # Unofficial extended version bytes taken from
    # https://bitcointalk.org/index.php?topic=409731
    EXT_PUBLIC_KEY = 0x0432A9A8
    EXT_SECRET_KEY = 0x0432A243
    BIP32_PATH = CryptoNetwork.P2PKH_TESTNET_PATH

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None  # P2WPKH not supported
    BECH32_PREFIX = None  # Bech32 not supported


class BlockcypherTestNet(CryptoNetwork):
    """Blockcypher TestNet version bytes.
    From http://dev.blockcypher.com/#testing
    """

    NAME = "BlockCypher"
    INTERNAL_NAME = wallet_pb2.Network.BLOCKCYPHER_TESTNET
    COIN = "BCY"
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x1F  # decimal 31
    PUBKEY_ADDRESS = 0x1B  # decimal 27
    SECRET_KEY = 0x49  # decimal 73
    EXT_PUBLIC_KEY = 0x2D413FF  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x2D40FC3  # Used to serialize private BIP32 addresses
    BIP32_PATH = CryptoNetwork.P2PKH_TESTNET_PATH

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = False
    CHAIN_ID = None
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None  # P2WPKH not supported
    BECH32_PREFIX = None  # Bech32 not supported


class EthereumMainNet(CryptoNetwork):
    """Ethereum MainNet version bytes."""

    NAME = "Ethereum"
    INTERNAL_NAME = wallet_pb2.Network.ETHEREUM_MAINNET
    COIN = "ETH"
    TESTNET = False
    ADDRESS_MODE = ["HEX"]

    # Ethereum doesn't put version bytes in front of keys or addresses.
    SCRIPT_ADDRESS = None
    PUBKEY_ADDRESS = None
    SECRET_KEY = None

    # I believe ETH uses BIP32
    EXT_PUBLIC_KEY = 0x0488B21E
    EXT_SECRET_KEY = 0x0488ADE4
    BIP32_PATH = "m/44'/60'/0'"

    SUPPORTS_SEGWIT = False
    SUPPORTS_EVM = True
    CHAIN_ID = 1  # Ethereum Mainnet
    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_SECRET_KEY = None
    BIP32_SEGWIT_PATH = None  # P2WPKH not supported
    BECH32_PREFIX = None  # Bech32 not supported


class EthereumSepoliaTestNet(EthereumMainNet):
    """Ethereum Sepolia TestNet version bytes."""

    # TESTNET flag is exclusively used for Bitcoin-like networks.
    # Instead we just hcange the CHAIN_ID
    CHAIN_ID = 11155111
