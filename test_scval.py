from stellar_sdk import scval, Address
import os

def test():
    id = "CDTL7BBCUZTD7GPRXXZ74W4FGGH43JQEWQ4PC4IYKFQGBBH53VL525VH"
    try:
        val = scval.to_address(id)
        print("SUCCESS with scval.to_address")
    except Exception as e:
        print(f"FAILED with scval.to_address: {e}")
        
    try:
        val = Address(id).to_xdr_sc_val()
        print("SUCCESS with Address(id).to_xdr_sc_val()")
    except Exception as e:
        print(f"FAILED with Address(id).to_xdr_sc_val(): {e}")

if __name__ == "__main__":
    test()
