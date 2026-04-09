import subprocess
import os

def run():
    source = os.getenv("HOUSE_ACCOUNT_SECRET")
    cmd = [
        "stellar", "contract", "deploy",
        "--wasm", "soroban_tipping_contract/target/wasm32-unknown-unknown/release/shx_tipping_contract.wasm",
        "--source-account", source,
        "--rpc-url", "https://soroban-testnet.stellar.org",
        "--network-passphrase", "Test SDF Network ; September 2015",
        "--salt", "ultra-nuclear-1000"
    ]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = proc.stdout.readline()
            if not line: break
            print(line.decode("utf-8", errors="ignore").strip())
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run()
