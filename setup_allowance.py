import os
import asyncio
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network

async def setup_allowance():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    shx_sac = os.getenv("SHX_SAC_CONTRACT_ID", "").strip()
    network_type = os.getenv("STELLAR_NETWORK", "testnet").strip()
    
    passphrase = Network.TESTNET_NETWORK_PASSPHRASE if network_type == "testnet" else Network.PUBLIC_NETWORK_PASSPHRASE
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
    
    kp = Keypair.from_secret(secret)
    server = SorobanServer(rpc_url)
    horizon = stellar.Server(os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip())
    
    # 1. Check Allowance
    print(f"Checking allowance for {kp.public_key} on contract {contract_id}...")
    # (Checking allowance via get_transaction or similar is complex, easier to just send an approve)
    
    # 2. Build Approve Transaction
    print("Building Approve transaction...")
    source_acc = horizon.load_account(kp.public_key)
    
    # Approve a large amount (1,000,000 SHX)
    amount_stroops = 1_000_000 * 10**7
    
    # We use the SAC contract to call 'approve'
    # approve(from: Address, spender: Address, amount: i128, expiration_ledger: u32)
    current_ledger = server.get_latest_ledger().sequence
    expiration = current_ledger + 100000 
    
    builder = (
        TransactionBuilder(source_acc, network_passphrase=passphrase, base_fee=100000)
        .append_invoke_contract_function_op(
            contract_id=shx_sac,
            function_name="approve",
            parameters=[
                scval.to_address(kp.public_key),
                scval.to_address(contract_id),
                scval.to_int128(amount_stroops),
                scval.to_uint32(expiration)
            ]
        )
        .set_timeout(30)
    )
    
    # Simulate for footprint
    print("Simulating...")
    sim = server.simulate_transaction(builder.build())
    print(f"DEBUG: Raw simulation response: {sim}")
    
    # Check for errors in the response
    if hasattr(sim, 'error'):
        print(f"CRITICAL: Simulation Error: {sim.error}")
        return
        
    # The SDK usually has soroban_data or it might be in results
    soroban_data = getattr(sim, 'soroban_data', getattr(sim, 'transaction_data', None))
    if not soroban_data:
        print("CRITICAL: No soroban_data or transaction_data found!")
        return
        
    builder.set_soroban_data(soroban_data)
    builder.set_soroban_resource_fee(sim.min_resource_fee + 20000)
    
    tx = builder.build()
    tx.sign(kp)
    print("Submitting approval...")
    res = server.send_transaction(tx)
    print(f"Initial Status: {res.status}")
    tx_hash = res.hash
    
    print(f"Polling for {tx_hash}...")
    for i in range(30):
        await asyncio.sleep(2)
        try:
            status_res = server.get_transaction(tx_hash)
            print(f"Attempt {i+1} Status: {status_res.status}")
            if status_res.status == stellar.GetTransactionStatus.SUCCESS:
                print("APPROVAL SUCCESSFUL!")
                break
            elif status_res.status == stellar.GetTransactionStatus.FAILED:
                print(f"APPROVAL FAILED: {status_res.error}")
                break
        except Exception as e:
            print(f"Polling error: {e}")
    
    await stellar.close_session()

if __name__ == "__main__":
    asyncio.run(setup_allowance())
