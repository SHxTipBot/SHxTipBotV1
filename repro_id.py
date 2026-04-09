import asyncio
import os
from stellar_sdk import SorobanServer, TransactionBuilder, Network, Keypair, Server, xdr, StrKey
from dotenv import load_dotenv

load_dotenv()
secret = os.getenv("HOUSE_ACCOUNT_SECRET")
kp = Keypair.from_secret(secret)
server = SorobanServer(os.getenv("SOROBAN_RPC_URL"))
horizon = Server(os.getenv("HORIZON_URL"))

async def repro():
    wasm_id = "b7a7ebb74f03a879aa2c43ef9ec3e7e720bae1601bf9868f44e5bd55e1a912f8" # From logs
    account = horizon.load_account(kp.public_key)
    
    builder = TransactionBuilder(account, Network.TESTNET_NETWORK_PASSPHRASE).append_create_contract_op(
        wasm_id=wasm_id,
        address=kp.public_key,
        salt=os.urandom(32)
    )
    tx = builder.build()
    sim = server.simulate_transaction(tx)
    
    if sim.error:
        print(f"Simulation Error: {sim.error}")
        return

    res_xdr = sim.results[0].xdr
    print(f"Result XDR: {res_xdr}")
    scval_obj = xdr.SCVal.from_xdr(res_xdr)
    print(f"SCVal Type: {scval_obj.type}")
    print(f"Address Type: {scval_obj.address.type}")
    
    if scval_obj.address.contract_id:
        c_id = scval_obj.address.contract_id
        print(f"Contract ID Object: {type(c_id)}")
        
        import base64
        res_bytes = base64.b64decode(res_xdr)
        sl_id_bytes = res_bytes[-32:]
        sl_id = StrKey.encode_contract(sl_id_bytes)
        print(f"SLICED ID: {sl_id}")
        
        # Also try to investigate Hash object
        h_obj = c_id.contract_id
        print(f"Hash Object Type: {type(h_obj)}")
        print(f"Hash Object Dir: {dir(h_obj)}")
        if hasattr(h_obj, 'hash'):
            print(f"H_OBJ.hash is valid bytes: {isinstance(h_obj.hash, bytes)}")
        
        try:
             print(f"BYTES(H_OBJ): {bytes(h_obj).hex()}")
        except Exception as be:
             print(f"BYTES(H_OBJ) failed: {be}")

asyncio.run(repro())
