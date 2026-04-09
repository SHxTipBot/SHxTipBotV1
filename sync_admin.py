import asyncio
import os
from dotenv import load_dotenv
import database as db

async def sync():
    load_dotenv()
    admin_id = "768342085644320799"
    pool = await db.get_pool()
    
    async with pool.acquire() as conn:
        # Check if user exists
        row = await conn.fetchrow("SELECT * FROM users WHERE discord_id = $1", admin_id)
        if not row:
            # Create user if missing (using admin_id as memo_id fallback)
            await conn.execute(
                "INSERT INTO users (discord_id, memo_id, internal_balance) VALUES ($1, $2, 3000.0)",
                admin_id, int(admin_id)
            )
            print(f"Created new user record for {admin_id} with 3000 SHx.")
        else:
            # Update existing user
            await conn.execute(
                "UPDATE users SET internal_balance = 3000.0 WHERE discord_id = $1",
                admin_id
            )
            print(f"Updated existing user {admin_id} balance to 3000 SHx.")
    
    # Verify
    new_bal = await db.get_internal_balance(admin_id)
    print(f"Verification: Internal Balance is now {new_bal} SHx")
    await db.close_db()

if __name__ == "__main__":
    asyncio.run(sync())
