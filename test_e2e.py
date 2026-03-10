"""
SHx Tip Bot — End-to-End Testnet Preparation Script

This script prepares a Stellar testnet account for testing the SHx Tip Bot.
It will:
  1. Fund the account with 10,000 XLM via Friendbot (if not already funded)
  2. Add a trustline for the test SHX asset
  3. Send 1,000 test SHX from the house account to the target account
  4. Verify and print the final SHX balance

Usage:
  venv\\Scripts\\python.exe test_e2e.py
  venv\\Scripts\\python.exe test_e2e.py GABC123...  (provide a custom public key)

By default, uses the account in the TARGET_PUBLIC_KEY variable below.
"""

import asyncio
import sys
import io
import os

import aiohttp
from dotenv import load_dotenv
from stellar_sdk import Keypair, Server, TransactionBuilder, Network, Asset

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────

# Default target account — override via command-line argument
TARGET_PUBLIC_KEY = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"

HORIZON_URL = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org")
FRIENDBOT_URL = "https://friendbot.stellar.org"
NETWORK_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE

SHX_ASSET_CODE = os.getenv("SHX_ASSET_CODE", "SHX")
SHX_ISSUER = os.getenv("SHX_ISSUER", "")

HOUSE_ACCOUNT_SECRET = os.getenv("HOUSE_ACCOUNT_SECRET", "")
HOUSE_ACCOUNT_PUBLIC = os.getenv("HOUSE_ACCOUNT_PUBLIC", "")

# Amount of test SHX to send
TEST_SHX_AMOUNT = "1000"


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_shx_asset() -> Asset:
    return Asset(SHX_ASSET_CODE, SHX_ISSUER)


async def check_account_exists(session, public_key: str) -> bool:
    """Check if a Stellar account exists on the network."""
    url = f"{HORIZON_URL}/accounts/{public_key}"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        return resp.status == 200


async def get_shx_balance(session, public_key: str) -> float | None:
    """Get SHX balance for an account."""
    url = f"{HORIZON_URL}/accounts/{public_key}"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        if resp.status != 200:
            return None
        data = await resp.json()
        for bal in data.get("balances", []):
            if (bal.get("asset_code") == SHX_ASSET_CODE
                    and bal.get("asset_issuer") == SHX_ISSUER):
                return float(bal["balance"])
        return 0.0  # account exists but no trustline yet


async def has_shx_trustline(session, public_key: str) -> bool:
    """Check if the account has an SHX trustline."""
    url = f"{HORIZON_URL}/accounts/{public_key}"
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        if resp.status != 200:
            return False
        data = await resp.json()
        for bal in data.get("balances", []):
            if (bal.get("asset_code") == SHX_ASSET_CODE
                    and bal.get("asset_issuer") == SHX_ISSUER):
                return True
        return False


# ── Main Flow ────────────────────────────────────────────────────────────────

