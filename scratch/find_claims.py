import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def find_claims():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        # Search for amount 25 or 100
        rows = await conn.fetch("SELECT id, amount, status, created_at, stellar_address FROM withdrawals WHERE amount IN (25, 100) ORDER BY created_at DESC LIMIT 10")
        print("Candidate Withdrawals:")
        for r in rows:
            print(f"ID: {r['id']} | Amount: {r['amount']} | Status: {r['status']} | Address: {r['stellar_address']}")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(find_claims())
