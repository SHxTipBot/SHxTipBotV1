import subprocess
import os
import re

def deploy():
    source = os.getenv("HOUSE_ACCOUNT_SECRET")
    cmd = [
        "stellar", "contract", "deploy",
        "--wasm", "soroban_tipping_contract/target/wasm32-unknown-unknown/release/shx_tipping_contract.wasm",
        "--source-account", source,
        "--rpc-url", "https://soroban-testnet.stellar.org",
        "--network-passphrase", "Test SDF Network ; September 2015",
        "--salt", "0000000000000000000000000000000000000000000000000000000000000001"
    ]
    try:
        # result = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
        # subprocess.run can sometimes fail with None in stdout if it crashes.
        # Let's use Popen for robustness.
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        out = (stdout or b"").decode("utf-8", errors="ignore") + (stderr or b"").decode("utf-8", errors="ignore")
        
        print("--- OUTPUT ---")
        print(out)
        print("--- END ---")
        
        match = re.search(r"C[A-Z2-7]{55}", out)
        if match:
            id = match.group(0)
            print(f"FOUND_REAL_ID:{id}")
            with open("real_id.txt", "w") as f:
                f.write(id)
        else:
            print("NOT FOUND")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    deploy()
