"""
This file contains parameters and constants for all supported networks.
"""

class BitcoinCashMainNet(object):
    """ Bitcoin Cash MainNet version bytes. """
    NAME = "Bitcoin Cash"
    COIN = "BCH"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x28  # int(0x28) = 40
    PUBKEY_ADDRESS = 0x1C  # int(0x00) = 28  # Used to create payment addresses
    SECRET_KEY = 0x80      # int(0x80) = 128  # Used for WIF format
    # same as Bitcoin
    EXT_PUBLIC_KEY = 0x0488b21E  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x0488ADE4  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/145'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported


class DashMainNet(object):
    """ Dash MainNet version bytes.
    
    OK, time for a little drama - Dash's xpub/xprv were originally drkp/drkv.

    But somehow, they were swapped when inerted into the refernece client.
    So there are actually two possible combinations of addresses in Dash
    (3, if you also count Bitcoin's xpub/xprv)

    See: https://www.dash.org/forum/index.php?threads/dash-bip32-serialization-values-dev-discussion-wont-apply-to-most.8092/
    """
    NAME = "Dash"
    COIN = "DASH"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x10  # int(0x10) = 16
    PUBKEY_ADDRESS = 0x4C  # int(0x4C) = 76  # Used to create payment addresses
    SECRET_KEY = 0xCC      # int(0xCC) = 204  # Used for WIF format
    EXT_PUBLIC_KEY = 0x02fe52cc  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x02fe52f8  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/5'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported

class DashInvertedMainNet(object):
    """Dash MainNet version bytes.
    
    This is the version that uses drkv/drkp as the public/private
    extended version bytes respectively. It intentionally has the same name
    and coin as the other Dash mainnets.
    """
    NAME = "Dash"
    COIN = "DASH"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x10  # int(0x10) = 16
    PUBKEY_ADDRESS = 0x4C  # int(0x4C) = 76  # Used to create payment addresses
    SECRET_KEY = 0xCC      # int(0xCC) = 204  # Used for WIF format
    EXT_PUBLIC_KEY = 0x02fe52f8  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x02fe52cc  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/5'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported

class DashBTCMainNet(object):
    """Dash MainNet version bytes.
    
    Extended version bytes are the same as for Bitcoin, i.e. xpub/xprv,
    for maximum wallet compatibility.
    """
    NAME = "Dash"
    COIN = "DASH"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x10  # int(0x10) = 16
    PUBKEY_ADDRESS = 0x4C  # int(0x4C) = 76  # Used to create payment addresses
    SECRET_KEY = 0xCC      # int(0xCC) = 204  # Used for WIF format
    EXT_PUBLIC_KEY = 0X0488B21E  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0X0488ADE4  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/5'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported


class DashTestNet(object):
    """Dash TestNet version bytes."""
    NAME = "Dash"
    COIN = "DASH"
    TESTNET = True
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x13  # int(0x13) = 19
    PUBKEY_ADDRESS = 0x8C  # int(0x8C) = 140  # Used to create payment addresses
    SECRET_KEY = 0xEF      # int(0xEF) = 239  # Used for WIF format
    EXT_PUBLIC_KEY = 0x3a805837  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x3a8061a0  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/1'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported

class DashInvertedTestNet(object):
    """Dash TestNet version bytes with inverted extended version bytes."""
    NAME = "Dash"
    COIN = "DASH"
    TESTNET = True
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x13  # int(0x13) = 19
    PUBKEY_ADDRESS = 0x8C  # int(0x8C) = 140  # Used to create payment addresses
    SECRET_KEY = 0xEF      # int(0xEF) = 239  # Used for WIF format
    EXT_PUBLIC_KEY = 0x3a8061a0  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x3a805837  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/1'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported

