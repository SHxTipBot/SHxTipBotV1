import asyncio
import os
from stellar_sdk import SorobanServer, TransactionBuilder, Network, Keypair, scval
from dotenv import load_dotenv

load_dotenv()

async def verify_contract():
    rpc_url = "https://mainnet.sorobanrpc.com"
    contract_id = "CDLSO3PZYXKBLXOXABZ4OLCTOG67XKQDBAGO6CJKMSS4QATY3I5ZBKUY"
    
    print(f"Verifying contract {contract_id} on {rpc_url}...")
    
    server = SorobanServer(rpc_url)
    
    # Create a dummy transaction to simulate a call
    # We call 'get_admin' or similar if it exists, or just any function
    source_kp = Keypair.from_secret("SCVPXHPECJJV7HYU7EDAX35UVYZZKUBCGGTJVLGKM3V6EBTIXC3ACJV3") # House secret from .env
    
    try:
        # Just building a minimal tx to simulate
        builder = TransactionBuilder(
            source_account=source_kp.public_key,
            network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
            base_fee=100
        ).append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="get_version", # Try a common function name or any
            parameters=[]
        )
        tx = builder.build()
        sim = server.simulate_transaction(tx)
        
        if sim.error:
            print(f"Simulation Error: {sim.error}")
            if "HostError: Error(Value, InvalidInput)" in str(sim.error):
                print("Result: Function might not exist, but contract ID was recognized (no 'ContractNotFound' error).")
            elif "ContractNotFound" in str(sim.error) or "ResourceNotFound" in str(sim.error):
                print("Result: CONTRACT NOT FOUND on Mainnet.")
            else:
                print("Result: Unexpected error during simulation.")
        else:
            print("Result: Simulation SUCCESS. Contract exists and responded.")
            
    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify_contract())
