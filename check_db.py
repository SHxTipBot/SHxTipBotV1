import asyncio
import database as db
import os
from dotenv import load_dotenv

async def check():
    load_dotenv()
    await db.init_db()
    pool = await db.get_pool()
    r = await pool.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='username'")
    print(f"Column Check: {r}")
    
    # Also check most recent user's username
    u = await pool.fetch("SELECT discord_id, username FROM users WHERE username IS NOT NULL ORDER BY updated_at DESC LIMIT 1")
    print(f"Recent User: {u}")
    
    await db.close_db()

if __name__ == "__main__":
    asyncio.run(check())
