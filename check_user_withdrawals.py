import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def check_user_withdrawals(discord_id: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch("SELECT id, status, amount, created_at, tx_hash FROM withdrawals WHERE discord_id = $1 ORDER BY created_at DESC", discord_id)
        print(f"Withdrawals for {discord_id}:")
        for r in rows:
            print(f"ID: {r['id']} | Status: {r['status']} | Amount: {r['amount']} SHx | Hash: {r['tx_hash']}")
            print("-" * 20)
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_user_withdrawals("768342085644320799"))
