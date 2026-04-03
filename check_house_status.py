import asyncio
import os
from dotenv import load_dotenv
import stellar_utils as stellar

async def check():
    load_dotenv()
    house_pub = os.getenv("HOUSE_ACCOUNT_PUBLIC")
    contract_id = os.getenv("SOROBAN_CONTRACT_ID")
    
    print(f"--- House Account Check ---")
    print(f"Public Key: {house_pub}")
    
    balance = await stellar.get_shx_balance(house_pub)
    print(f"SHx Balance: {balance}")
    
    allowance = await stellar.check_shx_allowance(house_pub, contract_id)
    print(f"Allowance for {contract_id}: {allowance}")
    
    await stellar.close_session()

if __name__ == "__main__":
    asyncio.run(check())
