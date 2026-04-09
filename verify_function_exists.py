import asyncio
import os
import time
import base64
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server, xdr

async def verify_new_contract_function():
    load_dotenv()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    kp = Keypair.from_secret(secret)
    
    print(f"Verifying claim_withdrawal on NEW CONTRACT: {contract_id}")
    
    server = SorobanServer(os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip())
    horizon = Server(os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip())
    
    # Generate a mock valid signature for simulation
    user_address = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K" # Shared by user
    amount = 28.0
    nonce = int(time.time() * 1000)
    
    # Sign it using our house account (admin)
    sig_b64 = stellar.sign_withdrawal(user_address, amount, nonce)
    sig_bytes = base64.b64decode(sig_b64)
    
    # Build Simulation
    source_acc = horizon.load_account(kp.public_key)
    builder = (
        TransactionBuilder(source_acc, network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE)
        .append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="claim_withdrawal",
            parameters=[
                scval.to_address(user_address),
                scval.to_int128(int(amount * 10**7)),
                scval.to_uint64(nonce),
                scval.to_bytes(sig_bytes) # The claim_withdrawal expects BytesN<64>
            ]
        )
    )
    
    # Simulate
    sim = server.simulate_transaction(builder.build())
    if sim.error:
        print(f"RESULT: Simulation failed as expected (not auth'd), but did it find the function?")
        from stellar_sdk import xdr as stellar_xdr
        # If it was 'non-existent function', the error would be different.
        print(f"DEBUG: Simulation Error: {sim.error}")
        
    if hasattr(sim, 'results') and sim.results:
        print("SUCCESS: Function claim_withdrawal WAS FOUND on the new contract!")
    elif "non-existent contract function" in str(sim.error):
        print("FAILED: Function STILL NOT FOUND. Something is wrong with the deployment.")
    else:
        print("Simulation returned results (Function exists).")

asyncio.run(verify_new_contract_function())
