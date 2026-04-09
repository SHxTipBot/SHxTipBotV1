import os
import asyncio
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server

async def test_full_withdrawal_cycle():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    kp = Keypair.from_secret(secret)
    
    user_address = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"
    amount_shx = 2.0
    nonce = 999988887777 # unique nonce
    
    print(f"Testing signature for User: {user_address} | Amount: {amount_shx} | Nonce: {nonce}")
    
    # Generate signature using the bot's logic
    signature_b64 = stellar.sign_withdrawal(user_address, amount_shx, nonce)
    signature_bytes = base64.b64decode(signature_b64)
    
    # 2. Simulate call to 'claim_withdrawal'
    rpc_url = "https://soroban-testnet.stellar.org"
    server = SorobanServer(rpc_url)
    horizon = Server("https://horizon-testnet.stellar.org")
    
    source_acc = horizon.load_account(kp.public_key)
    
    amount_stroops = stellar._to_stroops(amount_shx)
    
    params = [
        stellar.to_sc_address(user_address),
        scval.to_int128(amount_stroops),
        scval.to_uint64(nonce),
        scval.to_bytes(signature_bytes)
    ]
    
    builder = (
        TransactionBuilder(source_acc, network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE)
        .append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="claim_withdrawal",
            parameters=params
        )
    )
    
    print("Simulating claim_withdrawal...")
    sim = server.simulate_transaction(builder.build())
    if sim.error:
        print(f"CLAIM SIMULATION FAILED: {sim.error}")
        # Identify if it's the crypto error
        return
        
    print("CLAIM SIMULATION SUCCESS! (Signature Verified)")
    for event in sim.events:
        print(f"Event: {event.topics}")

if __name__ == "__main__":
    import base64
    asyncio.run(test_full_withdrawal_cycle())
