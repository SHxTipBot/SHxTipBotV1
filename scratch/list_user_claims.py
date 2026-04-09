import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def get_user_claims(discord_id):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch("SELECT id, amount, status, created_at FROM withdrawals WHERE discord_id = $1 ORDER BY created_at DESC", discord_id)
        for r in rows:
            print(f"ID: {r['id']} | Amount: {r['amount']} | Status: {r['status']} | Created: {r['created_at']}")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_user_claims("768342085644320799"))
