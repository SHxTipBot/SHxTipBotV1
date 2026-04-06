"""
Stellar / Soroban utilities for the SHx Tip Bot.
Handles balance queries, fee calculation, transaction construction, and contract invocation.
"""

import os
import time
import asyncio
import logging
import aiohttp
import base64
from stellar_sdk import (
    Keypair, Network, Server, ServerAsync, AiohttpClient, TransactionBuilder, Asset,
    SorobanServer, scval, TransactionEnvelope, xdr, StrKey
)
from stellar_sdk.soroban_rpc import GetTransactionStatus, SendTransactionStatus
from stellar_sdk.exceptions import NotFoundError

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("shx_tip_bot.stellar")

# ── Configuration (loaded from environment) ──────────────────────────────────

STELLAR_NETWORK = os.getenv("STELLAR_NETWORK", "testnet").strip()
HORIZON_URL = os.getenv("HORIZON_URL", "https://horizon-testnet.stellar.org").strip()
SOROBAN_RPC_URL = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org").strip()
SHX_ASSET_CODE = os.getenv("SHX_ASSET_CODE", "SHX").strip()
SHX_ISSUER = os.getenv("SHX_ISSUER", "GDSTRSHXHGJ7ZIVRBXEYE5Q74XUVCUSEKEBR7UCHEUUEK72N7I7KJ6JH").strip()
SHX_SAC_CONTRACT_ID = os.getenv("SHX_SAC_CONTRACT_ID", "").strip()
SOROBAN_CONTRACT_ID = os.getenv("SOROBAN_CONTRACT_ID", "").strip()
HOUSE_ACCOUNT_SECRET = os.getenv("HOUSE_ACCOUNT_SECRET", "").strip()
HOUSE_ACCOUNT_PUBLIC = os.getenv("HOUSE_ACCOUNT_PUBLIC", "").strip()
HOUSE_ACCOUNT_PUBLIC = os.getenv("HOUSE_ACCOUNT_PUBLIC", "").strip()

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


def to_sc_address(addr: str) -> xdr.SCVal:
    """
    Robust address conversion for Soroban.
    Handles both standard G-addresses and C-contract IDs.
    """
    if addr.startswith("C"):
        return xdr.SCVal(
            type=xdr.SCValType.SCV_ADDRESS,
            address=xdr.SCAddress(
                type=xdr.SCAddressType.SC_ADDRESS_TYPE_CONTRACT,
                contract_id=xdr.Hash(StrKey.decode_contract(addr))
            )
        )
    else:
        return scval.to_address(addr)

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
            return None
    except Exception as e:
        logger.error(f"Error fetching balance for {public_key[:8]}...: {e}")
        return None


async def check_shx_allowance(owner_public_key: str, spender_contract_id: str) -> float:
    """Check the current SHx allowance for a spender on an owner's account."""
    try:
        soroban_server = SorobanServer(SOROBAN_RPC_URL)
        # Call SHx SAC 'allowance' function
        # allowance(owner: Address, spender: Address) -> i128
        
        result = await _invoke_sac_read_only(
            SHX_SAC_CONTRACT_ID,
            "allowance",
            [
                to_sc_address(owner_public_key),
                to_sc_address(spender_contract_id),
            ]
        )
        if result is None:
            return 0.0
        # result is the xdr string from simulation
        print(f"DEBUG: check_shx_allowance raw result: {result}")
        scval_obj = xdr.SCVal.from_xdr(result)
        if scval_obj.type != xdr.SCValType.SCV_I128:
            print(f"DEBUG: result is not i128, type: {scval_obj.type}")
            return 0.0
            
        # Accessing i128 parts: lo is Uint64, hi is Int64
        parts = scval_obj.i128
        stroops = int(parts.lo.uint64) + (int(parts.hi.int64) << 64)
        return stroops / 10_000_000
    except Exception as e:
        logger.error(f"Error checking allowance for {owner_public_key[:8]}: {e}")
        return 0.0

