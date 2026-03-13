"""
Stellar / Soroban utilities for the SHx Tip Bot.
Handles balance queries, fee calculation, transaction construction, and contract invocation.
"""

import os
import asyncio
import logging
import aiohttp
from stellar_sdk import (
    Keypair, Network, Server, TransactionBuilder, Asset,
    SorobanServer, scval,
)
from stellar_sdk.soroban_rpc import GetTransactionStatus, SendTransactionStatus

logger = logging.getLogger("shx_tip_bot.stellar")

# ── Configuration (loaded from environment) ──────────────────────────────────

STELLAR_NETWORK = os.getenv("STELLAR_NETWORK", "testnet")
HORIZON_URL = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org")
SOROBAN_RPC_URL = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org")
SHX_ASSET_CODE = os.getenv("SHX_ASSET_CODE", "SHX")
SHX_ISSUER = os.getenv("SHX_ISSUER", "GDSTRSHXHGJ7ZIVRBXEYE5Q74XUVCUSEKEBR7UCHEUUEK72N7I7KJ6JH")
SHX_SAC_CONTRACT_ID = os.getenv("SHX_SAC_CONTRACT_ID", "")
SOROBAN_CONTRACT_ID = os.getenv("SOROBAN_CONTRACT_ID", "")
HOUSE_ACCOUNT_SECRET = os.getenv("HOUSE_ACCOUNT_SECRET", "")
HOUSE_ACCOUNT_PUBLIC = os.getenv("HOUSE_ACCOUNT_PUBLIC", "")
ESTIMATED_XLM_FEE = float(os.getenv("ESTIMATED_XLM_FEE", "0.05"))
GAS_BUFFER_PERCENT = 15  # safety margin on gas estimate
FALLBACK_GAS_SHX = float(os.getenv("FALLBACK_GAS_SHX", "0.5"))  # fallback if DEX price unavailable

NETWORK_PASSPHRASE = (
    Network.TESTNET_NETWORK_PASSPHRASE
    if STELLAR_NETWORK == "testnet"
    else Network.PUBLIC_NETWORK_PASSPHRASE
)

