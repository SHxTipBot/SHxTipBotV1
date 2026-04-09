"""
Definitive diagnostic for the withdrawal signature failure.
Tests EVERY layer independently to find the exact mismatch.
"""
import asyncio
import os
import base64
import struct
from dotenv import load_dotenv
load_dotenv()

from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, xdr, Network, Server, StrKey

async def main():
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    pubkey = os.getenv("HOUSE_ACCOUNT_PUBLIC", "").strip()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    
    kp = Keypair.from_secret(secret)
    
    print("=" * 60)
    print("LAYER 1: Key Pair Consistency")
    print("=" * 60)
    print(f"  HOUSE_ACCOUNT_SECRET derives pubkey: {kp.public_key}")
    print(f"  HOUSE_ACCOUNT_PUBLIC from .env:      {pubkey}")
    print(f"  MATCH: {kp.public_key == pubkey}")
    print(f"  Raw pubkey (hex): {kp.raw_public_key().hex()}")
    print()
    
    print("=" * 60)
    print("LAYER 2: Local Sign + Verify")
    print("=" * 60)
    test_message = b"hello world"
    sig = kp.sign(test_message)
    try:
        kp.verify(test_message, sig)
        print("  Local sign/verify: PASS")
    except Exception as e:
        print(f"  Local sign/verify: FAIL - {e}")
    print()
    
    print("=" * 60)
    print("LAYER 3: Contract Admin Pubkey Check")  
    print("=" * 60)
    # Read the contract instance storage to find adm_pub
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://mainnet.sorobanrpc.com")
    server = SorobanServer(rpc_url)
    
    # Build the correct ledger key for contract instance
    contract_bytes = StrKey.decode_contract(contract_id)
    sc_address = xdr.SCAddress(
        type=xdr.SCAddressType.SC_ADDRESS_TYPE_CONTRACT,
        contract_id=xdr.Hash(contract_bytes)
    )
    
    ledger_key = xdr.LedgerKey(
        type=xdr.LedgerEntryType.CONTRACT_DATA,
        contract_data=xdr.LedgerKeyContractData(
            contract=sc_address,
            key=xdr.SCVal(type=xdr.SCValType.SCV_LEDGER_KEY_CONTRACT_INSTANCE),
            durability=xdr.ContractDataDurability.PERSISTENT
        )
    )
    
    try:
        resp = server.get_ledger_entries([ledger_key])
        if resp.entries:
            data = xdr.LedgerEntryData.from_xdr(resp.entries[0].xdr)
            instance = data.contract_data.val.instance
            
            found_adm_pub = False
            if instance.storage:
                # SCMap resilience: check various ways to get entries
                entries = []
                if hasattr(instance.storage, "sc_map"):
                    entries = instance.storage.sc_map
                elif hasattr(instance.storage, "map"):
                    entries = instance.storage.map
                elif isinstance(instance.storage, list):
                    entries = instance.storage
                else:
                    # Final fallback for some SDK versions
                    try:
                        entries = list(instance.storage)
                    except:
                        print(f"  WARNING: Could not iterate storage directly. Type: {type(instance.storage)}")
                
                for entry in entries:
                    key_str = ""
                    if entry.key.type == xdr.SCValType.SCV_SYMBOL:
                        key_str = entry.key.sym.sc_symbol.decode()
                    
                    if key_str == "adm_pub":
                        found_adm_pub = True
                        # Extract the 32-byte key
                        val = entry.val
                        if val.type == xdr.SCValType.SCV_BYTES:
                            stored_key_hex = val.bytes.sc_bytes.hex()
                        else:
                            # Try raw bytes fallback
                            stored_key_hex = val.to_xdr().hex()
                        
                        expected_hex = kp.raw_public_key().hex()
                        print(f"  Stored adm_pub:  {stored_key_hex}")
                        print(f"  Expected pubkey: {expected_hex}")
                        print(f"  MATCH: {stored_key_hex == expected_hex}")
                        
                        if stored_key_hex != expected_hex:
                            print()
                            print("  !!! ROOT CAUSE FOUND !!!")
                            print("  The admin pubkey in the contract does NOT match")
                            print("  the HOUSE_ACCOUNT_SECRET signing key!")
                            print("  Fix: re-run setup_contract_pubkey.py")
                        break
                    
                # Also print ALL keys for debugging
                print()
                print("  All instance storage keys:")
                for entry in entries:
                    key_str = "?"
                    if entry.key.type == xdr.SCValType.SCV_SYMBOL:
                        key_str = entry.key.sym.sc_symbol.decode()
                    elif entry.key.type == xdr.SCValType.SCV_U32:
                        key_str = f"U32({entry.key.u32.uint32})"
                    else:
                        key_str = f"{entry.key.type}"
                    print(f"    - {key_str} (val type: {entry.val.type})")
                    
                # Also print ALL keys for debugging
                print()
                print("  All instance storage keys:")
                for entry in entries:
                    key_str = "?"
                    if entry.key.type == xdr.SCValType.SCV_SYMBOL:
                        key_str = entry.key.sym.sc_symbol.decode()
                    elif entry.key.type == xdr.SCValType.SCV_U32:
                        key_str = f"U32({entry.key.u32.uint32})"
                    else:
                        key_str = f"{entry.key.type}"
                    print(f"    - {key_str} (val type: {entry.val.type})")
            
            if not found_adm_pub:
                print("  !!! adm_pub NOT FOUND in contract storage !!!")
                print("  The set_admin_pubkey function was never called successfully.")
                print("  Fix: run setup_contract_pubkey.py")
        else:
            print("  ERROR: No contract data found. Is the contract ID correct?")
    except Exception as e:
        print(f"  ERROR reading contract storage: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("LAYER 4: Payload Encoding Comparison")
    print("=" * 60)
    
    # Show what Python produces for each encoding style  
    amount_stroops = 20_000_000  # 2 SHx
    nonce = 12345
    user_addr = pubkey
    
    # Style A: Full ScVal XDR (includes type discriminant)
    c_a = scval.to_address(contract_id).to_xdr_bytes()
    u_a = scval.to_address(user_addr).to_xdr_bytes()
    a_a = scval.to_int128(amount_stroops).to_xdr_bytes()
    n_a = scval.to_uint64(nonce).to_xdr_bytes()
    
    # Style B: Inner type only (no ScVal wrapper)
    c_b = scval.to_address(contract_id).address.to_xdr_bytes()
    u_b = scval.to_address(user_addr).address.to_xdr_bytes()
    a_b = scval.to_int128(amount_stroops).i128.to_xdr_bytes()
    n_b = scval.to_uint64(nonce).u64.to_xdr_bytes()
    
    print(f"  Style A (full ScVal):")
    print(f"    Contract addr: {len(c_a)} bytes -> {c_a.hex()}")
    print(f"    User addr:     {len(u_a)} bytes -> {u_a.hex()}")
    print(f"    Amount:        {len(a_a)} bytes -> {a_a.hex()}")
    print(f"    Nonce:         {len(n_a)} bytes -> {n_a.hex()}")
    print(f"    Total payload: {len(c_a+u_a+a_a+n_a)} bytes")
    print()
    print(f"  Style B (inner type, no wrapper):")
    print(f"    Contract addr: {len(c_b)} bytes -> {c_b.hex()}")
    print(f"    User addr:     {len(u_b)} bytes -> {u_b.hex()}")
    print(f"    Amount:        {len(a_b)} bytes -> {a_b.hex()}")
    print(f"    Nonce:         {len(n_b)} bytes -> {n_b.hex()}")
    print(f"    Total payload: {len(c_b+u_b+a_b+n_b)} bytes")
    
    print()
    print("=" * 60)
    print("LAYER 5: Live Contract Simulation (both styles)")
    print("=" * 60)
    
    horizon_url = os.getenv("HORIZON_URL", "https://horizon.stellar.org")
    horizon = Server(horizon_url)
    network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
    
    source_acc = horizon.load_account(kp.public_key)
    nonce_live = 777888999111  # unique nonce for test
    
    for style_name, style_payload_fn in [
        ("ScVal", lambda: scval.to_address(contract_id).to_xdr_bytes() + scval.to_address(user_addr).to_xdr_bytes() + scval.to_int128(amount_stroops).to_xdr_bytes() + scval.to_uint64(nonce_live).to_xdr_bytes()),
        ("Raw",   lambda: scval.to_address(contract_id).address.to_xdr_bytes() + scval.to_address(user_addr).address.to_xdr_bytes() + scval.to_int128(amount_stroops).i128.to_xdr_bytes() + scval.to_uint64(nonce_live).u64.to_xdr_bytes()),
    ]:
        payload = style_payload_fn()
        sig_bytes = kp.sign(payload)
        
        params = [
            scval.to_address(user_addr),
            scval.to_int128(amount_stroops),
            scval.to_uint64(nonce_live),
            scval.to_bytes(sig_bytes),
        ]
        
        builder = TransactionBuilder(
            source_acc, network_passphrase=network_passphrase, base_fee=100_000
        ).append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="claim_withdrawal",
            parameters=params,
        ).set_timeout(30)
        
        tx = builder.build()
        sim = server.simulate_transaction(tx)
        
        has_sig_error = False
        if sim.events:
            for ev in sim.events:
                decoded = base64.b64decode(ev)
                if b"failed ED25519" in decoded:
                    has_sig_error = True
                    break
        
        if sim.error and has_sig_error:
            print(f"  {style_name}: SIGNATURE REJECTED")
        elif sim.error:
            err_str = str(sim.error)[:100]
            print(f"  {style_name}: PASSED SIGNATURE! (Failed later: {err_str})")
        else:
            print(f"  {style_name}: FULLY SUCCEEDED!")
    
    print()
    print("=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