async def _invoke_sac_read_only(contract_id: str, function_name: str, parameters: list):
    """Internal helper to call a read-only SAC function."""
    try:
        soroban_server = SorobanServer(SOROBAN_RPC_URL)
        builder = TransactionBuilder(
            source_account=await get_dummy_account(), # Just need a placeholder
            network_passphrase=NETWORK_PASSPHRASE,
        )
        builder.append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name=function_name,
            parameters=parameters,
        )
        tx = builder.build()
        sim = soroban_server.simulate_transaction(tx)
        if sim.error:
            return None
        return sim.results[0].xdr
    except Exception:
        return None

async def get_dummy_account():
    """Returns a dummy Account object for simulation purposes."""
    return Server(HORIZON_URL).load_account("GAHO2LQHLZHYRRUE4CNT7QHWFDXJWK322XPUWO6RSFGB3FMI4H67OH5J") # House account is fine

async def approve_shx(secret: str, amount: float = 1_000_000):
    """
    Submit an 'approve' transaction for the tipping contract.
    Returns dict with success/error.
    """
    try:
        keypair = Keypair.from_secret(secret)
        public_key = keypair.public_key
        horizon_server = Server(HORIZON_URL)
        soroban_server = SorobanServer(SOROBAN_RPC_URL)
        
        # FIX: Load account and calculate stroops
        account = horizon_server.load_account(public_key)
        stroops = _to_stroops(amount)
        
        builder = TransactionBuilder(
            source_account=account,
            network_passphrase=NETWORK_PASSPHRASE,
            base_fee=100_000,
        )
        builder.append_invoke_contract_function_op(
            contract_id=SHX_SAC_CONTRACT_ID,
            function_name="approve",
            parameters=[
                to_sc_address(public_key),
                to_sc_address(SOROBAN_CONTRACT_ID),
                scval.to_int128(stroops),
                scval.to_uint32(3_000_000), # expiration
            ],
        )
        builder.set_timeout(300)
        tx = builder.build()
        sim = soroban_server.simulate_transaction(tx)
        if sim.error:
            return {"success": False, "error": f"Approve simulation failed: {sim.error}"}
        
        tx = soroban_server.prepare_transaction(tx, sim)
        tx.sign(keypair)
        
        resp = soroban_server.send_transaction(tx)
        if resp.status == SendTransactionStatus.ERROR:
             return {"success": False, "error": f"Approve submit error (XDR): {resp.error_result_xdr}"}
             
        # Just return success without waiting for ledger for speed, 
        # as next tx might still fail if too fast, but usually fine.
        return {"success": True, "hash": resp.hash}
    except Exception as e:
        logger.error(f"approve_shx error: {e}")
        return {"success": False, "error": str(e)}

async def check_shx_trustline(public_key: str) -> bool:
    """Check if a Stellar account has an active SHx trustline."""
    balance = await get_shx_balance(public_key)
    # balance == 0.0 means trustline exists with zero balance; None means no trustline/account
    return balance is not None


# ── Dynamic Fee Calculation & Oracles ────────────────────────────────────────

_usd_price_cache = {"price": 0.0, "timestamp": 0.0}

