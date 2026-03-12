"""
SHx Tip Bot - Testnet Setup Script
Creates and funds testnet accounts, sets up a test SHX asset,
establishes trustlines, mints test tokens, and outputs .env values.

Run: venv\\Scripts\\python.exe setup_testnet.py
"""

import asyncio
import json
import sys
import io
import aiohttp
from stellar_sdk import Keypair, Server, TransactionBuilder, Network, Asset

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HORIZON_URL = "https://horizon-testnet.stellar.org"
FRIENDBOT_URL = "https://friendbot.stellar.org"
NETWORK_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE


async def fund_account(session, public_key, label):
    """Fund a testnet account via Friendbot."""
    print(f"  Funding {label} ({public_key[:12]}...)...", end=" ", flush=True)
    try:
        async with session.get(
            f"{FRIENDBOT_URL}?addr={public_key}",
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status == 200:
                print("[OK]")
            else:
                text = await resp.text()
                if "createAccountAlreadyExist" in text:
                    print("[OK - already exists]")
                else:
                    print(f"[FAIL - {resp.status}]")
                    raise Exception(f"Friendbot failed for {label}: {text[:200]}")
    except aiohttp.ClientError as e:
        print(f"[FAIL - {e}]")
        raise


async def main():
    print("=" * 55)
    print("  SHx Tip Bot - Testnet Setup")
    print("=" * 55)

    # -- Step 1: Generate Keypairs --
    print("\n[Step 1] Generating keypairs...\n")

    house_kp = Keypair.random()
    treasury_kp = Keypair.random()
    issuer_kp = Keypair.random()

    print(f"  House:    {house_kp.public_key}")
    print(f"  Treasury: {treasury_kp.public_key}")
    print(f"  Issuer:   {issuer_kp.public_key}")

    # -- Step 2: Fund via Friendbot --
    print("\n[Step 2] Funding accounts via Friendbot...\n")

    async with aiohttp.ClientSession() as session:
        await fund_account(session, house_kp.public_key, "House")
        await fund_account(session, treasury_kp.public_key, "Treasury")
        await fund_account(session, issuer_kp.public_key, "Issuer")

    print("\n  Waiting for ledger confirmation (6s)...")
    await asyncio.sleep(6)

    # -- Step 3: Create SHX asset + trustlines --
    print("\n[Step 3] Creating test SHX asset...\n")

    server = Server(HORIZON_URL)
    shx_asset = Asset("SHX", issuer_kp.public_key)

    # House: add SHX trustline
    print("  Adding SHX trustline to House...", end=" ", flush=True)
    house_account = server.load_account(house_kp.public_key)
    tx = (
        TransactionBuilder(
            source_account=house_account,
            network_passphrase=NETWORK_PASSPHRASE,
            base_fee=100,
        )
        .append_change_trust_op(asset=shx_asset)
        .set_timeout(300)
        .build()
    )
    tx.sign(house_kp)
    server.submit_transaction(tx)
    print("[OK]")

    # Treasury: add SHX trustline
    print("  Adding SHX trustline to Treasury...", end=" ", flush=True)
    treasury_account = server.load_account(treasury_kp.public_key)
    tx = (
        TransactionBuilder(
            source_account=treasury_account,
            network_passphrase=NETWORK_PASSPHRASE,
            base_fee=100,
        )
        .append_change_trust_op(asset=shx_asset)
        .set_timeout(300)
        .build()
    )
    tx.sign(treasury_kp)
    server.submit_transaction(tx)
    print("[OK]")

    # Issuer: mint SHX to House
    print("  Minting 10,000,000 SHX to House...", end=" ", flush=True)
    issuer_account = server.load_account(issuer_kp.public_key)
    tx = (
        TransactionBuilder(
            source_account=issuer_account,
            network_passphrase=NETWORK_PASSPHRASE,
            base_fee=100,
        )
        .append_payment_op(
            destination=house_kp.public_key,
            asset=shx_asset,
            amount="10000000",
        )
        .set_timeout(300)
        .build()
    )
    tx.sign(issuer_kp)
    server.submit_transaction(tx)
    print("[OK]")

    # -- Step 4: Output --
    print("\n" + "=" * 55)
    print("  [OK] Testnet Setup Complete!")
    print("=" * 55)

    env_values = {
        "STELLAR_NETWORK": "testnet",
        "HORIZON_URL": HORIZON_URL,
        "SOROBAN_RPC_URL": "https://soroban-testnet.stellar.org",
        "SHX_ASSET_CODE": "SHX",
        "SHX_ISSUER": issuer_kp.public_key,
        "HOUSE_ACCOUNT_PUBLIC": house_kp.public_key,
        "HOUSE_ACCOUNT_SECRET": house_kp.secret,
        "TREASURY_ACCOUNT": treasury_kp.public_key,
    }

    print("\nCopy these into your .env file:\n")
    print("-" * 55)
    for key, val in env_values.items():
        print(f"{key}={val}")
    print("-" * 55)

    # Save to files
    with open("testnet_accounts.json", "w") as f:
        json.dump(
            {
                "house": {"public": house_kp.public_key, "secret": house_kp.secret},
                "treasury": {"public": treasury_kp.public_key, "secret": treasury_kp.secret},
                "issuer": {"public": issuer_kp.public_key, "secret": issuer_kp.secret},
                "shx_asset": {"code": "SHX", "issuer": issuer_kp.public_key},
            },
            f,
            indent=2,
        )

    with open("testnet_secrets.env", "w") as f:
        for key, val in env_values.items():
            f.write(f"{key}={val}\n")

    print(f"\nAccount details saved to testnet_accounts.json")
    print(f"Env values saved to testnet_secrets.env")
    print(f"\n[!] NEVER commit these files to git!")
    print(f"\nHouse account has 10,000,000 test SHX ready.")
    print(f"\nNext: Deploy the Soroban contract and update SOROBAN_CONTRACT_ID in .env")


if __name__ == "__main__":
    asyncio.run(main())
