import os
import asyncio
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server

async def horizon_admin_setup():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    
    kp = Keypair.from_secret(secret)
    network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE if os.getenv("STELLAR_NETWORK") == "testnet" else Network.PUBLIC_NETWORK_PASSPHRASE
    horizon_url = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip()
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
    
    server = SorobanServer(rpc_url)
    horizon = Server(horizon_url)
    
    print(f"Setting Admin Pubkey via HORIZON submit...")
    source_acc = horizon.load_account(kp.public_key)
    print(f"Horizon Seq: {source_acc.sequence}")
    
    raw_pubkey = kp.raw_public_key()
    
    builder = (
        TransactionBuilder(source_acc, network_passphrase=network_passphrase, base_fee=250000)
        .append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="set_admin_pubkey",
            parameters=[scval.to_bytes(raw_pubkey)]
        )
        .set_timeout(300)
    )
    
    print("Simulating...")
    sim = server.simulate_transaction(builder.build())
    if sim.error:
        print(f"Sim Error: {sim.error}")
        return
        
    tx = builder.build()
    tx = server.prepare_transaction(tx, sim)
    tx.sign(kp)
    
    print("Submitting via HORIZON...")
    try:
        resp = horizon.submit_transaction(tx)
        print(f"SUCCESS! Hash: {resp['hash']}")
    except Exception as e:
        print(f"Horizon Submit Failed: {e}")

if __name__ == "__main__":
    asyncio.run(horizon_admin_setup())