async def main():
    target_key = sys.argv[1] if len(sys.argv) > 1 else TARGET_PUBLIC_KEY

    print("=" * 60)
    print("  SHx Tip Bot — Testnet E2E Preparation")
    print("=" * 60)
    print(f"\n  Target account:  {target_key}")
    print(f"  House account:   {HOUSE_ACCOUNT_PUBLIC[:12]}...")
    print(f"  SHX asset:       {SHX_ASSET_CODE} / {SHX_ISSUER[:12]}...")
    print(f"  Network:         Testnet")
    print(f"  Horizon:         {HORIZON_URL}")

    if not HOUSE_ACCOUNT_SECRET:
        print("\n[ERROR] HOUSE_ACCOUNT_SECRET not set in .env!")
        sys.exit(1)
    if not SHX_ISSUER:
        print("\n[ERROR] SHX_ISSUER not set in .env!")
        sys.exit(1)

    house_kp = Keypair.from_secret(HOUSE_ACCOUNT_SECRET)
    server = Server(HORIZON_URL)
    shx_asset = get_shx_asset()

    async with aiohttp.ClientSession() as session:

        # ── Step 1: Fund account via Friendbot ───────────────────────────
        print(f"\n[Step 1] Funding {target_key[:12]}... via Friendbot...")

        account_exists = await check_account_exists(session, target_key)
        if account_exists:
            print("  → Account already exists, skipping Friendbot.")
        else:
            async with session.get(
                f"{FRIENDBOT_URL}?addr={target_key}",
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 200:
                    print("  → Funded with 10,000 XLM! ✓")
                else:
                    text = await resp.text()
                    if "createAccountAlreadyExist" in text:
                        print("  → Account already exists. ✓")
                    else:
                        print(f"  → ERROR: {text[:200]}")
                        sys.exit(1)

            print("  → Waiting 6s for ledger confirmation...")
            await asyncio.sleep(6)

        # ── Step 2: Add SHX trustline ────────────────────────────────────
        print(f"\n[Step 2] Checking SHX trustline...")

        has_tl = await has_shx_trustline(session, target_key)
        if has_tl:
            print("  → SHX trustline already exists. ✓")
        else:
            print("  → Adding SHX trustline...")
            print()
            print("  ┌─────────────────────────────────────────────────────┐")
            print("  │  NOTE: This step requires the TARGET account's     │")
            print("  │  SECRET KEY to sign the trustline transaction.      │")
            print("  │                                                     │")
            print("  │  Since you only provided the public key, you have   │")
            print("  │  two options:                                       │")
            print("  │                                                     │")
            print("  │  OPTION A: Add the trustline in Lobstr/Freighter:   │")
            print(f"  │    Asset code: {SHX_ASSET_CODE:46}│")
            print(f"  │    Issuer: {SHX_ISSUER[:44]}... │")
            print("  │                                                     │")
            print("  │  OPTION B: Set TARGET_SECRET_KEY env var and re-run │")
            print("  └─────────────────────────────────────────────────────┘")

            # Try to use TARGET_SECRET_KEY if available
            target_secret = os.getenv("TARGET_SECRET_KEY", "")
            if target_secret:
                try:
                    target_kp = Keypair.from_secret(target_secret)
                    target_account = server.load_account(target_key)
                    tx = (
                        TransactionBuilder(
                            source_account=target_account,
                            network_passphrase=NETWORK_PASSPHRASE,
                            base_fee=100,
                        )
                        .append_change_trust_op(asset=shx_asset)
                        .set_timeout(300)
                        .build()
                    )
                    tx.sign(target_kp)
                    server.submit_transaction(tx)
                    print("\n  → SHX trustline added! ✓")
                except Exception as e:
                    print(f"\n  → ERROR adding trustline: {e}")
                    print("  → Please add the trustline manually via your wallet.")
                    sys.exit(1)
            else:
                print("\n  → Skipping trustline (no secret key available).")
                print("  → Please add the SHX trustline manually in your wallet.")
                print(f"     Asset: {SHX_ASSET_CODE} | Issuer: {SHX_ISSUER}")
                print("\n  After adding the trustline, re-run this script to proceed.\n")
                sys.exit(0)

        # ── Step 3: Send test SHX from house account ─────────────────────
        print(f"\n[Step 3] Sending {TEST_SHX_AMOUNT} test SHX...")

        try:
            house_account = server.load_account(house_kp.public_key)
            tx = (
                TransactionBuilder(
                    source_account=house_account,
                    network_passphrase=NETWORK_PASSPHRASE,
                    base_fee=100,
                )
                .append_payment_op(
                    destination=target_key,
                    asset=shx_asset,
                    amount=TEST_SHX_AMOUNT,
                )
                .set_timeout(300)
                .build()
            )
            tx.sign(house_kp)
            result = server.submit_transaction(tx)
            tx_hash = result.get("hash", "unknown")
            print(f"  → Sent {TEST_SHX_AMOUNT} SHX! ✓")
            print(f"  → TX hash: {tx_hash}")
            print(f"  → View: https://stellar.expert/explorer/testnet/tx/{tx_hash}")
        except Exception as e:
            print(f"  → ERROR sending SHX: {e}")
            # Not fatal — might already have enough from a previous run

        # ── Step 4: Verify balance ───────────────────────────────────────
        print(f"\n[Step 4] Verifying SHX balance...")
        await asyncio.sleep(3)  # wait for ledger

        balance = await get_shx_balance(session, target_key)
        if balance is not None:
            print(f"  → SHX balance: {balance:,.7f} SHX ✓")
        else:
            print(f"  → Could not fetch balance (account may not exist).")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  ✅ Testnet Preparation Complete!")
    print("=" * 60)
    print(f"""
  Your account {target_key[:12]}... is now ready for testing.

  Next steps:
  1. Start the bot + web server:
       venv\\Scripts\\python.exe run.py

  2. In Discord, type:  /link
     → Click the link to open the wallet-linking page

  3. On the web page, enter your public key:
       {target_key}

  4. Complete the wallet linking flow

  5. In Discord, type:  /balance
     → Confirm your SHX balance shows up

  6. To test tipping, link a 2nd testnet account to another Discord user,
     then use:  /tip @user 1 test tip!
""")


if __name__ == "__main__":
    asyncio.run(main())
