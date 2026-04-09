import asyncio
import os
import requests
from dotenv import load_dotenv

load_dotenv()
HOUSE_ACCOUNT = os.getenv("HOUSE_ACCOUNT_PUBLIC")
HORIZON_URL = os.getenv("HORIZON_URL")

def check_deposits():
    try:
        url = f"{HORIZON_URL}/accounts/{HOUSE_ACCOUNT}/payments?limit=20&order=desc"
        r = requests.get(url)
        payments = r.json()['_embedded']['records']
        for p in payments:
            if p['type'] == 'payment' and float(p['amount']) == 5.0:
                tx_url = p['_links']['transaction']['href']
                tx_r = requests.get(tx_url)
                if tx_r.status_code == 200:
                    tx_data = tx_r.json()
                    print(f"ID: {p['id']} | Hash: {p['transaction_hash']} | Memo: {tx_data.get('memo')} | From: {p['from']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_deposits()
