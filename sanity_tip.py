import asyncio
import os
from dotenv import load_dotenv
import stellar_utils as stellar

async def sanity_tip():
    load_dotenv()
    # Tip 0.1 SHx from House to House (or to a test key)
    house_public = os.getenv("HOUSE_ACCOUNT_PUBLIC")
    recipient = "GAHO2LQHLZHYRRUE4CNT7QHWFDXJWK322XPUWO6RSFGB3FMI4H67OH5J" # Just a test burner
    
    print(f"Executing sanity tip of 0.1 SHx from {house_public[:8]} to {recipient[:8]}...")
    
    res = await stellar.execute_tip(
        sender_public_key=house_public,
        recipient_public_key=recipient,
        amount=0.1,
        fee=0.01
    )
    
    print(f"Result: {res['success']}")
    if res['success']:
        print(f"TX Hash: {res['tx_hash']}")
        print(f"TX URL: {res['tx_url']}")
    else:
        print(f"Error: {res['error']}")

if __name__ == "__main__":
    asyncio.run(sanity_tip())
