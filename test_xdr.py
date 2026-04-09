import os
import asyncio
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import scval, xdr, StrKey

def test_xdr_bytes():
    load_dotenv()
    cid = "CC53YR33JDEQDIMDTAIHOEZLTKTYJLQSQDLYLQIJHT7ZET7H2WF32UJM"
    user = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"
    amount = 20000000
    nonce = 1775360306152
    
    # 1. SCV_ADDRESS
    sc_cid = stellar.to_sc_address(cid)
    # 2. SCV_ADDRESS
    sc_user = stellar.to_sc_address(user)
    # 3. SCV_I128
    sc_amt = scval.to_int128(amount)
    # 4. SCV_U64
    sc_nonce = scval.to_uint64(nonce)
    
    print(f"Contract XDR: {sc_cid.to_xdr_bytes().hex()}")
    print(f"User XDR: {sc_user.to_xdr_bytes().hex()}")
    print(f"Amount XDR: {sc_amt.to_xdr_bytes().hex()}")
    print(f"Nonce XDR: {sc_nonce.to_xdr_bytes().hex()}")

if __name__ == "__main__":
    test_xdr_bytes()
