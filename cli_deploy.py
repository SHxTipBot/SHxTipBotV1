import subprocess
import os
from dotenv import load_dotenv

def deploy():
    load_dotenv()
    source = os.getenv("HOUSE_ACCOUNT_SECRET")
    wasm = "soroban_tipping_contract/target/wasm32-unknown-unknown/release/shx_tipping_contract.wasm"
    rpc = "https://soroban-testnet.stellar.org"
    network = "Test SDF Network ; September 2015"
    
    cmd = [
        "stellar", "contract", "deploy",
        "--wasm", wasm,
        "--source-account", source,
        "--rpc-url", rpc,
        "--network-passphrase", network
    ]
    
    print(f"Running: {' '.join(cmd)}")
    try:
        # Capture stdout and stderr
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8")
        print("--- CLI OUTPUT ---")
        print(output)
        print("--- END OUTPUT ---")
        
        # Look for the C... Strkey (56 chars)
        import re
        match = re.search(r"C[A-Z0-9]{55}", output)
        if match:
            contract_id = match.group(0)
            print(f"FOUND_ID:{contract_id}")
            with open("final_full_id.txt", "w") as f:
                f.write(contract_id)
        else:
            print("COULD NOT FIND ID IN OUTPUT")
            
    except subprocess.CalledProcessError as e:
        print(f"CLI FAILED: {e.output.decode('utf-8')}")

if __name__ == "__main__":
    deploy()
