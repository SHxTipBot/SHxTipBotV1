"""
Utility to swap accumulated SHX in the house account back to XLM via the Stellar DEX.
This maintains XLM liquidity for the house account to continue paying for tip transaction fees.

Usage: python swap_shx_xlm.py --amount 100
"""

import os
import argparse
import asyncio
from dotenv import load_dotenv
from stellar_sdk import Keypair, Network, Server, TransactionBuilder, Asset

load_dotenv()

# Load config from .env
HOUSE_ACCOUNT_SECRET = os.getenv("HOUSE_ACCOUNT_SECRET")
HOUSE_ACCOUNT_PUBLIC = os.getenv("HOUSE_ACCOUNT_PUBLIC")
SHX_ASSET_CODE = os.getenv("SHX_ASSET_CODE", "SHX")
SHX_ISSUER = os.getenv("SHX_ISSUER")
HORIZON_URL = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org")
STELLAR_NETWORK = os.getenv("STELLAR_NETWORK", "testnet")

NETWORK_PASSPHRASE = (
    Network.TESTNET_NETWORK_PASSPHRASE
    if STELLAR_NETWORK == "testnet"
    else Network.PUBLIC_NETWORK_PASSPHRASE
)

async def main():
    parser = argparse.ArgumentParser(description="Swap SHX to XLM via Stellar DEX")
    parser.add_argument("--amount", type=float, required=True, help="Amount of SHX to swap")
    args = parser.parse_args()

    if not HOUSE_ACCOUNT_SECRET or not SHX_ISSUER:
        print("Error: Missing HOUSE_ACCOUNT_SECRET or SHX_ISSUER in .env")
        return

    print(f"Swapping {args.amount} {SHX_ASSET_CODE} to XLM for house account {HOUSE_ACCOUNT_PUBLIC}...")

    kp = Keypair.from_secret(HOUSE_ACCOUNT_SECRET)
    server = Server(HORIZON_URL)

    # Assets
    shx_asset = Asset(SHX_ASSET_CODE, SHX_ISSUER)
    xlm_asset = Asset.native()

    # Load account
    source = server.load_account(kp.public_key)

    # Build Path Payment transaction
    # We use path_payment_strict_send to swap a fixed amount of SHX for as much XLM as possible
    builder = TransactionBuilder(
        source_account=source,
        network_passphrase=NETWORK_PASSPHRASE,
        base_fee=100_000, # Higher fee for DEX operations
    )

    builder.append_path_payment_strict_send_op(
        send_asset=shx_asset,
        send_amount=str(args.amount),
        destination=HOUSE_ACCOUNT_PUBLIC,
        dest_asset=xlm_asset,
        dest_min="0.1", # Minimum XLM to receive (safety slider)
        path=[] # Direct swap if market exists
    )

    builder.set_timeout(300)
    tx = builder.build()
    tx.sign(kp)

    # Submit
    print("Submitting swap to Horizon...")
    try:
        response = server.submit_transaction(tx)
        print(f"Successfully swapped! Hash: {response['hash']}")
    except Exception as e:
        print(f"Swap failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
