"""
Neon Postgres database layer for the SHx Tip Bot.
Stores Discord ID → Stellar public key mappings, link tokens, balances, and tip history.
"""

import asyncpg
import os
import time
import secrets
import logging
from typing import Any, List, Dict, Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from dotenv import load_dotenv

logger = logging.getLogger("shx_tip_bot.database")

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# ── Global Connection Pool Management ─────────────────────────────────────────

_pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    """Get or create a global persistent database connection pool.
       Uses statement_cache_size=0 to avoid stale schema cache errors.
       Sanitizes the URL to remove parameters unsupported by asyncpg (e.g. sslmode).
    """
    global _pool
    if _pool is None:
        raw_url = os.getenv("DATABASE_URL")
        if not raw_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        # ── Sanitize URL for asyncpg ──
        # asyncpg does not support 'sslmode', 'channel_binding', etc. in the connection string.
        requires_ssl = False
        try:
            parsed = urlparse(raw_url)
            query = parse_qs(parsed.query)
            
            if 'sslmode' in query and any('require' in v.lower() for v in query['sslmode']):
                requires_ssl = True
            
            # Remove unsupported fields
            unsupported = ['sslmode', 'channel_binding']
            for field in unsupported:
                query.pop(field, None)
            
            # Reconstruct the URL without unsupported fields
            new_query = urlencode(query, doseq=True)
            url = urlunparse(parsed._replace(query=new_query))
        except Exception as e:
            logger.warning(f"URL sanitization failed (using raw): {e}")
            url = raw_url
            if 'sslmode=require' in raw_url.lower():
                requires_ssl = True
                
        try:
            # statement_cache_size=0 prevents "cached statement plan is invalid" errors
            # after ALTER TABLE migrations run
            ssl_ctx = 'require' if requires_ssl else None
            _pool = await asyncpg.create_pool(url, statement_cache_size=0, ssl=ssl_ctx)
            logger.info("Database connection pool established.")
        except Exception as e:
            logger.error(f"Failed to establish database connection pool: {e}")
            raise
    return _pool

