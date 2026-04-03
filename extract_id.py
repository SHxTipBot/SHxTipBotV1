import re

def extract():
    with open("soroban_tipping_contract/new_contract_id.txt", "r") as f:
        content = f.read()
        match = re.search(r"C[A-Z0-9]{55}", content)
        if match:
            print(f"ID:{match.group(0)}")
        else:
            print("NOT FOUND")

if __name__ == "__main__":
    extract()
