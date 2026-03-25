import asyncio
import database

async def check_users():
    await database.init_db()
    pool = await database.get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users")
        print("Users Table Contents:")
        for user in users:
            print(f"Discord ID: {user['discord_id']} | Key: {user['stellar_public_key'][:8]}... | Approved: {user['is_approved']}")
    await database.close_db()

if __name__ == "__main__":
    asyncio.run(check_users())
