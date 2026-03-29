import asyncio
import os
import sys
import uuid
import time

# Add current dir to path
sys.path.append(os.getcwd())

import database as db

async def test_cancel_flow():
    print("🚀 Starting Cancellation Logic Test...")
    await db.init_db()
    
    discord_id = "1234567890"
    withdrawal_id = f"test_withdraw_{uuid.uuid4().hex[:8]}"
    initial_amount = 500.0
    withdraw_amount = 100.0
    
    try:
        # 1. Setup User
        print(f"--- Setting up user {discord_id} with {initial_amount} SHx ---")
        await db.get_or_create_user(discord_id)
        # Manually set balance for test
        pool = await db.get_pool()
        await pool.execute("UPDATE users SET internal_balance = $1 WHERE discord_id = $2", initial_amount, discord_id)
        
        # 2. Simulate Withdrawal Initiation
        print(f"--- Initiating withdrawal {withdrawal_id} for {withdraw_amount} SHx ---")
        # Deduct balance (like bot.py does)
        await pool.execute("UPDATE users SET internal_balance = internal_balance - $1 WHERE discord_id = $2", withdraw_amount, discord_id)
        await db.create_withdrawal(withdrawal_id, discord_id, "G_TEST_ADDR", withdraw_amount, int(time.time()), "test_sig")
        
        bal_after_withdraw = await db.get_internal_balance(discord_id)
        print(f"Balance after withdraw: {bal_after_withdraw}")
        assert bal_after_withdraw == initial_amount - withdraw_amount
        
        # 3. Cancel Withdrawal
        print(f"--- Cancelling withdrawal {withdrawal_id} ---")
        success = await db.cancel_withdrawal(withdrawal_id)
        assert success is True
        
        # 4. Verify Refund
        final_bal = await db.get_internal_balance(discord_id)
        print(f"Balance after cancel: {final_bal}")
        assert final_bal == initial_amount
        
        # 5. Verify Status
        withdrawal = await db.get_withdrawal(withdrawal_id)
        print(f"Withdrawal status: {withdrawal['status']}")
        assert withdrawal['status'] == "CANCELLED"
        
        # 6. Try to cancel again (should fail)
        print("--- Trying to cancel again (should fail) ---")
        fail_res = await db.cancel_withdrawal(withdrawal_id)
        assert fail_res is False
        
        print("\n✅ CANCELLATION LOGIC TEST PASSED!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close_db()

if __name__ == "__main__":
    asyncio.run(test_cancel_flow())
