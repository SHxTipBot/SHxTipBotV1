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
from typing import Optional

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

def _footer(embed: discord.Embed) -> discord.Embed:
    embed.set_footer(text="SHx Tip Bot • Stronghold Community")
    return embed

class AirdropView(discord.ui.View):
    def __init__(self, airdrop_id: str):
        super().__init__(timeout=None)
        self.airdrop_id = airdrop_id

    @discord.ui.button(label="Claim SHx", style=discord.ButtonStyle.green, custom_id="claim_airdrop_btn")
    async def claim_button(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        
        ad = await db.get_airdrop(self.airdrop_id)
        if not ad:
            await interaction.followup.send("❌ This airdrop is no longer active or fully claimed.", ephemeral=True)
            return
            
        if await db.has_user_claimed(self.airdrop_id, user_id):
            await interaction.followup.send("❌ You have already claimed this airdrop.", ephemeral=True)
            return
            
        creator_id = ad["creator_discord_id"]
        amount = ad["amount_per_claim"]
        
        await db.get_or_create_user(user_id)
        
        success = await db.transfer_internal(creator_id, user_id, amount, 0.0, f"Airdrop {self.airdrop_id}")
        if success:
            await db.add_airdrop_claim(self.airdrop_id, user_id)
            await interaction.followup.send(f"✅ Successfully claimed **{amount:,.2f} SHx**! Check `/balance`.", ephemeral=True)
        else:
            await interaction.followup.send("❌ The airdrop creator's balance is too low to fulfill this claim.", ephemeral=True)



async def parse_amount(input_str: str) -> float | None:
    """Parse a string to an SHx float. Handles raw SHx or fiat ($ USD)."""
    input_str = str(input_str).strip().lower()
    is_usd = input_str.startswith('$') or input_str.endswith('usd')
    clean_str = input_str.replace('$', '').replace('usd', '').replace(',', '').strip()
    try:
        val = float(clean_str)
        if val <= 0: return None
        if is_usd:
            usd_price = await stellar.get_shx_usd_price()
            if not usd_price or usd_price <= 0: return None
            return val / usd_price
        return val
    except ValueError:
        return None

# ══════════════════════════════════════════════════════════════════════════════
# COMMANDS — define ALL 5 commands BEFORE on_ready so they exist in the tree
# ══════════════════════════════════════════════════════════════════════════════


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
            f"⏰ Verification link expires in **15 minutes**.{relink_note}"
        ),
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
        await interaction.followup.send("❌ Failed to fetch balance. Please try again later.", ephemeral=True)


# ── /deposit ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="deposit", description="Show your SHx deposit address and unique Memo ID")
async def deposit_command(interaction: Interaction):
    logger.info(f"COMMAND | /deposit | User: {interaction.user} ({interaction.user.id})")
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)

    user_data = await db.get_or_create_user(discord_id)
    memo_id = user_data.get("memo_id", discord_id)

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

    await interaction.followup.send(
        content="⚠️ **IMPORTANT**: You MUST include the Memo ID or your deposit will be lost.",
        embed=embed, ephemeral=True
    )


# ── /withdraw ─────────────────────────────────────────────────────────────────

