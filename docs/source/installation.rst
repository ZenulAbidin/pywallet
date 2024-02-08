Installation
============

To start using ZPyWallet, you can choose to install it either from PyPI using `pip` or from source using `setup.py`.

Installing from PyPI
--------------------
Follow the steps below to install ZPyWallet from PyPI using `pip`:

1. Create a virtual environment (optional but recommended) to isolate the ZPyWallet installation from your system-wide Python packages.

2. Activate the virtual environment.

3. Install ZPyWallet by running the following command:

   .. code-block:: bash

      pip install zpywallet

   This command will download and install the latest version of ZPyWallet from the Python Package Index (PyPI) along with its dependencies.

4. Verify the installation by importing ZPyWallet in a Python script or interactive Python session:

   .. code-block:: python

      import zpywallet

   If the import succeeds without any errors, the installation was successful.

5. Congratulations! You have successfully installed ZPyWallet.

Installing from Source
----------------------
If you prefer to install ZPyWallet from source or want to contribute to its development, you can follow these steps:

1. Clone the ZPyWallet repository from the GitHub repository:

   .. code-block:: bash

      git clone https://github.com/ZenulAbidin/zpywallet.git

2. Navigate to the cloned directory:

   .. code-block:: bash

      cd zpywallet

3. Install ZPyWallet and its dependencies by running the following command:

   .. code-block:: bash

      python setup.py install

   This command will install ZPyWallet and its dependencies by executing the setup script.

4. Verify the installation by importing ZPyWallet in a Python script or interactive Python session:

   .. code-block:: python

      import zpywallet

   If the import succeeds without any errors, the installation was successful.

5. Congratulations! You have successfully installed ZPyWallet from source.

Development Setup
-----------------
If you plan to contribute to the development of ZPyWallet, it is recommended to set up a development environment with the following additional steps:

1. Install development dependencies by running the following command in the ZPyWallet repository root:

   .. code-block:: bash

      pip install -r requirements-dev.txt

   This command will install the dev dependencies required for development, testing, and linting.

2. Run the tests to ensure everything is working as expected. Execute the following command in the repository root:

   .. code-block:: bash

      pytest

   All tests should pass without any errors.

3. You are now ready to start developing or contributing to ZPyWallet.

Upgrading
---------
To upgrade ZPyWallet to the latest version, use the following command:

.. code-block:: bash

   pip install --upgrade zpywallet

Uninstallation
--------------
If you no longer need ZPyWallet and want to uninstall it, execute the following command:

.. code-block:: bash

   pip uninstall zpywallet

This command will remove ZPyWallet and its associated packages from your Python environment.

Dependencies
------------
ZPyWallet has the following dependencies, which will be automatically installed when you install ZPyWallet via `pip` or `setup.py`:

- coincurve
- scrypt
- requests
- protobuf
- pycryptodomex
- web3
- websocket-client


We try to keep the number of runtime dependencies to an absolute minimum to avoid the possibility of supply chain attacks, so it is mostly restricted to modules
written in native code.

Development dependencies include additional packages required for development, testing, and linting, which can be installed from the `requirements-dev.txt` file.

If you encounter any issues during the installation process or have specific requirements, please refer to the ZPyWallet documentation for troubleshooting steps
or create a Github issue.

Indices and Tables
------------------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
