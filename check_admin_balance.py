import asyncio
import os
from dotenv import load_dotenv
import database as db

async def check():
    load_dotenv()
    admin_id = os.getenv("ADMIN_DISCORD_IDS", "").split(',')[0].strip()
    balance = await db.get_internal_balance(admin_id)
    print(f"Admin Discord ID: {admin_id}")
    print(f"Internal Balance: {balance} SHx")
    
    # Also list recent deposits to see if any came through
    user_data = await db.get_or_create_user(admin_id)
    print(f"Memo ID: {user_data['memo_id']}")

if __name__ == "__main__":
    asyncio.run(check())
