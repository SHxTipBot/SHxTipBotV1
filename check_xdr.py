import stellar_utils as stellar
from stellar_sdk import scval

val = scval.to_int128(10000000)
print(f"SCVal i128 XDR: {val.to_xdr_bytes().hex()}")
print(f"Raw i128 parts XDR: {val.i128.to_xdr_bytes().hex()}")

addr = scval.to_address("GAHO2LQHLZHYRRUE4CNT7QHWFDXJWK322XPUWO6RSFGB3FMI4H67OH5J")
print(f"SCVal Address XDR: {addr.to_xdr_bytes().hex()}")
print(f"Raw Address parts XDR: {addr.address.to_xdr_bytes().hex()}")

nonce = scval.to_uint64(12345)
print(f"SCVal u64 XDR: {nonce.to_xdr_bytes().hex()}")
print(f"Raw u64 parts XDR: {nonce.u64.to_xdr_bytes().hex()}")
