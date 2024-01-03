import hashlib
from .blockcypher import *

def broadcast_transaction_bcy(raw_transaction_hex: bytes):
    errors = []

    try:
        broadcast_transaction_bcy_blockcypher(raw_transaction_hex.decode())
    except NetworkException as e:
        errors.append(e)
    
    return hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest(), errors