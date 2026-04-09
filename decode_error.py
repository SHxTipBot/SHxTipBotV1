from stellar_sdk import xdr
import base64

xdr_str = "AAAAAAAAik3////7AAAAAA=="
decoded = xdr.TransactionResult.from_xdr(xdr_str)
print(f"Result: {decoded.result.code}")
