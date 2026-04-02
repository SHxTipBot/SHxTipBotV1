import asyncio
import os
from dotenv import load_dotenv
import web
import database as db
import stellar_utils as stellar
import secrets
from pydantic import BaseModel

load_dotenv()

class WebWithdrawRequest(BaseModel):
    token: str
    amount: str

async def verify():
    # 1. Setup mock data
    discord_id = "123456789"
    public_key = "GAHO2LQHLZHYRRUE4CNT7QHWFDXJWK322XPUWO6RSFGB3FMI4H67OH5J" # Using house for test
    
    print("--- 1. Initializing DB ---")
    await db.init_db()
    
    print("--- 2. Linking user ---")
    await db.link_user(discord_id, public_key, True)
    
    print("--- 3. Funding internal balance ---")
    # Add enough balance for testing
    await db.add_deposit(discord_id, f"test_fund_{secrets.token_hex(4)}", 100.0)
    
    print("--- 4. Creating link token ---")
    token = await db.create_link_token(discord_id)
    
    print(f"--- 5. Testing api_web_withdraw for token {token[:8]}... ---")
    req = WebWithdrawRequest(token=token, amount="10.0")
    
    try:
        # Call the logic directly
        res = await web.api_web_withdraw(req)
        print("SUCCESS! Response:", res)
    except Exception as e:
        print("FAILED! Error:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify())
