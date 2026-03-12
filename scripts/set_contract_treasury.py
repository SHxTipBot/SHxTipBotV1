"""
Utility to update the tipping contract's treasury address to the house account.
This ensures gas reimbursements flow back to the account that pays for XLM fees.

Usage: python set_contract_treasury.py
"""

import os
import asyncio
from dotenv import load_dotenv
from stellar_sdk import Keypair, Network, SorobanServer, Server, TransactionBuilder, scval
from stellar_sdk.soroban_rpc import SendTransactionStatus, GetTransactionStatus

load_dotenv()

# Load config from .env
SOROBAN_CONTRACT_ID = os.getenv("SOROBAN_CONTRACT_ID")
HOUSE_ACCOUNT_SECRET = os.getenv("HOUSE_ACCOUNT_SECRET")
HOUSE_ACCOUNT_PUBLIC = os.getenv("HOUSE_ACCOUNT_PUBLIC")
SOROBAN_RPC_URL = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org")
HORIZON_URL = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org")
STELLAR_NETWORK = os.getenv("STELLAR_NETWORK", "testnet")

NETWORK_PASSPHRASE = (
    Network.TESTNET_NETWORK_PASSPHRASE
    if STELLAR_NETWORK == "testnet"
    else Network.PUBLIC_NETWORK_PASSPHRASE
)

async def main():
    if not SOROBAN_CONTRACT_ID or not HOUSE_ACCOUNT_SECRET:
        print("Error: Missing SOROBAN_CONTRACT_ID or HOUSE_ACCOUNT_SECRET in .env")
        return

    print(f"Updating treasury for contract {SOROBAN_CONTRACT_ID}...")
    print(f"New Treasury: {HOUSE_ACCOUNT_PUBLIC}")

    kp = Keypair.from_secret(HOUSE_ACCOUNT_SECRET)
    soroban_server = SorobanServer(SOROBAN_RPC_URL)
    horizon_server = Server(HORIZON_URL)

    # Load account
    source = horizon_server.load_account(kp.public_key)

    # Build tx
    builder = TransactionBuilder(
        source_account=source,
        network_passphrase=NETWORK_PASSPHRASE,
        base_fee=100_000,
    )

    builder.append_invoke_contract_function_op(
        contract_id=SOROBAN_CONTRACT_ID,
        function_name="set_treasury",
        parameters=[
            scval.to_address(HOUSE_ACCOUNT_PUBLIC),
        ],
    )

    builder.set_timeout(300)
    tx = builder.build()

    # Simulate
    print("Simulating...")
    sim = soroban_server.simulate_transaction(tx)
    if sim.error:
        print(f"Simulation failed: {sim.error}")
        return

    # Prepare & Sign
    tx = soroban_server.prepare_transaction(tx, sim)
    tx.sign(kp)

    # Submit
    print("Submitting...")
    resp = soroban_server.send_transaction(tx)
    if resp.status == SendTransactionStatus.ERROR:
        print(f"Submit error: {resp.error}")
        return

    tx_hash = resp.hash
    print(f"Transaction submitted. Hash: {tx_hash}")

    # Poll
    print("Waiting for confirmation...")
    for _ in range(60):
        result = soroban_server.get_transaction(tx_hash)
        if result.status == GetTransactionStatus.SUCCESS:
            print("Successfully updated treasury to house account!")
            return
        if result.status == GetTransactionStatus.FAILED:
            print("Transaction failed on-chain.")
            return
        await asyncio.sleep(1)

    print("Transaction timed out.")

if __name__ == "__main__":
    asyncio.run(main())