@bot.tree.command(name="withdraw", description="Withdraw SHx from your tipping balance to an external wallet")
@app_commands.describe(amount="Amount of SHx or USD (e.g. 100 or $5.00)", destination="Stellar address (G...)")
async def withdraw_command(interaction: Interaction, amount: str, destination: str):
    logger.info(f"COMMAND | /withdraw | User: {interaction.user} ({interaction.user.id}) | Amount: {amount}")
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)

    parsed_amount = await parse_amount(amount)
    if parsed_amount is None:
        await interaction.followup.send("❌ Invalid amount. Enter a positive number or fiat string (like `$5`).", ephemeral=True)
        return
    amount_f = parsed_amount

    if not destination.startswith("G") or len(destination) != 56:
        await interaction.followup.send("❌ Invalid Stellar address.", ephemeral=True)
        return

    current_bal = await db.get_internal_balance(discord_id)
    if amount_f > current_bal:
        await interaction.followup.send(f"❌ Insufficient balance. You have **{current_bal:,.2f} SHx**.", ephemeral=True)
        return

    result = await stellar.execute_tip(
        sender_public_key=stellar.HOUSE_ACCOUNT_PUBLIC,
        recipient_public_key=destination,
        amount=amount_f,
        fee=0.0
    )

    if result["success"]:
        await db.add_deposit(discord_id, result["hash"], -amount_f)

        embed = _footer(discord.Embed(
            title="✅ Withdrawal Successful",
            description=f"Sent **{amount_f:,.2f} SHx** to `{destination[:8]}...`",
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
    amount="Amount of SHx or USD (e.g. 100 or $5)",
    reason="Optional reason for the tip",
)
async def tip_command(
    interaction: Interaction,
    user: discord.User,
    amount: str,
    reason: str = None,
    memo: str = None,
):
    actual_reason = reason if reason else memo
    logger.info(f"COMMAND | /tip | From: {interaction.user} To: {user} | Amount: {amount}")
    await interaction.response.defer()
    sender_id = str(interaction.user.id)
    recipient_id = str(user.id)
    is_admin = sender_id in ADMIN_DISCORD_IDS

    if user.bot:
        await interaction.followup.send("❌ Cannot tip bots.", ephemeral=True)
        return
    if sender_id == recipient_id:
        await interaction.followup.send("❌ Cannot tip yourself.", ephemeral=True)
        return
        
    parsed_amount = await parse_amount(amount)
    if parsed_amount is None:
        await interaction.followup.send("❌ Invalid amount. Enter a positive native integer or fiat string (e.g., `$5`).", ephemeral=True)
        return

    fee_shx = 0.0
    total_needed = parsed_amount + fee_shx

    # Ensure recipient exists in DB
    await db.get_or_create_user(recipient_id)

    # QoL for Admins: Auto-fund them instantly if their personal internal balance is too low
    if is_admin:
        admin_bal = await db.get_internal_balance(sender_id)
        if admin_bal < total_needed:
            await db.admin_fund_internal(sender_id, total_needed + 5000.0)

    success = await db.transfer_internal(sender_id, recipient_id, parsed_amount, fee_shx, actual_reason)

    if success:
        embed = _footer(discord.Embed(title="✅ Tip Sent!", color=SUCCESS_COLOR))
        embed.add_field(name="From", value=interaction.user.mention, inline=True)
        embed.add_field(name="To", value=user.mention, inline=True)
        embed.add_field(name="Amount", value=f"**{parsed_amount:,.2f} SHx**", inline=True)
        embed.add_field(name="Fee", value=f"{fee_shx:,.2f} SHx", inline=True)
        if actual_reason:
            embed.add_field(name="Reason", value=actual_reason, inline=False)
        await interaction.followup.send(embed=embed)
        logger.info(f"INTERNAL TIP OK | {sender_id}→{recipient_id} | {parsed_amount} SHx")
    else:
        # PRIVACY FIX: Explicitly scrub balances from the rejection log so nothing is shown in chat!
        await interaction.followup.send(
            f"❌ Transaction failed due to insufficient funds.\n"
            f"Please type `/balance` to privately check your available SHx.",
            ephemeral=True
        )


# ── /fund ─────────────────────────────────────────────────────────────────────

@bot.tree.command(name="fund", description="[Admin] Fund a user's internal SHx balance")
@app_commands.describe(user="User to fund", amount="Amount of SHx or USD (e.g. 1000 or $50)")
async def fund_command(interaction: Interaction, user: discord.User, amount: str):
    logger.info(f"COMMAND | /fund | User: {interaction.user} Target: {user.id} Amount: {amount}")
    await interaction.response.defer()
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ You do not have permission to use this command.", ephemeral=True)
        return
        
    parsed_amount = await parse_amount(amount)
    if parsed_amount is None:
        await interaction.followup.send("❌ Invalid amount. Enter numbers or a fiat string (e.g. `$5`).", ephemeral=True)
        return
        
    await db.get_or_create_user(str(user.id))
    await db.admin_fund_internal(str(user.id), parsed_amount)
    
    embed = _footer(discord.Embed(title="🏦 User Funded", color=SUCCESS_COLOR))
    embed.add_field(name="User", value=user.mention, inline=True)
    embed.add_field(name="Amount", value=f"**{parsed_amount:,.2f} SHx**", inline=True)
    await interaction.followup.send(embed=embed)

# ── /airdrop ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="airdrop", description="Create an SHx airdrop in the current channel")
@app_commands.describe(total_amount="Total SHx or USD (e.g. 100 or $10)", claims="Number of people who can claim", duration_minutes="Optional expiration time in minutes")
async def airdrop_command(interaction: Interaction, total_amount: str, claims: int, duration_minutes: Optional[int] = None):
    logger.info(f"COMMAND | /airdrop | User: {interaction.user} Total: {total_amount} Claims: {claims} Mins: {duration_minutes}")
    await interaction.response.defer()
    creator_id = str(interaction.user.id)
    
    parsed_amount = await parse_amount(total_amount)
    if parsed_amount is None or claims <= 0:
        await interaction.followup.send("❌ Invalid amount or claims. Must be > 0.", ephemeral=True)
        return
        
    amount_per_claim = parsed_amount / claims
    if amount_per_claim < 1.0:
        await interaction.followup.send("❌ Amount per claim must be at least 1 SHx.", ephemeral=True)
        return
        
    # Check balance
    bal = await db.get_internal_balance(creator_id)
    if bal < parsed_amount:
        await interaction.followup.send(f"❌ Insufficient balance. You have **{bal:,.2f} SHx**.", ephemeral=True)
        return
        
    airdrop_id = secrets.token_hex(4)
    await db.create_airdrop(
        airdrop_id, creator_id, parsed_amount, amount_per_claim, claims, "Channel Airdrop", duration_minutes
    )
    
    embed = _footer(discord.Embed(
        title="🪂 SHx Airdrop!",
        description=f"{interaction.user.mention} is dropping **{parsed_amount:,.2f} SHx**!" + (f"\n⏳ *Expires in {duration_minutes} minutes*" if duration_minutes else ""),
        color=0xFF00AA
    ))
    embed.add_field(name="Amount per claim", value=f"**{amount_per_claim:,.2f} SHx**", inline=True)
    embed.add_field(name="Total claims", value=f"**{claims}**", inline=True)
    
    view = AirdropView(airdrop_id)
    await interaction.followup.send(embed=embed, view=view)


# ══════════════════════════════════════════════════════════════════════════════
# EVENTS & BACKGROUND TASKS
# ══════════════════════════════════════════════════════════════════════════════


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    logger.error(f"App command error on {interaction.command.name if interaction.command else 'Unknown'}: {error}", exc_info=error)
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ An internal error occurred.", ephemeral=True)
        else:
            await interaction.followup.send("❌ An internal error occurred.", ephemeral=True)
    except:
        pass

@bot.event
async def on_ready():
    logger.info(f"Bot online as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Guild: {DISCORD_GUILD_ID} | Network: {stellar.STELLAR_NETWORK}")

    # Initialize DB and HTTP session
    await db.init_db()
    await stellar.get_session()

    try:
        # Copy the globally defined python commands to the specific guild
        # This guarantees interactions work whether Discord sends a global or guild payload!
        bot.tree.copy_global_to(guild=guild_obj)
        synced_guild = await bot.tree.sync(guild=guild_obj)
        logger.info(f"Synced {len(synced_guild)} guild slash commands.")
        
        # Sync the global tree as well to replace any old global commands 
        synced_global = await bot.tree.sync()
        logger.info(f"Cleared global slash commands.")
    except Exception as e:
        logger.error(f"Command sync failed: {e}", exc_info=True)

    # Start background tasks
    bot.loop.create_task(heartbeat())
    bot.loop.create_task(start_deposit_monitor())


async def start_deposit_monitor():
    """Start the Stellar deposit polling monitor."""
    import re

    async def handle_deposit(memo_val, tx_hash, amount_shx, memo_type):
        try:
            target_discord_id = None

            if memo_type == "id":
                target_discord_id = str(memo_val)
            elif memo_type == "text" and memo_val:
                id_match = re.search(r'(\d{17,20})', str(memo_val))
                if id_match:
                    target_discord_id = id_match.group(1)

            if not target_discord_id:
                logger.warning(f"DEPOSIT | Ignored tx {tx_hash} | No valid memo ({memo_type}: {memo_val})")
                return

            await db.add_deposit(target_discord_id, tx_hash, amount_shx)
            logger.info(f"DEPOSIT | Credited {amount_shx} SHx to {target_discord_id}")

            user = bot.get_user(int(target_discord_id))
            if user:
                embed = _footer(discord.Embed(
                    title="💰 Deposit Confirmed",
                    description=f"Your account has been credited with **{amount_shx:,.2f} SHx**.",
                    color=SUCCESS_COLOR
                ))
                try:
                    await user.send(embed=embed)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error processing deposit {tx_hash}: {e}")

    await stellar.stream_deposits(cursor="now", callback=handle_deposit)


async def heartbeat():
    """Log bot health every 15 minutes."""
    while True:
        try:
            logger.info(f"HEARTBEAT | Bot Healthy | Latency: {bot.latency * 1000:.2f}ms")
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
