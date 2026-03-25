import os
import asyncio
from dotenv import load_dotenv
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset

async def send_simple_payment():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    target = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"
    network_type = os.getenv("STELLAR_NETWORK", "testnet").strip()
    
    passphrase = Network.TESTNET_NETWORK_PASSPHRASE if network_type == "testnet" else Network.PUBLIC_NETWORK_PASSPHRASE
    horizon_url = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip()
    
    print(f"Network: {network_type}")
    print(f"Horizon: {horizon_url}")
    print(f"Passphrase: {passphrase}")
    
    kp = Keypair.from_secret(secret)
    server = Server(horizon_url)
    
    print(f"Source Account: {kp.public_key}")
    source_acc = server.load_account(kp.public_key)
    
    tx = (
        TransactionBuilder(source_acc, network_passphrase=passphrase, base_fee=100000)
        .append_payment_op(destination=target, amount="0.0001", asset=Asset.native())
        .set_timeout(30)
        .build()
    )
    
    tx.sign(kp)
    print("Submitting simple payment...")
    try:
        res = server.submit_transaction(tx)
        print(f"SUCCESS! Hash: {res['hash']}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(send_simple_payment())
