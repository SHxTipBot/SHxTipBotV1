import asyncio
import os
import base64
from dotenv import load_dotenv

load_dotenv()

import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server

async def sweep():
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    kp = Keypair.from_secret(secret)
    
    # Needs a real user with a trustline? Not needed for signature validation, only for transfer. 
    # Actually, if signature validation fails, it traps early. If it succeeds, it might fail later for insufficient balance.
    # We just want to get PAST the signature validation!
    user_address = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"
    amount_shx = 2.0
    amount_stroops = stellar._to_stroops(amount_shx)
    nonce = 999988887777 # unique nonce
    
    rpc_url = "https://mainnet.sorobanrpc.com"
    server = SorobanServer(rpc_url)
    horizon = Server("https://horizon.stellar.org")
    source_acc = horizon.load_account(kp.public_key)
    
    print(f"Contract: {contract_id}")

    # Generate all possible payloads
    # 1. ScVal format
    payloads = []
    
    c_scval = scval.to_address(contract_id).to_xdr_bytes()
    u_scval = scval.to_address(user_address).to_xdr_bytes()
    a_scval = scval.to_int128(amount_stroops).to_xdr_bytes()
    n_scval = scval.to_uint64(nonce).to_xdr_bytes()
    
    c_raw = scval.to_address(contract_id).address.to_xdr_bytes()
    u_raw = scval.to_address(user_address).address.to_xdr_bytes()
    a_raw = scval.to_int128(amount_stroops).i128.to_xdr_bytes()
    n_raw = scval.to_uint64(nonce).u64.to_xdr_bytes()
    
    # Try fully raw
    payloads.append(("ALL_RAW", c_raw + u_raw + a_raw + n_raw))
    # Try fully ScVal
    payloads.append(("ALL_SCVAL", c_scval + u_scval + a_scval + n_scval))
    # Try raw address, ScVal for ints?
    payloads.append(("RAW_ADDR_SCVAL_INTS", c_raw + u_raw + a_scval + n_scval))
    payloads.append(("SCVAL_ADDR_RAW_INTS", c_scval + u_scval + a_raw + n_raw))

    for name, data in payloads:
        signature_bytes = kp.sign(data)
        
        params = [
            stellar.to_sc_address(user_address),
            scval.to_int128(amount_stroops),
            scval.to_uint64(nonce),
            scval.to_bytes(signature_bytes)
        ]
        
        builder = (
            TransactionBuilder(source_acc, network_passphrase=Network.PUBLIC_NETWORK_PASSPHRASE)
            .append_invoke_contract_function_op(
                contract_id=contract_id,
                function_name="claim_withdrawal",
                parameters=params
            )
        )
        sim = server.simulate_transaction(builder.build())
        events_str = str(sim.events) if sim.events else ""
        error_str = sim.error if sim.error else ""
        
        if "failed ED25519 verification" in events_str or "InvalidInput" in events_str:
            print(f"{name}: FAILED (Signature rejected)")
        elif error_str == "" and "withdraw" in events_str:
            print(f"{name}: SUCCESS! Completely valid!")
        else:
            print(f"{name}: PASSED SIG! Failed later: {error_str} / Events: {events_str}")

if __name__ == "__main__":
    asyncio.run(sweep())