async def close_db():
    """Close the global database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed.")

async def init_db():
    """Initialize the database schema and run migrations."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Create tables if they don't exist
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                username TEXT,
                stellar_public_key TEXT,
                internal_balance REAL DEFAULT 0.0,
                memo_id BIGINT,
                is_approved BOOLEAN NOT NULL DEFAULT FALSE,
                linked_at DOUBLE PRECISION,
                updated_at DOUBLE PRECISION,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS link_tokens (
                token TEXT PRIMARY KEY,
                discord_id TEXT NOT NULL,
                created_at DOUBLE PRECISION NOT NULL,
                expires_at DOUBLE PRECISION NOT NULL,
                used INTEGER DEFAULT 0
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                tx_hash TEXT PRIMARY KEY,
                discord_id TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at DOUBLE PRECISION NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS internal_tips (
                id SERIAL PRIMARY KEY,
                sender_discord_id TEXT NOT NULL,
                recipient_discord_id TEXT NOT NULL,
                amount REAL NOT NULL,
                fee REAL NOT NULL,
                reason TEXT,
                created_at DOUBLE PRECISION NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS airdrops (
                id TEXT PRIMARY KEY,
                creator_discord_id TEXT NOT NULL,
                total_amount REAL NOT NULL,
                amount_per_claim REAL NOT NULL,
                max_claims INTEGER NOT NULL,
                claims_count INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                reason TEXT,
                created_at DOUBLE PRECISION NOT NULL,
                expires_at DOUBLE PRECISION,
                channel_id TEXT,
                message_id TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS airdrop_claims (
                id SERIAL PRIMARY KEY,
                airdrop_id TEXT NOT NULL,
                user_discord_id TEXT NOT NULL,
                tx_hash TEXT,
                created_at DOUBLE PRECISION NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id TEXT PRIMARY KEY,
                discord_id TEXT NOT NULL,
                stellar_address TEXT,
                amount REAL NOT NULL,
                nonce BIGINT NOT NULL,
                signature TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                tx_hash TEXT,
                created_at DOUBLE PRECISION NOT NULL,
                completed_at DOUBLE PRECISION
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS service_cursors (
                service_name TEXT PRIMARY KEY,
                cursor_val TEXT NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
    
    # Run migrations: comprehensively sanitize all legacy NOT NULL constraints for Tip.cc zero-friction architecture
    migration_queries = [
        "ALTER TABLE users ALTER COLUMN stellar_public_key DROP NOT NULL",
        "ALTER TABLE users ALTER COLUMN linked_at DROP NOT NULL",
        "ALTER TABLE users ALTER COLUMN updated_at DROP NOT NULL",
        "ALTER TABLE users ALTER COLUMN memo_id DROP NOT NULL",
        "ALTER TABLE users ALTER COLUMN internal_balance DROP NOT NULL",
        "ALTER TABLE internal_tips ALTER COLUMN tx_hash DROP NOT NULL",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS internal_balance REAL DEFAULT 0.0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS memo_id BIGINT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT",
        "ALTER TABLE airdrops ADD COLUMN IF NOT EXISTS expires_at DOUBLE PRECISION",
        "ALTER TABLE withdrawals ALTER COLUMN amount TYPE DOUBLE PRECISION",
        "ALTER TABLE internal_tips ALTER COLUMN amount TYPE DOUBLE PRECISION",
        "ALTER TABLE internal_tips ALTER COLUMN fee TYPE DOUBLE PRECISION",
        "ALTER TABLE deposits ALTER COLUMN amount TYPE DOUBLE PRECISION",
        "ALTER TABLE airdrops ALTER COLUMN total_amount TYPE DOUBLE PRECISION",
        "ALTER TABLE airdrops ALTER COLUMN amount_per_claim TYPE DOUBLE PRECISION",
        "ALTER TABLE users ALTER COLUMN internal_balance TYPE DOUBLE PRECISION"
    ]
    
    async with pool.acquire() as conn:
        for query in migration_queries:
            try:
                await conn.execute(query)
            except Exception as e:
                # If it's a 'column already exists' error, it's safe to ignore.
                # Otherwise, log it as a warning.
                if "already exists" in str(e).lower():
                    logger.debug(f"Migration note (safe to ignore): {e}")
                else:
                    logger.warning(f"Migration query failed: {query} -> {e}")

    logger.info("Database initialized successfully.")


# ── Cursor Management (for Deposit Monitor) ───────────────────────────────────

async def get_cursor(service_name: str) -> str | None:
    """Get the last saved paging token for a service."""
    try:
        pool = await get_pool()
        row = await pool.fetchrow("SELECT cursor_val FROM service_cursors WHERE service_name = $1", service_name)
        return row["cursor_val"] if row else None
    except Exception as e:
        logger.error(f"get_cursor error: {e}")
        return None

async def save_cursor(service_name: str, cursor_val: str):
    """Persist a paging token for a service."""
    try:
        pool = await get_pool()
        await pool.execute(
            """
            INSERT INTO service_cursors (service_name, cursor_val, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (service_name) DO UPDATE SET cursor_val = $2, updated_at = NOW()
            """,
            service_name, cursor_val
        )
    except Exception as e:
        logger.error(f"save_cursor error: {e}")


# ── Implementation Functions ──────────────────────────────────────────────────

async def create_link_token(discord_id: str, ttl_seconds: int = 900) -> str:
    """Create a unique link token for a Discord user. Expires in 15 minutes."""
    token = secrets.token_urlsafe(32)
    now = time.time()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE link_tokens SET used = 1 WHERE discord_id = $1 AND used = 0",
            discord_id
        )
        await conn.execute(
            "INSERT INTO link_tokens (token, discord_id, created_at, expires_at) VALUES ($1, $2, $3, $4)",
            token, discord_id, now, now + ttl_seconds
        )
    return token

async def validate_link_token(token: str) -> Optional[str]:
    """Validate a link token. Returns discord_id if valid, None otherwise."""
    now = time.time()
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT discord_id, expires_at, used FROM link_tokens WHERE token = $1",
        token
    )
    if not row:
        return None
    if row["expires_at"] <= now:
        return None
    return row["discord_id"]

async def mark_token_used(token: str):
    """Mark a link token as used."""
    pool = await get_pool()
    await pool.execute("UPDATE link_tokens SET used = 1 WHERE token = $1", token)

async def get_or_create_user(discord_id: str, username: Optional[str] = None) -> Dict[str, Any]:
    """Get a user or create them (assigning a memo_id). Updates username if provided."""
    pool = await get_pool()
    memo_id = int(discord_id)
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE discord_id = $1", discord_id)
        if not row:
            await conn.execute(
                "INSERT INTO users (discord_id, username, memo_id, internal_balance) VALUES ($1, $2, $3, 0.0)",
                discord_id, username, memo_id
            )
            row = await conn.fetchrow("SELECT * FROM users WHERE discord_id = $1", discord_id)
        elif username:
            await conn.execute("UPDATE users SET username = $1 WHERE discord_id = $2", username, discord_id)
            row = dict(row)
            row["username"] = username
        return dict(row)

async def link_user(discord_id: str, stellar_public_key: str, is_approved: bool = False, username: Optional[str] = None):
    """Link a Discord user to a Stellar public key (upserts). Updates username if provided."""
    now = time.time()
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO users (discord_id, stellar_public_key, is_approved, linked_at, updated_at, memo_id, username)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT(discord_id) DO UPDATE SET
                stellar_public_key = EXCLUDED.stellar_public_key,
                is_approved = EXCLUDED.is_approved,
                updated_at = EXCLUDED.updated_at,
                username = COALESCE(EXCLUDED.username, users.username)""",
        discord_id, stellar_public_key, is_approved, now, now, int(discord_id), username
    )
    logger.info(f"Linked Discord user {username or discord_id} to Stellar key {stellar_public_key[:8]}...")

async def unlink_user(discord_id: str):
    """Unlink a Stellar public key from a Discord user."""
    now = time.time()
    pool = await get_pool()
    await pool.execute(
        "UPDATE users SET stellar_public_key = NULL, is_approved = FALSE, updated_at = $1 WHERE discord_id = $2",
        now, discord_id
    )
    logger.info(f"Unlinked Discord user {discord_id}")

async def get_internal_balance(discord_id: str) -> float:
    """Get the user's internal SHx balance."""
    pool = await get_pool()
    val = await pool.fetchval("SELECT internal_balance FROM users WHERE discord_id = $1", discord_id)
    if val is None:
        return 0.0
    return float(val)

async def add_deposit(discord_id: str, tx_hash: str, amount_shx: float):
    """Credit internal balance from an on-chain deposit (amount in SHx)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE users SET internal_balance = internal_balance + $1 WHERE discord_id = $2",
                amount_shx, discord_id
            )
            await conn.execute(
                "INSERT INTO deposits (tx_hash, discord_id, amount, created_at) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                tx_hash, discord_id, amount_shx, time.time()
            )
            logger.info(f"Credited {amount_shx} SHx to user {discord_id} for tx {tx_hash}")

async def transfer_internal(sender_id: str, recipient_id: str, amount_shx: float, fee_shx: float, reason: Optional[str] = None) -> bool:
    """Move SHx internally between users. Returns True if successful."""
    total_needed = amount_shx + fee_shx
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Atomic update: only decrement if balance is sufficient
            res = await conn.execute(
                "UPDATE users SET internal_balance = internal_balance - $1 WHERE discord_id = $2 AND internal_balance >= $1",
                total_needed, sender_id
            )
            
            # Check if any row was actually updated
            if res == "UPDATE 0":
                return False
                
            # Ensure recipient exists
            try:
                memo = int(recipient_id)
            except ValueError:
                memo = 0 # System accounts don't need a real memo mapping
                
            await conn.execute(
                "INSERT INTO users (discord_id, memo_id, internal_balance) VALUES ($1, $2, 0.0) ON CONFLICT DO NOTHING",
                recipient_id, memo
            )
            
            # Increment recipient balance
            await conn.execute("UPDATE users SET internal_balance = internal_balance + $1 WHERE discord_id = $2", amount_shx, recipient_id)
            
            # Record tip history
            await conn.execute(
                """INSERT INTO internal_tips 
                   (sender_discord_id, recipient_discord_id, amount, fee, reason, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                sender_id, recipient_id, amount_shx, fee_shx, reason, time.time()
            )
        return True

async def get_user_stellar_key(discord_id: str) -> Optional[str]:
    """Get the Stellar public key for a Discord user."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT stellar_public_key FROM users WHERE discord_id = $1",
        discord_id
    )
    return row["stellar_public_key"] if row else None

async def get_user_link_details(discord_id: str) -> Optional[Dict[str, Any]]:
    """Get the link details (key and approval status) for a Discord user."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT stellar_public_key, is_approved FROM users WHERE discord_id = $1",
        discord_id
    )
    return dict(row) if row else None

async def create_airdrop(
    airdrop_id: str,
    creator_id: str,
    total_amount: float,
    reason: Optional[str] = None,
    duration_minutes: Optional[int] = None
):
    """Create a new airdrop entry for the Equal Split model."""
    pool = await get_pool()
    now = time.time()
    expires_at = now + (duration_minutes * 60) if duration_minutes else now + (24 * 60 * 60) # Default 24h
    await pool.execute(
        """INSERT INTO airdrops
            (id, creator_discord_id, total_amount, amount_per_claim, max_claims, reason, created_at, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        airdrop_id, creator_id, total_amount, 0.0, 0, reason, now, expires_at
    )
    
async def update_airdrop_message(airdrop_id: str, channel_id: str, message_id: str):
    pool = await get_pool()
    await pool.execute(
        "UPDATE airdrops SET channel_id = $1, message_id = $2 WHERE id = $3",
        channel_id, message_id, airdrop_id
    )

async def get_airdrop(airdrop_id: str) -> Optional[Dict[str, Any]]:
    """Get active airdrop details, bypassing if expired."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM airdrops WHERE id = $1 AND active = 1",
        airdrop_id
    )
    if row:
        expires_at = row.get("expires_at")
        if expires_at and time.time() > expires_at:
            return None
        return dict(row)
    return None

async def get_airdrop_by_message(message_id: str) -> Optional[dict]:
    """Retrieve an active airdrop by its tied message ID."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM airdrops WHERE message_id = $1 AND active = 1",
        message_id
    )
    if row:
        expires_at = row.get("expires_at")
        if expires_at and time.time() > expires_at:
            return None
        return dict(row)
    return None

async def has_user_claimed(airdrop_id: str, discord_id: str) -> bool:
    """Check if a user has already claimed from this airdrop."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT 1 FROM airdrop_claims WHERE airdrop_id = $1 AND user_discord_id = $2",
        airdrop_id, discord_id
    )
    return row is not None

async def add_airdrop_claim(airdrop_id: str, discord_id: str):
    """Record an internal claim and update counts."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO airdrop_claims (airdrop_id, user_discord_id, tx_hash, created_at) VALUES ($1, $2, $3, $4)",
                airdrop_id, discord_id, "internal_custodial", time.time()
            )
            await conn.execute(
                "UPDATE airdrops SET claims_count = claims_count + 1 WHERE id = $1",
                airdrop_id
            )

async def get_expired_airdrops() -> List[Dict[str, Any]]:
    """Retrieve all active airdrops that have surpassed their expires_at time."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT * FROM airdrops WHERE active = 1 AND expires_at < $1",
        time.time()
    )
    return [dict(r) for r in rows]

