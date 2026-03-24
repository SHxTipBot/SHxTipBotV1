"""
SHx Tip Bot — Discord Bot
Simple custodial tipping bot for SHx on the Stellar network.
Commands: /link, /balance, /deposit, /withdraw, /tip
"""

import os
import sys
import time
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
import discord
from discord import app_commands, Interaction
from discord.ext import commands
import secrets

import database as db
import stellar_utils as stellar

# ── Load Environment ──────────────────────────────────────────────────────────
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:8080")
ADMIN_DISCORD_IDS = [
    x.strip() for x in os.getenv("ADMIN_DISCORD_IDS", "").split(",") if x.strip()
]
LOG_FILE = os.getenv("LOG_FILE", "shx_tip_bot.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Logging ───────────────────────────────────────────────────────────────────
logger = logging.getLogger("shx_tip_bot")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

_fmt = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
_fh = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
_fh.setFormatter(_fmt)
_ch = logging.StreamHandler(sys.stdout)
_ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(_fh)
logger.addHandler(_ch)

# ── Discord Bot Setup ─────────────────────────────────────────────────────────
intents = discord.Intents.default()
try:
    intents.members = True
except Exception:
    pass
bot = commands.Bot(command_prefix="!", intents=intents)
guild_obj = discord.Object(id=DISCORD_GUILD_ID)

EMBED_COLOR = 0x00C9FF
ERROR_COLOR = 0xFF4C4C
SUCCESS_COLOR = 0x00FF88

# ── Helpers ───────────────────────────────────────────────────────────────────

def _footer(embed: discord.Embed) -> discord.Embed:
    embed.set_footer(text="SHx Tip Bot • Stronghold Community")
    return embed


# ── Events ────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    logger.info(f"Bot online as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Guild: {DISCORD_GUILD_ID} | Network: {stellar.STELLAR_NETWORK}")
    
    # Initialize DB and HTTP session
    await db.init_db()
    await stellar.get_session()
    
    try:
        # Clear ALL old guild commands, then re-sync only what's defined
        bot.tree.clear_commands(guild=guild_obj)
        bot.tree.copy_global_to(guild=guild_obj)
        synced = await bot.tree.sync(guild=guild_obj)
        logger.info(f"Synced {len(synced)} slash commands (old commands cleared).")
    except Exception as e:
        logger.error(f"Command sync failed: {e}", exc_info=True)
    
    # Start background tasks
    bot.loop.create_task(heartbeat())
    bot.loop.create_task(start_deposit_monitor())

async def start_deposit_monitor():
    """Starts the Stellar deposit polling monitor."""
    async def handle_deposit(memo_val: str, tx_hash: str, amount_shx: float, memo_type: str):
        try:
            target_discord_id = None
            
            # Case A: Numeric Memo ID (Standard Custodial)
            if memo_type == "id":
                target_discord_id = str(memo_val)
            
            # Case B: Text Memo (Moderator Funding)
            elif memo_type == "text" and memo_val:
                import re
                id_match = re.search(r'(\d{17,20})', str(memo_val))
                if id_match:
                    target_discord_id = id_match.group(1)
                else:
                    logger.warning(f"DEPOSIT | Could not parse target user from text memo: '{memo_val}'")

            if not target_discord_id:
                logger.warning(f"DEPOSIT | Ignored tx {tx_hash} | No valid target user in memo ({memo_type}: {memo_val})")
                return

            # Credit the user
            await db.add_deposit(target_discord_id, tx_hash, amount_shx)
            
            # Notify user
            user = bot.get_user(int(target_discord_id))
            if user:
                embed = _footer(discord.Embed(
                    title="💰 Deposit Confirmed",
                    description=f"Your account has been credited with **{amount_shx:,.2f} SHx**.",
                    color=SUCCESS_COLOR
                ))
                embed.add_field(name="Transaction", value=f"[View]({stellar.get_explorer_url(tx_hash)})")
                try:
                    await user.send(embed=embed)
                except:
                    pass
        except Exception as e:
            logger.error(f"Error processing deposit {tx_hash}: {e}")

    await stellar.stream_deposits(cursor="now", callback=handle_deposit)

async def heartbeat():
    """Background task to log bot health every 15 minutes."""
    while True:
        try:
            logger.info(f"HEARTBEAT | Bot Healthy | Latency: {bot.latency*1000:.2f}ms")
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
        await asyncio.sleep(900)

# Cleanup on shutdown
_original_close = bot.close
async def patched_close():
    logger.info("Closing bot and cleaning up resources...")
    await stellar.close_session()
    await db.close_db()
    await _original_close()
bot.close = patched_close


# ── /link ─────────────────────────────────────────────────────────────────────

@bot.tree.command(name="link", description="Verify your wallet for SHx withdrawals")
async def link_command(interaction: Interaction):
    logger.info(f"COMMAND | /link | User: {interaction.user} ({interaction.user.id})")
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)

    user_data = await db.get_or_create_user(discord_id)
    existing = user_data.get("stellar_public_key")
    
    relink_note = ""
    if existing:
        relink_note = (
            f"\n\n⚠️ You are verified with `{existing[:8]}...{existing[-8:]}`. "
            "Re-linking will update your verified withdrawal address."
        )

    token = await db.create_link_token(discord_id)
    link_url = f"{WEB_BASE_URL}/register?token={token}"

    embed = _footer(discord.Embed(
        title="🔗 Verify Your Stellar Wallet",
        description=(
            "To withdraw your tips, you must verify your Stellar address.\n\n"
            f"**[→ Click here to Verify]({link_url})**\n\n"
            "⏰ Verification link expires in **15 minutes**.{relink}"
        ).replace("{relink}", relink_note),
        color=EMBED_COLOR,
    ))

    await interaction.followup.send(embed=embed, ephemeral=True)