STELLAR_EXPERT_BASE = (
    "https://stellar.expert/explorer/testnet"
    if STELLAR_NETWORK == "testnet"
    else "https://stellar.expert/explorer/public"
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_shx_asset() -> Asset:
    """Return the SHx Asset object."""
    return Asset(SHX_ASSET_CODE, SHX_ISSUER)


def get_explorer_url(tx_hash: str) -> str:
    """Get the Stellar Expert URL for a transaction."""
    return f"{STELLAR_EXPERT_BASE}/tx/{tx_hash}"


def _to_stroops(amount: float) -> int:
    """Convert a human-readable amount to 7-decimal stroops (Stellar precision)."""
    return int(round(amount * 10_000_000))


# ── Global Session Management ────────────────────────────────────────────────

_session: aiohttp.ClientSession | None = None

async def get_session() -> aiohttp.ClientSession:
    """Get or create a global aiohttp session."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
    return _session

async def close_session():
    """Close the global aiohttp session."""
    global _session
    if _session and not _session.closed:
        await _session.close()


# ── Balance & Trustline ──────────────────────────────────────────────────────

async def get_shx_balance(public_key: str) -> float | None:
    """Query the SHx balance for a Stellar account via Horizon."""
    try:
        session = await get_session()
        url = f"{HORIZON_URL}/accounts/{public_key}"
        async with session.get(url) as resp:
            if resp.status != 200:
                logger.warning(f"Horizon returned {resp.status} for account {public_key[:8]}...")
                return None
            data = await resp.json()
            for bal in data.get("balances", []):
                if (
                    bal.get("asset_code") == SHX_ASSET_CODE
                    and bal.get("asset_issuer") == SHX_ISSUER
                ):
                    return float(bal["balance"])
            # Account exists but has no SHx trustline
            return 0.0
    except Exception as e:
        logger.error(f"Error fetching balance for {public_key[:8]}...: {e}")
        return None


async def check_shx_trustline(public_key: str) -> bool:
    """Check if a Stellar account has an active SHx trustline."""
    balance = await get_shx_balance(public_key)
    # balance == 0.0 means trustline exists with zero balance; None means no trustline/account
    return balance is not None


# ── Dynamic Fee Calculation ──────────────────────────────────────────────────

async def get_shx_xlm_price() -> float | None:
    """
    Get the current price of SHx in XLM from the Stellar DEX orderbook.
    Returns XLM-per-SHx (how much XLM 1 SHx is worth).
    """
    try:
        session = await get_session()
        url = (
            f"{HORIZON_URL}/order_book"
            f"?selling_asset_type=credit_alphanum4"
            f"&selling_asset_code={SHX_ASSET_CODE}"
            f"&selling_asset_issuer={SHX_ISSUER}"
            f"&buying_asset_type=native"
            f"&limit=1"
        )
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            # Bids = people willing to buy SHx (price = XLM per SHx)
            if data.get("bids"):
                return float(data["bids"][0]["price"])
            return None
    except Exception as e:
        logger.error(f"Error fetching SHx/XLM price: {e}")
        return None


async def calculate_gas_shx() -> float:
    """
    Calculate the SHx equivalent of the XLM gas cost for a Soroban tip.
    """
    xlm_per_shx = await get_shx_xlm_price()

    if xlm_per_shx and xlm_per_shx > 0:
        gas_shx = ESTIMATED_XLM_FEE / xlm_per_shx
        gas_shx *= 1 + (GAS_BUFFER_PERCENT / 100)
        return round(gas_shx, 7)
    else:
        logger.warning("DEX price unavailable — using fallback gas estimate.")
        return FALLBACK_GAS_SHX


# ── Soroban Contract Invocation ──────────────────────────────────────────────

async def execute_tip(
    sender_public_key: str,
    recipient_public_key: str,
    amount: float,
    fee: float,
) -> dict:
    """
    Execute a tip via the Soroban tipping contract.

    The contract's `tip` function calls the SHx SAC `transfer_from` to move:
      • `amount` SHx  →  sender → recipient
      • `fee` SHx     →  sender → treasury

    The sender must have previously approved the tipping contract for an
    allowance ≥ amount + fee on the SHx SAC.

    Returns dict with keys: success, tx_hash, tx_url, error.
    """
    try:
        house_keypair = Keypair.from_secret(HOUSE_ACCOUNT_SECRET)
        soroban_server = SorobanServer(SOROBAN_RPC_URL)
        horizon_server = Server(HORIZON_URL)

        # Load house account (source that pays XLM fees)
        house_account = horizon_server.load_account(house_keypair.public_key)

        amount_i128 = _to_stroops(amount)
        fee_i128 = _to_stroops(fee)

        # Build Soroban invoke transaction
        builder = TransactionBuilder(
            source_account=house_account,
            network_passphrase=NETWORK_PASSPHRASE,
            base_fee=100_000,
        )

        builder.append_invoke_contract_function_op(
            contract_id=SOROBAN_CONTRACT_ID,
            function_name="tip",
            parameters=[
                scval.to_address(sender_public_key),
                scval.to_address(recipient_public_key),
                scval.to_int128(amount_i128),
                scval.to_int128(fee_i128),
            ],
        )

        builder.set_timeout(300)
        tx = builder.build()

        # Simulate
        sim = soroban_server.simulate_transaction(tx)
        if sim.error:
            logger.error(f"Soroban Simulation Error: {sim.error}")
            if hasattr(sim, 'events') and sim.events:
                logger.error(f"Simulation Events: {sim.events}")
            return _fail(f"Simulation failed: {sim.error}")

        # Prepare (attach resource footprint, adjust fees)
        tx = soroban_server.prepare_transaction(tx, sim)
        tx.sign(house_keypair)

        # Submit
        response = soroban_server.send_transaction(tx)
        if response.status == SendTransactionStatus.ERROR:
            logger.error(f"Soroban Submit Error: {response.error}")
            return _fail(f"Submit error: {response.error}")

        tx_hash = response.hash

        # Poll for confirmation (up to ~60 s)
        for _ in range(60):
            result = soroban_server.get_transaction(tx_hash)
            if result.status == GetTransactionStatus.SUCCESS:
                return {
                    "success": True,
                    "tx_hash": tx_hash,
                    "tx_url": get_explorer_url(tx_hash),
                    "error": None,
                }
            if result.status == GetTransactionStatus.FAILED:
                logger.error(f"Transaction failed on-chain: {result.error_result_xdr if hasattr(result, 'error_result_xdr') else 'Unknown'}")
                return _fail("Transaction failed on-chain.", tx_hash)
            await asyncio.sleep(1)

        return _fail("Transaction timed out.", tx_hash)

    except Exception as e:
        logger.error(f"execute_tip error: {e}", exc_info=True)
        return _fail(str(e))


def _fail(error: str, tx_hash: str = None) -> dict:
    """Helper to build a failure result dict."""
    return {
        "success": False,
        "tx_hash": tx_hash,
        "tx_url": get_explorer_url(tx_hash) if tx_hash else None,
        "error": error,
    }


# ── Approve Transaction Builder (for the web linking flow) ───────────────────

async def build_approve_tx_xdr(
    user_public_key: str,
    allowance_amount: float = 1_000_000,
) -> str:
    """
    Build an *unsigned* transaction XDR that calls `approve` on the SHx SAC.
    """
    if not SHX_SAC_CONTRACT_ID:
        raise Exception("Environment variable SHX_SAC_CONTRACT_ID is missing or empty.")
    if not SOROBAN_CONTRACT_ID:
        raise Exception("Environment variable SOROBAN_CONTRACT_ID is missing or empty.")

    horizon_server = Server(HORIZON_URL)

    # Check if the account exists; on testnet, auto-fund if not
    account_exists = True
    try:
        horizon_server.load_account(user_public_key)
    except Exception:
        account_exists = False

    if not account_exists:
        if STELLAR_NETWORK != "testnet":
            raise Exception(
                "Account does not exist on the Stellar public network. "
                "Please fund it with at least 2 XLM first."
            )
        # Auto-fund via Friendbot on testnet
        logger.info(f"Account {user_public_key[:8]}... not found on testnet, funding via Friendbot...")
        session = await get_session()
        async with session.get(
            f"https://friendbot.stellar.org?addr={user_public_key}"
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                if "createAccountAlreadyExist" not in text:
                    raise Exception(f"Friendbot funding failed: {text[:200]}")
        # Wait for ledger close
        await asyncio.sleep(5)
        logger.info(f"Funded {user_public_key[:8]}... via Friendbot.")

    # Reload account (now it should exist)
    user_account = horizon_server.load_account(user_public_key)

    # Check if account has SHX trustline; add it if missing (testnet only)
    balance = await get_shx_balance(user_public_key)
    has_trustline = balance is not None and balance >= 0.0

    if not has_trustline and STELLAR_NETWORK == "testnet":
        logger.info(f"Adding SHX trustline for {user_public_key[:8]}... (will be included in approve tx)")

    allowance_stroops = _to_stroops(allowance_amount)
    expiration_ledger = 3_000_000

    builder = TransactionBuilder(
        source_account=user_account,
        network_passphrase=NETWORK_PASSPHRASE,
        base_fee=100_000,
    )

    # If on testnet and no trustline, add the change_trust op first
    if not has_trustline and STELLAR_NETWORK == "testnet":
        shx_asset = Asset(SHX_ASSET_CODE, SHX_ISSUER)
        builder.append_change_trust_op(asset=shx_asset)

    builder.append_invoke_contract_function_op(
        contract_id=SHX_SAC_CONTRACT_ID,
        function_name="approve",
        parameters=[
            scval.to_address(user_public_key),       # owner
            scval.to_address(SOROBAN_CONTRACT_ID),   # spender (tipping contract)
            scval.to_int128(allowance_stroops),       # amount
            scval.to_uint32(expiration_ledger),       # expiration_ledger
        ],
    )

    builder.set_timeout(300)
    tx = builder.build()
    return tx.to_xdr()

