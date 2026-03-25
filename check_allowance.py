import os
import asyncio
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import SorobanServer, Keypair, scval, Network, TransactionBuilder

async def check_allowance():
    load_dotenv()
    source_secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    shx_sac = os.getenv("SHX_SAC_CONTRACT_ID", "").strip()
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
    
    kp = Keypair.from_secret(source_secret)
    server = SorobanServer(rpc_url)
    horizon = stellar.Server(os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip())
    
    print(f"Checking allowance for {kp.public_key} to spender {contract_id} on SAC {shx_sac}...")
    
    source_acc = horizon.load_account(kp.public_key)
    builder = (
        TransactionBuilder(source_acc, network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE if os.getenv("STELLAR_NETWORK") == "testnet" else Network.PUBLIC_NETWORK_PASSPHRASE)
        .append_invoke_contract_function_op(
            contract_id=shx_sac,
            function_name="allowance",
            parameters=[
                scval.to_address(kp.public_key),
                scval.to_address(contract_id)
            ]
        )
    )
    
    sim = server.simulate_transaction(builder.build())
    if sim.error:
        print(f"Simulation Error: {sim.error}")
        return
        
    # The result of simulation for a read-only call is in the result
    print(f"DEBUG: Simulation results: {sim.results}")
    if not sim.results:
        print("No results in simulation.")
        return
        
    result_xdr = sim.results[0].xdr
    print(f"DEBUG: Result XDR: {result_xdr}")
    
    # Try to parse result
    try:
        from stellar_sdk import xdr as stellar_xdr
        # This is complex, just print it for now
        print("Please check the Result XDR above.")
    except Exception as e:
        print(f"Parse error: {e}")

if __name__ == "__main__":
    asyncio.run(check_allowance())
