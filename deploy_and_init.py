import os
import asyncio
import logging
from dotenv import load_dotenv, set_key
from stellar_sdk import scval
import stellar_utils

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("shx_deployer")

async def run_deployment():
    load_dotenv()
    
    # 1. Configuration
    secret = os.getenv("HOUSE_ACCOUNT_SECRET")
    public = os.getenv("HOUSE_ACCOUNT_PUBLIC")
    shx_sac = os.getenv("SHX_SAC_CONTRACT_ID")
    treasury = os.getenv("HOUSE_ACCOUNT_PUBLIC") # Default treasury to house
    
    if not secret:
        logger.error("HOUSE_ACCOUNT_SECRET not found in .env")
        return

    wasm_path = "soroban_tipping_contract.wasm"
    
    if not os.path.exists(wasm_path):
        logger.error(f"WASM file not found at {wasm_path}")
        return

    logger.info("Step 1: Installing WASM on-chain...")
    try:
        wasm_id = await stellar_utils.deploy_contract_wasm(secret, wasm_path)
        logger.info(f"SUCCESS: WASM installed. ID: {wasm_id}")
    except Exception as e:
        logger.error(f"FAILED to install WASM: {e}")
        return

    logger.info("Step 2: Deploying contract instance...")
    try:
        contract_id = await stellar_utils.deploy_contract_instance(secret, wasm_id)
        logger.info(f"SUCCESS: Contract deployed. ID: {contract_id}")
    except Exception as e:
        logger.error(f"FAILED to deploy instance: {e}")
        return

    logger.info(f"Step 3: Initializing contract {contract_id[:8]}...")
    # initialize(env: Env, admin: Address, shx_contract: Address, treasury: Address)
    params = [
        scval.to_address(public),   # admin
        scval.to_address(shx_sac),  # shx_contract
        scval.to_address(treasury), # treasury
    ]
    try:
        res = await stellar_utils.invoke_contract_function(secret, contract_id, "initialize", params)
        if res["success"]:
            logger.info("SUCCESS: Contract initialized.")
        else:
            logger.error(f"FAILED to initialize: {res['error']}")
            return
    except Exception as e:
        logger.error(f"EXCEPTION during initialization: {e}")
        return

    logger.info("Step 4: Setting Bot Admin Public Key (for signature verification)...")
    # set_admin_pubkey(env: Env, admin: Address, new_pubkey: BytesN<32>)
    # Note: stellar_utils.get_house_pubkey_hex() returns the 32-byte raw pubkey
    pubkey_hex = stellar_utils.get_house_pubkey_hex()
    params = [
        scval.to_address(public),
        scval.from_xdr_bytes(bytes.fromhex(f"0000000a00000020{pubkey_hex}")), # BytesN<32>
    ]
    # Wait, scval.from_xdr_bytes is for raw XDR. Let's use scval.to_bytes instead.
    params = [
        scval.to_address(public),
        scval.to_bytes(bytes.fromhex(pubkey_hex)), # ScValBytes
    ]
    
    try:
        res = await stellar_utils.invoke_contract_function(secret, contract_id, "set_admin_pubkey", params)
        if res["success"]:
            logger.info("SUCCESS: Bot Admin Public Key set.")
        else:
            logger.error(f"FAILED to set admin pubkey: {res['error']}")
            return
    except Exception as e:
        logger.error(f"EXCEPTION during admin setup: {e}")
        return

    logger.info("Step 5: Updating .env file...")
    set_key(".env", "SOROBAN_CONTRACT_ID", contract_id)
    logger.info(f"HANDOVER COMPLETE | Contract ID: {contract_id}")
    logger.info("Don't forget to GRANT ALLOWANCE to the house account using the bot or script.")

if __name__ == "__main__":
    asyncio.run(run_deployment())
