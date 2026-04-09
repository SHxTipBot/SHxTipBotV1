import asyncio
import os
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network

async def mainnet_approve():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    shx_sac = os.getenv("SHX_SAC_CONTRACT_ID", "").strip()
    
    kp = Keypair.from_secret(secret)
    server = SorobanServer("https://mainnet.sorobanrpc.com")
    horizon = stellar.Server("https://horizon.stellar.org")
    
    print(f"Approving {contract_id} on SAC {shx_sac} for {kp.public_key}...")
    
    source_acc = horizon.load_account(kp.public_key)
    amount_stroops = 1_000_000 * 10**7
    
    current_ledger = server.get_latest_ledger().sequence
    expiration = current_ledger + 500_000
    
    builder = (
        TransactionBuilder(source_acc, network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE, base_fee=200000)
        .append_invoke_contract_function_op(
            contract_id=shx_sac,
            function_name="approve",
            parameters=[
                stellar.to_sc_address(kp.public_key),
                stellar.to_sc_address(contract_id),
                scval.to_int128(amount_stroops),
                scval.to_uint32(expiration)
            ]
        )
        .set_timeout(300)
    )
    
    tx = builder.build()
    sim = server.simulate_transaction(tx)
    if sim.error:
        print(f"Sim error: {sim.error}")
        return
        
    tx = server.prepare_transaction(tx, sim)
    tx.sign(kp)
    
    res = server.send_transaction(tx)
    print(f"Sent: {res.status} | Hash: {res.hash}")
    
    if res.status != "PENDING" and res.status != "SUCCESS":
        print(f"Error: {res.__dict__}")
        return
        
    for _ in range(60):
        status_res = server.get_transaction(res.hash)
        print(f"Status: {status_res.status}")
        if status_res.status == stellar.GetTransactionStatus.SUCCESS:
            print("SUCCESS!")
            return
        elif status_res.status == stellar.GetTransactionStatus.FAILED:
            print(f"FAILED: {status_res.result_xdr}")
            return
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(mainnet_approve())
