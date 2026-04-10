import os
import asyncio
import logging
from dotenv import load_dotenv, set_key
from stellar_sdk import scval
import stellar_utils

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("nuclear_deploy")

async def deploy():
    load_dotenv()
    
    secret = os.getenv("HOUSE_ACCOUNT_SECRET")
    public = os.getenv("HOUSE_ACCOUNT_PUBLIC")
    shx_sac = os.getenv("SHX_SAC_CONTRACT_ID")
    
    wasm_path = "soroban_tipping_contract.wasm"
    
    logger.info("Installing new WASM...")
    wasm_id = await stellar_utils.deploy_contract_wasm(secret, wasm_path)
    logger.info(f"WASM ID: {wasm_id}")
    
    logger.info("Deploying instance...")
    contract_id = await stellar_utils.deploy_contract_instance(secret, wasm_id)
    logger.info(f"CONTRACT ID: {contract_id}")
    
    logger.info("Initializing...")
    params = [
        scval.to_address(public),   # admin
        scval.to_address(shx_sac),  # shx_contract
        scval.to_address(public),   # treasury
    ]
    await stellar_utils.invoke_contract_function(secret, contract_id, "initialize", params)
    
    logger.info("Setting Admin PubKey...")
    pubkey_hex = stellar_utils.get_house_pubkey_hex()
    await stellar_utils.invoke_contract_function(secret, contract_id, "set_admin_pubkey", [scval.to_bytes(bytes.fromhex(pubkey_hex))])
    
    logger.info("Updating .env...")
    # Update WITHOUT quotes
    with open(".env", "r") as f:
        lines = f.readlines()
    with open(".env", "w") as f:
        for line in lines:
            if line.startswith("SOROBAN_CONTRACT_ID="):
                f.write(f"SOROBAN_CONTRACT_ID={contract_id}\n")
            else:
                f.write(line)
                
    logger.info(f"DEPLOYMENT COMPLETE: {contract_id}")
    await stellar_utils.close_session()

if __name__ == "__main__":
    asyncio.run(deploy())
