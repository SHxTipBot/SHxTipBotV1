import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def check_deposits_exist():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        hashes = [
            '563db5aa9436df0c5c9b285d135b3ac6948b822f9dad787fdbf5851caba602a8',
            'ad0d39d432c5279631b495f3b0acd42605f49e0492e0a94f5dd83a320107814f'
        ]
        rows = await conn.fetch("SELECT * FROM deposits WHERE tx_hash = ANY($1)", hashes)
        print(f"Deposits found in DB: {len(rows)}")
        for r in rows:
            print(dict(r))
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_deposits_exist())
