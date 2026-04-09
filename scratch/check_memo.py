import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def check_memo():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        memo_id = 887682978392702997
        row = await conn.fetchrow("SELECT discord_id, username, memo_id, internal_balance FROM users WHERE memo_id = $1", memo_id)
        if row:
            print(dict(row))
        else:
            print("No User Found with that memo.")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_memo())
