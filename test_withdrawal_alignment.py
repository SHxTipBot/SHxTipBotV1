import asyncio
import os
from dotenv import load_dotenv
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, xdr, Server
import stellar_utils as stellar

load_dotenv()

async def test_alignment():
    print("=" * 60)
    print("VERIFYING WITHDRAWAL SIGNATURE ALIGNMENT")
    print("=" * 60)
    
    contract_id = os.getenv("SOROBAN_CONTRACT_ID")
    secret = os.getenv("HOUSE_ACCOUNT_SECRET")
    kp = Keypair.from_secret(secret)
    
    user_addr = kp.public_key # Use self as test user
    amount_shx = 2.0
    amount_stroops = int(amount_shx * 10_000_000)
    nonce = int(asyncio.get_event_loop().time() * 1000)
    
    # 1. Sign using the NEW shared logic
    print(f"Signing for User: {user_addr}")
    print(f"Amount: {amount_shx} SHx ({amount_stroops} stroops)")
    print(f"Nonce: {nonce}")
    
    sig_b64 = stellar.sign_withdrawal(user_addr, amount_shx, nonce)
    from base64 import b64decode
    sig_bytes = b64decode(sig_b64)
    
    # 2. Simulate call to Mainnet contract
    rpc_url = os.getenv("SOROBAN_RPC_URL")
    server = SorobanServer(rpc_url)
    network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
    
    # We need a source account for simulation
    horizon = Server(os.getenv("HORIZON_URL"))
    source_acc = horizon.load_account(kp.public_key)
    
    params = [
        scval.to_address(user_addr),
        scval.to_int128(amount_stroops),
        scval.to_uint64(nonce),
        scval.to_bytes(sig_bytes),
    ]
    
    builder = TransactionBuilder(
        source_acc, network_passphrase=network_passphrase, base_fee=100_000
    ).append_invoke_contract_function_op(
        contract_id=contract_id,
        function_name="claim_withdrawal",
        parameters=params,
    ).set_timeout(30)
    
    tx = builder.build()
    print("\nSimulating transaction on Mainnet...")
    sim = server.simulate_transaction(tx)
    
    if sim.error:
        print(f"❌ SIMULATION FAILED: {sim.error}")
        # Check if it was specifically a signature error
        if "failed ED25519" in str(sim.error) or "InvalidInput" in str(sim.error):
             print("   -> Root Cause: Signature Mismatch confirmed.")
        else:
             print(f"   -> Other error: {sim.error}")
    else:
        print("✅ SUCCESS: Signature verified by Mainnet contract simulation!")
        print(f"   Resource usage: {sim.min_resource_fee} stroops")

if __name__ == "__main__":
    asyncio.run(test_alignment())
