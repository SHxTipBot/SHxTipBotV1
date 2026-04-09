import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def check_tx_in_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        tx_hash = 'c6ece5f4a7e947e3d4839a7ae94664c68b30289c52a6ecdf3d9f3ac38733a87a'
        row = await conn.fetchrow("SELECT tx_hash, amount FROM deposits WHERE tx_hash = $1", tx_hash)
        if row:
            print(dict(row))
        else:
            print("Not in DB")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_tx_in_db())
