from web3 import Web3
from ...errors import NetworkException


async def broadcast_transaction_eth_generic(raw_transaction_hex, **kwargs):
    """Broadcast an Ethereum transaction using a full node.
    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
        url (str): The Web3 URL of the node. Include the port if necessary.
    """

    try:
        w3 = Web3(Web3.HTTPProvider(kwargs.get("url")))
        transaction_hash = w3.eth.sendRawTransaction(raw_transaction_hex)
        return transaction_hash.hex()
    except Exception as e:
        raise NetworkException(
            f"Failed to broadcast Ethereum transaction using generic provider: {e}"
        )
