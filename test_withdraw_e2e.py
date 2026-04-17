"""
End-to-end withdrawal test that bypasses Discord completely.
Signs a withdrawal ticket and simulates the claim against the live contract.
"""
import asyncio
import os
import time
import base64
from dotenv import load_dotenv
load_dotenv()

import stellar_utils as stellar
from stellar_sdk import (
    Keypair, SorobanServer, TransactionBuilder, scval, 
    Network, Server, xdr
)

async def test_e2e():
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    pubkey = os.getenv("HOUSE_ACCOUNT_PUBLIC", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://mainnet.sorobanrpc.com")
    horizon_url = os.getenv("HORIZON_URL", "https://horizon.stellar.org")
    network = os.getenv("STELLAR_NETWORK", "public")
    
    if network == "public":
        passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
    else:
        passphrase = Network.TESTNET_NETWORK_PASSPHRASE
    
    kp = Keypair.from_secret(secret)
    
    print("=" * 60)
    print("E2E WITHDRAWAL TEST")
    print("=" * 60)
    print(f"Network:  {network}")
    print(f"Contract: {contract_id}")
    print(f"User:     {pubkey}")
    print(f"Note:     User IS the house account (self-withdrawal)")
    print()
    
    # Step 1: Generate signature using the CURRENT code
    amount_shx = 1.0  # Small test amount
    nonce = int(time.time() * 1000)  # Unique nonce (ms timestamp)
    amount_stroops = stellar._to_stroops(amount_shx)
    
    print(f"Step 1: Generating signature...")
    print(f"  Amount: {amount_shx} SHx ({amount_stroops} stroops)")
    print(f"  Nonce:  {nonce}")
    
    expires_at = int(time.time() + 900)
    sig_b64 = stellar.sign_withdrawal(pubkey, amount_shx, nonce, expires_at)
    sig_bytes = base64.b64decode(sig_b64)
    print(f"  Signature (b64): {sig_b64[:40]}...")
    
    # Step 1b: Verify the payload construction matches what we tested
    payload = (
        scval.to_address(contract_id).to_xdr_bytes() +
        scval.to_address(pubkey).to_xdr_bytes() +
        scval.to_int128(amount_stroops).to_xdr_bytes() +
        scval.to_uint64(nonce).to_xdr_bytes() +
        scval.to_uint64(expires_at).to_xdr_bytes()
    )
    print(f"  Payload size: {len(payload)} bytes")
    
    # Verify locally
    try:
        kp.verify(payload, sig_bytes)
        print(f"  Local verify: PASS")
    except Exception as e:
        print(f"  Local verify: FAIL - {e}")
        print(f"  This means sign_withdrawal is using a different payload format!")
        # Debug: what is sign_withdrawal actually signing?
        print(f"  Let's check what sign_withdrawal builds...")
        
        # Manually rebuild what sign_withdrawal does
        inner_payload = (
            scval.to_address(contract_id).to_xdr_bytes() +
            scval.to_address(pubkey).to_xdr_bytes() +
            scval.to_int128(amount_stroops).to_xdr_bytes() +
            scval.to_uint64(nonce).to_xdr_bytes()
        )
        print(f"  Expected payload hex: {inner_payload.hex()}")
        return
    
    # Step 2: Build the claim_withdrawal transaction
    print()
    print(f"Step 2: Building claim_withdrawal transaction...")
    
    server = SorobanServer(rpc_url)
    horizon = Server(horizon_url)
    source_acc = horizon.load_account(kp.public_key)
    
    params = [
        scval.to_address(pubkey),       # user
        scval.to_int128(amount_stroops), # amount
        scval.to_uint64(nonce),          # nonce
        scval.to_uint64(expires_at),     # expires_at
        scval.to_bytes(sig_bytes),       # signature
    ]
    
    builder = TransactionBuilder(
        source_acc, network_passphrase=passphrase, base_fee=100_000
    ).append_invoke_contract_function_op(
        contract_id=contract_id,
        function_name="claim_withdrawal",
        parameters=params,
    ).set_timeout(300)
    
    tx = builder.build()
    
    # Step 3: Simulate
    print(f"Step 3: Simulating against live contract...")
    sim = server.simulate_transaction(tx)
    
    if sim.error:
        print(f"  SIMULATION FAILED: {sim.error}")
        
        # Decode events to find the specific error
        if sim.events:
            for i, ev in enumerate(sim.events):
                decoded = base64.b64decode(ev)
                if b"failed ED25519" in decoded:
                    print(f"  Event {i}: SIGNATURE VERIFICATION FAILED")
                elif b"NonceAlreadyUsed" in decoded:
                    print(f"  Event {i}: NONCE ALREADY USED")
                elif b"InsufficientAllowance" in decoded:
                    print(f"  Event {i}: INSUFFICIENT ALLOWANCE (House -> Contract)")
                elif b"trap" in decoded:
                    print(f"  Event {i}: VM TRAP (see above for root cause)")
                elif b"fn_call" in decoded:
                    print(f"  Event {i}: Function call logged")
                else:
                    # Try to find readable strings
                    readable = bytes(b for b in decoded if 32 <= b < 127).decode('ascii', errors='ignore')
                    print(f"  Event {i}: {readable[:100]}")
    else:
        print(f"  SIMULATION SUCCEEDED!")
        print()
        print(f"  The signature is valid and the contract would accept this claim.")
        print(f"  To actually submit, you would sign and send the prepared transaction.")
        print()
        
        # Optionally prepare and submit
        answer = input("  Submit this transaction for real? (y/N): ").strip().lower()
        if answer == 'y':
            print(f"  Preparing transaction...")
            prepared_tx = server.prepare_transaction(tx, sim)
            prepared_tx.sign(kp)
            
            print(f"  Submitting...")
            resp = server.send_transaction(prepared_tx)
            print(f"  Status: {resp.status}")
            print(f"  Hash:   {resp.hash}")
            
            if resp.status != "ERROR":
                print(f"  Waiting for confirmation...")
                for _ in range(30):
                    result = server.get_transaction(resp.hash)
                    if result.status == "SUCCESS":
                        print(f"  TRANSACTION CONFIRMED!")
                        explorer = stellar.get_explorer_url(resp.hash)
                        print(f"  Explorer: {explorer}")
                        break
                    elif result.status == "FAILED":
                        print(f"  TRANSACTION FAILED ON-CHAIN")
                        break
                    await asyncio.sleep(2)
    
    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_e2e())
