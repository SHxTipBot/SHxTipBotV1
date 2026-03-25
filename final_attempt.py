import os
import asyncio
import time
from dotenv import load_dotenv
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server

async def main():
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
    horizon = Server(horizon_url)
    
    print(f"Network: {network_type}")
    print(f"Contract: {contract_id}")
    
    # Check Balance
    source_acc = horizon.load_account(kp.public_key)
    
    # Step 1: APPROVE
    print("Step 1: Approving...")
    builder = (
        TransactionBuilder(source_acc, network_passphrase=passphrase, base_fee=100_000)
        .append_invoke_contract_function_op(
            contract_id=shx_sac,
            function_name="approve",
            parameters=[
                scval.to_address(kp.public_key),
                scval.to_address(contract_id),
                scval.to_int128(1_000_000 * 10**7),
                scval.to_uint32(server.get_latest_ledger().sequence + 1000)
            ]
        )
        .set_timeout(120)
    )
    tx_base = builder.build()
    sim = server.simulate_transaction(tx_base)
    if sim.error:
        print(f"Approve Sim Error: {sim.error}")
        return
    tx_approve = server.prepare_transaction(tx_base, sim)
    tx_approve.sign(kp)
    res_approve = server.send_transaction(tx_approve)
    print(f"Approve Submitted: {res_approve.hash}")
    
    # Wait for confirmation
    while True:
        await asyncio.sleep(2)
        r = server.get_transaction(res_approve.hash)
        if r.status == "SUCCESS":
            print("Approve Confirmed!")
            break
        elif r.status == "FAILED":
            print(f"Approve FAILED: {r.error}")
            return

    # 2. TIP
    print("\nStep 2: Tipping 0.1 SHX...")
    source_acc = horizon.load_account(kp.public_key)
    builder = (
        TransactionBuilder(source_acc, network_passphrase=passphrase, base_fee=100_000)
        .append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="tip",
            parameters=[
                scval.to_address(kp.public_key),
                scval.to_address(target),
                scval.to_int128(int(0.1 * 10**7)),
                scval.to_int128(0)
            ]
        )
        .set_timeout(120)
    )
    tx_base_tip = builder.build()
    sim = server.simulate_transaction(tx_base_tip)
    if sim.error:
        print(f"TIP Simulation FAILED: {sim.error}")
        return
    tx_tip = server.prepare_transaction(tx_base_tip, sim)
    tx_tip.sign(kp)
    res_tip = server.send_transaction(tx_tip)
    print(f"Tip Submitted: {res_tip.hash}")
    
    while True:
        await asyncio.sleep(2)
        r = server.get_transaction(res_tip.hash)
        if r.status == "SUCCESS":
            print(f"DONE! FINAL HASH: {res_tip.hash}")
            break
        elif r.status == "FAILED":
            print(f"Tip FAILED: {r.error}")
            break

if __name__ == "__main__":
    asyncio.run(main())
