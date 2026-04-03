import asyncio
import os
from dotenv import load_dotenv

# load_dotenv must be before importing stellar_utils
load_dotenv()

import stellar_utils as stellar
from stellar_sdk import Keypair, scval

async def setup_contract():
    print(f"Contract ID: {stellar.SOROBAN_CONTRACT_ID}")
    print(f"House Public Key: {stellar.HOUSE_ACCOUNT_PUBLIC}")
    
    # We call set_admin_pubkey on the contract
    # pubkey: BytesN<32>
    kp = Keypair.from_public_key(stellar.HOUSE_ACCOUNT_PUBLIC)
    pubkey_bytes = kp.raw_public_key()
    
    print(f"Setting admin_pubkey on-chain...")
    
    try:
        # Note: set_admin_pubkey requires Admin auth.
        #Admin should be HOUSE_ACCOUNT_PUBLIC or whatever was passed to initialize.
        res = await stellar.invoke_contract_function(
            secret=stellar.HOUSE_ACCOUNT_SECRET,
            contract_id=stellar.SOROBAN_CONTRACT_ID,
            function_name="set_admin_pubkey",
            parameters=[scval.to_bytes(pubkey_bytes)]
        )
        
        if res.get("success"):
            print(f"✅ SUCCESS: Admin pubkey set on-chain. Hash: {res.get('hash')}")
        else:
            print(f"❌ FAILED: {res.get('error')}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(setup_contract())
