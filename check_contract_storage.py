import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from stellar_sdk import Keypair, SorobanServer, scval, xdr, StrKey

async def main():
    contract_id = os.getenv("SOROBAN_CONTRACT_ID")
    rpc_url = "https://mainnet.sorobanrpc.com"
    server = SorobanServer(rpc_url)
    
    contract_addr = scval.to_address(contract_id)
    
    key = xdr.LedgerKey(
        type=xdr.LedgerEntryType.CONTRACT_DATA,
        contract_data=xdr.LedgerKeyContractData(
            contract=contract_addr,
            key=xdr.SCVal(xdr.SCValType.SCV_LEDGER_KEY_CONTRACT_INSTANCE),
            durability=xdr.ContractDataDurability.PERSISTENT
        )
    )
    
    try:
        resp = server.get_ledger_entries([key])
        if resp.entries:
            entry = resp.entries[0]
            val = entry.val
            instance = val.contract_data.val.instance
            
            if instance.storage:
                for map_entry in instance.storage:
                    key_val = map_entry.key
                    val_val = map_entry.val
                    if key_val.type == xdr.SCValType.SCV_SYMBOL and key_val.sym.decode() == "adm_pub":
                        print("FOUND adm_pub!")
                        if hasattr(val_val, "bytes"):
                             raw_bytes = val_val.bytes
                        elif hasattr(val_val, "sym"):
                             raw_bytes = val_val.sym
                        elif hasattr(val_val, "obj"):
                             raw_bytes = val_val.obj.bytes
                        else:
                             print(f"Unknown val_val format: {dir(val_val)}")
                             raw_bytes = val_val.to_xdr_bytes()
                             
                        print("ADMIN KEY IN CONTRACT (hex):", raw_bytes.hex())
                        
                        pk = os.getenv("HOUSE_ACCOUNT_PUBLIC")
                        kp = Keypair.from_public_key(pk)
                        expected = kp.raw_public_key().hex()
                        print("EXPECTED IN DB (hex):       ", expected)
                        return
            print("adm_pub not found in instance storage")
    except Exception as e:
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
