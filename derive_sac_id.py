import os
import asyncio
from dotenv import load_dotenv
from stellar_sdk import Asset, xdr
import hashlib

def get_sac_id():
    load_dotenv()
    asset_code = os.getenv("SHX_ASSET_CODE", "SHX").strip()
    asset_issuer = os.getenv("SHX_ISSUER", "GDSTRSHXHGJ7ZIVRBXEYE5Q74XUVCUSEKEBR7UCHEUUEK72N7I7KJ6JH").strip()
    network_passphrase = "Test Stellar Network ; September 2015"
    
    asset = Asset(asset_code, asset_issuer)
    
    # Deriving SAC ID
    # 1. Asset XDR
    asset_xdr = asset.to_xdr_object()
    
    # 2. Hash(network_passphrase + ENVELOPE_TYPE_CONTRACT_ID_FROM_ASSET + AssetXDR)
    packer = xdr.Xdr()
    xdr.HashIdPreimage(
        type=xdr.EnvelopeType.ENVELOPE_TYPE_CONTRACT_ID_FROM_ASSET,
        from_asset=xdr.HashIdPreimageFromAsset(
            network_id=hashlib.sha256(network_passphrase.encode()).digest(),
            asset=asset_xdr
        )
    ).pack(packer)
    
    preimage_hash = hashlib.sha256(packer.get_buffer()).digest()
    
    # Contract ID is hex of the hash
    contract_id = preimage_hash.hex()
    print(f"Derived SAC ID (hex): {contract_id}")
    
    # Convert to C string format? No, Soroban uses C... format.
    # We can use StrKey to encode.
    from stellar_sdk import strkey
    c_id = strkey.StrKey.encode_contract(preimage_hash)
    print(f"Derived SAC ID (C...): {c_id}")

if __name__ == "__main__":
    get_sac_id()
