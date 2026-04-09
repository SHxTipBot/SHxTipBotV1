from stellar_sdk import xdr, scval
import stellar_utils as stellar

def test_xdr():
    # 1. Address
    addr = "GABY3YD3CDWT7M5LN7W3G27VJ7US6A3TSBQZSGS7KH54DNJ2F6NBFN4K"
    sc_val = stellar.to_sc_address(addr)
    full_xdr = sc_val.to_xdr_bytes()
    inner_xdr = sc_val.address.to_xdr_bytes()
    print(f"Address Full (SCVal) Len: {len(full_xdr)} | Inner (SCAddress) Len: {len(inner_xdr)}")
    print(f"Full: {full_xdr.hex()}")
    print(f"Inner: {inner_xdr.hex()}")
    
    # 2. i128
    amt = 1000 * 10**7
    sc_val_i128 = scval.to_int128(amt)
    full_i128_xdr = sc_val_i128.to_xdr_bytes()
    inner_i128_xdr = sc_val_i128.i128.to_xdr_bytes()
    print(f"i128 Full Len: {len(full_i128_xdr)} | Inner Len: {len(inner_i128_xdr)}")
    
    # 3. u64
    nonce = 12345
    sc_val_u64 = scval.to_uint64(nonce)
    full_u64_xdr = sc_val_u64.to_xdr_bytes()
    inner_u64_xdr = sc_val_u64.u64.to_xdr_bytes()
    print(f"u64 Full Len: {len(full_u64_xdr)} | Inner Len: {len(inner_u64_xdr)}")

test_xdr()
