import asyncio
import os
from dotenv import load_dotenv
import stellar_utils as stellar
from stellar_sdk import scval, xdr as stellar_xdr

load_dotenv()

async def check_contract():
    print(f"Contract ID: {stellar.SOROBAN_CONTRACT_ID}")
    
    # Check admin_pubkey (adm_pub symbol)
    # symbol_short!("adm_pub")
    try:
        # In Soroban SDK, symbol_short!("adm_pub") is the key.
        # We need to find the XDR for this symbol.
        # symbol_short only supports up to 9 chars.
        symbol_xdr = scval.to_symbol("adm_pub").to_xdr_bytes().hex()
        print(f"Symbol 'adm_pub' XDR: {symbol_xdr}")
        
        # Read the instance storage for this key? 
        # Actually, let's just use the simulate_transaction to call a getter if one exists.
        # There is no set_admin_pubkey getter in lib.rs.
        
        # We can try to read the Ledger Entry directly if we know the key XDR.
        # But easier to just trust the setup or provide a script to re-set it.
        
        house_pub = stellar.HOUSE_ACCOUNT_PUBLIC
        print(f"House Public Key: {house_pub}")
        print(f"House Pubkey Hex (for contract): {stellar.get_house_pubkey_hex()}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_contract())
