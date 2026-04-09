from stellar_sdk import Keypair, scval
import os
from dotenv import load_dotenv

load_dotenv()

contract_id = os.getenv("SOROBAN_CONTRACT_ID")
house_secret = os.getenv("HOUSE_ACCOUNT_SECRET")
kp = Keypair.from_secret(house_secret)

# The data from the user's error msg
pubkey = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"
amount_stroops = 1210000000
nonce = 1775620664054
sig_hex = "6deeaf47502399cb3994e1cabf6fbed1cc38c90368985dd16bc6b24b718ec97451bd5a2973f4c331a9c1e6e831765dd1d4f61de5c3740526164bcb7510e24e06"

# Recreate the ScVal payload (style A)
p_a = scval.to_address(contract_id).to_xdr_bytes() + scval.to_address(pubkey).to_xdr_bytes() + scval.to_int128(amount_stroops).to_xdr_bytes() + scval.to_uint64(nonce).to_xdr_bytes()

# Recreate the raw payload (style B)
p_b = scval.to_address(contract_id).address.to_xdr_bytes() + scval.to_address(pubkey).address.to_xdr_bytes() + scval.to_int128(amount_stroops).i128.to_xdr_bytes() + scval.to_uint64(nonce).u64.to_xdr_bytes()

sig_bytes = bytes.fromhex(sig_hex)

try:
    kp.verify(p_a, sig_bytes)
    print("MATCHES STYLE A (ScVal)")
except:
    print("DOES NOT MATCH STYLE A")
    
try:
    kp.verify(p_b, sig_bytes)
    print("MATCHES STYLE B (Raw)")
except:
    print("DOES NOT MATCH STYLE B")

def to_xdr_str(amount, nonce):
    return (scval.to_address(contract_id).to_xdr_bytes() + 
            scval.to_address(pubkey).to_xdr_bytes() + 
            scval.to_int128(amount).to_xdr_bytes() + 
            scval.to_uint64(nonce).to_xdr_bytes())

import stellar_utils as stellar
new_sig = stellar.sign_withdrawal(pubkey, amount_stroops / 10000000.0, nonce)
import base64
print("NEW SIG EXPECTED (Hex):", base64.b64decode(new_sig).hex())
print("USER SIG GENERATED:    ", sig_hex)
