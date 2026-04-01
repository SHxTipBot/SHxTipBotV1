import asyncio
import os
from stellar_sdk import Keypair, Network, TransactionBuilder, Account
import stellar_utils as stellar

async def repro():
    # 1. Setup
    os.environ["STELLAR_NETWORK"] = "testnet"
    # Ensure stellar_utils is re-initialized if needed, but here we just use the functions
    
    # Generate a dummy user keypair
    kp = Keypair.random()
    public_key = kp.public_key
    discord_id = "768342085644320799"
    
    print(f"Reproduction | User: {public_key}")
    print(f"Reproduction | Discord: {discord_id}")
    
    # 2. Build Transaction (same as frontend)
    # Frontend uses fee 1000 and networkPassphrase Standard
    passphrase = Network.TESTNET_NETWORK_PASSPHRASE
    
    # We need a dummy account object with a sequence number
    source_account = Account(public_key, 123) 
    
    builder = TransactionBuilder(
        source_account=source_account,
        network_passphrase=passphrase,
        base_fee=1000
    )
    builder.append_manage_data_op(data_name="link_discord", data_value=discord_id)
    builder.set_timeout(300)
    tx = builder.build()
    
    # 3. Sign
    tx.sign(kp)
    signature_xdr = tx.to_xdr()
    
    print(f"Reproduction | Signed XDR: {signature_xdr[:50]}...")
    
    # 4. Verify (using backend logic)
    is_valid, error = stellar.verify_link_signature_xdr(public_key, signature_xdr, discord_id)
    
    if is_valid:
        print("✅ SUCCESS: Signature verified locally!")
    else:
        print(f"❌ FAILED: {error}")

if __name__ == "__main__":
    asyncio.run(repro())
