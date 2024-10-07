ZPyWallet
===========

.. image:: https://img.shields.io/pypi/pyversions/zpywallet.svg?maxAge=60
    :target: https://pypi.python.org/pypi/zpywallet
    :alt: Python version

.. image:: https://img.shields.io/pypi/v/zpywallet.svg?maxAge=60
    :target: https://pypi.python.org/pypi/zpywallet
    :alt: PyPi version

.. image:: https://img.shields.io/pypi/status/zpywallet.svg?maxAge=60
    :target: https://pypi.python.org/pypi/zpywallet
    :alt: PyPi status

.. image:: https://codecov.io/gh/ZenulAbidin/zpywallet/branch/master/graph/badge.svg?token=G2tC6LpTNm
    :target: https://codecov.io/gh/ZenulAbidin/zpywallet
    :alt: Code coverage

.. image:: https://i.imgur.com/h611jJK.png
    :alt: Logo

ZPyWallet is a Python-based hierarchical deterministic (HD) wallet generator and transaction manager.
HD wallets allow you to  generate a tree-like structure of cryptographic key pairs from a single
seed phrase, providing a convenient way to manage multiple accounts or addresses securely.

ZPyWallet can generate transactions quickly, because it defers transaction validity to the broadcasting
stage. It can also coordinate the creation and broadcasting of transactions to different nodes,
and can decode transactions as well.

BIP32 (or HD for "hierarchical deterministic") wallets allow you to create
child wallets which can only generate public keys and don't expose a
private key to an insecure server.

**This is beta software. Only use it if you know what you're doing. There might be bugs.**


Features
========

- Simple BIP32 (HD) wallet creation for BTC, BCH, ETH, LTC, DASH, DOGE, and many other networks
- Generate a hierarchical deterministic wallet from a mnemonic seed phrase.
- Create and broadcast RBF-aware transactions to pre-defined or custom nodes
- Decode existing transactions
- Monitor for incoming transactions
- Get the latest fee rates for mainnet networks
- Derive multiple accounts or addresses from the generated wallet.
- Support for popular cryptocurrencies such as Bitcoin, Ethereum, and more.
- BIP32 and BIP39 compliant.
- Secure key generation using the industry-standard libsecp256k1 library, resistant to side-channel attacks.
- Supports generating P2WPKH (segwit) keys and bech32 addresses for supported networks
- Sign and verify messages in Bitcoin-Qt and RFC2440 format

Limitations
===========

- Address types that use complex scripts such as P2WSH, P2WPKH-P2SH, and Taproot currently can only be decoded but not created.
- Multisig addresses are not supported.
- Transactions cannot be created with timelocks yet.
- In the case of Ethereum, alternate chains (e.g. Testnet) are not supported yet.

History
=======

ZPyWallet started out as a fork of `PyWallet <https://github.com/ranaroussi/pywallet>` with elements of
`Bitmerchant <https://github.com/sbuss/bitmerchant>`, just to simply make these modules run. At the time,
it was just an HD wallet generator. However, as time went by, I discovered serious bugs in both programs,
such as incorrect master private key genration, and the use of ECDSA code that is vulnerable to side-channel
attacks, Thus I have embarked on a complete rewrite of the codebase so that it follows crypto security best
practices. And thus we arrive to the present day: A robust wallet generator that supports altcoins, segwit,
sign/verify, and can be used as a backend to implement custom wallet software.

Enjoy!

--------------

Installation
-------------

Install via PiP:

.. code:: bash

   $ pip install zpywallet

Or build directly:

.. code:: bash

   $ git clone https://github.com/ZenulAbidin/zpywallet
   $ cd zpywallet
   # Developers should also run "pip install -r requirements-dev.txt"
   $ python setup.py install


Example code:
=============

Consult the documentation for up-to-date code snippets.

Contributing
============

Bugfixes and enhancements are welcome. Please read CONTRIBUTING.md for contributing instructions.

At the moment, I'm not accepting pull requests for new coins unless they are big and historic coins such as Tether (ERC20), BNB and XMR.

Security
========

This module has been hardened against various types of attacks:

- Runtime dependencies are kept to an absolute minimum. Only modules that have compile-time native
  code are installed using pip. The rest are hardcoded directly into ZPyWallet. This prevents many kinds
  of supply chain attacks.
- All random numbers are generated with a secure RNG. ZPyWallet does not use pseudorandom number generators.
- Coincurve is using libsecp256k1, which protects keys from various power and RF frequency analysis side-channels.


NO WARRANTY
===========

ZPyWallet is provided without any sort of warranty of any kind. Additionally, I am not responsible for damages caused by the use of this program, including but not limited to lost coins. Read the license file for full details.
