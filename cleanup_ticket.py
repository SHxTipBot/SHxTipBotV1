"""
Manual cleanup script to mark a specific withdrawal as completed.
Use this if a transaction succeeded on-chain but the dashboard still shows it as 'PENDING'.
"""

import asyncio
import sys
import os

# Add current dir to path to import database and stellar_utils
sys.path.append(os.getcwd())

import database as db
import stellar_utils as stellar

async def cleanup_withdrawal(withdrawal_id: str, tx_hash: str):
    print(f"--- Withdrawal Cleanup Tool ---")
    print(f"Target Withdrawal ID: {withdrawal_id}")
    print(f"Target TX Hash:       {tx_hash}")
    
    # 1. Verify existence in DB
    withdrawal = await db.get_withdrawal(withdrawal_id)
    if not withdrawal:
        print(f"ERROR: Withdrawal {withdrawal_id} not found in database.")
        return

    if withdrawal['status'] != 'PENDING':
        print(f"NOTE: Withdrawal is already in status: {withdrawal['status']}.")
        return

    # 2. Verify success on-chain
    print(f"Verifying transaction on-chain...")
    confirmed = await stellar.verify_transaction_status(tx_hash)
    if not confirmed:
        print(f"WARNING: Transaction {tx_hash} was NOT confirmed as SUCCESS on-chain.")
        print(f"If you are SURE it went through (e.g. checked on Stellar.expert), you can proceed.")
        confirm = input("Proceed anyway? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return

    # 3. Mark as completed
    print(f"Marking withdrawal as COMPLETED...")
    await db.complete_withdrawal(withdrawal_id, tx_hash)
    print(f"SUCCESS: Withdrawal {withdrawal_id} has been marked as COMPLETED.")

if __name__ == "__main__":
    # If arguments are provided via command line: python cleanup_ticket.py <id> <hash>
    if len(sys.argv) > 2:
        asyncio.run(cleanup_withdrawal(sys.argv[1], sys.argv[2]))
    else:
        # Interactive mode
        w_id = input("Enter Withdrawal ID (or 'test'): ").strip()
        t_hash = input("Enter Transaction Hash: ").strip()
        if w_id and t_hash:
            asyncio.run(cleanup_withdrawal(w_id, t_hash))
        else:
            print("Missing required information.")
