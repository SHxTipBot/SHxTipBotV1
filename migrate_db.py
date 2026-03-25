import database
import asyncio

async def migrate():
    print("Starting migration...")
    pool = await database.get_pool()
    async with pool.acquire() as conn:
        await conn.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_approved BOOLEAN NOT NULL DEFAULT FALSE')
    print("Migration successful: added is_approved column to users table.")
    await database.close_db()

if __name__ == "__main__":
    asyncio.run(migrate())
