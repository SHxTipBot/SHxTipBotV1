from stellar_sdk import xdr
import base64

xdr_str = "AAAAAAABYAz////7AAAAAA=="
try:
    # Try as TransactionResult
    decoded = xdr.TransactionResult.from_xdr(xdr_str)
    print(f"TransactionResult Result: {decoded.result.code}")
except:
    pass

try:
    # Try as PathPaymentStrictReceiveResult
    decoded = xdr.TransactionResultPair.from_xdr(xdr_str)
    print(f"TransactionResultPair: {decoded}")
except:
    pass
