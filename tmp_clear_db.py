import asyncio
import os
import asyncpg
from dotenv import load_dotenv

async def clear_database():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return
        
    print(f"Connecting to database to clear tables...")
    try:
        # Sanitize for asyncpg (minimal version)
        if "sslmode=require" in db_url:
            ssl_ctx = "require"
        else:
            ssl_ctx = None
            
        conn = await asyncpg.connect(db_url, ssl=ssl_ctx)
        
        tables = [
            "link_tokens", 
            "deposits", 
            "internal_tips", 
            "airdrop_claims", 
            "airdrops", 
            "withdrawals",
            "users"
        ]
        
        for table in tables:
            print(f"Truncating {table}...")
            await conn.execute(f"TRUNCATE TABLE {table} CASCADE")
            
        print("SUCCESS: All tables cleared for Mainnet migration.")
        await conn.close()
    except Exception as e:
        print(f"FAILED to clear database: {e}")

if __name__ == "__main__":
    asyncio.run(clear_database())
