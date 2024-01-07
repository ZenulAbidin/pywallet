import binascii
import hashlib
from .blockcypher import *

def tx_hash_bcy(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest())

def broadcast_transaction_bcy(raw_transaction_hex: bytes):
    errors = []

    try:
        broadcast_transaction_bcy_blockcypher(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)
    
    return errors