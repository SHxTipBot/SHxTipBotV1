import asyncio
import os
import requests
import time
from dotenv import load_dotenv
load_dotenv()

from stellar_sdk import Keypair, Server, TransactionBuilder, Network, scval, SorobanServer
from stellar_utils import (
    HOUSE_ACCOUNT_SECRET, HOUSE_ACCOUNT_PUBLIC, SHX_SAC_CONTRACT_ID, 
    SOROBAN_CONTRACT_ID, NETWORK_PASSPHRASE, HORIZON_URL, SOROBAN_RPC_URL,
    to_sc_address, _to_stroops
)

async def fix_allowance():
    print("--- Fixing House Account Allowance (Attempt 3) ---")
    
    # 1. Fetch current ledger
    try:
        resp = requests.get(f"{HORIZON_URL}/")
        current_ledger = resp.json()["history_latest_ledger"]
        print(f"Current Ledger: {current_ledger}")
    except Exception as e:
        print(f"Failed to fetch ledger sequence: {e}")
        return

    # 2. Setup transaction details
    new_expiration = current_ledger + 1000000 # ~57 days
    amount_shx = 2000000 # 2 million SHx
    amount_stroops = _to_stroops(amount_shx)
    
    print(f"New Expiration Ledger: {new_expiration}")
    print(f"Allowance Amount: {amount_shx} SHx")

    # 3. Build Approve Transaction
    kp = Keypair.from_secret(HOUSE_ACCOUNT_SECRET)
    server = Server(HORIZON_URL)
    soroban_server = SorobanServer(SOROBAN_RPC_URL)
    
    account = server.load_account(kp.public_key)
    builder = TransactionBuilder(
        source_account=account,
        network_passphrase=NETWORK_PASSPHRASE,
        base_fee=1000000, # 0.1 XLM base fee
    )
    builder.set_timeout(300) # 5 minutes
    
    builder.append_invoke_contract_function_op(
        contract_id=SHX_SAC_CONTRACT_ID,
        function_name="approve",
        parameters=[
            to_sc_address(kp.public_key),
            to_sc_address(SOROBAN_CONTRACT_ID),
            scval.to_int128(amount_stroops),
            scval.to_uint32(new_expiration)
        ]
    )
    
    tx = builder.build()
    
    print("Simulating...")
    sim = soroban_server.simulate_transaction(tx)
    if sim.error:
        print(f"Simulation failed: {sim.error}")
        return
    
    print("Preparing...")
    tx = soroban_server.prepare_transaction(tx, sim)
    
    # Manually increase fee even more to be sure
    tx.fee = 2_000_000 # 0.2 XLM total fee
    
    tx.sign(kp)
    
    print("Submitting...")
    resp = soroban_server.send_transaction(tx)
    print(f"Transaction Hash: {resp.hash}")
    
    print("Waiting for confirmation...")
    for i in range(60):
        res = soroban_server.get_transaction(resp.hash)
        if res.status == "SUCCESS":
            print(f"✅ Allowance successfully updated on-chain! Ledger: {res.ledger}")
            return
        elif res.status == "FAILED":
            print(f"❌ Transaction failed: {res.result_xdr}")
            return
        elif res.status == "NOT_FOUND":
            if i % 5 == 0:
                print("...")
        else:
            print(f"Status: {res.status}")
            
        await asyncio.sleep(2)
    
    print("Transaction timed out.")

if __name__ == "__main__":
    asyncio.run(fix_allowance())
