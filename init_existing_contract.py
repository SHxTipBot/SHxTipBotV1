import os
import asyncio
import logging
from dotenv import load_dotenv, set_key
from stellar_sdk import scval
import stellar_utils

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("shx_initializer")

async def run_init():
    load_dotenv()
    
    # 1. Configuration - USE THE NEW CONTRACT ID
    contract_id = "CCQWDN7ISJLGDR6BCTXCUKZNWHZ2XG7PS2TFGBK75QJ2F2X7F4KLPNMX"
    
    secret = os.getenv("HOUSE_ACCOUNT_SECRET")
    public = os.getenv("HOUSE_ACCOUNT_PUBLIC")
    shx_sac = os.getenv("SHX_SAC_CONTRACT_ID")
    treasury = os.getenv("HOUSE_ACCOUNT_PUBLIC")
    
    if not secret:
        logger.error("HOUSE_ACCOUNT_SECRET not found in .env")
        return

    logger.info(f"Initializing contract {contract_id}...")
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
            # Note: Might already be initialized if I retried, but let's see.
    except Exception as e:
        logger.error(f"EXCEPTION during initialization: {e}")

    logger.info("Setting Bot Admin PubKey (for signature verification)...")
    pubkey_hex = stellar_utils.get_house_pubkey_hex()
    
    # set_admin_pubkey(env: Env, pubkey: BytesN<32>)
    params = [
        scval.to_bytes(bytes.fromhex(pubkey_hex)), # ScValBytes
    ]
    
    try:
        res = await stellar_utils.invoke_contract_function(secret, contract_id, "set_admin_pubkey", params)
        if res["success"]:
            logger.info("SUCCESS: Bot Admin Public Key set.")
        else:
            logger.error(f"FAILED to set admin pubkey: {res['error']}")
    except Exception as e:
        logger.error(f"EXCEPTION during admin setup: {e}")

    logger.info("Updating .env file...")
    set_key(".env", "SOROBAN_CONTRACT_ID", contract_id)
    logger.info(f"DONE | New Contract ID: {contract_id}")

    await stellar_utils.close_session()

if __name__ == "__main__":
    asyncio.run(run_init())
