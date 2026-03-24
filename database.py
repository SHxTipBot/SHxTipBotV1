"""
Neon Postgres database layer for the SHx Tip Bot.
Stores Discord ID → Stellar public key mappings, link tokens, and tip history.
"""

import asyncpg
import os
import time
import secrets
import logging
from typing import Any, List, Dict, Optional

from dotenv import load_dotenv

logger = logging.getLogger("shx_tip_bot.database")

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# ── Global Connection Pool Management ─────────────────────────────────────────

_pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    """Get or create a global persistent database connection pool."""
    global _pool
    if _pool is None:
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL environment variable is not set")
        try:
            _pool = await asyncpg.create_pool(url)
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
    """Initialize the database schema."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    discord_id TEXT PRIMARY KEY,
                    stellar_public_key TEXT,
                    internal_balance REAL DEFAULT 0.0,
                    memo_id INTEGER,
                    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
                    linked_at DOUBLE PRECISION,
                    updated_at DOUBLE PRECISION,
                    last_active TEXT,
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
                    total_amount DOUBLE PRECISION NOT NULL,
                    amount_per_claim DOUBLE PRECISION NOT NULL,
                    max_claims INTEGER NOT NULL,
                    claims_count INTEGER DEFAULT 0,
                    reason TEXT,
                    created_at DOUBLE PRECISION NOT NULL,
                    active INTEGER DEFAULT 1
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS airdrop_claims (
                    airdrop_id TEXT NOT NULL,
                    user_discord_id TEXT NOT NULL,
                    tx_hash TEXT,
                    created_at DOUBLE PRECISION NOT NULL,
                    PRIMARY KEY (airdrop_id, user_discord_id)
                )
            """)
    logger.info("Database initialized successfully.")
    
    # Migration: ensure internal_balance column exists (may be missing on older DBs)
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS internal_balance REAL DEFAULT 0.0
            """)
            await conn.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS memo_id BIGINT
            """)
            logger.info("Database migration check complete.")
        except Exception as e:
            logger.warning(f"Migration note: {e}")

# ── Helper for param conversion ───────────────────────────────────────────────

def _sql(query: str) -> str:
    """
    Helper to convert SQLite-style '?' placeholders to Postgres '$1', '$2', etc.
    """
    import re
    count = 0
    def repl(match):
        nonlocal count
        count += 1
        return f"${count}"
    return re.sub(r'\?', repl, query)

# ── Implementation Functions ──────────────────────────────────────────────────

async def create_link_token(discord_id: str, ttl_seconds: int = 900) -> str:
    """Create a unique link token for a Discord user. Expires in 15 minutes."""
    token = secrets.token_urlsafe(32)
    now = time.time()
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Invalidate existing unused tokens for this user
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
        logger.warning(f"Token validation failed: Token not found in database. Token: {token[:8]}...")
        return None
    
    if row["used"] == 1:
        logger.warning(f"Token validation failed: Token already used. Token: {token[:8]}...")
        return None
        
    if row["expires_at"] <= now:
        logger.warning(f"Token validation failed: Token expired. now={now}, expires_at={row['expires_at']}. Token: {token[:8]}...")
        return None
    
    return row["discord_id"]

async def mark_token_used(token: str):
    """Mark a link token as used."""
    pool = await get_pool()
    await pool.execute("UPDATE link_tokens SET used = 1 WHERE token = $1", token)

async def get_or_create_user(discord_id: str) -> Dict[str, Any]:
    """Get a user or create them (assigning a memo_id)."""
    pool = await get_pool()
    # Memo ID is just the numeric part of the Discord ID if possible, 
    # but Discord IDs can be 64-bit, and Stellar Memo ID is 64-bit.
    memo_id = int(discord_id)
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE discord_id = $1", discord_id)
        if not row:
            await conn.execute(
                "INSERT INTO users (discord_id, memo_id, internal_balance) VALUES ($1, $2, 0.0)",
                discord_id, memo_id
            )
            row = await conn.fetchrow("SELECT * FROM users WHERE discord_id = $1", discord_id)
        return dict(row)

