from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stellar_utils as stellar

async def fix():
    print("Fixing House Allowance...")
    
    secret = os.getenv("HOUSE_ACCOUNT_SECRET")
    public = os.getenv("HOUSE_ACCOUNT_PUBLIC")
    contract = os.getenv("SOROBAN_CONTRACT_ID")
    
    if not secret or not contract:
        print("❌ Missing environment variables (HOUSE_ACCOUNT_SECRET or SOROBAN_CONTRACT_ID)")
        return

    print(f"House Account: {public}")
    print(f"Spender (Contract): {contract}")
    print(f"SHX SAC: {os.getenv('SHX_SAC_CONTRACT_ID')}")

    # Check current allowance
    allowance = await stellar.check_shx_allowance(public, contract)
    print(f"Current Allowance: {allowance:,.2f} SHx")

    # Approve 1,000,000 SHx
    print("Setting allowance to 1,000,000 SHx...")
    res = await stellar.approve_shx(secret, amount=1_000_000)
    
    if res.get("success"):
        print(f"✅ Success! Hash: {res.get('hash')}")
        # Final check
        await asyncio.sleep(5)
        new_allowance = await stellar.check_shx_allowance(public, contract)
        print(f"New Allowance: {new_allowance:,.2f} SHx")
    else:
        print(f"❌ Failed: {res.get('error')}")

if __name__ == "__main__":
    asyncio.run(fix())
