from zpywallet import Destination
from zpywallet import Wallet
from zpywallet.network import BitcoinSegwitTestNet
wallet = Wallet(BitcoinSegwitTestNet, "staff enact raw satisfy tape rude spring treat hole coin call sorry", "topaz", receive_gap_limit=3)
d = Destination("tb1qcg3f6ehwlaseqz6x0zers5lq4pgzmat2tl6znq", 0.0001, BitcoinSegwitTestNet)
x = wallet.create_transaction("topaz", [d], 5)
print(x)
wallet.broadcast_transaction(x)