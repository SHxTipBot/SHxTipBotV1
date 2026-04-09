import os
import asyncio
import requests
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server
from stellar_sdk.soroban_rpc import SendTransactionStatus, GetTransactionStatus

async def simple_admin_pubkey():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    
    kp = Keypair.from_secret(secret)
    network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE if os.getenv("STELLAR_NETWORK") == "testnet" else Network.PUBLIC_NETWORK_PASSPHRASE
    horizon_url = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip()
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
    server = SorobanServer(rpc_url)
    horizon = Server(horizon_url)
    
    print(f"Setting Admin Pubkey for contract {contract_id}...")
    source_acc = horizon.load_account(kp.public_key)
    print(f"Current Account Seq: {source_acc.sequence}")
    
    raw_pubkey = kp.raw_public_key()
    
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
        return
        
    tx = builder.build()
    tx = server.prepare_transaction(tx, sim)
    tx.sign(kp)
    
    res = server.send_transaction(tx)
    print(f"Status: {res.status}")
    if res.hash:
        print(f"Hash: {res.hash}")
        # Wait for confirmation
        for i in range(20):
            await asyncio.sleep(3)
            st = server.get_transaction(res.hash)
            print(f"Poll {i}: {st.status}")
            if st.status == GetTransactionStatus.SUCCESS:
                print("SUCCESS!")
                return
            if st.status == GetTransactionStatus.FAILED:
                print(f"FAILED: {st.result_xdr}")
                return
    else:
        print(f"No hash produced. Error XDR: {res.error_result_xdr}")

if __name__ == "__main__":
    asyncio.run(simple_admin_pubkey())