async def get_airdrop_participants(airdrop_id: str) -> List[str]:
    """Get unique Discord IDs of users who clicked claim for this airdrop."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT DISTINCT user_discord_id FROM airdrop_claims WHERE airdrop_id = $1",
        airdrop_id
    )
    return [r["user_discord_id"] for r in rows]

async def close_airdrop(airdrop_id: str):
    """Mark an airdrop as inactive."""
    pool = await get_pool()
    await pool.execute("UPDATE airdrops SET active = 0 WHERE id = $1", airdrop_id)

async def admin_fund_internal(discord_id: str, amount_shx: float):
    """Admin function to literally mint/fund SHx into a user's internal balance, no on-chain tx required."""
    pool = await get_pool()
    await pool.execute(
        "UPDATE users SET internal_balance = internal_balance + $1 WHERE discord_id = $2",
        amount_shx, discord_id
    )

async def create_withdrawal(
    withdrawal_id: str,
    discord_id: str,
    stellar_address: str,
    amount: float,
    nonce: int,
    signature: str,
    expires_at: int
):
    """Create a pending withdrawal entry."""
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO withdrawals 
            (id, discord_id, stellar_address, amount, nonce, signature, created_at, expires_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        withdrawal_id, discord_id, stellar_address, amount, nonce, signature, time.time(), expires_at
    )

