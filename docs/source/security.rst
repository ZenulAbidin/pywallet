Security
========

When you create cryptocurrency applications, there are a few basic procedures you need to perform to ensure that your code runs safely and securely.
Additionally, it is important to use a library that does not leak private keys and other secret data for potential attackers to use. Unfortunately,
many libraries on the internet are not suitable for this kind of production use because they do not pay attention to security. ZPywallet aims to be
a wallet implementaiton safe for production use. Should you find any security vulnerability, please follow the instructions in the
`Security Policy <https://github.com/ZenulAbidin/zpywallet/tree/master/SECURITY.md>`_ to report it safely.

Keys
====

ZPyWallet uses the industry-standard libsecp256k1 library to generate private keys. This library has been audited by many researchers and independent
firms, and is resistant to make different kinds of key sniffing attacks.

For creating seed phrases, ZPyWallet sources entropy from ``os.urandom``. On Unix-like systems, this gets entropy from ``/dev/urandom``. On Windows,
it use the ``CryptAcquireContextA`` and ``CryptGenRandom`` functions to get entropy. The entropy gathered through these functions is high quality.
Nevertheless, if you do not trust the strength of the entropy sources on your system, you also have the option to supply your own entropy.

Auditing
========

ZPyWallet has not been audited by a security organization or researcher. However, we have taken steps to ensure that it is both easy to use and save
for production use. Sensitive data inside the library is wiped after it is used. Additionally, all private keys and seed phrases inside the wallet
are in an encrypted state when they are not needed.

Tips For Creating Secure Applications
=====================================

- Never put private keys or seed phrases directly in source code. Store them in environment variables or another secure solution.
- Always use the library methods for generating private keys, seeds, and wallets. These have high entropy. Avoid using your own entropy
  unless you are certain that it is secure.
- Do not use brainwallets in production applications.
- Always protect your wallets with a strong password.
- Regularly review and update the dependencies in your project to mitigate security vulnerabilities.

Indices and Tables
------------------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

