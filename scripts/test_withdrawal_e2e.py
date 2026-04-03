import asyncio
import os
import base64
import secrets
import aiohttp
import os
import sys
from dotenv import load_dotenv

# Ensure the root directory is in sys.path so we can import stellar_utils
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

# Load environment variables explicitly from the root .env
load_dotenv(os.path.join(root_dir, '.env'))

import stellar_utils as stellar
import time
from stellar_sdk import Keypair, Network, SorobanServer, TransactionBuilder, scval, xdr as stellar_xdr, Server

async def test_withdrawal_e2e():
    print("--- Starting End-to-End Withdrawal Test on Testnet ---")
    
    # 1. Configuration Check
    contract_id = os.getenv("SOROBAN_CONTRACT_ID")
    house_public = os.getenv("HOUSE_ACCOUNT_PUBLIC")
    if not contract_id or not house_public:
        print("❌ Error: SOROBAN_CONTRACT_ID or HOUSE_ACCOUNT_PUBLIC not set in .env")
        return

    print(f"Contract: {contract_id}")
    print(f"House Account: {house_public}")

    # 2. Check House Account Allowance
    print("Checking House Account allowance...")
    allowance = await stellar.check_shx_allowance(house_public, contract_id)
    print(f"Current Allowance: {allowance} SHx")
    
    if allowance < 100:
        print("Allowance low. Granting 1M SHx allowance to contract...")
        res = await stellar.approve_shx(os.getenv("HOUSE_ACCOUNT_SECRET"), amount=1_000_000)
        if res["success"]:
            print(f"✅ Allowance granted. Hash: {res['hash']}")
            await asyncio.sleep(5)
        else:
            print(f"❌ Failed to grant allowance: {res['error']}")
            return

    # 3. Create a Temporary Test User
    print("Creating temporary test user...")
    user_kp = Keypair.random()
    user_public = user_kp.public_key
    print(f"Test User Public Key: {user_public}")

    # 4. Fund Test User via Friendbot
    print("Funding user via Friendbot...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://friendbot.stellar.org?addr={user_public}") as resp:
            if resp.status == 200:
                print("✅ User funded.")
            else:
                print(f"❌ Friendbot failed: {await resp.text()}")
                return
    
    await asyncio.sleep(5) # Wait for network propagation

    # 5. Add SHx Trustline for Test User
    print("Adding SHx trustline to test user...")
    shx_asset = stellar.get_shx_asset()
    horizon_server = Server(stellar.HORIZON_URL)
    
    try:
        user_account = horizon_server.load_account(user_public)
        builder = TransactionBuilder(
            source_account=user_account,
            network_passphrase=stellar.NETWORK_PASSPHRASE,
            base_fee=100000,
        ).append_change_trust_op(asset=shx_asset).set_timeout(30)
        
        tx = builder.build()
        tx.sign(user_kp)
        horizon_server.submit_transaction(tx)
        print("✅ Trustline added.")
    except Exception as e:
        print(f"❌ Failed to add trustline: {e}")
        return

    # 6. Generate Withdrawal Signature
    amount = 10.0
    nonce = int(time.time() * 1000)
    print(f"Generating signature for {amount} SHx, Nonce: {nonce}...")
    
    try:
        signature_b64 = stellar.sign_withdrawal(user_public, amount, nonce)
        print(f"✅ Signature (B64): {signature_b64}")
    except Exception as e:
        print(f"❌ Failed to generate signature: {e}")
        return

    # 7. Claim Withdrawal on Testnet (User signs and pays gas)
    print("Submitting claim_withdrawal to Soroban...")
    soroban_server = SorobanServer(stellar.SOROBAN_RPC_URL)
    horizon_server = Server(stellar.HORIZON_URL)
    
    # Reload user account for fresh sequence
    user_account = horizon_server.load_account(user_public)
    
    sig_bytes = base64.b64decode(signature_b64)
    amount_stroops = stellar._to_stroops(amount)
    
    builder = TransactionBuilder(
        source_account=user_account,
        network_passphrase=stellar.NETWORK_PASSPHRASE,
        base_fee=100_000,
    ).set_timeout(300)
    
    builder.append_invoke_contract_function_op(
        contract_id=contract_id,
        function_name="claim_withdrawal",
        parameters=[
            scval.to_address(user_public),
            scval.to_int128(amount_stroops),
            scval.to_uint64(nonce),
            scval.to_bytes(sig_bytes), # Soroban BytesN<64> can be passed as Bytes
        ],
    )
    
    tx = builder.build()
    
    print("Simulating transaction...")
    sim = soroban_server.simulate_transaction(tx)
    if sim.error:
        print(f"❌ Simulation failed: {sim.error}")
        if hasattr(sim, 'events') and sim.events:
            for event in sim.events:
                print(f"  Event: {event}")
        return

    print("Preparing and signing transaction...")
    tx = soroban_server.prepare_transaction(tx, sim)
    tx.sign(user_kp)
    
    print("Submitting to network...")
    resp = soroban_server.send_transaction(tx)
    if resp.status == "ERROR":
        print(f"❌ Submission error: {resp.error_result_xdr}")
        return
    
    tx_hash = resp.hash
    print(f"Transaction Hash: {tx_hash}")
    
    # 8. Poll for confirmation
    print("Waiting for ledger confirmation...")
    for _ in range(60):
        res = soroban_server.get_transaction(tx_hash)
        if res.status == "SUCCESS":
            print("\nSUCCESS! Withdrawal confirmed on-chain.")
            print(f"Verification Link: {stellar.get_explorer_url(tx_hash)}")
            print(f"👤 Test User: {user_public}")
            print(f"💰 Amount: {amount} SHx")
            return
        elif res.status == "FAILED":
            print(f"❌ FAILED: Transaction failed on-chain. XDR: {res.result_xdr}")
            return
        await asyncio.sleep(2)

    print("⌛ Timed out waiting for confirmation.")

if __name__ == "__main__":
    import time
    asyncio.run(test_withdrawal_e2e())
