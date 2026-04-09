import asyncio
import os
import sys

# Add the bot directory to sys.path so we can import things
bot_dir = r"c:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot"
sys.path.insert(0, bot_dir)

from stellar_sdk import ServerAsync, AiohttpClient
from dotenv import load_dotenv

load_dotenv(os.path.join(bot_dir, ".env"))
HORIZON_URL = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org")
HOUSE_ACCOUNT_PUBLIC = os.getenv("HOUSE_ACCOUNT_PUBLIC")
SHX_ASSET_CODE = os.getenv("SHX_ASSET_CODE", "SHX")
SHX_ISSUER = os.getenv("SHX_ISSUER", "GDSTRSHXHGJ7ZIVRBXEYE5Q74XUVCUSEKEBR7UCHEUUEK72N7I7KJ6JH")

import database as db

async def main():
    print(f"Checking recent payments to {HOUSE_ACCOUNT_PUBLIC}")
    try:
        await db.init_db()
    except Exception as e:
        print(f"DB Error: {e}")

    async with ServerAsync(HORIZON_URL, client=AiohttpClient()) as server:
        response = await server.payments().for_account(HOUSE_ACCOUNT_PUBLIC).order("desc").limit(30).call()
        records = response.get("_embedded", {}).get("records", [])
        
        pool = await db.get_pool()
        
        for r in records:
            if r.get("type") not in ("payment", "path_payment_strict_receive"):
                continue
            if r.get("asset_code") != SHX_ASSET_CODE or r.get("asset_issuer") != SHX_ISSUER:
                continue
            if r.get("to") != HOUSE_ACCOUNT_PUBLIC:
                continue
                
            tx_hash = r.get("transaction_hash")
            amount = float(r.get("amount"))
            
            try:
                tx = await server.transactions().transaction(tx_hash).call()
                memo_type = tx.get("memo_type")
                memo_val = tx.get("memo")
            except Exception as e:
                memo_type = "ERROR"
                memo_val = str(e)

            # check DB
            in_db = False
            if pool:
                row = await pool.fetchrow("SELECT amount FROM deposits WHERE tx_hash = $1", tx_hash)
                if row:
                    in_db = True

            print(f"TxHash: {tx_hash} | Amount: {amount} SHx | MType: {memo_type} | MVal: {memo_val} | In DB: {in_db}")

asyncio.run(main())
