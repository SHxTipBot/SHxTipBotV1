import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure the root directory is in sys.path so we can import stellar_utils
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.insert(0, root_dir)

# Load environment variables explicitly from the root .env
load_dotenv(os.path.join(root_dir, '.env'))

import stellar_utils as stellar
from stellar_sdk import scval, xdr as stellar_xdr

async def main():
    load_dotenv()
    print(f"Contract: {stellar.SOROBAN_CONTRACT_ID}")
    
    # Check version
    res = await stellar._invoke_sac_read_only(stellar.SOROBAN_CONTRACT_ID, "get_version", [])
    if res:
        val = stellar_xdr.SCVal.from_xdr(res)
        print(f"Version: {val.u32}")
    else:
        print("Failed to get version (simulation error or uninitialized)")

    # Check Treasury
    res = await stellar._invoke_sac_read_only(stellar.SOROBAN_CONTRACT_ID, "get_treasury", [])
    if res:
        val = stellar_xdr.SCVal.from_xdr(res)
        print(f"Treasury: {val.address.account_id}")

    await stellar.close_session()

if __name__ == "__main__":
    asyncio.run(main())
