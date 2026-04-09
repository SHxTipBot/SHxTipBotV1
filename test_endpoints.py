import requests
import json

endpoints = [
    "https://soroban-rpc.mainnet.stellar.org",
    "https://mainnet.sorobanrpc.com",
    "https://stellar-mainnet.publicnode.com",
    "https://horizon.stellar.org"
]

for url in endpoints:
    try:
        # Simple health check or info call
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getNetwork",
            "params": {}
        }
        resp = requests.post(url, json=payload, timeout=5)
        print(f"{url}: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  Response: {resp.text[:100]}")
    except Exception as e:
        print(f"{url}: FAILED - {e}")
