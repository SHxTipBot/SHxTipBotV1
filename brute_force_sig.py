import os
import asyncio
import base64
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server, xdr

async def test_combination(contract_id, user_address, amount_shx, nonce, kp, server, horizon, 
                           c_addr_style, u_addr_style, amt_style, nonce_style):
    
    amount_stroops = stellar._to_stroops(amount_shx)
    
    # 1. Build Payload
    def get_xdr(val, style, type_hint=None):
        if style == 'raw':
            if type_hint == 'address':
                return scval.to_address(val).address.to_xdr_bytes()
            if type_hint == 'i128':
                return scval.to_int128(val).i128.to_xdr_bytes()
            if type_hint == 'u64':
                return scval.to_uint64(val).u64.to_xdr_bytes()
        else: # scval
            if type_hint == 'address':
                return scval.to_address(val).to_xdr_bytes()
            if type_hint == 'i128':
                return scval.to_int128(val).to_xdr_bytes()
            if type_hint == 'u64':
                return scval.to_uint64(val).to_xdr_bytes()
        return b''

    c_addr_xdr = get_xdr(contract_id, c_addr_style, 'address')
    u_addr_xdr = get_xdr(user_address, u_addr_style, 'address')
    amt_xdr = get_xdr(amount_stroops, amt_style, 'i128')
    n_xdr = get_xdr(nonce, nonce_style, 'u64')
    
    payload = c_addr_xdr + u_addr_xdr + amt_xdr + n_xdr
    
    # 2. Sign
    house_kp = Keypair.from_secret(os.getenv("HOUSE_ACCOUNT_SECRET"))
    sig_bytes = house_kp.sign(payload)
    
    # 3. Simulate
    source_acc = horizon.load_account(house_kp.public_key)
    params = [
        stellar.to_sc_address(user_address),
        scval.to_int128(amount_stroops),
        scval.to_uint64(nonce),
        scval.to_bytes(sig_bytes)
    ]
    
    builder = (
        TransactionBuilder(source_acc, network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE)
        .append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="claim_withdrawal",
            parameters=params
        )
    )
    
    sim = server.simulate_transaction(builder.build())
    
    style_str = f"C:{c_addr_style} U:{u_addr_style} A:{amt_style} N:{nonce_style}"
    if sim.error:
        print(f"[-] {style_str} | FAILED: {sim.error}")
        return False
    else:
        print(f"[+] {style_str} | SUCCESS!")
        return True

async def main():
    load_dotenv()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID")
    user_address = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"
    amount_shx = 1.0
    nonce = int(os.urandom(4).hex(), 16) # random nonce
    
    rpc_url = "https://soroban-testnet.stellar.org"
    server = SorobanServer(rpc_url)
    horizon = Server("https://horizon-testnet.stellar.org")
    
    styles = ['raw', 'scval']
    
    for c in styles:
        for u in styles:
            for a in styles:
                for n in styles:
                    # To keep it simple, assume amount and nonce always use same style
                    if a != n: continue
                    
                    await test_combination(contract_id, user_address, amount_shx, nonce, None, server, horizon, c, u, a, n)

if __name__ == "__main__":
    asyncio.run(main())