# ── /balance ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="balance", description="Check your internal SHx tip balance")
async def balance_command(interaction: Interaction):
    logger.info(f"COMMAND | /balance | User: {interaction.user} ({interaction.user.id})")
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)
    
    try:
        await db.get_or_create_user(discord_id)
        balance = await db.get_internal_balance(discord_id)

        embed = _footer(discord.Embed(title="💰 Your SHx Tip Balance", color=EMBED_COLOR))
        embed.add_field(name="Available Balance", value=f"**{balance:,.2f} SHx**", inline=False)
        embed.add_field(
            name="Tip others",
            value="Use `/tip @user amount` to send SHx to other members instantly.",
            inline=False,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"Balance command error: {e}", exc_info=True)
        await interaction.followup.send("❌ Failed to fetch balance. Please try again.", ephemeral=True)


# ── /deposit ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="deposit", description="Show your SHx deposit address and unique Memo ID")
async def deposit_command(interaction: Interaction):
    logger.info(f"COMMAND | /deposit | User: {interaction.user} ({interaction.user.id})")
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)
    
    user_data = await db.get_or_create_user(discord_id)
    memo_id = user_data["memo_id"]
    
    embed = _footer(discord.Embed(
        title="📥 Deposit SHx",
        description=(
            "To add SHx to your tipping balance, send SHx to the bot's house address "
            "with your **Unique Memo ID**."
        ),
        color=EMBED_COLOR
    ))
    
    embed.add_field(name="Bot Deposit Address", value=f"`{stellar.HOUSE_ACCOUNT_PUBLIC}`", inline=False)
    embed.add_field(name="Required Memo ID", value=f"`{memo_id}`", inline=False)
    embed.add_field(name="Asset", value=f"SHX (Issuer: `{stellar.SHX_ISSUER[:8]}...`)", inline=False)
    
    embed.set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={stellar.HOUSE_ACCOUNT_PUBLIC}")
    
    note = (
        "⚠️ **IMPORTANT**: You MUST include the Memo ID or your deposit will be lost. "
        "Funds are usually credited within 10-30 seconds after confirmation."
    )
    await interaction.followup.send(content=note, embed=embed, ephemeral=True)


# ── /withdraw ─────────────────────────────────────────────────────────────────

@bot.tree.command(name="withdraw", description="Withdraw SHx from your tipping balance to an external wallet")
@app_commands.describe(amount="Amount of SHx to withdraw", destination="Stellar address (G...)")
async def withdraw_command(interaction: Interaction, amount: float, destination: str):
    logger.info(f"COMMAND | /withdraw | User: {interaction.user} ({interaction.user.id}) | Amount: {amount}")
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)
    
    # Validation
    if amount <= 0:
        await interaction.followup.send("❌ Amount must be greater than 0.", ephemeral=True)
        return
        
    if not destination.startswith("G") or len(destination) != 56:
        await interaction.followup.send("❌ Invalid Stellar address.", ephemeral=True)
        return

    # Check internal balance
    current_bal = await db.get_internal_balance(discord_id)
    if amount > current_bal:
        await interaction.followup.send(f"❌ Insufficient balance. You have **{current_bal:,.2f} SHx**.", ephemeral=True)
        return

    # Process withdrawal
    await interaction.followup.send(f"⏳ Processing withdrawal of **{amount:,.2f} SHx**...", ephemeral=True)
    
    withdrawal_memo = f"Withdrawal ({interaction.user.name})"
    result = await stellar.send_withdrawal(destination, amount, memo=withdrawal_memo)
    
    if result["success"]:
        await db.add_deposit(discord_id, result["hash"], -amount)
        
        embed = _footer(discord.Embed(
            title="✅ Withdrawal Successful",
            description=f"Sent **{amount:,.2f} SHx** to `{destination[:8]}...`",
            color=SUCCESS_COLOR
        ))
        embed.add_field(name="Transaction", value=f"[View]({stellar.get_explorer_url(result['hash'])})")
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(f"❌ Withdrawal failed: {result['error']}", ephemeral=True)


