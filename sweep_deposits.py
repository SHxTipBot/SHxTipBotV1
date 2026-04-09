import asyncio
import os
import sys

bot_dir = r"c:\Users\Naugl\OneDrive\Desktop\SHx Tip Bot"
sys.path.insert(0, bot_dir)

import logging
from stellar_sdk import ServerAsync, AiohttpClient
from dotenv import load_dotenv

load_dotenv(os.path.join(bot_dir, ".env"))
HORIZON_URL = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org")
HOUSE_ACCOUNT_PUBLIC = os.getenv("HOUSE_ACCOUNT_PUBLIC")
SHX_ASSET_CODE = os.getenv("SHX_ASSET_CODE", "SHX")
SHX_ISSUER = os.getenv("SHX_ISSUER", "GDSTRSHXHGJ7ZIVRBXEYE5Q74XUVCUSEKEBR7UCHEUUEK72N7I7KJ6JH")

import database as db
import re

async def main():
    print("Sweeping missed deposits...")
    await db.init_db()

    async with ServerAsync(HORIZON_URL, client=AiohttpClient()) as server:
        response = await server.payments().for_account(HOUSE_ACCOUNT_PUBLIC).order("desc").limit(50).call()
        records = response.get("_embedded", {}).get("records", [])
        
        pool = await db.get_pool()
        count = 0
        
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
                continue

            target_discord_id = None
            if memo_type == "id":
                target_discord_id = str(memo_val)
            elif memo_type == "text" and memo_val:
                id_match = re.search(r'(\d{17,20})', str(memo_val))
                if id_match:
                    target_discord_id = id_match.group(1)
            
            if not target_discord_id:
                continue

            # Check if in DB
            row = await pool.fetchrow("SELECT amount FROM deposits WHERE tx_hash = $1", tx_hash)
            if not row:
                print(f"Recovering Missed Deposit! TxHash: {tx_hash} | Amount: {amount} SHx | For: {target_discord_id}")
                await db.get_or_create_user(target_discord_id)
                await db.add_deposit(target_discord_id, tx_hash, amount)
                count += 1
                
        print(f"Swept {count} missed deposits successfully!")

asyncio.run(main())
