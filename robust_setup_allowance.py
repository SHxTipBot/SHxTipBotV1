import os
import asyncio
import time
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server

async def robust_allowance():
    load_dotenv()
    # Adding extra 10s sleep to let testnet settle
    print("Waiting 10s for sequence to settle...")
    time.sleep(10)
    
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    shx_sac = os.getenv("SHX_SAC_CONTRACT_ID", "").strip()
    
    kp = Keypair.from_secret(secret)
    horizon = Server(os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip())
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
    server = SorobanServer(rpc_url)
    
    passphrase = Network.TESTNET_NETWORK_PASSPHRASE if os.getenv("STELLAR_NETWORK") == "testnet" else Network.PUBLIC_NETWORK_PASSPHRASE

    print(f"Granting allowance from {kp.public_key} to {contract_id}...")
    
    source_acc = horizon.load_account(kp.public_key)
    print(f"Starting Sequence: {source_acc.sequence}")
    
    # Approve a very large amount
    amount_stroops = 1_000_000 * 10**7
    current_ledger = server.get_latest_ledger().sequence
    expiration = current_ledger + 500_000 # ~1 month
    
    builder = (
        TransactionBuilder(source_acc, network_passphrase=passphrase, base_fee=250000)
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
        .set_timeout(120)
    )
    
    sim = server.simulate_transaction(builder.build())
    if sim.error:
        print(f"Simulation Error: {sim.error}")
        return
        
    tx = builder.build()
    tx = server.prepare_transaction(tx, sim)
    tx.sign(kp)
    
    print(f"Submitting transaction...")
    res = server.send_transaction(tx)
    print(f"Status: {res.status}")
    from stellar_sdk.soroban_rpc import SendTransactionStatus, GetTransactionStatus
    print(f"Status: {res.status}")
    if res.status == SendTransactionStatus.ERROR:
        print(f"ERROR_XDR: {res.error_result_xdr}")
        return
    else:
        print(f"Tx Hash: {res.hash}")
        print("Waiting for confirmation...")
        for _ in range(60):
            time.sleep(2)
            try:
                st = server.get_transaction(res.hash)
                if st.status == "success":
                    print("SUCCESSFULLY GRANTED ALLOWANCE!")
                    return
                if st.status == "failed":
                    print(f"FAILED: {st.result_xdr}")
                    return
            except:
                pass
        print("Timed out waiting for confirmation.")

if __name__ == "__main__":
    asyncio.run(robust_allowance())