# ── /tip ──────────────────────────────────────────────────────────────────────

@bot.tree.command(name="tip", description="Tip another user with SHx")
@app_commands.describe(
    user="The user to tip",
    amount="Amount of SHx to send",
    reason="Optional reason for the tip",
)
async def tip_command(
    interaction: Interaction,
    user: discord.Member,
    amount: float,
    reason: str = None,
):
    logger.info(f"COMMAND | /tip | From: {interaction.user} To: {user} | Amount: {amount}")
    await interaction.response.defer()
    sender_id = str(interaction.user.id)
    recipient_id = str(user.id)
    is_admin = sender_id in ADMIN_DISCORD_IDS

    # Validation
    if user.bot:
        await interaction.followup.send("❌ Cannot tip bots.", ephemeral=True)
        return
    if sender_id == recipient_id:
        await interaction.followup.send("❌ Cannot tip yourself.", ephemeral=True)
        return
    if amount <= 0:
        await interaction.followup.send("❌ Amount must be greater than 0.", ephemeral=True)
        return

    # ── CASE 1: Admin Reward (On-Chain) ───────────────────────────────────
    if is_admin:
        recipient_key = await db.get_user_stellar_key(recipient_id)
        if not recipient_key:
            await interaction.followup.send(f"❌ {user.mention} hasn't linked a wallet yet.", ephemeral=True)
            return
            
        if not await stellar.check_shx_trustline(recipient_key):
            await interaction.followup.send(f"❌ {user.mention} lacks an SHx trustline.", ephemeral=True)
            return

        memo_text = reason if reason else f"Tip from {interaction.user.name}"
        if len(memo_text) > 28: memo_text = memo_text[:25] + "..."

        result = await stellar.execute_tip(stellar.HOUSE_ACCOUNT_PUBLIC, recipient_key, amount, 0.0, memo=memo_text)
        
        if result["success"]:
            embed = _footer(discord.Embed(title="🎁 Reward Sent!", color=SUCCESS_COLOR))
            embed.add_field(name="From", value=interaction.user.mention, inline=True)
            embed.add_field(name="To", value=user.mention, inline=True)
            embed.add_field(name="Amount", value=f"**{amount:,.2f} SHx**", inline=True)
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Transaction", value=f"[View]({result['tx_url']})")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ On-chain reward failed: {result['error']}", ephemeral=True)
        return

    # ── CASE 2: User Tip (Internal Transfer) ─────────────────────────────
    fee_shx = 1.0 
    total_needed = amount + fee_shx

    success = await db.transfer_internal(sender_id, recipient_id, amount, fee_shx, reason)

    if success:
        embed = _footer(discord.Embed(title="✅ Tip Sent!", color=SUCCESS_COLOR))
        embed.add_field(name="From", value=interaction.user.mention, inline=True)
        embed.add_field(name="To", value=user.mention, inline=True)
        embed.add_field(name="Amount", value=f"**{amount:,.2f} SHx**", inline=True)
        embed.add_field(name="Fee", value=f"{fee_shx:,.2f} SHx", inline=True)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        
        await interaction.followup.send(embed=embed)
        logger.info(f"INTERNAL TIP OK | {sender_id}→{recipient_id} | {amount} SHx")
    else:
        current_bal = await db.get_internal_balance(sender_id)
        await interaction.followup.send(
            f"❌ Transaction failed. Check your balance (`/balance`).\n"
            f"Need: **{total_needed:,.2f} SHx** (Includes {fee_shx} fee)\n"
            f"Have: **{current_bal:,.2f} SHx**",
            ephemeral=True
        )


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_TOKEN not set. Check your .env file.")
        sys.exit(1)
    if not DISCORD_GUILD_ID:
        print("ERROR: DISCORD_GUILD_ID not set. Check your .env file.")
        sys.exit(1)
    bot.run(DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
