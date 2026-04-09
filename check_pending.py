import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def check_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch("SELECT id, discord_id, stellar_address, amount FROM withdrawals WHERE status = 'PENDING'")
        for r in rows:
            print(f"Withdrawal ID: {r['id']}")
            print(f"User: {r['discord_id']}")
            print(f"Stellar Address: {r['stellar_address']}")
            print(f"Amount: {r['amount']} SHx")
            print("-" * 20)
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
