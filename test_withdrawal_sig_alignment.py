import asyncio
import os
import base64
from dotenv import load_dotenv

# load_dotenv must be called before importing stellar_utils
load_dotenv()

import stellar_utils as stellar
from stellar_sdk import Keypair, scval

async def test_sig():

    print("--- Testing Withdrawal Signature Alignment ---")
    
    # 1. Setup
    user_address = "GDSTRSHXHGJ7ZIVRBXEYE5Q74XUVCUSEKEBR7UCHEUUEK72N7I7KJ6JH"
    amount = 50.0
    nonce = 123456789
    
    print(f"User: {user_address}")
    print(f"Amount: {amount}")
    print(f"Nonce: {nonce}")
    print(f"Contract: {stellar.SOROBAN_CONTRACT_ID}")
    
    # 2. Generate Signature
    try:
        sig = stellar.sign_withdrawal(user_address, amount, nonce)
        print(f"Generated Signature (B64): {sig}")
        
        # 3. Simulate the payload construction manually to verify parts
        amount_stroops = int(round(amount * 10000000))
        
        # This matches stellar_utils.py's new logic
        contract_addr_xdr = scval.to_address(stellar.SOROBAN_CONTRACT_ID).address.to_xdr_bytes()
        user_addr_xdr = scval.to_address(user_address).address.to_xdr_bytes()
        amount_xdr = scval.to_int128(amount_stroops).i128.to_xdr_bytes()
        nonce_xdr = scval.to_uint64(nonce).u64.to_xdr_bytes()
        
        payload = contract_addr_xdr + user_addr_xdr + amount_xdr + nonce_xdr
        print(f"Payload Hex: {payload.hex()}")
        
        # 4. Verify locally
        kp = Keypair.from_public_key(stellar.HOUSE_ACCOUNT_PUBLIC)
        sig_bytes = base64.b64decode(sig)
        
        try:
            kp.verify(payload, sig_bytes)
            print("✅ SUCCESS: Signature is valid for the payload!")
        except Exception as e:
            print(f"❌ FAILED: Local verification failed: {e}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sig())