async def get_shx_usd_price() -> float | None:
    """
    Get the current price of SHx in USD.
    
    Logic:
    1. If on Testnet, returns a mock value of $0.001.
    2. If on Mainnet, tries CoinGecko first (most stable).
    3. If CoinGecko fails, falls back to the Stellar DEX (SHX/USDC pair).
    4. Caches results for 5 minutes.
    """
    now = time.time()
    if now - _usd_price_cache["timestamp"] < 300:
        if _usd_price_cache["price"] > 0:
            return _usd_price_cache["price"]

    # 1. Testnet Mock
    if STELLAR_NETWORK == "testnet":
        return 0.001

    price = None

    # 2. Try CoinGecko (Mainnet)
    try:
        session = await get_session()
        cg_url = "https://api.coingecko.com/api/v3/simple/price?ids=stronghold-token&vs_currencies=usd"
        async with session.get(cg_url) as resp:
            if resp.status == 200:
                data = await resp.json()
                price = float(data.get("stronghold-token", {}).get("usd", 0.0))
                if price > 0:
                    logger.info(f"Price Oracle | CoinGecko | SHX = ${price:.6f}")
                    _usd_price_cache["price"] = price
                    _usd_price_cache["timestamp"] = now
                    return price
    except Exception as e:
        logger.warning(f"Price Oracle | CoinGecko failed: {e}")

    # 3. Try Stellar DEX Fallback (Mainnet)
    try:
        session = await get_session()
        # USDC (Centre) on Stellar Mainnet
        USDC_CODE = "USDC"
        USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335XOP3IA2M6GKP5V7SUCTS6XY"
        
        dex_url = (
            f"{HORIZON_URL}/order_book"
            f"?selling_asset_type=credit_alphanum4"
            f"&selling_asset_code={SHX_ASSET_CODE}"
            f"&selling_asset_issuer={SHX_ISSUER}"
            f"&buying_asset_type=credit_alphanum4"
            f"&buying_asset_code={USDC_CODE}"
            f"&buying_asset_issuer={USDC_ISSUER}"
            f"&limit=1"
        )
        async with session.get(dex_url) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("bids"):
                    price = float(data["bids"][0]["price"])
                    if price > 0:
                        logger.info(f"Price Oracle | Stellar DEX | SHX = ${price:.6f}")
                        _usd_price_cache["price"] = price
                        _usd_price_cache["timestamp"] = now
                        return price
    except Exception as e:
        logger.error(f"Price Oracle | Stellar DEX failed: {e}")

    # 4. Final Fallback to Cache
    return _usd_price_cache["price"] if _usd_price_cache["price"] > 0 else None

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




def usd_to_shx(usd_amount: float, shx_price_usd: float) -> float:
    """Convert USD amount to SHx amount based on current price."""
    if shx_price_usd <= 0:
        return 0.0
    return round(usd_amount / shx_price_usd, 7)


# ── Soroban Contract Invocation ──────────────────────────────────────────────

