import os
import asyncio
from dotenv import load_dotenv
from stellar_sdk import Keypair, SorobanServer, TransactionBuilder, scval, Network, Server

async def test_sac():
    load_dotenv()
    secret = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
    shx_sac = os.getenv("SHX_SAC_CONTRACT_ID", "").strip()
    
    kp = Keypair.from_secret(secret)
    rpc_url = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
    server = SorobanServer(rpc_url)
    horizon = Server(os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip())
    
    source_acc = horizon.load_account(kp.public_key)
    
    builder = (
        TransactionBuilder(source_acc, network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE if os.getenv("STELLAR_NETWORK") == "testnet" else Network.PUBLIC_NETWORK_PASSPHRASE)
        .append_invoke_contract_function_op(
            contract_id=shx_sac,
            function_name="balance",
            parameters=[scval.to_address(kp.public_key)]
        )
    )
    
    sim = server.simulate_transaction(builder.build())
    print(f"SAC Check Sim Result: {sim.results[0] if not sim.error else sim.error}")

if __name__ == "__main__":
    asyncio.run(test_sac())
