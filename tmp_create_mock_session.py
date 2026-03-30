import asyncio
import os
import time
import secrets
from dotenv import load_dotenv
import asyncpg

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    
    discord_id = "768342085644320799" # Admin ID from .env
    token = secrets.token_urlsafe(32)
    now = time.time()
    ttl = 3600 # 1 hour
    
    # Create user
    await conn.execute(
        "INSERT INTO users (discord_id, memo_id, internal_balance) VALUES ($1, $2, 1000.0) ON CONFLICT DO NOTHING",
        discord_id, int(discord_id)
    )
    
    # Create token
    await conn.execute(
        "INSERT INTO link_tokens (token, discord_id, created_at, expires_at, used) VALUES ($1, $2, $3, $4, 0)",
        token, discord_id, now, now + ttl
    )
    
    print(f"MOCK_TOKEN={token}")
    print(f"URL=http://localhost:8080/register?token={token}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
