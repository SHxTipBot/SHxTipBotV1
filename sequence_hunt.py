import os
import asyncio
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server

async def sequence_hunt():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    kp = Keypair.from_secret(secret)
    network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
    horizon_url = "https://horizon-testnet.stellar.org"
    rpc_url = "https://soroban-testnet.stellar.org"
    
    server = SorobanServer(rpc_url)
    horizon = Server(horizon_url)
    
    # Get current ledger sequence
    resp = requests.get(f"{horizon_url}/accounts/{kp.public_key}")
    ledger_seq = int(resp.json()["sequence"])
    print(f"Ledger Seq from Horizon: {ledger_seq}")

    raw_pubkey = kp.raw_public_key()

    # Try 3 around it
    for i in [0, 1, -1, 2]:
        target_seq = ledger_seq + i
        print(f"\n--- Trying Transaction Seq {target_seq} (offset {i}) ---")
        
        # Build manually
        source_acc = horizon.load_account(kp.public_key)
        # In SDK, the transaction seq will be source_acc.sequence + 1
        # So we set source_acc.sequence = target_seq - 1
        source_acc.sequence = target_seq - 1
        
        builder = (
            TransactionBuilder(source_acc, network_passphrase=network_passphrase, base_fee=250000)
            .append_invoke_contract_function_op(
                contract_id=contract_id,
                function_name="set_admin_pubkey",
                parameters=[scval.to_bytes(raw_pubkey)]
            )
            .set_timeout(300)
        )
        
        sim = server.simulate_transaction(builder.build())
        if sim.error:
            print(f"Sim Error: {sim.error}")
            continue
            
        tx = builder.build()
        tx = server.prepare_transaction(tx, sim)
        tx.sign(kp)
        
        try:
            r = horizon.submit_transaction(tx)
            print(f"SUCCESS! Hash: {r['hash']}")
            return
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    import requests
    asyncio.run(sequence_hunt())