class OmniMainNet(object):
    """Bitcoin MainNet version bytes.
    From https://github.com/OmniLayer/omnicore/blob/develop/src/chainparams.cpp
    """
    NAME = "Omni"
    COIN = "USDT"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x05  # int(0x05) = 5
    PUBKEY_ADDRESS = 0x00  # int(0x00) = 0  # Used to create payment addresses
    SECRET_KEY = 0x80      # int(0x80) = 128  # Used for WIF format
    EXT_PUBLIC_KEY = 0x0488B21E  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x0488ADE4  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/0'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported

class OmniTestNet(object):
    """Bitcoin MainNet version bytes.
    From https://github.com/OmniLayer/omnicore/blob/develop/src/chainparams.cpp
    """
    NAME = "Omni"
    COIN = "USDT"
    TESTNET = True
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0xc4  # int(0xc4) = 196
    PUBKEY_ADDRESS = 0x6f  # int(0x6f) = 111  # Used to create payment addresses
    SECRET_KEY = 0xef      # int(0xef) = 239  # Used for WIF format
    EXT_PUBLIC_KEY = 0x043587CF  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x04358394  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/0'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported

class BitcoinMainNet(object):
    """Bitcoin MainNet version bytes.
    From https://github.com/bitcoin/bitcoin/blob/v0.9.0rc1/src/chainparams.cpp
    """
    NAME = "Bitcoin"
    COIN = "BTC"
    TESTNET = False
    ADDRESS_MODE = ["BECH32", "BASE58"]
    SCRIPT_ADDRESS = 0x05  # int(0x05) = 5
    PUBKEY_ADDRESS = 0x00  # int(0x00) = 0  # Used to create payment addresses
    SECRET_KEY = 0x80      # int(0x80) = 128  # Used for WIF format

    EXT_PUBLIC_KEY = 0x0488B21E  # Used to serialize public keys in BIP32 legacy (P2PKH)
    EXT_SECRET_KEY = 0x0488ADE4  # Used to serialize private keys in BIP32 legacy (P2PKH)
    BIP32_PATH = "m/44'/0'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = 0x04b24746 # Used to serialize public keys in BIP32 segwit (P2WPKH)
    EXT_SEGWIT_PRIVATE_KEY = 0x04b2430c # Used to serialize private keys in BIP32 segwit (P2WPKH)
    BIP32_SEGWIT_PATH = "m/84'/0'/0'/"
    BECH32_PREFIX = "bc"

class BitcoinTestNet(object):
    """Bitcoin TestNet version bytes.
    From https://github.com/bitcoin/bitcoin/blob/v0.9.0rc1/src/chainparams.cpp
    """
    NAME = "Bitcoin"
    COIN = "BTC"
    TESTNET = True
    ADDRESS_MODE = ["BECH32", "BASE58"]
    SCRIPT_ADDRESS = 0xc4  # int(0xc4) = 196
    PUBKEY_ADDRESS = 0x6f  # int(0x6f) = 111
    SECRET_KEY = 0xEF      # int(0xef) = 239

    EXT_PUBLIC_KEY = 0x043587CF # Used to serialize public keys in BIP32 legacy (P2PKH)
    EXT_SECRET_KEY = 0x04358394 # Used to serialize private keys in BIP32 legacy (P2PKH)
    BIP32_PATH = "m/44'/1'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = 0x045f1cf6 # Used to serialize public keys in BIP32 segwit (P2WPKH)
    EXT_SEGWIT_PRIVATE_KEY = 0x045f18bc # Used to serialize private keys in BIP32 segwit (P2WPKH)
    BIP32_SEGWIT_PATH = "m/84'/1'/0'/"
    BECH32_PREFIX = "tb"

