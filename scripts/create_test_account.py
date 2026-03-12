"""Generate, fund, and prepare a second testnet account for tip testing."""
import asyncio, os, io, sys
import aiohttp
from dotenv import load_dotenv
from stellar_sdk import Keypair, Server, TransactionBuilder, Network, Asset

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
load_dotenv()

HORIZON = "https://horizon-testnet.stellar.org"
SHX_ISSUER = os.getenv("SHX_ISSUER", "")
HOUSE_SECRET = os.getenv("HOUSE_ACCOUNT_SECRET", "")

async def main():
    kp = Keypair.random()
    print("=" * 60)
    print("  Second Testnet Account for Tip Testing")
    print("=" * 60)
    print(f"\n  Public Key:  {kp.public_key}")
    print(f"  Secret Key:  {kp.secret}")
    print("\n  SAVE THESE! You need the public key to link in Discord.\n")

    async with aiohttp.ClientSession() as session:
        # 1. Fund
        print("[1] Funding via Friendbot...")
        async with session.get(
            f"https://friendbot.stellar.org?addr={kp.public_key}",
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            print(f"  -> {'Funded!' if resp.status == 200 else 'Already exists'}")

        await asyncio.sleep(5)

        # 2. Trustline
        print("[2] Adding SHX trustline...")
        server = Server(HORIZON)
        acc = server.load_account(kp.public_key)
        tx = (
            TransactionBuilder(
                source_account=acc,
                network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
                base_fee=100,
            )
            .append_change_trust_op(asset=Asset("SHX", SHX_ISSUER))
            .set_timeout(300)
            .build()
        )
        tx.sign(kp)
        server.submit_transaction(tx)
        print("  -> Trustline added!")

        # 3. Send SHX
        print("[3] Sending 500 test SHX from house account...")
        house_kp = Keypair.from_secret(HOUSE_SECRET)
        house_acc = server.load_account(house_kp.public_key)
        tx2 = (
            TransactionBuilder(
                source_account=house_acc,
                network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
                base_fee=100,
            )
            .append_payment_op(
                destination=kp.public_key,
                asset=Asset("SHX", SHX_ISSUER),
                amount="500",
            )
            .set_timeout(300)
            .build()
        )
        tx2.sign(house_kp)
        result = server.submit_transaction(tx2)
        print(f"  -> Sent 500 SHX! TX: {result['hash']}")

    print("\n" + "=" * 60)
    print("  Done! Link this account to your alt Discord user:")
    print(f"  Public Key: {kp.public_key}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
