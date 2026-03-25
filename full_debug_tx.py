import os
import asyncio
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network

async def full_debug():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    shx_sac = os.getenv("SHX_SAC_CONTRACT_ID", "").strip()
    network_type = os.getenv("STELLAR_NETWORK", "testnet").strip()
    target = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"
    
    passphrase = Network.TESTNET_NETWORK_PASSPHRASE if network_type == "testnet" else Network.PUBLIC_NETWORK_PASSPHRASE
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
    horizon_url = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip()
    
    kp = Keypair.from_secret(secret)
    server = SorobanServer(rpc_url)
    horizon = stellar.Server(horizon_url)
    
    print(f"--- DEBUG START ---")
    print(f"Network: {network_type} ({passphrase})")
    print(f"SAC ID: {shx_sac}")
    print(f"Tipping Contract: {contract_id}")
    print(f"House Account: {kp.public_key}")
    
    # 1. Check SHX Balance
    print("\n[1] Checking SHX Balance...")
    balance = await stellar.get_shx_balance(kp.public_key)
    print(f"House Balance: {balance} SHX")
    
    # 2. Grant Allowance (Confirming Success)
    print("\n[2] Granting Allowance...")
    source_acc = horizon.load_account(kp.public_key)
    current_ledger = server.get_latest_ledger().sequence
    expiration = current_ledger + 50000 
    
    builder = (
        TransactionBuilder(source_acc, network_passphrase=passphrase, base_fee=100_000)
        .append_invoke_contract_function_op(
            contract_id=shx_sac,
            function_name="approve",
            parameters=[
                scval.to_address(kp.public_key),
                scval.to_address(contract_id),
                scval.to_int128(100_000_000 * 10**7), # 100M SHX
                scval.to_uint32(expiration)
            ]
        )
        .set_timeout(60)
    )
    
    sim = server.simulate_transaction(builder.build())
    if sim.error:
        print(f"Approve Simulation Error: {sim.error}")
        return
        
    builder.set_soroban_data(sim.transaction_data)
    builder.set_soroban_resource_fee(sim.min_resource_fee + 50_000)
    tx = builder.build()
    tx.sign(kp)
    
    send_res = server.send_transaction(tx)
    print(f"Approve Submitted: {send_res.hash}")
    
    for _ in range(30):
        await asyncio.sleep(2)
        res = server.get_transaction(send_res.hash)
        if res.status == stellar.GetTransactionStatus.SUCCESS:
            print("Approve CONFIRMED!")
            break
        elif res.status == stellar.GetTransactionStatus.FAILED:
            print(f"Approve FAILED: {res.error}")
            return
            
    # 3. Execute Tip
    print(f"\n[3] Executing Tip for 1 SHX to {target}...")
    result = await stellar.execute_tip(
        kp.public_key,
        target,
        1.0,
        0.0
    )
    
    if result["success"]:
        print(f"TIP SUCCESS! Hash: {result['tx_hash']}")
        print(f"Link: {result['tx_url']}")
    else:
        print(f"TIP FAILED: {result['error']}")

    await stellar.close_session()

if __name__ == "__main__":
    asyncio.run(full_debug())