class LitecoinMainNet(object):
    """Litecoin MainNet version bytes

    Primary version bytes from:
    https://github.com/litecoin-project/litecoin/blob/master-0.8/src/base58.h

    Extemded version bytes from https://bitcointalk.org/index.php?topic=453395.0
    """
    NAME = "Litecoin"
    COIN = "LTC"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x05  # int(0x05) = 5
    PUBKEY_ADDRESS = 0x30  # int(0x30) = 48
    SECRET_KEY = PUBKEY_ADDRESS + 128  # = int(0xb0) = 176

    # Litecoin is using xpub/xpriv - same as Bitcoin
    # According to [1] and [2], Litecoin was supposed to use Lpub/Lprv
    # but Litecoin devs never got around to implementing that.
    # [1]: https://www.reddit.com/r/litecoin/comments/7rorqa/electrum_using_bitcoin_xpub_headers/dszq9d5/?context=3
    # [2]: https://github.com/ranaroussi/pywallet/issues/6
    EXT_PUBLIC_KEY = 0x019da462
    EXT_SECRET_KEY = 0x019d9cfe
    BIP32_PATH = "m/44'/2'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported

class LitecoinBTCMainNet(object):
    """Litecoin MainNet version bytes

    Primary version bytes from:
    https://github.com/litecoin-project/litecoin/blob/master-0.8/src/base58.h

    Extended version bytes same as bitcoin's
    """
    NAME = "Litecoin"
    COIN = "LTC"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x05  # int(0x05) = 5
    PUBKEY_ADDRESS = 0x30  # int(0x30) = 48
    SECRET_KEY = PUBKEY_ADDRESS + 128  # = int(0xb0) = 176

    # Litecoin is using xpub/xpriv - same as Bitcoin
    # According to [1] and [2], Litecoin was supposed to use Lpub/Lprv
    # but Litecoin devs never got around to implementing that.
    # Although some wallets such as Trezor are still implementing Ltub/Ltpv
    # [1]: https://www.reddit.com/r/litecoin/comments/7rorqa/electrum_using_bitcoin_xpub_headers/dszq9d5/?context=3
    # [2]: https://github.com/ranaroussi/pywallet/issues/6
    EXT_PUBLIC_KEY = 0x0488B21E
    EXT_SECRET_KEY = 0x0488ADE4

    BIP32_PATH = "m/44'/2'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = 0x04b24746 # Used to serialize public keys in BIP32 segwit (P2WPKH)
    EXT_SEGWIT_PRIVATE_KEY = 0x04b2430c # Used to serialize private keys in BIP32 segwit (P2WPKH)
    BIP32_SEGWIT_PATH = "m/84'/0'/0'/"
    BECH32_PREFIX = None # Bech32 not supported

class LitecoinTestNet(object):
    """Litecoin TestNet version bytes

    Primary version bytes from:
    https://github.com/litecoin-project/litecoin/blob/master-0.8/src/base58.h
    """
    NAME = "Litecoin"
    COIN = "LTC"
    TESTNET = True
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0xc4  # int(0xc4) = 196
    PUBKEY_ADDRESS = 0x6f  # int(0x6f) = 111
    SECRET_KEY = PUBKEY_ADDRESS + 128  # = int(0xef) = 239

    EXT_PUBLIC_KEY = 0x0436f6e1
    EXT_SECRET_KEY = 0x0436ef7d
    BIP32_PATH = "m/44'/1'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported


class DogecoinMainNet(object):
    """Dogecoin MainNet version bytes

    Primary version bytes from:
    https://github.com/dogecoin/dogecoin/blob/1.5.2/src/base58.h

    Unofficial extended version bytes from
    https://bitcointalk.org/index.php?topic=409731
    """
    NAME = "Dogecoin"
    COIN = "DOGE"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x16  # int(0x16) = 22
    PUBKEY_ADDRESS = 0x1e  # int(0x1e) = 30
    SECRET_KEY = PUBKEY_ADDRESS + 128  # int(0x9e) = 158

    # Unofficial extended version bytes taken from
    # https://bitcointalk.org/index.php?topic=409731
    # and https://github.com/dogecoin/dogecoin/blob/3a29ba6d497cd1d0a32ecb039da0d35ea43c9c85/src/chainparams.cpp
    EXT_PUBLIC_KEY = 0x02facafd
    EXT_SECRET_KEY = 0x02fac398
    BIP32_PATH = "m/44'/3'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported


class DogecoinBTCMainNet(object):
    """Dogecoin MainNet version bytes

    Primary version bytes from:
    https://github.com/dogecoin/dogecoin/blob/1.5.2/src/base58.h

    Extended version bytes are the same as for Bitocin mainnet,
    i.e. xpub/xprv, for wallet compatibility.
    """
    NAME = "Dogecoin"
    COIN = "DOGE"
    TESTNET = False
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x16  # int(0x16) = 22
    PUBKEY_ADDRESS = 0x1e  # int(0x1e) = 30
    SECRET_KEY = PUBKEY_ADDRESS + 128  # int(0x9e) = 158

    # Unofficial extended version bytes taken from
    # https://bitcointalk.org/index.php?topic=409731
    # and https://github.com/dogecoin/dogecoin/blob/3a29ba6d497cd1d0a32ecb039da0d35ea43c9c85/src/chainparams.cpp
    EXT_PUBLIC_KEY = 0x02facafd
    EXT_SECRET_KEY = 0x02fac398
    BIP32_PATH = "m/44'/3'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported


class DogecoinTestNet(object):
    """Dogecoin TestNet version bytes

    Primary version bytes from:
    https://github.com/dogecoin/dogecoin/blob/1.5.2/src/base58.h

    Unofficial extended version bytes from
    https://bitcointalk.org/index.php?topic=409731
    """
    NAME = "Dogecoin"
    COIN = "DOGE"
    TESTNET = True
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0xc4  # int(0xc4) = 196
    PUBKEY_ADDRESS = 0x71  # int(0x71) = 113
    SECRET_KEY = PUBKEY_ADDRESS + 128  # int(0xf1) = 241

    # Unofficial extended version bytes taken from
    # https://bitcointalk.org/index.php?topic=409731
    EXT_PUBLIC_KEY = 0x0432a9a8
    EXT_SECRET_KEY = 0x0432a243
    BIP32_PATH = "m/44'/1'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported


class BlockCypherTestNet(object):
    """BlockCypher TestNet version bytes.
    From http://dev.blockcypher.com/#testing
    """
    NAME = "BlockCypher"
    COIN = "BCY"
    ADDRESS_MODE = ["BASE58"]
    SCRIPT_ADDRESS = 0x1f  # int(0x1f) = 31
    PUBKEY_ADDRESS = 0x1b  # int(0x1b) = 27  # Used to create payment addresses
    SECRET_KEY = 0x49      # int(0x49) = 73  # Used for WIF format
    EXT_PUBLIC_KEY = 0x2d413ff  # Used to serialize public BIP32 addresses
    EXT_SECRET_KEY = 0x2d40fc3  # Used to serialize private BIP32 addresses
    BIP32_PATH = "m/44'/1'/0'/"

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported

class EthereumMainNet(object):
    """Ethereum MainNet version bytes."""
    NAME = "Ethereum"
    COIN = "ETH"
    TESTNET = False
    ADDRESS_MODE = ["HEX"]

    # Ethereum doesn't put version bytes in front of keys or addresses.
    SCRIPT_ADDRESS = None
    PUBKEY_ADDRESS = None
    SECRET_KEY = None

    EXT_PUBLIC_KEY = None  # Ethereum does not use BIP32
    EXT_SECRET_KEY = None  # Ethereum does not use BIP32
    BIP32_PATH = None  # Ethereum does not use BIP32

    EXT_SEGWIT_PUBLIC_KEY = None
    EXT_SEGWIT_PRIVATE_KEY = None
    BIP32_SEGWIT_PATH = None # P2WPKH not supported
    BECH32_PREFIX = None # Bech32 not supported
