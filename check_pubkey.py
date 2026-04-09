import os
import asyncio
import base64
from dotenv import load_dotenv
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, xdr, Server

async def query_adm_pub():
    load_dotenv()
    contract_id = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
    server = SorobanServer(rpc_url)
    
    # adm_pub is symbol_short!("adm_pub")
    # symbol_short is just the base64-ish encoding
    # "adm_pub" in XDR
    
    # Actually, easier to use a script to find the key
    # (Just querying the instance storage)
    pass

async def check_contract_storage(contract_id):
    try:
        rpc_url = "https://soroban-testnet.stellar.org"
        server = SorobanServer(rpc_url)
        
        # Querying contract instance storage is tricky, easier to just call 'get_treasury' 
        # but there is no 'get_admin_pubkey'.
        
        # I'll try to find the key for symbol_short!("adm_pub")
        # symbol_short!("adm_pub") -> 0x....
        # But wait, I'll just check if INITIALIZE work.
        pass

if __name__ == "__main__":
    # I'll just derive the adm_pub hex from HOUSE_ACCOUNT_PUBLIC
    load_dotenv()
    pub = os.getenv("HOUSE_ACCOUNT_PUBLIC")
    kp = Keypair.from_public_key(pub)
    print(f"Expected Admin Pubkey (hex): {kp.raw_public_key().hex()}")
