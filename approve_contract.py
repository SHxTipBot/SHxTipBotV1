"""
SHx Tip Bot — Approve Tipping Contract (Testnet)

When you link a wallet manually, the on-chain 'approve' transaction is skipped.
This script submits the approve transaction so the tipping contract can call
transfer_from on your SHX.

Usage:
  venv\\Scripts\\python.exe approve_contract.py <SECRET_KEY>

The secret key is needed to sign the approve transaction.
"""

import asyncio
import sys
import io
import os

from dotenv import load_dotenv
from stellar_sdk import (
    Keypair, Server, TransactionBuilder, Network, Asset,
    SorobanServer, scval,
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
load_dotenv()

HORIZON_URL = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org")
SOROBAN_RPC_URL = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org")
SHX_SAC_CONTRACT_ID = os.getenv("SHX_SAC_CONTRACT_ID", "")
SOROBAN_CONTRACT_ID = os.getenv("SOROBAN_CONTRACT_ID", "")
NETWORK_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE


def to_stroops(amount: float) -> int:
    return int(round(amount * 10_000_000))


async def main():
    if len(sys.argv) < 2:
        print("Usage: venv\\Scripts\\python.exe approve_contract.py <SECRET_KEY>")
        print("\nProvide the Stellar SECRET KEY for the account you want to approve.")
        sys.exit(1)

    secret_key = sys.argv[1].strip()

    try:
        user_kp = Keypair.from_secret(secret_key)
    except Exception as e:
        print(f"Invalid secret key: {e}")
        sys.exit(1)

    public_key = user_kp.public_key

    print("=" * 60)
    print("  SHx Tip Bot — Approve Tipping Contract")
    print("=" * 60)
    print(f"\n  Account:           {public_key}")
    print(f"  Tipping Contract:  {SOROBAN_CONTRACT_ID[:16]}...")
    print(f"  SHX SAC Contract:  {SHX_SAC_CONTRACT_ID[:16]}...")
    print(f"  Allowance:         1,000,000 SHX")

    if not SHX_SAC_CONTRACT_ID or not SOROBAN_CONTRACT_ID:
        print("\n[ERROR] SHX_SAC_CONTRACT_ID or SOROBAN_CONTRACT_ID not set in .env!")
        sys.exit(1)

    horizon_server = Server(HORIZON_URL)
    soroban_server = SorobanServer(SOROBAN_RPC_URL)

    # Load account
    print("\n[1] Loading account...")
    user_account = horizon_server.load_account(public_key)
    print(f"  -> Account loaded (seq: {user_account.sequence})")

    # Build approve transaction
    print("[2] Building approve transaction...")

    allowance_stroops = to_stroops(1_000_000)  # 1M SHX allowance
    expiration_ledger = 3_000_000  # within testnet max of ~3.1M

    builder = TransactionBuilder(
        source_account=user_account,
        network_passphrase=NETWORK_PASSPHRASE,
        base_fee=100_000,
    )

    builder.append_invoke_contract_function_op(
        contract_id=SHX_SAC_CONTRACT_ID,
        function_name="approve",
        parameters=[
            scval.to_address(public_key),            # owner
            scval.to_address(SOROBAN_CONTRACT_ID),   # spender (tipping contract)
            scval.to_int128(allowance_stroops),       # amount
            scval.to_uint32(expiration_ledger),        # expiration_ledger
        ],
    )

    builder.set_timeout(300)
    tx = builder.build()

    # Simulate
    print("[3] Simulating transaction...")
    sim = soroban_server.simulate_transaction(tx)
    if sim.error:
        print(f"  -> Simulation FAILED: {sim.error}")
        sys.exit(1)
    print("  -> Simulation OK!")

    # Prepare (attach footprint, adjust fees)
    print("[4] Preparing and signing...")
    tx = soroban_server.prepare_transaction(tx, sim)
    tx.sign(user_kp)
    print("  -> Signed!")

    # Submit
    print("[5] Submitting to network...")
    response = soroban_server.send_transaction(tx)
    if response.status == "ERROR":
        print(f"  -> Submit ERROR: {response.error}")
        sys.exit(1)

    tx_hash = response.hash
    print(f"  -> Submitted! TX hash: {tx_hash}")

    # Poll for confirmation
    print("[6] Waiting for confirmation...")
    for i in range(30):
        result = soroban_server.get_transaction(tx_hash)
        if result.status == "SUCCESS":
            print(f"  -> CONFIRMED! ✓")
            print(f"  -> View: https://stellar.expert/explorer/testnet/tx/{tx_hash}")
            break
        elif result.status == "FAILED":
            print(f"  -> Transaction FAILED on-chain.")
            sys.exit(1)
        await asyncio.sleep(1)
    else:
        print("  -> Timed out waiting for confirmation.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  ✅ Approval Complete!")
    print(f"  Account {public_key[:12]}... can now tip via the bot.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
