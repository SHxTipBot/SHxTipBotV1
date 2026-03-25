import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import stellar_utils as stellar

async def run_test():
    load_dotenv()
    print(f"DEBUG: HOUSE_ACCOUNT_SECRET length: {len(os.getenv('HOUSE_ACCOUNT_SECRET', ''))}")
    print(f"DEBUG: HOUSE_ACCOUNT_SECRET starts with: {os.getenv('HOUSE_ACCOUNT_SECRET', '')[:5]}")
    target = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"
    
    # 1. Check Balance
    balance = await stellar.get_shx_balance(target)
    print(f"Current Balance: {balance}")
    
    if balance is None:
        print("Account does not exist or Horizon error.")
    
    # 2. Execute a small distribution (0.1 SHX)
    print(f"Executing test distribution of 0.1 SHX to {target}...")
    result = await stellar.execute_tip(
        stellar.HOUSE_ACCOUNT_PUBLIC,
        target,
        0.1,
        0.0  # Zero fee for distribution
    )
    
    if result["success"]:
        print(f"SUCCESS! TX Hash: {result['tx_hash']}")
        print(f"URL: {result['tx_url']}")
    else:
        print(f"FAILED: {result['error']}")
    
    await stellar.close_session()

if __name__ == "__main__":
    asyncio.run(run_test())
