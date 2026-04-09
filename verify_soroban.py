import asyncio
import os
from stellar_sdk import SorobanServer, TransactionBuilder, Network, Keypair, scval, xdr as stellar_xdr
from dotenv import load_dotenv

load_dotenv()

async def verify_contract():
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://mainnet.sorobanrpc.com")
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "CDLSO3PZYXKBLXOXABZ4OLCTOG67XKQDBAGO6CJKMSS4QATY3I5ZBKUY")
    
    print(f"Checking Contract: {contract_id} on {rpc_url}")
    
    server = SorobanServer(rpc_url)
    
    try:
        # We can use get_ledger_entries if we know the key, 
        # but a simple simulation of a non-existent method is enough to see if the contract exists.
        # If the contract doesn't exist, we get a specific error.
        
        kp = Keypair.random()
        source = kp.public_key
        
        # Build a dummy call
        # We need a sequence number? No, simulate_transaction doesn't strictly need a valid one for just checking existence, 
        # but the SDK might complain if we don't have an account object.
        # Actually, let's just use the 'get_network' or similar if we just want to test RPC.
        # To test the contract, we MUST use simulate.
        
        # Let's try to get the ledger entry for the contract instance.
        # Key for contract instance is ContractData with key: LedgerKeyContractCode
        # Actually, easier: simulate_transaction with a dummy call.
        
        builder = TransactionBuilder(
            source_account=source,
            network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE,
            base_fee=100,
        ).append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="hello", # Likely doesn't exist, but it will test if contract exists
            parameters=[]
        )
        # We need to set a sequence number to 0 for simulation if we don't load the account
        tx = builder.build()
        sim = server.simulate_transaction(tx)
        
        if sim.error:
            err_str = str(sim.error)
            print(f"Simulation Error: {err_str}")
            if "ContractNotFound" in err_str:
                print("RESULT: Contract NOT FOUND.")
            elif "ResourceNotFound" in err_str:
                print("RESULT: Contract NOT FOUND (Resource).")
            else:
                print("RESULT: Contract EXISTS (but method 'hello' failed as expected).")
        else:
            print("RESULT: Contract EXISTS and method 'hello' (somehow) succeeded!")
            
    except Exception as e:
        print(f"Verification FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(verify_contract())
