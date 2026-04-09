import asyncio
import database as db
import os
from dotenv import load_dotenv

async def check_ticket():
    load_dotenv()
    await db.init_db()
    pool = await db.get_pool()
    
    # Query the specific ticket from the user's report
    rows = await pool.fetch("SELECT id, discord_id, status FROM withdrawals WHERE id LIKE '%445c3297'")
    print(f"Ticket Data: {rows}")
    
    # Query the user linked to the current token (if I had it, but I'll check all tokens)
    tokens = await pool.fetch("SELECT token, discord_id, used FROM link_tokens WHERE used = 0 ORDER BY created_at DESC LIMIT 5")
    print(f"Recent Tokens: {tokens}")
    
    await db.close_db()

if __name__ == "__main__":
    asyncio.run(check_ticket())
