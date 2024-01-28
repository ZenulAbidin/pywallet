
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


ZPyWallet is a Python-based hierarchical deterministic (HD) wallet generator and transaction manager.
HD wallets allow you to  generate a tree-like structure of cryptographic key pairs from a single
seed phrase, providing a convenient way to manage multiple accounts or addresses securely.

ZPyWallet can generate transactions quickly, because it defers transaction validity to the broadcasting
stage. It can also coordinate the creation and broadcasting of transactions to different nodes,
and can decode transactions as well.

BIP32 (or HD for "hierarchical deterministic") wallets allow you to create
child wallets which can only generate public keys and don't expose a
private key to an insecure server.


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

Note that this code is probably out-of-date.

Create HD Wallet
----------------

The following code creates a new Bitcoin HD wallet:

.. code:: python

    # create_btc_wallet.py

    from zpywallet import wallet

    # creates a wallet with a new, random mnemonic phrase.
    # By default, it creates Bitcoin Mainnet wallets.
    w = wallet.create_wallet_json(children=1)

    print(w)

Output looks like this:

.. code:: bash

    $ python create_btc_wallet.py

    {
        'address': 'bc1qjvugs62gt5w97rv4sw3kkhnmv2s2kg58lucmux',
        'children': [{'address': 'bc1q5vyxj4a6c2v4p9dxrd59vztfussg9hdywr5yrn',
                    'bip32_path': "m/44'/0'/0'/0",
                    'path': 'm/0',
                    'xpublic_key': 'xpub68yG1oCYQLpAKxj3DPo6cvqAzNEeUFMhMfEhXcEyem1vqK87QeaQH8o7uUw8fYkhtuVcMiJrxbLFDyESnK8YPQ97fSzPpPLTiauEWyqTX76'}],
        'coin': 'BTC',
        'private_key': '45471d4504a3631425371a590d168fa0df4f01c7fe5df2b355da6434145b6915',
        'public_key': '0286e42376ab09ce71b2be8174f2ebbf2f79fef9ca0c255838c2016951b7b4411f',
        'seed': 'spring ahead flat scheme can opera genre tribe airport friend nurse '
                'exclude',
        'wif': '5JLoBxMCZCAqnue56GZZLquzPwob6XHdJttKJn19qGShKQgE2xM',
        'xprivate_key': 'xprv9s21ZrQH143K28nnAjfgJ9eRCmQMYuBtbKWVZLqsEc7aBYh81uLFHQoKt2dZdSyKAu6KaFSiqjWyZejrtx3FmRjRaf1KsBFgkNM4CMm66Jh',
        'xpublic_key': 'xpub661MyMwAqRbcEcsFGmCgfHb9koEqxMujxYS6MjFUnweZ4M2GZSeVqD7ojJAE5QvmbXn16QPHcHLk5bkdkqXtcV1nj1aVyRqax9NeaTAnhH6',
        'xpublic_key_prime': 'xpub68yG1oCgk1M8XBxmkp6f6JgRdTyX6XJd7a6LmDG14DomrswTMkxGiByKiwpf5p6szSqDciybesxjDC7yKBrgbaczQe6q1puBHbvfKxg1uqr'
    }

Similarly, you can do the same for an Ethereum wallet:

.. code:: python

    # create_eth_wallet.py

    from zpywallet import wallet
    
    w = wallet.create_wallet_json(network="ETH", children=1)

    print(w)

Output looks like this (no WIF or xpub/prv for Ethereum as its not supported):

.. code:: bash

    $ python create_eth_wallet.py

    {
        'address': '0x8dbe02c146eacbe410f63348f489a16160deb6f0',
        'children': [{'address': '0xdd030270458ad17b125c200bb2f11d0fdbf7e05c',
                    'path': 'm/0'}],
        'coin': 'ETH',
        'private_key': '85b41c45f425dd1f7f431326449afc0564b2d110f7f89563f1a1ee4055a4ce39',
        'public_key': '026e93d77ee81bd28e2d2e0962928a00ee27a20f0da2b7437db8bce39e23c6d873',
        'seed': 'admit push digital opinion system snap announce help gas business '
                'trigger please',
        'wif': '',
        'xprivate_key': '',
        'xpublic_key': ''}

Consult the documentation for more information about the API.

Create Child Wallet
-------------------

You can create child-wallets (BIP32 wallets) from the HD wallet's
**Extended Public Key** to generate new public addresses without
revealing your private key.

Example:

.. code-block:: python

    # create_child_wallet.py

    from zpywallet import wallet
    from zpywallet.utils.bip32 import Wallet

    w = Wallet.from_mnemonic(wallet.generate_mnemonic())

    # generate address for specific user (id = 10)
    child_w = w.get_child_for_path("m/10")
    user_addr = child_w.address()

    print(f"User Address: {user_addr}")

Output looks like this:

.. code:: bash

    $ python create_child_wallet.py

    User Address: bc1qdwfh4duva4hvzva9cdyguh9c9k2hez3r7taerg


CONTRIBUTING
============

Bugfixes and enhancements are welcome. Please read CONTRIBUTING.md for contributing instructions.

At the moment, I'm not accepting pull requests for new coins unless they are big and historic coins such as Tether (ERC20), BNB and XMR.

SECURITY
========

This module has been hardened against various types of attacks:

- Runtime dependencies are kept to an absolute minimum. Only modules that have compile-time native
  code are installed using pip. The rest are hardcoded directly into ZPyWallet. This prevents many kinds
  of supply chain attacks.
- Coincurve is using libsecp256k1, which protects keys from various power and RF frequency analysis side-channels.


NO WARRANTY
===========

ZPyWallet is provided without any sort of warranty of any kind. Additionally, I am not responsible for damages caused by the use of this program, including but not limited to lost coins. Read the license file for full details.
