import os
import asyncio
import logging
from dotenv import load_dotenv
from stellar_sdk import scval
import stellar_utils

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("py_deployer")

async def deploy():
    load_dotenv()
    
    secret = os.getenv("HOUSE_ACCOUNT_SECRET")
    wasm_path = "soroban_tipping_contract/target/wasm32-unknown-unknown/release/shx_tipping_contract.wasm"
    
    logger.info("Installing WASM...")
    wasm_id = await stellar_utils.deploy_contract_wasm(secret, wasm_path)
    logger.info(f"WASM ID: {wasm_id}")
    
    logger.info("Deploying instance...")
    # This calls the SDK natively, so no terminal truncation!
    contract_id = await stellar_utils.deploy_contract_instance(secret, wasm_id)
    print(f"FULL_CONTRACT_ID:{contract_id}")
    
    with open("full_id.txt", "w") as f:
        f.write(contract_id)

if __name__ == "__main__":
    asyncio.run(deploy())
