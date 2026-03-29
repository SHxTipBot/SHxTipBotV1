import asyncio
import database as db

async def get_test_token():
    try:
        await db.init_db()
        token = await db.create_link_token("123456789")
        print(f"CREATED_TOKEN: {token}")
        await db.close_db()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(get_test_token())
