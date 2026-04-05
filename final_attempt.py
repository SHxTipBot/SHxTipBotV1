import os
import asyncio
import requests
import time
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server
from stellar_sdk.soroban_rpc import SendTransactionStatus

async def brute_force_allowance():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    shx_sac = os.getenv("SHX_SAC_CONTRACT_ID", "").strip()
    
    kp = Keypair.from_secret(secret)
    horizon_url = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip()
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
    server = SorobanServer(rpc_url)
    horizon = Server(horizon_url)
    passphrase = Network.TESTNET_NETWORK_PASSPHRASE if os.getenv("STELLAR_NETWORK") == "testnet" else Network.PUBLIC_NETWORK_PASSPHRASE

    print(f"Brute-forcing allowance for {kp.public_key}...")
    
    # Get base sequence directly from Horizon
    resp = requests.get(f"{horizon_url}/accounts/{kp.public_key}")
    base_seq = int(resp.json()["sequence"])
    print(f"Base Sequence from Horizon: {base_seq}")

    for offset in range(0, 10):
        target_seq = base_seq + offset
        print(f"\n--- Attempt with Sequence {target_seq} (offset {offset}) ---")
        
        source_acc = horizon.load_account(kp.public_key)
        source_acc.sequence = target_seq
        
        amount_stroops = 1_000_000 * 10**7
        current_ledger = server.get_latest_ledger().sequence
        expiration = current_ledger + 500000 
        
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
            .set_timeout(60)
        )
        
        sim = server.simulate_transaction(builder.build())
        if sim.error:
            print(f"Simulation Error: {sim.error}")
            continue
            
        tx = builder.build()
        tx = server.prepare_transaction(tx, sim)
        tx.sign(kp)
        
        res = server.send_transaction(tx)
        print(f"Initial Status: {res.status}")
        
        if res.status == SendTransactionStatus.ERROR:
            print(f"Error Result XDR: {res.error_result_xdr}")
            # Identify bad sequence
            if "AAAAAAAAik3" in res.error_result_xdr:
                print("TX_BAD_SEQ detected. Moving to next sequence...")
                continue
            else:
                print("Other error detected. Skipping attempt.")
                continue
        
        # If pending, wait for confirmation
        tx_hash = res.hash
        print(f"Polling for {tx_hash}...")
        for i in range(10):
            await asyncio.sleep(2)
            try:
                st = server.get_transaction(tx_hash)
                print(f"Poll {i+1} Status: {st.status}")
                if st.status == "success":
                    print("SUCCESSFULLY GRANTED ALLOWANCE!")
                    return
                elif st.status == "failed":
                    print(f"FAILED: {st.result_xdr}")
                    break
            except:
                pass
        
    print("Brute-force failed.")

if __name__ == "__main__":
    asyncio.run(brute_force_allowance())
