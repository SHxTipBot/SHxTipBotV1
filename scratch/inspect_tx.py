import asyncio
import os
import requests
from dotenv import load_dotenv
from stellar_sdk import xdr, StrKey

load_dotenv()

def get_tx_info(tx_hash):
    try:
        url = f"https://horizon.stellar.org/transactions/{tx_hash}"
        r = requests.get(url)
        if r.status_code != 200:
            return None
        
        data = r.json()
        print(f"Hash: {tx_hash} | Ledger: {data['ledger']} | Success: {data['successful']}")
        
        # We can also check the operations to see if it's an InvokeHostFunction
        url_ops = f"https://horizon.stellar.org/transactions/{tx_hash}/operations"
        r_ops = requests.get(url_ops)
        ops = r_ops.json()['_embedded']['records']
        for op in ops:
            print(f"  Op Type: {op['type']}")
            
        return True
    except Exception as e:
        print(f"Error checking {tx_hash}: {e}")
        return False

if __name__ == "__main__":
    hashes = [
        'dbe8cad9a5767a3b552efe6a5de8fd371bbdb3bdb96b3f9f48081ae9a8b51e4d',
        'f3c1e9e68034628615e30701d309affcc0433845499daa3ab8d350d9014062f8',
        '72396dc2821788795ec45a32d26306ca4b89e275283c34aa6ac4b6598b5de890'
    ]
    for h in hashes:
        get_tx_info(h)