async def get_withdrawal(withdrawal_id: str) -> Optional[Dict[str, Any]]:
    """Get withdrawal details."""
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM withdrawals WHERE id = $1", withdrawal_id)
    return dict(row) if row else None

async def complete_withdrawal(withdrawal_id: str, tx_hash: str):
    """Mark a withdrawal as completed."""
    pool = await get_pool()
    await pool.execute(
        "UPDATE withdrawals SET status = 'COMPLETED', tx_hash = $1, completed_at = $2 WHERE id = $3",
        tx_hash, time.time(), withdrawal_id
    )

async def cancel_withdrawal(withdrawal_id: str) -> bool:
    """
    Cancel a pending withdrawal and refund the SHx back to the user's internal balance.
    Returns True if successfully cancelled, False if not pending or not found.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1. Check current status and get details
            row = await conn.fetchrow(
                "SELECT discord_id, amount, status FROM withdrawals WHERE id = $1", 
                withdrawal_id
            )
            if not row or row["status"] != "PENDING":
                return False
                
            discord_id = row["discord_id"]
            amount = row["amount"]
            
            # 2. Update status to CANCELLED
            await conn.execute(
                "UPDATE withdrawals SET status = 'CANCELLED', completed_at = $2 WHERE id = $1",
                withdrawal_id, time.time()
            )
            
            # 3. Credit the user back (Refund)
            # Use f"CANCEL_{withdrawal_id}" as the tx_hash for tracking
            await conn.execute(
                "UPDATE users SET internal_balance = internal_balance + $1 WHERE discord_id = $2",
                amount, discord_id
            )
            await conn.execute(
                "INSERT INTO deposits (tx_hash, discord_id, amount, created_at) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                f"CANCEL_{withdrawal_id}", discord_id, amount, time.time()
            )
            
            logger.info(f"WITHDRAWAL CANCELLED | ID: {withdrawal_id} | Refunding {amount} SHx to {discord_id}")
            return True

async def get_latest_pending_withdrawal(discord_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent pending withdrawal for a user."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM withdrawals WHERE discord_id = $1 AND status = 'PENDING' ORDER BY created_at DESC LIMIT 1",
        discord_id
    )
    return dict(row) if row else None

async def get_pending_withdrawals(discord_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get all pending withdrawals for a user (up to the specified limit)."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT * FROM withdrawals WHERE discord_id = $1 AND status = 'PENDING' ORDER BY created_at DESC LIMIT $2",
        discord_id, limit
    )
    return [dict(r) for r in rows]

