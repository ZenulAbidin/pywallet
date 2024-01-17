Bugs and Limitations
--------------------
While we strive to keep ZPyWallet as bug-free as possible, sometimes errors do slip in. Here are a list of things that are currently not supported by ZPywallet:

**Bugs:**

- Individual address providers only retain the transaction history of the last provider address. As a workaround, use the load balancer
  instead. (This is a bug.)

**Limitations:**

- ``Desination`` classes **do not take integer sats or wei values.** They only take floating-point values, which means that if you are careless
with doing monetary arithmetic, your amount might be slightly wrong. For example, if you calculate 0.1+0.2 in floating point, you will get
0.30000000000000004, not 0.3. This issue particularly affects Ethereum amounts since it uses 18 decimal places. In order to avoid this pitfall,
use Python's ``Decimal`` class and convert the floating-point values to strings first before doing arithmetic, like this:

.. code-block:: python

    from decimal import Decimal
    a = 0.1
    b = 0.2
    amount = float(Decimal(str(a)) + Decimal(str(b)))

We do not currently provide helper functions for this.

For more information about this error which is prevalent in most programming languages, see `Floating Point Math <https://0.30000000000000004.com/>`_.

- ZPyWallet cannot send coins from script hashes eg. P2SH, P2WSH addresses.

- Multisig is not supported.

- P2WPKH-P2SH is currently not supported.

- Timelocks are currently not supported.

- In the case of Ethereum, contract addresses are not officially supported. Interaction may not work.

Indices and Tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