async def link_user(discord_id: str, stellar_public_key: str, is_approved: bool = False):
    """Link a Discord user to a Stellar public key (upserts)."""
    now = time.time()
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO users (discord_id, stellar_public_key, is_approved, linked_at, updated_at, memo_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT(discord_id) DO UPDATE SET
                stellar_public_key = EXCLUDED.stellar_public_key,
                is_approved = EXCLUDED.is_approved,
                updated_at = EXCLUDED.updated_at""",
        discord_id, stellar_public_key, is_approved, now, now, int(discord_id)
    )
    logger.info(f"Linked Discord user {discord_id} to Stellar key {stellar_public_key[:8]}...")

async def get_internal_balance(discord_id: str) -> float:
    """Get the user's internal SHx balance (converted from stroops)."""
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
            # 1. Update balance
            await conn.execute(
                "UPDATE users SET internal_balance = internal_balance + $1 WHERE discord_id = $2",
                amount_shx, discord_id
            )
            # 2. Add deposit record
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
        # Simple atomicity check
        sender_bal = await conn.fetchval("SELECT internal_balance FROM users WHERE discord_id = $1", sender_id)
        if sender_bal is None or sender_bal < total_needed:
            return False
            
        async with conn.transaction():
            # Deduct from sender
            await conn.execute("UPDATE users SET internal_balance = internal_balance - $1 WHERE discord_id = $2", total_needed, sender_id)
            # Credit recipient
            await conn.execute("UPDATE users SET internal_balance = internal_balance + $1 WHERE discord_id = $2", amount_shx, recipient_id)
            # Record tip
            await conn.execute(
                """INSERT INTO internal_tips 
                   (sender_discord_id, recipient_discord_id, amount, fee, reason, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                sender_id, recipient_id, amount_shx, fee_shx, reason, time.time()
            )
        return True

async def get_user_link_details(discord_id: str) -> Optional[Dict[str, Any]]:
    """Get the link details (key and approval status) for a Discord user."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT stellar_public_key, is_approved FROM users WHERE discord_id = $1",
        discord_id
    )
    return dict(row) if row else None


async def get_user_stellar_key(discord_id: str) -> Optional[str]:
    """Get just the Stellar public key for a Discord user (legacy helper)."""
    details = await get_user_link_details(discord_id)
    return details["stellar_public_key"] if details else None

async def record_tip(
    sender_id: str,
    recipient_id: str,
    amount: float,
    fee: float,
    tx_hash: str,
    reason: Optional[str] = None,
):
    """Record a completed tip transaction."""
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO tip_history
            (sender_discord_id, recipient_discord_id, amount, fee, tx_hash, reason, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        sender_id, recipient_id, amount, fee, tx_hash, reason, time.time()
    )

async def get_user_tip_count_since(discord_id: str, since_timestamp: float) -> int:
    """Count tips a user has sent since a timestamp (for rate limiting)."""
    pool = await get_pool()
    count = await pool.fetchval(
        "SELECT COUNT(*) FROM tip_history WHERE sender_discord_id = $1 AND created_at > $2",
        discord_id, since_timestamp
    )
    return count or 0

async def create_airdrop(
    airdrop_id: str,
    creator_id: str,
    total_amount: float,
    amount_per_claim: float,
    max_claims: int,
    reason: Optional[str] = None,
):
    """Create a new airdrop entry."""
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO airdrops
            (id, creator_discord_id, total_amount, amount_per_claim, max_claims, reason, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        airdrop_id, creator_id, total_amount, amount_per_claim, max_claims, reason, time.time()
    )

async def get_airdrop(airdrop_id: str) -> Optional[Dict[str, Any]]:
    """Get airdrop details."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM airdrops WHERE id = $1 AND active = 1",
        airdrop_id
    )
    return dict(row) if row else None

async def has_user_claimed(airdrop_id: str, discord_id: str) -> bool:
    """Check if a user has already claimed from this airdrop."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT 1 FROM airdrop_claims WHERE airdrop_id = $1 AND user_discord_id = $2",
        airdrop_id, discord_id
    )
    return row is not None

async def add_airdrop_claim(airdrop_id: str, discord_id: str, tx_hash: str):
    """Record a claim and increment the claim count."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1. Record claim
            await conn.execute(
                "INSERT INTO airdrop_claims (airdrop_id, user_discord_id, tx_hash, created_at) VALUES ($1, $2, $3, $4)",
                airdrop_id, discord_id, tx_hash, time.time()
            )
            # 2. Increment count
            await conn.execute(
                "UPDATE airdrops SET claims_count = claims_count + 1 WHERE id = $1",
                airdrop_id
            )
            # 3. Deactivate if full
            await conn.execute(
                "UPDATE airdrops SET active = 0 WHERE id = $1 AND claims_count >= max_claims",
                airdrop_id
            )

async def unlink_user(discord_id: str):
    """Remove the Stellar link for a Discord user."""
    pool = await get_pool()
    await pool.execute("DELETE FROM users WHERE discord_id = $1", discord_id)
    logger.info(f"Unlinked Discord user {discord_id}")