async def execute_tip(
    sender_public_key: str,
    recipient_public_key: str,
    amount: float,
    fee: float,
    memo: str = None,
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

        # AUTO-APPROVE for House Account:
        # If the sender is the house account, it can sign its own approval.
        if sender_public_key == HOUSE_ACCOUNT_PUBLIC:
            allowance = await check_shx_allowance(sender_public_key, SOROBAN_CONTRACT_ID)
            if allowance < (amount + fee):
                logger.info(f"Auto-approving House Account ({sender_public_key[:8]}) for Soroban tipping...")
                await approve_shx(HOUSE_ACCOUNT_SECRET, amount=1_000_000)
                await asyncio.sleep(5) # Wait for approval to clear

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

        if memo:
            builder.add_text_memo(memo[:28])

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
            logger.error(f"Soroban Submit Error: {response.error_result_xdr}")
            return _fail(f"Submit error (XDR): {response.error_result_xdr}")

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
                logger.error(f"Transaction failed on-chain: {result.result_xdr if hasattr(result, 'result_xdr') else 'Unknown'}")
                return _fail("Transaction failed on-chain.", tx_hash)
            await asyncio.sleep(1)

        return _fail("Transaction timed out.", tx_hash)

    except Exception as e:
        logger.error(f"execute_tip error: {e}", exc_info=True)
        return _fail(str(e))


async def execute_batch_tip(
    sender_public_key: str,
    recipients: list, # List of dicts: {"public_key": str, "amount": float, "fee": float}
) -> dict:
    """
    Execute multiple tips in a single Soroban transaction.
    """
    try:
        house_keypair = Keypair.from_secret(HOUSE_ACCOUNT_SECRET)
        soroban_server = SorobanServer(SOROBAN_RPC_URL)
        horizon_server = Server(HORIZON_URL)

        # Load house account (source that pays XLM fees)
        house_account = horizon_server.load_account(house_keypair.public_key)

        # AUTO-APPROVE for House Account in batch:
        if sender_public_key == HOUSE_ACCOUNT_PUBLIC:
             total_needed = sum(r["amount"] + r["fee"] for r in recipients)
             allowance = await check_shx_allowance(sender_public_key, SOROBAN_CONTRACT_ID)
             if allowance < total_needed:
                logger.info(f"Auto-approving House Account ({sender_public_key[:8]}) for batch tips...")
                await approve_shx(HOUSE_ACCOUNT_SECRET, amount=max(1_000_000, total_needed + 100))
                await asyncio.sleep(5)

        # Build Soroban invoke transaction
        builder = TransactionBuilder(
            source_account=house_account,
            network_passphrase=NETWORK_PASSPHRASE,
            base_fee=100_000,
        )

        for rec in recipients:
            amount_i128 = _to_stroops(rec["amount"])
            fee_i128 = _to_stroops(rec["fee"])

            builder.append_invoke_contract_function_op(
                contract_id=SOROBAN_CONTRACT_ID,
                function_name="tip",
                parameters=[
                    scval.to_address(sender_public_key),
                    scval.to_address(rec["public_key"]),
                    scval.to_int128(amount_i128),
                    scval.to_int128(fee_i128),
                ],
            )

        builder.set_timeout(300)
        tx = builder.build()

        # Simulate
        sim = soroban_server.simulate_transaction(tx)
        if sim.error:
            logger.error(f"Soroban Batch Simulation Error: {sim.error}")
            return _fail(f"Batch simulation failed: {sim.error}")

        # Prepare (attach resource footprint, adjust fees)
        tx = soroban_server.prepare_transaction(tx, sim)
        tx.sign(house_keypair)

        # Submit
        response = soroban_server.send_transaction(tx)
        if response.status == SendTransactionStatus.ERROR:
            logger.error(f"Soroban Batch Submit Error: {response.error_result_xdr}")
            return _fail(f"Batch submit error (XDR): {response.error_result_xdr}")

        tx_hash = response.hash

        # Poll for confirmation
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
                return _fail("Batch transaction failed on-chain.", tx_hash)
            await asyncio.sleep(1)

        return _fail("Batch transaction timed out.", tx_hash)

    except Exception as e:
        logger.error(f"execute_batch_tip error: {e}", exc_info=True)
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

    # Reload account (now it should exist)
    try:
        user_account = horizon_server.load_account(user_public_key)
    except Exception as e:
        if STELLAR_NETWORK == "testnet":
            # Auto-fund via Friendbot on testnet
            logger.info(f"Account {user_public_key[:8]}... not found on testnet, funding via Friendbot...")
            session = await get_session()
            
            # Retry up to 3 times for friendbot
            funded = False
            for attempt in range(3):
                try:
                    async with session.get(
                        f"https://friendbot.stellar.org?addr={user_public_key}"
                    ) as resp:
                        text = await resp.text()
                        if resp.status == 200 or "createAccountAlreadyExist" in text:
                            funded = True
                            break
                        logger.warning(f"Friendbot attempt {attempt+1} failed: {text[:100]}")
                except Exception as fe:
                    logger.warning(f"Friendbot attempt {attempt+1} exception: {fe}")
                
                await asyncio.sleep(2)

            if not funded:
                raise Exception("Friendbot funding failed after multiple attempts.")
            
            # Wait for ledger close
            await asyncio.sleep(5)
            logger.info(f"Funded {user_public_key[:8]}... via Friendbot.")
            user_account = horizon_server.load_account(user_public_key)
        else:
            raise Exception(
                "Account does not exist on the Stellar public network. "
                "Please fund it with at least 2 XLM first."
            ) from e

    # Check if account has SHX trustline; add it if missing (testnet only)
    balance = await get_shx_balance(user_public_key)
    has_trustline = balance is not None and balance >= 0.0

    if not has_trustline:
        logger.info(f"Adding SHX trustline for {user_public_key[:8]}... (will be included in approve tx)")

    allowance_stroops = _to_stroops(allowance_amount)
    expiration_ledger = 3_000_000

    builder = TransactionBuilder(
        source_account=user_account,
        network_passphrase=NETWORK_PASSPHRASE,
        base_fee=100_000,
    )

    # If no trustline, add the change_trust op first
    if not has_trustline:
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

# ── Custodial Operations ─────────────────────────────────────────────────────

async def stream_deposits(cursor: str = "now", callback=None):
    """
    Continually poll for payments to the House account using ServerAsync with an explicit AiohttpClient.
    """
    logger.info(f"Starting deposit monitor for {HOUSE_ACCOUNT_PUBLIC[:8]}... from cursor {cursor}")
    
    while True:
        try:
            # Explicit AiohttpClient() to bypass internal HAS_AIOHTTP check issues
            async with ServerAsync(HORIZON_URL, client=AiohttpClient()) as server:
                while True:
                    # Polling 10 at a time
                    response = await server.payments().for_account(HOUSE_ACCOUNT_PUBLIC).cursor(cursor).limit(10).call()
                    records = response.get("_embedded", {}).get("records", [])
                    
                    if not records:
                        # No new records, wait 10 seconds
                        await asyncio.sleep(10)
                        continue

                    for r in records:
                        # Update cursor
                        cursor = r.get("paging_token", cursor)
                        
                        if r.get("type") not in ("payment", "path_payment_strict_receive"):
                            continue
                        
                        if (r.get("asset_code") != SHX_ASSET_CODE or 
                            r.get("asset_issuer") != SHX_ISSUER):
                            continue
                        
                        if r.get("to") != HOUSE_ACCOUNT_PUBLIC:
                            continue

                        tx_hash = r.get("transaction_hash")
                        amount_shx = float(r.get("amount"))
                        
                        try:
                            tx = await server.transactions().transaction(tx_hash).call()
                            memo_type = tx.get("memo_type")
                            memo_val = tx.get("memo")
                            
                            if callback:
                                await callback(memo_val, tx_hash, amount_shx, memo_type)
                        except Exception as ex:
                            logger.error(f"Error fetching tx details for {tx_hash}: {ex}")

        except Exception as e:
            logger.error(f"Deposit monitor encountered error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)

async def send_withdrawal(destination: str, amount_shx: float, memo: str = None) -> dict:
    """
    LEGACY: Direct withdrawal from House Account (Bot-Paid fee).
    Replaced by User-Paid 'claim' model.
    """
    # ... existing implementation omitted for brevity or kept for admin etc
    pass

async def deploy_contract_wasm(secret: str, wasm_path: str) -> str:
    """
    Install the contract WASM code on-chain.
    Returns the WASM ID.
    """
    kp = Keypair.from_secret(secret)
    horizon_server = Server(HORIZON_URL)
    soroban_server = SorobanServer(SOROBAN_RPC_URL)
    
    with open(wasm_path, "rb") as f:
        wasm_content = f.read()

    account = horizon_server.load_account(kp.public_key)
    builder = TransactionBuilder(account, NETWORK_PASSPHRASE).append_upload_contract_wasm_op(wasm_content)
    
    tx = builder.build()
    sim = soroban_server.simulate_transaction(tx)
    if sim.error:
        raise Exception(f"Install simulation failed: {sim.error}")
    
    tx = soroban_server.prepare_transaction(tx, sim)
    tx.sign(kp)
    
    resp = soroban_server.send_transaction(tx)
    if resp.status == SendTransactionStatus.ERROR:
        raise Exception(f"Install submit error: {resp.error_result_xdr}")
    
    # Wait for completion
    for _ in range(30):
        res = soroban_server.get_transaction(resp.hash)
        if res.status == GetTransactionStatus.SUCCESS:
            import hashlib
            return hashlib.sha256(wasm_content).digest().hex()
        await asyncio.sleep(2)
    
    raise Exception("Install timed out")

async def deploy_contract_instance(secret: str, wasm_id: str) -> str:
    """
    Deploy a contract instance using a WASM ID.
    Returns the Contract ID.
    """
    kp = Keypair.from_secret(secret)
    horizon_server = Server(HORIZON_URL)
    soroban_server = SorobanServer(SOROBAN_RPC_URL)
    
    account = horizon_server.load_account(kp.public_key)
    builder = TransactionBuilder(account, NETWORK_PASSPHRASE).append_create_contract_op(
        wasm_id=wasm_id,
        address=kp.public_key,
        salt=os.urandom(32)
    )
    
    tx = builder.build()
    sim = soroban_server.simulate_transaction(tx)
    if sim.error:
        raise Exception(f"Deploy simulation failed: {sim.error}")
        
    tx = soroban_server.prepare_transaction(tx, sim)
    tx.sign(kp)
    resp = soroban_server.send_transaction(tx)
    if resp.status == SendTransactionStatus.ERROR:
        raise Exception(f"Deploy submit error: {resp.error_result_xdr}")

    # Predict contract ID from simulation result (the Address return value)
    from stellar_sdk import StrKey
    res_xdr = sim.results[0].xdr
    scval_obj = xdr.SCVal.from_xdr(res_xdr)
    
    # In stellar-sdk 13.x, xdr.Hash/ContractID must be converted to bytes 
    # for StrKey encoding. Slicing from raw XDR is the most resilient fallback.
    try:
        # Path: scval.address (SCAddress) -> .contract_id (ContractID) -> .contract_id (Hash) -> .hash (bytes)
        contract_id_bytes = scval_obj.address.contract_id.contract_id.hash
    except (AttributeError, TypeError):
        try:
             # Fallback 1: Try common byte field names
             contract_id_bytes = scval_obj.address.contract_id.hash
        except (AttributeError, TypeError):
             # Fallback 2: Raw XDR slicing (last 32 bytes of the address SCVal)
             import base64
             res_bytes = base64.b64decode(sim.results[0].xdr)
             contract_id_bytes = res_bytes[-32:]
    
    contract_id = StrKey.encode_contract(contract_id_bytes)
    
    # Wait for confirmation
    for _ in range(30):
        res = soroban_server.get_transaction(resp.hash)
        if res.status == GetTransactionStatus.SUCCESS:
            return contract_id
        await asyncio.sleep(2)
        
    raise Exception("Deploy timed out")

async def invoke_contract_function(secret: str, contract_id: str, function_name: str, parameters: list) -> dict:
    """
    Invoke a Soroban contract function and wait for confirmation.
    """
    try:
        kp = Keypair.from_secret(secret)
        horizon_server = Server(HORIZON_URL)
        soroban_server = SorobanServer(SOROBAN_RPC_URL)
        
        account = horizon_server.load_account(kp.public_key)
        builder = TransactionBuilder(account, NETWORK_PASSPHRASE, base_fee=100_000)
        builder.append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name=function_name,
            parameters=parameters,
        )
        builder.set_timeout(300)
        tx = builder.build()
        
        sim = soroban_server.simulate_transaction(tx)
        if sim.error:
            return {"success": False, "error": f"Invocation simulation failed: {sim.error}"}
            
        tx = soroban_server.prepare_transaction(tx, sim)
        tx.sign(kp)
        
        resp = soroban_server.send_transaction(tx)
        if resp.status == SendTransactionStatus.ERROR:
             return {"success": False, "error": f"Invocation submit error: {resp.error_result_xdr}"}
             
        # Wait for confirmation
        for _ in range(30):
            res = soroban_server.get_transaction(resp.hash)
            if res.status == GetTransactionStatus.SUCCESS:
                return {"success": True, "hash": resp.hash}
            if res.status == GetTransactionStatus.FAILED:
                return {"success": False, "error": "Transaction failed on-chain"}
            await asyncio.sleep(2)
            
        return {"success": False, "error": "Invocation timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def sign_withdrawal(user_address: str, amount_shx: float, nonce: int) -> str:
    """
    Generate an Ed25519 signature for a withdrawal claim.
    Matches Soroban contract: [ContractAddress, User, Amount, Nonce]
    
    The contract appends the XDR of each element individually to a Bytes object.
    In Soroban:
    - Address.to_xdr(&env) produces an ScAddress (discriminant 0 for account, 1 for contract)
    - i128.to_xdr(&env) produces the 16 bytes representing the Int128Parts
    - u64.to_xdr(&env) produces the 8 bytes of the Uint64
    """
    kp = Keypair.from_secret(HOUSE_ACCOUNT_SECRET)
    amount_stroops = _to_stroops(amount_shx)
    
    # 1. Build the components matching the Soroban contract's ToXdr behavior
    # In Soroban: val.to_xdr(&env) on Address, i128, u64 produces the FULL SCVal XDR,
    # which includes a 4-byte discriminant tag at the beginning of each value.
    contract_addr_xdr = scval.to_address(SOROBAN_CONTRACT_ID).to_xdr_bytes()
    user_addr_xdr = scval.to_address(user_address).to_xdr_bytes()
    amount_xdr = scval.to_int128(amount_stroops).to_xdr_bytes()
    nonce_xdr = scval.to_uint64(nonce).to_xdr_bytes()
    
    data = contract_addr_xdr + user_addr_xdr + amount_xdr + nonce_xdr
    
    logger.debug(f"WITHDRAW SIGN | User: {user_address[:8]}... | Amt: {amount_stroops} | Nonce: {nonce}")
    logger.debug(f"WITHDRAW SIGN | Payload (hex): {data.hex()}")
    
    signature_bytes = kp.sign(data)
    return base64.b64encode(signature_bytes).decode('utf-8')


def get_house_pubkey_hex() -> str:
    """Return the raw 32-byte public key in hex format for contract setup."""
    kp = Keypair.from_public_key(HOUSE_ACCOUNT_PUBLIC)
    return kp.raw_public_key().hex()

def verify_link_signature_xdr(public_key: str, signature_xdr: str, expected_discord_id: str) -> tuple[bool, str]:
    """
    Verify a signed transaction XDR for wallet linking.
    Returns (success, error_message).
    """
    try:
        from stellar_sdk import TransactionEnvelope, Keypair
        logger.info(f"Verify Link | Starting verification for {public_key[:8]}...")
        
        # 1. Parse Transaction Envelope
        try:
            te = TransactionEnvelope.from_xdr(signature_xdr, NETWORK_PASSPHRASE)
        except Exception as parse_err:
            msg = f"XDR Parse Error: {parse_err}"
            logger.error(f"Verify Link | {msg}")
            return False, msg

        tx = te.transaction
        
        # 2. Verify source account (handle Muxed Addresses)
        tx_source_raw = tx.source
        # Normalize both keys to G-addresses for comparison
        try:
            source_key_g = Keypair.from_public_key(str(tx_source_raw.account_id if hasattr(tx_source_raw, "account_id") else tx_source_raw)).public_key
            provided_key_g = Keypair.from_public_key(public_key).public_key
        except Exception as key_err:
            msg = f"Key normalization error: {key_err}"
            logger.error(f"Verify Link | {msg}")
            return False, msg

        if source_key_g != provided_key_g:
            msg = f"Source mismatch: {source_key_g[:8]} != {provided_key_g[:8]}"
            logger.warning(f"Verify Link | {msg}")
            return False, msg
            
        # 3. Verify operations
        found_link_op = False
        operation_names = []
        for op_idx, op in enumerate(tx.operations):
            op_type = type(op).__name__
            op_name = getattr(op, "data_name", None)
            operation_names.append(f"{op_type}({op_name})" if op_name else op_type)
            
            if hasattr(op, "data_name") and op.data_name == "link_discord":
                if op.data_value is not None:
                    # Some JS SDKs send value as string, others as base64-encoded bytes in XDR
                    val = op.data_value.decode("utf-8", errors="ignore").strip("\x00")
                    if val == str(expected_discord_id):
                        found_link_op = True
                        break
                    else:
                        msg = f"Data value mismatch: '{val}' != '{expected_discord_id}'"
                        logger.warning(f"Verify Link | {msg}")
                        return False, msg
        
        if not found_link_op:
            msg = f"Required op 'link_discord' not found. Ops seen: {operation_names}"
            logger.warning(f"Verify Link | {msg}")
            return False, msg
            
        # 4. Verify Signature Math
        try:
            tx_hash = te.hash()
            kp = Keypair.from_public_key(provided_key_g)
            
            # Check all signatures in the envelope for a match
            is_signed_correctly = False
            for sig in te.signatures:
                try:
                    kp.verify(tx_hash, sig.signature)
                    is_signed_correctly = True
                    break
                except Exception:
                    continue
            
            if not is_signed_correctly:
                msg = "No valid signature found matching the provided public key for this transaction."
                logger.warning(f"Verify Link | {msg}")
                return False, msg
                
        except Exception as sig_err:
            msg = f"Signature verification failure: {sig_err}"
            logger.warning(f"Verify Link | {msg}")
            return False, msg

        logger.info(f"Verify Link | SUCCESS | {public_key[:8]} linked successfully.")
        return True, "Success"
    except Exception as e:
        msg = f"Verification logic error: {type(e).__name__}: {e}"
        logger.error(f"Verify Link | {msg}", exc_info=True)
        return False, msg


