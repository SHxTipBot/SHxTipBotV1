import asyncio
import database as db

async def test():
    await db.init_db()
    u = await db.get_or_create_user('768342085644320799')
    print('USER:', u)
    b = await db.get_internal_balance('768342085644320799')
    print('BALANCE:', b)
    await db.close_db()

asyncio.run(test())
