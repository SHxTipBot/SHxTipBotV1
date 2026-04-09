import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from stellar_utils import check_shx_allowance, HOUSE_ACCOUNT_PUBLIC, SOROBAN_CONTRACT_ID

async def main():
    print(f"House Account: {HOUSE_ACCOUNT_PUBLIC}")
    print(f"Tipping Contract: {SOROBAN_CONTRACT_ID}")
    
    allowance = await check_shx_allowance(HOUSE_ACCOUNT_PUBLIC, SOROBAN_CONTRACT_ID)
    print(f"Current Allowance: {allowance} SHx")

if __name__ == "__main__":
    asyncio.run(main())
