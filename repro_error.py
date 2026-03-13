from stellar_sdk import scval, Keypair
import os
from dotenv import load_dotenv

load_dotenv()

def test_conversion():
    try:
        user_public_key = "GAHO2LQHLZHYRRUE4CNT7QHWFDXJWK322XPUWO6RSFGB3FMI4H67OH5J" # Just a sample G address
        soroban_contract_id = os.getenv("SOROBAN_CONTRACT_ID", "")
        shx_sac_contract_id = os.getenv("SHX_SAC_CONTRACT_ID", "")
        
        print(f"Testing with:")
        print(f"  User Key: {user_public_key}")
        print(f"  Soroban ID: '{soroban_contract_id}'")
        print(f"  SHx SAC ID: '{shx_sac_contract_id}'")
        
        print("Converting User Key...")
        u = scval.to_address(user_public_key)
        print("OK")
        
        print("Converting Soroban ID...")
        s = scval.to_address(soroban_contract_id)
        print("OK")
        
        print("Converting SHx SAC ID...")
        sh = scval.to_address(shx_sac_contract_id)
        print("OK")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_conversion()
