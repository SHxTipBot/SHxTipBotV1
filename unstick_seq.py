import os
import asyncio
from dotenv import load_dotenv
from stellar_sdk import Keypair, Server, Network, TransactionBuilder

async def unstick_sequence():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    kp = Keypair.from_secret(secret)
    network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE if os.getenv("STELLAR_NETWORK") == "testnet" else Network.PUBLIC_NETWORK_PASSPHRASE
    horizon_url = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip()
    server = Server(horizon_url)
    
    print(f"Unsticking sequence for {kp.public_key} via self-payment...")
    source_acc = server.load_account(kp.public_key)
    print(f"Current Seq: {source_acc.sequence}")
    
    # Use Asset.native() for native XLM
    from stellar_sdk import Asset
    
    tx = (
        TransactionBuilder(source_acc, network_passphrase=network_passphrase, base_fee=100000)
        .append_payment_op(kp.public_key, Asset.native(), "1")
        .set_timeout(30)
        .build()
    )
    tx.sign(kp)
    
    try:
        resp = server.submit_transaction(tx)
        print(f"Self-payment success! Hash: {resp['hash']}")
        print(f"Final Seq: {source_acc.sequence}")
    except Exception as e:
        print(f"Self-payment failed: {e}")

if __name__ == "__main__":
    asyncio.run(unstick_sequence())
