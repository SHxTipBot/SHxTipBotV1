"""
SQLite database layer for the SHx Tip Bot.
Stores Discord ID → Stellar public key mappings, link tokens, and tip history.
"""

import aiosqlite
import os
import time
import secrets
import logging

logger = logging.getLogger("shx_tip_bot.database")

DB_PATH = os.getenv("DB_PATH", "shx_tip_bot.db")


async def init_db():
    """Initialize the database schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                stellar_public_key TEXT NOT NULL,
                linked_at REAL NOT NULL,
                updated_at REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS link_tokens (
                token TEXT PRIMARY KEY,
                discord_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                used INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tip_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_discord_id TEXT NOT NULL,
                recipient_discord_id TEXT NOT NULL,
                amount REAL NOT NULL,
                fee REAL NOT NULL,
                tx_hash TEXT,
                reason TEXT,
                created_at REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS airdrops (
                id TEXT PRIMARY KEY,
                creator_discord_id TEXT NOT NULL,
                total_amount REAL NOT NULL,
                amount_per_claim REAL NOT NULL,
                max_claims INTEGER NOT NULL,
                claims_count INTEGER DEFAULT 0,
                reason TEXT,
                created_at REAL NOT NULL,
                active INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS airdrop_claims (
                airdrop_id TEXT NOT NULL,
                user_discord_id TEXT NOT NULL,
                tx_hash TEXT,
                created_at REAL NOT NULL,
                PRIMARY KEY (airdrop_id, user_discord_id)
            )
        """)
        await db.commit()
    logger.info("Database initialized successfully.")


async def create_link_token(discord_id: str, ttl_seconds: int = 900) -> str:
    """Create a unique link token for a Discord user. Expires in 15 minutes."""
    token = secrets.token_urlsafe(32)
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        # Invalidate existing unused tokens for this user
        await db.execute(
            "UPDATE link_tokens SET used = 1 WHERE discord_id = ? AND used = 0",
            (discord_id,),
        )
        await db.execute(
            "INSERT INTO link_tokens (token, discord_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, discord_id, now, now + ttl_seconds),
        )
        await db.commit()
    return token


async def validate_link_token(token: str) -> str | None:
    """Validate a link token. Returns discord_id if valid, None otherwise."""
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT discord_id FROM link_tokens WHERE token = ? AND used = 0 AND expires_at > ?",
            (token, now),
        )
        row = await cursor.fetchone()
        if row:
            return row["discord_id"]
    return None


async def mark_token_used(token: str):
    """Mark a link token as used."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE link_tokens SET used = 1 WHERE token = ?", (token,))
        await db.commit()


async def link_user(discord_id: str, stellar_public_key: str):
    """Link a Discord user to a Stellar public key (upserts)."""
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (discord_id, stellar_public_key, linked_at)
               VALUES (?, ?, ?)
               ON CONFLICT(discord_id) DO UPDATE SET
                   stellar_public_key = excluded.stellar_public_key,
                   updated_at = ?""",
            (discord_id, stellar_public_key, now, now),
        )
        await db.commit()
    logger.info(f"Linked Discord user {discord_id} to Stellar key {stellar_public_key[:8]}...")


async def get_user_stellar_key(discord_id: str) -> str | None:
    """Get the Stellar public key for a Discord user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT stellar_public_key FROM users WHERE discord_id = ?",
            (discord_id,),
        )
        row = await cursor.fetchone()
        if row:
            return row["stellar_public_key"]
    return None


async def record_tip(
    sender_id: str,
    recipient_id: str,
    amount: float,
    fee: float,
    tx_hash: str,
    reason: str = None,
):
    """Record a completed tip transaction."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO tip_history
                (sender_discord_id, recipient_discord_id, amount, fee, tx_hash, reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sender_id, recipient_id, amount, fee, tx_hash, reason, time.time()),
        )
        await db.commit()


async def get_user_tip_count_since(discord_id: str, since_timestamp: float) -> int:
    """Count tips a user has sent since a timestamp (for rate limiting)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM tip_history WHERE sender_discord_id = ? AND created_at > ?",
            (discord_id, since_timestamp),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0
# ── Airdrops ─────────────────────────────────────────────────────────────────

async def create_airdrop(
    airdrop_id: str,
    creator_id: str,
    total_amount: float,
    amount_per_claim: float,
    max_claims: int,
    reason: str = None,
):
    """Create a new airdrop entry."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO airdrops
                (id, creator_discord_id, total_amount, amount_per_claim, max_claims, reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (airdrop_id, creator_id, total_amount, amount_per_claim, max_claims, reason, time.time()),
        )
        await db.commit()


async def get_airdrop(airdrop_id: str) -> dict | None:
    """Get airdrop details."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM airdrops WHERE id = ? AND active = 1",
            (airdrop_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def has_user_claimed(airdrop_id: str, discord_id: str) -> bool:
    """Check if a user has already claimed from this airdrop."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM airdrop_claims WHERE airdrop_id = ? AND user_discord_id = ?",
            (airdrop_id, discord_id),
        )
        return await cursor.fetchone() is not None


async def add_airdrop_claim(airdrop_id: str, discord_id: str, tx_hash: str):
    """Record a claim and increment the claim count."""
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Record claim
        await db.execute(
            "INSERT INTO airdrop_claims (airdrop_id, user_discord_id, tx_hash, created_at) VALUES (?, ?, ?, ?)",
            (airdrop_id, discord_id, tx_hash, time.time()),
        )
        # 2. Increment count
        await db.execute(
            "UPDATE airdrops SET claims_count = claims_count + 1 WHERE id = ?",
            (airdrop_id,),
        )
        # 3. Deactivate if full
        await db.execute(
            "UPDATE airdrops SET active = 0 WHERE id = ? AND claims_count >= max_claims",
            (airdrop_id,),
        )
        await db.commit()
