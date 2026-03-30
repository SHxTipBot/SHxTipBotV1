import asyncio
import database

async def main():
    await database.init_db()
    token = await database.create_link_token("123456789123456789")
    print(f"TOKEN:{token}")
    await database.close_db()

if __name__ == "__main__":
    asyncio.run(main())
