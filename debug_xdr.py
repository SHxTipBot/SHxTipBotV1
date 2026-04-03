from stellar_sdk import xdr, StrKey

def test():
    # Mock a contract ID SCVal
    # SCAddress(type=CONTRACT, contract_id=Hash(32 bytes))
    raw_bytes = b"\x01" * 32
    hash_obj = xdr.Hash(raw_bytes)
    sc_addr = xdr.SCAddress(type=xdr.SCAddressType.SC_ADDRESS_TYPE_CONTRACT, contract_id=hash_obj)
    sc_val = xdr.SCVal(type=xdr.SCValType.SCV_ADDRESS, address=sc_addr)
    
    try:
        raw_xdr = sc_val.to_xdr()
        # Offset 8 is common for SCVal Address Contract Hash
        manual_bytes = raw_xdr[8:40]
        encoded = StrKey.encode_contract(manual_bytes)
        print(f"SUCCESS with slice[8:40]: {encoded}")
    except Exception as e:
        print(f"FAILED with slice[8:40]: {e}")
    
    print(f"Object: {sc_val.address.contract_id}")
    print(f"Dir: {dir(sc_val.address.contract_id)}")
    
    for attr in ["hash", "contract_id", "_hash", "_data", "data"]:
        if hasattr(sc_val.address.contract_id, attr):
            print(f"SUCCESS with .{attr}: {getattr(sc_val.address.contract_id, attr).hex()}")
    
    try:
        print(f"SUCCESS with bytes(): {bytes(sc_val.address.contract_id).hex()}")
    except Exception as e:
        print(f"FAILED with bytes(): {e}")

if __name__ == "__main__":
    test()
