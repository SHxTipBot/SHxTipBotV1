import asyncio
import database as db

async def main():
    pool = await db.get_pool()
    rows = await pool.fetch("SELECT id, discord_id, stellar_address, amount, created_at FROM withdrawals WHERE status = 'PENDING' ORDER BY created_at DESC LIMIT 5")
    for r in rows:
        print(f"ID: {r['id']} | User: {r['discord_id']} | Address: {r['stellar_address']} | Amount: {r['amount']} | Created: {r['created_at']}")

if __name__ == "__main__":
    asyncio.run(main())
