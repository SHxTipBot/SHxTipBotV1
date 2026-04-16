import asyncio
import os
from dotenv import load_dotenv
from stellar_sdk import Keypair, Asset, Network, TransactionBuilder, scval, SorobanServer, StrKey
from stellar_sdk.soroban_rpc import GetTransactionStatus, SendTransactionStatus
from stellar_sdk.server import Server

load_dotenv()

HOUSE_SRC = os.getenv("HOUSE_ACCOUNT_SECRET")
HOUSE_KP = Keypair.from_secret(HOUSE_SRC)
HORIZON_URL = os.getenv("HORIZON_URL", "https://horizon.stellar.org")
SOROBAN_URL = os.getenv("SOROBAN_RPC_URL", "https://mainnet.sorobanrpc.com")
NETWORK_PASSPHRASE = Network.PUBLIC_NETWORK_PASSPHRASE
SHX_SAC = os.getenv("SHX_SAC_CONTRACT_ID")

async def deploy():
    soroban = SorobanServer(SOROBAN_URL)
    horizon = Server(HORIZON_URL)
    
    # 1. Install the WASM (Already done, we have the hash)
    # The output previously said: Hash: ccbade3fd924c5502188092526aa38be4ae517cd5f7d390f4cb793b7fdb5dc80
    wasm_hash = "ccbade3fd924c5502188092526aa38be4ae517cd5f7d390f4cb793b7fdb5dc80"
    print(f"Using WASM Hash: {wasm_hash}")
    
    # 2. Deploy Contract
    # 2. Deploy Contract (SKIPPED - Already Deployed)
    new_contract_id = os.getenv("SOROBAN_CONTRACT_ID")
    print(f"Using ALREADY DEPLOYED CONTRACT ID: {new_contract_id}")
         
    # 3. Initialize Contract
    print(f"Skipping init for {new_contract_id}...")
        
    # 4. Set Admin Pubkey
    print("Setting admin pubkey...")
    house_acc = horizon.load_account(HOUSE_KP.public_key)
    builder = TransactionBuilder(house_acc, NETWORK_PASSPHRASE, base_fee=100000)
    
    from stellar_sdk.strkey import StrKey
    ed25519_bytes = StrKey.decode_ed25519_public_key(HOUSE_KP.public_key)
    builder.append_invoke_contract_function_op(
        contract_id=new_contract_id,
        function_name="set_admin_pubkey",
        parameters=[
            scval.to_bytes(ed25519_bytes)
        ]
    )
    tx = builder.build()
    sim = soroban.simulate_transaction(tx)
    if sim.error:
         print("AdminPubkey sim err:", sim.error)
         return
    tx = soroban.prepare_transaction(tx, sim)
    tx.sign(HOUSE_KP)
    
    resp = soroban.send_transaction(tx)
    tx_hash = resp.hash
    for _ in range(60):
         res = soroban.get_transaction(tx_hash)
         if res.status == GetTransactionStatus.SUCCESS:
              print("Admin pubkey set!")
              break
         elif res.status == GetTransactionStatus.FAILED:
              print("AdminPubkey failed.")
              return
         await asyncio.sleep(2)
         
    # 5. Approve House Account
    print("Approving House Account to allow Contract to spend SHX...")
    house_acc = horizon.load_account(HOUSE_KP.public_key)
    builder = TransactionBuilder(house_acc, NETWORK_PASSPHRASE, base_fee=100000)
    current_ledger = horizon.root().call()["core_latest_ledger"]
    
    # max i128
    amount_stroops = (100_000_000 * 10_000_000) # 100M SHX
    builder.append_invoke_contract_function_op(
        contract_id=SHX_SAC,
        function_name="approve",
        parameters=[
            scval.to_address(HOUSE_KP.public_key), # original token holder
            scval.to_address(new_contract_id),     # the spender contract
            scval.to_int128(amount_stroops),
            scval.to_uint32(current_ledger + 500_000) # 30d+
        ]
    )
    tx = builder.build()
    sim = soroban.simulate_transaction(tx)
    if sim.error:
         print("Approve sim err:", sim.error)
         return
    tx = soroban.prepare_transaction(tx, sim)
    tx.sign(HOUSE_KP)
    
    resp = soroban.send_transaction(tx)
    tx_hash = resp.hash
    for _ in range(40):
         res = soroban.get_transaction(tx_hash)
         if res.status == GetTransactionStatus.SUCCESS:
              print(f"Approved successfully! Your new SOROBAN_CONTRACT_ID is: {new_contract_id}")
              return
         elif res.status == GetTransactionStatus.FAILED:
              print("Approve failed.")
              return
         await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(deploy())
