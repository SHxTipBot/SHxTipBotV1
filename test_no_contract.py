from stellar_sdk import Keypair, scval
import os
from dotenv import load_dotenv

load_dotenv()

contract_id = os.getenv("SOROBAN_CONTRACT_ID")
house_secret = os.getenv("HOUSE_ACCOUNT_SECRET")
kp = Keypair.from_secret(house_secret)

pubkey = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"
amount_stroops = 1210000000
nonce = 1775620664054
sig_hex = "6deeaf47502399cb3994e1cabf6fbed1cc38c90368985dd16bc6b24b718ec97451bd5a2973f4c331a9c1e6e831765dd1d4f61de5c3740526164bcb7510e24e06"
sig_bytes = bytes.fromhex(sig_hex)

# Try no contract ID
p_no_contract = scval.to_address(pubkey).to_xdr_bytes() + scval.to_int128(amount_stroops).to_xdr_bytes() + scval.to_uint64(nonce).to_xdr_bytes()
try:
    kp.verify(p_no_contract, sig_bytes)
    print("MATCHES NO CONTRACT_ID!")
except:
    print("DOES NOT MATCH NO CONTRACT_ID")

# Try strings?
p_strings = f"{pubkey}:{amount_stroops}:{nonce}".encode()
try:
    kp.verify(p_strings, sig_bytes)
    print("MATCHES STRINGS!")
except:
    pass

import stellar_utils as stellar
try:
    v = stellar.sign_withdrawal(pubkey, 121.0, nonce)
    print("MATCHES NEW CODE?")
    import base64
    if base64.b64decode(v) == sig_bytes:
        print("YES!")
    else:
        print("NO!")
except:
    pass
