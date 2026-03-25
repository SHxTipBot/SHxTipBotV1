import os
import asyncio
from dotenv import load_dotenv
from stellar_sdk import SorobanServer
from stellar_sdk.soroban_rpc import GetTransactionStatus

async def check_tx():
    load_dotenv()
    url = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
    tx_hash = "6710b777413661eb7eaef954ad8ae24869278972e92c28de552787864f1dc0b0"
    
    print(f"Checking {tx_hash} on {url}...")
    server = SorobanServer(url)
    try:
        res = server.get_transaction(tx_hash)
        print(f"Status: {res.status}")
        if hasattr(res, 'error'):
            print(f"Error: {res.error}")
        if hasattr(res, 'result_xdr'):
            print(f"Result XDR: {res.result_xdr}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(check_tx())
