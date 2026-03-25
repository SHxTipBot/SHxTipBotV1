import asyncio
import time
import database as db

async def test():
    await db.init_db()
    
    start = time.time()
    user_data = await db.get_or_create_user("768342085644320799")
    print(f"get_or_create_user took {time.time()-start:.2f}s")
    
    start = time.time()
    token = await db.create_link_token("768342085644320799")
    print(f"create_link_token took {time.time()-start:.2f}s")

asyncio.run(test())
