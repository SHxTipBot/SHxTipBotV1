import subprocess
import os
import time

def deploy():
    source = os.getenv("HOUSE_ACCOUNT_SECRET")
    # Use a unique salt to avoid "already exists" errors
    salt = f"salt_{int(time.time())}"
    
    cmd = [
        "stellar", "contract", "deploy",
        "--wasm", "soroban_tipping_contract/target/wasm32-unknown-unknown/release/shx_tipping_contract.wasm",
        "--source-account", source,
        "--rpc-url", "https://soroban-testnet.stellar.org",
        "--network-passphrase", "Test SDF Network ; September 2015",
        "--salt", salt
    ]
    
    # Run with os.environ update for columns
    env = os.environ.copy()
    env["COLUMNS"] = "1000"
    
    print(f"Deploying with salt: {salt}...")
    try:
        # We use a file to capture output to avoid any encoding/buffering issues
        with open("deploy_output.txt", "w") as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
            
        with open("deploy_output.txt", "r", encoding="utf-8", errors="ignore") as f:
            out = f.read()
            
        print("--- CAPTURED OUTPUT ---")
        print(out)
        
        import re
        match = re.search(r"C[A-Z2-7]{55}", out)
        if match:
             id = match.group(0)
             print(f"FOUND_VALID_ID:{id}")
             with open("valid_id.txt", "w") as f:
                 f.write(id)
        else:
             print("ID NOT FOUND")
             
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    deploy()
