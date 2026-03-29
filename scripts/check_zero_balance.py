import asyncio
import os
import sys
import logging

# Add current dir to path to find local modules
sys.path.append(os.getcwd())

import database as db

async def check_user_history():
    await db.init_db()
    pool = await db.get_pool()
    
    # 1. Find the most recent withdrawal
    print("--- RECENT WITHDRAWALS ---")
    withdrawals = await pool.fetch("SELECT * FROM withdrawals ORDER BY created_at DESC LIMIT 5")
    for w in withdrawals:
        print(f"ID: {w['id']} | User: {w['discord_id']} | Amount: {w['amount']} | Created: {w['created_at']}")
        
    # 2. Find recent internal tips
    print("\n--- RECENT TIPS ---")
    tips = await pool.fetch("SELECT * FROM internal_tips ORDER BY created_at DESC LIMIT 5")
    for t in tips:
        print(f"From: {t['sender_discord_id']} | To: {t['recipient_discord_id']} | Amount: {t['amount']} | Created: {t['created_at']}")
        
    # 3. Find most recent users whose balance is zero
    print("\n--- ZERO BALANCE USERS ---")
    users = await pool.fetch("SELECT * FROM users WHERE internal_balance = 0.0 ORDER BY updated_at DESC LIMIT 5")
    for u in users:
        print(f"User: {u['discord_id']} | Balance: {u['internal_balance']} | Updated: {u.get('updated_at', 'N/A')}")

    await db.close_db()

if __name__ == "__main__":
    asyncio.run(check_user_history())
