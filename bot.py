"""
SHx Tip Bot — Discord Bot
Slash-command interface for tipping SHx on the Stellar network.
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
RATE_LIMIT_TIPS = int(os.getenv("RATE_LIMIT_TIPS_PER_MINUTE", "5"))
ADMIN_DISCORD_IDS = [
    x.strip() for x in os.getenv("ADMIN_DISCORD_IDS", "").split(",") if x.strip()
]
LOG_FILE = os.getenv("LOG_FILE", "shx_tip_bot.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

KNIGHT_ROLE_ID = int(os.getenv("KNIGHT_ROLE_ID", "0"))
SQUIRE_ROLE_ID = int(os.getenv("SQUIRE_ROLE_ID", "0"))
DUKE_ROLE_ID = int(os.getenv("DUKE_ROLE_ID", "0"))
VANGUARD_ROLE_ID = int(os.getenv("VANGUARD_ROLE_ID", "0"))
CAPTAIN_ROLE_ID = int(os.getenv("CAPTAIN_ROLE_ID", "0"))

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
# members intent is optional; enable it in the Developer Portal for best UX
try:
    intents.members = True
except Exception:
    pass
bot = commands.Bot(command_prefix="!", intents=intents)
guild_obj = discord.Object(id=DISCORD_GUILD_ID)

EMBED_COLOR = 0x00C9FF
ERROR_COLOR = 0xFF4C4C
SUCCESS_COLOR = 0x00FF88
WARN_COLOR = 0xFFAA00

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_elevated_role(member: discord.Member) -> bool:
    """Check if the user has any of the 'elevated' roles."""
    if not isinstance(member, discord.Member):
        return False
    role_ids = [DUKE_ROLE_ID, KNIGHT_ROLE_ID, SQUIRE_ROLE_ID, VANGUARD_ROLE_ID, CAPTAIN_ROLE_ID]
    return any(role.id in role_ids for role in member.roles if role.id != 0)

def get_role_level(member: discord.Member) -> int:
    """Get the hierarchy level of a member. 6=Admin, 5=Duke, 4=Knight, 3=Squire, 2=Vanguard, 1=Captain, 0=Member."""
    if str(member.id) in ADMIN_DISCORD_IDS:
        return 6
    role_ids = [r.id for r in member.roles]
    if DUKE_ROLE_ID != 0 and DUKE_ROLE_ID in role_ids:
        return 5
    if KNIGHT_ROLE_ID != 0 and KNIGHT_ROLE_ID in role_ids:
        return 4
    if SQUIRE_ROLE_ID != 0 and SQUIRE_ROLE_ID in role_ids:
        return 3
    if VANGUARD_ROLE_ID != 0 and VANGUARD_ROLE_ID in role_ids:
        return 2
    if CAPTAIN_ROLE_ID != 0 and CAPTAIN_ROLE_ID in role_ids:
        return 1
    return 0


# ── Airdrop Claim View (Persistent) ──────────────────────────────────────────

class AirdropView(discord.ui.View):
    """
    Persistent view for airdrop claim buttons.
    To be persistent: timeout=None and all buttons have custom_id.
    """

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim SHx", style=discord.ButtonStyle.green, custom_id="claim_airdrop")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        user_id = str(interaction.user.id)
        message = interaction.message
        
        # 1. Extract Airdrop ID from message footer
        # Expected format: "Airdrop ID: <hex> | Click below to claim!"
        try:
            footer_text = message.embeds[0].footer.text
            airdrop_id = footer_text.split("Airdrop ID: ")[1].split(" |")[0]
        except (IndexError, AttributeError, ValueError):
            await interaction.followup.send("❌ Could not identify airdrop ID.", ephemeral=True)
            return

        # 2. Check if airdrop is still active
        airdrop = await db.get_airdrop(airdrop_id)
        if not airdrop or not airdrop["active"]:
            await interaction.followup.send("❌ This airdrop has ended or is no longer active.", ephemeral=True)
            return

        # 3. Check if user already claimed
        if await db.has_user_claimed(airdrop_id, user_id):
            await interaction.followup.send("❌ You have already claimed from this airdrop.", ephemeral=True)
            return

        # 4. Check wallet link
        user_key = await db.get_user_stellar_key(user_id)
        if not user_key:
            await interaction.followup.send("❌ Your wallet is not linked. Use `/link` first.", ephemeral=True)
            return

        # 5. Check trustline
        if not await stellar.check_shx_trustline(user_key):
            await interaction.followup.send("❌ You need an SHx trustline to claim. Please add one in your wallet.", ephemeral=True)
            return

        # 6. Execute transfer (House -> User)
        # We use the house account because Stronghold manages the airdrop supply
        gas_shx = await stellar.calculate_gas_shx()
        amount_per_claim = airdrop["amount_per_claim"]
        net_amount = amount_per_claim - gas_shx
        
        if net_amount <= 0:
            await interaction.followup.send("❌ Airdrop amount is too small to cover gas.", ephemeral=True)
            return

        result = await stellar.execute_tip(stellar.HOUSE_ACCOUNT_PUBLIC, user_key, net_amount, gas_shx)

        if result["success"]:
            await db.add_airdrop_claim(airdrop_id, user_id, result["tx_hash"])
            
            # Update progress
            updated_airdrop = await db.get_airdrop(airdrop_id)
            status_note = ""
            if updated_airdrop:
                count = updated_airdrop["claims_count"]
                max_c = updated_airdrop["max_claims"]
                status_note = f" ({count}/{max_c} claimed)"
            
            await interaction.followup.send(
                f"✅ Claimed **{net_amount:,.2f} SHx**!{status_note}\n"
                f"[View Transaction]({result['tx_url']})",
                ephemeral=True
            )
        else:
            await interaction.followup.send(f"❌ Claim failed: {result['error']}", ephemeral=True)


def _footer(embed: discord.Embed) -> discord.Embed:
    embed.set_footer(text="SHx Tip Bot • Stronghold Community")
    return embed


# ── Events ────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    logger.info(f"Bot online as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Guild: {DISCORD_GUILD_ID} | Network: {stellar.STELLAR_NETWORK}")
    
    # Initialize persistent DB and Session
    await db.init_db()
    await stellar.get_session()
    
    # Register persistent views
    bot.add_view(AirdropView())
    
    try:
        bot.tree.copy_global_to(guild=guild_obj)
        synced = await bot.tree.sync(guild=guild_obj)
        logger.info(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        logger.error(f"Command sync failed: {e}", exc_info=True)
    
    # Start heartbeat and deposit monitor
    bot.loop.create_task(heartbeat())
    bot.loop.create_task(start_deposit_monitor())

async def start_deposit_monitor():
    """Starts the Stellar Horizon stream to monitor for SHx deposits."""
    async def handle_deposit(memo_val: str, tx_hash: str, amount_shx: float, memo_type: str):
        try:
            # 1. Fetch transaction details (for source address and full memo)
            server = stellar.Server(stellar.HORIZON_URL)
            tx = await server.transactions().transaction(tx_hash).call()
            source_addr = tx.get("source_account")
            
            # 2. Identify the target Discord User
            target_discord_id = None
            
            # Case A: Numeric Memo ID (Standard Custodial)
            if memo_type == "id":
                target_discord_id = str(memo_val)
            
            # Case B: Text Memo (Moderator Funding)
            elif memo_type == "text" and memo_val:
                # Look for @username or <@!id> or <@id>
                import re
                mention_match = re.search(r'<@!?(\d+)>', str(memo_val))
                if mention_match:
                    target_discord_id = mention_match.group(1)
                else:
                    # Try raw numeric string if present
                    id_match = re.search(r'(\d{17,20})', str(memo_val))
                    if id_match:
                        target_discord_id = id_match.group(1)
                    else:
                        logger.warning(f"DEPOSIT | Could not parse target user from text memo: '{memo_val}'")

            if not target_discord_id:
                logger.warning(f"DEPOSIT | Ignored tx {tx_hash} | No valid target user in memo ({memo_type}: {memo_val})")
                return

            # 3. Anti-Farming check
            # (Existing logic remains but updated for SHx)
            other_users = await db.get_pool().fetch(
                "SELECT DISTINCT discord_id FROM deposits WHERE tx_hash IN (SELECT tx_hash FROM deposits WHERE source_address = $1)",
                source_addr
            )
            if other_users and any(u["discord_id"] != target_discord_id for u in other_users):
                logger.warning(f"ANTI-FARM ALERT | Source {source_addr[:8]}... deposited to multiple accounts.")

            # 4. Credit the user
            await db.add_deposit(target_discord_id, tx_hash, amount_shx)
            
            # 5. Notify user
            user = bot.get_user(int(target_discord_id))
            if user:
                embed = _footer(discord.Embed(
                    title="💰 Deposit Confirmed",
                    description=f"Your account has been credited with **{amount_shx:,.2f} SHx**.",
                    color=SUCCESS_COLOR
                ))
                embed.add_field(name="Transaction", value=f"[View]({stellar.get_explorer_url(tx_hash)})")
                if memo_type == "text":
                    embed.add_field(name="Memo", value=str(memo_val))
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
        await asyncio.sleep(900) # 15 minutes

async def payroll_monitor():
    """
    Background task that monitors the House account for incoming tips from admins.
    Automatically triggers payroll distribution.
    """
    logger.info("Payroll monitor started.")
    last_token = "now" # Start polling from now
    
    # Load last token from file if exists
    token_file = "last_payroll_token.txt"
    if os.path.exists(token_file):
        try:
            with open(token_file, "r") as f:
                last_token = f.read().strip()
                logger.info(f"Resuming payroll monitor from token: {last_token}")
        except Exception:
            pass

    while True:
        try:
            # 1. Fetch admin stellar keys
            admin_keys = []
            for aid in ADMIN_DISCORD_IDS:
                key = await db.get_user_stellar_key(aid)
                if key: admin_keys.append(key)

            if not admin_keys:
                await asyncio.sleep(60)
                continue

            # 2. Check Horizon for new payments to House
            url = f"{stellar.HORIZON_URL}/accounts/{stellar.HOUSE_ACCOUNT_PUBLIC}/payments?cursor={last_token}&order=asc&limit=10"
            session = await stellar.get_session()
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    records = data.get("_embedded", {}).get("records", [])
                    
                    for record in records:
                        last_token = record["paging_token"]
                        
                        # We only care about RECEIVED payments of SHx
                        is_payment = record["type"] == "payment"
                        is_shx = record.get("asset_code") == stellar.SHX_ASSET_CODE and record.get("asset_issuer") == stellar.SHX_ISSUER
                        is_to_house = record["to"] == stellar.HOUSE_ACCOUNT_PUBLIC
                        is_from_admin = record["from"] in admin_keys
                        
                        if is_payment and is_shx and is_to_house and is_from_admin:
                            amount = float(record["amount"])
                            logger.info(f"PAYROLL TRIGGER | Received {amount} SHx from Admin {record['from']}")
                            
                            # Trigger distribution
                            main_guild = bot.get_guild(DISCORD_GUILD_ID)
                            if main_guild:
                                await run_automated_payroll(main_guild, amount, record["from"])

                        # Save token after each record
                        with open(token_file, "w") as f:
                            f.write(last_token)
                elif resp.status == 404:
                    # Cursor might be invalid or no new payments
                    pass

        except Exception as e:
            logger.error(f"Payroll monitor error: {e}", exc_info=True)
        
        await asyncio.sleep(60) # Poll every minute

async def run_automated_payroll(guild, received_amount, admin_key):
    """Internal function to run the payroll distribution automatically."""
    logger.info(f"Starting automated payroll distribution for guild {guild.id}")
    
    # 1. Calculate
    class MockInteraction:
        def __init__(self, guild): self.guild = guild
    
    data, error = await _calculate_payroll(MockInteraction(guild))
    if error:
        logger.error(f"Automated payroll calculation failed: {error}")
        return

    payments = data["payments"]
    if not payments:
        logger.info("Automated payroll: No pending payments found.")
        return

    # 2. Execute
    batch_size = 20
    success_count = 0
    total_shx = 0
    
    for i in range(0, len(payments), batch_size):
        batch = payments[i:i + batch_size]
        result = await stellar.execute_batch_tip(stellar.HOUSE_ACCOUNT_PUBLIC, batch)
        if result["success"]:
            success_count += len(batch)
            for p in batch:
                total_shx += p["amount"]
                await db.record_tip("HOUSE", p["discord_id"], p["amount"], p["fee"], result["tx_hash"], f"Auto-Payroll ({p['role']})")
        else:
            logger.error(f"Auto-payroll batch fail: {result['error']}")

    logger.info(f"AUTO-PAYROLL OK | Distributed {total_shx:,.2f} SHx to {success_count} members.")

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
    logger.info(f"COMMAND RECEIVED | /link | User: {interaction.user} ({interaction.user.id})")
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)

    # Ensure user exists in DB with a memo_id
    user_data = await db.get_or_create_user(discord_id)
    existing = user_data.get("stellar_public_key")
    
    relink_note = ""
    if existing:
        relink_note = (
            f"\n\n⚠️ You are verified with `{existing[:8]}...{existing[-8:]}`. "
            "Re-linking will update your verified withdrawal address."
        )

    token = await db.create_link_token(discord_id)
    # The registration page now focuses on wallet verification, not allowance
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


# ── /register (alias) ────────────────────────────────────────────────────────

@bot.tree.command(name="register", description="Alias for /link — connect your Stellar wallet")
async def register_command(interaction: Interaction):
    await link_command.callback(interaction)


# ── /balance ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="balance", description="Check your internal SHx tip balance")
async def balance_command(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)
    
    # Ensure user exists
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


@bot.tree.command(name="deposit", description="Show your SHx deposit address and unique Memo ID")
async def deposit_command(interaction: Interaction):
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


@bot.tree.command(name="withdraw", description="Withdraw SHx from your tipping balance to an external wallet")
@app_commands.describe(amount="Amount of SHx to withdraw", destination="Stellar address (G...)")
async def withdraw_command(interaction: Interaction, amount: float, destination: str):
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)
    
    # 1. Validation
    if amount <= 0:
        await interaction.followup.send("❌ Amount must be greater than 0.", ephemeral=True)
        return
        
    if not destination.startswith("G") or len(destination) != 56:
        await interaction.followup.send("❌ Invalid Stellar address.", ephemeral=True)
        return

    # 2. Check internal balance
    current_bal = await db.get_internal_balance(discord_id)
    if amount > current_bal:
        await interaction.followup.send(f"❌ Insufficient balance. You have **{current_bal:,.2f} SHx**.", ephemeral=True)
        return

    # 3. Process withdrawal
    await interaction.followup.send(f"⏳ Processing withdrawal of **{amount:,.2f} SHx**...", ephemeral=True)
    
    # Withdrawal memo for on-chain clarity
    withdrawal_memo = f"Withdrawal ({interaction.user.name})"
    result = await stellar.send_withdrawal(destination, amount, memo=withdrawal_memo)
    
    if result["success"]:
        # Record the deduction in DB (negative deposit)
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
    await interaction.response.defer()
    sender_id = str(interaction.user.id)
    recipient_id = str(user.id)
    is_admin = sender_id in ADMIN_DISCORD_IDS or is_elevated_role(interaction.user)

    # ── Validation ────────────────────────────────────────────────────────
    if user.bot:
        await interaction.followup.send("❌ Cannot tip bots.", ephemeral=True)
        return
    if sender_id == recipient_id:
        await interaction.followup.send("❌ Cannot tip yourself.", ephemeral=True)
        return
    if amount <= 0:
        await interaction.followup.send("❌ Amount must be greater than 0.", ephemeral=True)
        return

    # ── CASE 1: Moderator Reward (On-Chain) ───────────────────────────────
    if is_admin:
        # Moderators can reward users directly from the House account on-chain
        # This provides a real Stellar transaction with a Memo descriptive of the "reason"
        recipient_key = await db.get_user_stellar_key(recipient_id)
        if not recipient_key:
            await interaction.followup.send(f"❌ {user.mention} hasn't linked a verified Stellar wallet yet.", ephemeral=True)
            return
            
        # Optional: Check trustline
        if not await stellar.check_shx_trustline(recipient_key):
            await interaction.followup.send(f"❌ {user.mention} lacks an SHx trustline.", ephemeral=True)
            return

        memo_text = reason if reason else f"Tip from {interaction.user.name}"
        if len(memo_text) > 28: memo_text = memo_text[:25] + "..."

        result = await stellar.execute_tip(stellar.HOUSE_ACCOUNT_PUBLIC, recipient_key, amount, 0.0, memo=memo_text)
        
        if result["success"]:
            embed = _footer(discord.Embed(title="🎁 Moderator Reward Sent!", color=SUCCESS_COLOR))
            embed.add_field(name="From", value=interaction.user.mention, inline=True)
            embed.add_field(name="To", value=user.mention, inline=True)
            embed.add_field(name="Amount", value=f"**{amount:,.2f} SHx**", inline=True)
            if reason:
                embed.add_field(name="Reason/Memo", value=reason, inline=False)
            embed.add_field(name="Transaction", value=f"[View]({result['tx_url']})")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ On-chain reward failed: {result['error']}", ephemeral=True)
        return

    # ── CASE 2: User Tip (Internal Transfer) ─────────────────────────────
    # Standard users tip each other instantly using their internal custodial balance
    fee_shx = 1.0 
    total_needed = amount + fee_shx

    # Execute Internal Transfer
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


# ── /tip-multiple ────────────────────────────────────────────────────────────

@bot.tree.command(name="tip-multiple", description="Tip multiple users at once")
@app_commands.describe(
    users="The users to tip (mention them or paste IDs)",
    amount="Amount of SHx to send to EACH user",
    reason="Optional reason for the tip",
)
async def tip_multiple_command(
    interaction: Interaction,
    users: str,
    amount: float,
    reason: str = None,
):
    await interaction.response.defer()
    sender_id = str(interaction.user.id)

    # 1. Parse recipients
    # We look for <@!123> or <@123> or raw IDs
    import re
    raw_ids = re.findall(r'\d{17,20}', users)
    unique_ids = list(set(raw_ids))
    
    if not unique_ids:
        await interaction.followup.send("❌ No valid users found. Please mention them or use their IDs.", ephemeral=True)
        return

    if sender_id in unique_ids:
        unique_ids.remove(sender_id)
        if not unique_ids:
            await interaction.followup.send("❌ Cannot tip yourself.", ephemeral=True)
            return

    if amount <= 0 or amount > 100_000:
        await interaction.followup.send("❌ Amount per user must be between 0 and 100,000 SHx.", ephemeral=True)
        return

    # 2. Validation & Prep
    valid_recipients = []
    failed_recipients = []
    
    fee_shx = 1.0 # Standard internal fee
    amount_stroops = int(amount * 10_000_000)
    fee_stroops = int(fee_shx * 10_000_000)
    
    for rid in unique_ids:
        # Check if user exists or create them
        await db.get_or_create_user(rid)
        valid_recipients.append(rid)

    if not valid_recipients:
        await interaction.followup.send("❌ No valid recipients found.", ephemeral=True)
        return

    # 3. Balance Check
    grand_total_stroops = (amount_stroops + fee_stroops) * len(valid_recipients)
    current_bal = await db.get_internal_balance(sender_id)
    
    if (current_bal * 10_000_000) < grand_total_stroops:
        await interaction.followup.send(
            f"❌ Insufficient balance to tip {len(valid_recipients)} users.\n"
            f"Need: **{(grand_total_stroops/10_000_000):,.2f} SHx** (Includes {fee_shx} fee per tip)\n"
            f"Have: **{current_bal:,.2f} SHx**",
            ephemeral=True
        )
        return

    # 4. Execute Batch Internal
    await interaction.followup.send(f"⏳ Processing internal batch tip for {len(valid_recipients)} users...")
    
    success_count = 0
    for rid in valid_recipients:
        if await db.transfer_internal(sender_id, rid, amount_stroops, fee_stroops, reason):
            success_count += 1
        else:
            failed_recipients.append(f"<@{rid}> (Insufficient funds during batch)")

    if success_count > 0:
        success_mentions = " ".join([f"<@{rid}>" for rid in valid_recipients[:10]])
        if len(valid_recipients) > 10: success_mentions += " ..."
        
        embed = _footer(discord.Embed(title="✅ Batch Tip Sent!", color=SUCCESS_COLOR))
        embed.add_field(name="Amount per User", value=f"**{amount:,.2f} SHx**", inline=True)
        embed.add_field(name="Fee per User", value=f"{fee_shx:,.2f} SHx", inline=True)
        embed.add_field(name="Total Distributed", value=f"**{(amount * success_count):,.2f} SHx**", inline=True)
        embed.add_field(name="Recipients", value=f"{success_count} users", inline=True)
        
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        
        await interaction.followup.send(embed=embed)
        logger.info(f"BATCH TIP OK | {sender_id} | {success_count} users")
    else:
        await interaction.followup.send("❌ Batch tip failed. No successful transfers.", ephemeral=True)


# ── Payroll / Role Distribution ──────────────────────────────────────────────

async def _calculate_payroll(interaction: Interaction):
    """Internal helper to calculate payroll amounts for Knights and Squires."""
    guild = interaction.guild
    if not guild:
        return None, "Not in a server."

    knight_role = guild.get_role(KNIGHT_ROLE_ID)
    squire_role = guild.get_role(SQUIRE_ROLE_ID)

    if not knight_role and not squire_role:
        return None, "Knight or Squire roles not found. Check KNIGHT_ROLE_ID and SQUIRE_ROLE_ID in .env."

    shx_price = await stellar.get_shx_usd_price()
    if not shx_price:
        return None, "Could not fetch SHx price from DEX."

    gas_shx = await stellar.calculate_gas_shx()

    knights = knight_role.members if knight_role else []
    squires = squire_role.members if squire_role else []

    payments = []
    skipped = []

    # Process Knights ($200 flat)
    for m in knights:
        if m.bot: continue
        pub_key = await db.get_user_stellar_key(str(m.id))
        if not pub_key:
            skipped.append(f"{m.mention} (No wallet linked)")
            continue
        
        if not await stellar.check_shx_trustline(pub_key):
            skipped.append(f"{m.mention} (No trustline)")
            continue

        amount_shx = stellar.usd_to_shx(200.0, shx_price)
        payments.append({
            "discord_id": str(m.id),
            "mention": m.mention,
            "public_key": pub_key,
            "amount": amount_shx,
            "fee": gas_shx,
            "role": "Knight",
            "usd": 200.0
        })

    # Process Squires (Top-up to $100)
    for m in squires:
        if m.bot: continue
        if any(p["discord_id"] == str(m.id) for p in payments): continue # Skip if already processed as Knight

        pub_key = await db.get_user_stellar_key(str(m.id))
        if not pub_key:
            skipped.append(f"{m.mention} (No wallet linked)")
            continue
        
        if not await stellar.check_shx_trustline(pub_key):
            skipped.append(f"{m.mention} (No trustline)")
            continue

        balance_shx = await stellar.get_shx_balance(pub_key)
        if balance_shx is None:
            skipped.append(f"{m.mention} (Could not fetch balance)")
            continue

        current_usd = balance_shx * shx_price
        target_usd = 100.0
        diff_usd = target_usd - current_usd

        if diff_usd <= 0:
            skipped.append(f"{m.mention} (Balance already ≥ $100)")
            continue

        amount_shx = stellar.usd_to_shx(diff_usd, shx_price)
        payments.append({
            "discord_id": str(m.id),
            "mention": m.mention,
            "public_key": pub_key,
            "amount": amount_shx,
            "fee": gas_shx,
            "role": "Squire",
            "usd": diff_usd
        })

    return {
        "payments": payments,
        "skipped": skipped,
        "shx_price": shx_price,
        "gas_shx": gas_shx
    }, None


@bot.tree.command(name="payroll-preview", description="[Admin] Preview pending payments for Knights and Squires")
async def payroll_preview_command(interaction: Interaction):
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    data, error = await _calculate_payroll(interaction)
    if error:
        await interaction.followup.send(f"❌ Error: {error}", ephemeral=True)
        return

    payments = data["payments"]
    skipped = data["skipped"]
    shx_price = data["shx_price"]

    total_shx = sum(p["amount"] for p in payments)
    total_usd = sum(p["usd"] for p in payments)

    embed = _footer(discord.Embed(
        title="📋 Payroll Preview",
        description=f"Current SHx Price: **${shx_price:,.6f}**\nTotal Estimate: **{total_shx:,.2f} SHx** (~${total_usd:,.2f})",
        color=EMBED_COLOR
    ))

    if payments:
        p_list = "\n".join([f"{p['mention']} ({p['role']}): **{p['amount']:,.2f} SHx** (${p['usd']:,.2f})" for p in payments[:15]])
        if len(payments) > 15: p_list += f"\n...and {len(payments)-15} more"
        embed.add_field(name="Pending Payments", value=p_list, inline=False)
    else:
        embed.add_field(name="Pending Payments", value="None found.", inline=False)

    if skipped:
        s_list = "\n".join(skipped[:10])
        if len(skipped) > 10: s_list += f"\n...and {len(skipped)-10} more"
        embed.add_field(name="Skipped", value=s_list, inline=False)

    embed.set_footer(text=f"Use /payroll-run to execute | SHx Price: ${shx_price:,.6f}")
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="payroll-run", description="[Admin] Execute payments for Knights and Squires")
async def payroll_run_command(interaction: Interaction):
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    data, error = await _calculate_payroll(interaction)
    if error:
        await interaction.followup.send(f"❌ Error: {error}", ephemeral=True)
        return

    payments = data["payments"]
    if not payments:
        await interaction.followup.send("❌ No pending payments to process.", ephemeral=True)
        return

    # Check if House account has enough balance
    total_needed = sum(p["amount"] for p in payments) + sum(p["fee"] for p in payments)
    house_balance = await stellar.get_shx_balance(stellar.HOUSE_ACCOUNT_PUBLIC)
    
    if house_balance is None or house_balance < total_needed:
        await interaction.followup.send(
            f"❌ House account insufficient funds.\nNeed: **{total_needed:,.2f} SHx**\nHave: **{house_balance:,.2f} SHx**",
            ephemeral=True
        )
        return

    await interaction.followup.send(f"🚀 Executing payroll for {len(payments)} members...")

    # Execute in batches (max 20 operations per transaction for safety)
    batch_size = 20
    success_count = 0
    fail_count = 0
    tx_urls = []

    for i in range(0, len(payments), batch_size):
        batch = payments[i:i + batch_size]
        result = await stellar.execute_batch_tip(stellar.HOUSE_ACCOUNT_PUBLIC, batch)
        
        if result["success"]:
            success_count += len(batch)
            tx_urls.append(result["tx_url"])
            # Record each in DB
            for p in batch:
                await db.record_tip("HOUSE", p["discord_id"], p["amount"], p["fee"], result["tx_hash"], f"Payroll ({p['role']})")
        else:
            fail_count += len(batch)
            logger.error(f"PAYROLL BATCH FAIL: {result['error']}")

    embed = _footer(discord.Embed(
        title="✅ Payroll Completed",
        description=f"Successfully distributed SHx to **{success_count}** members.",
        color=SUCCESS_COLOR
    ))
    embed.add_field(name="Success", value=str(success_count), inline=True)
    embed.add_field(name="Failed", value=str(fail_count), inline=True)
    
    if tx_urls:
        links = "\n".join([f"[Transaction {i+1}]({url})" for i, url in enumerate(tx_urls)])
        embed.add_field(name="Transactions", value=links, inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)
    logger.info(f"PAYROLL COMPLETE | Success: {success_count} | Fail: {fail_count}")

@bot.tree.command(name="distribute", description="Admin: Distribute SHx from Stronghold supply to a user/mod")
@app_commands.describe(
    user="The user to receive SHx",
    amount="Amount of SHx to send",
)
async def distribute_command(
    interaction: Interaction,
    user: discord.Member,
    amount: float,
):
    await interaction.response.defer(ephemeral=True)

    # Admin check
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ Only admins can use this command.", ephemeral=True)
        return

    recipient_key = await db.get_user_stellar_key(str(user.id))
    if not recipient_key:
        await interaction.followup.send(f"❌ {user.mention} hasn't linked their wallet yet.", ephemeral=True)
        return

    # Use 0 fee for distribution as it's from the supply wallet (house signed)
    # The house account pays the XLM for this, which is fine for initial funding
    result = await stellar.execute_tip(stellar.HOUSE_ACCOUNT_PUBLIC, recipient_key, amount, 0.0)

    if result["success"]:
        embed = _footer(discord.Embed(title="✅ Distribution Successful", color=SUCCESS_COLOR))
        embed.add_field(name="Recipient", value=user.mention, inline=True)
        embed.add_field(name="Amount", value=f"{amount:,.7f} SHx", inline=True)
        embed.add_field(name="Transaction", value=f"[View]({result['tx_url']})", inline=False)
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"❌ Distribution failed: {result['error']}", ephemeral=True)


# (Class AirdropView moved to top for persistence setup)


# ── /airdrop ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="airdrop", description="Admin: Create an airdrop in the current channel")
@app_commands.describe(
    total_amount="Total SHx to distribute",
    max_claims="Maximum number of people who can claim",
    reason="Optional reason for the airdrop",
)
async def airdrop_command(
    interaction: Interaction,
    total_amount: float,
    max_claims: int,
    reason: str = None,
):
    await interaction.response.defer()

    # Admin check
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ Only admins can start airdrops.", ephemeral=True)
        return

    if total_amount <= 0 or max_claims <= 0:
        await interaction.followup.send("❌ Invalid amount or claim count.", ephemeral=True)
        return

    amount_per_claim = total_amount / max_claims
    airdrop_id = secrets.token_hex(8)

    # 1. Store in DB
    await db.create_airdrop(airdrop_id, str(interaction.user.id), total_amount, amount_per_claim, max_claims, reason)

    # 2. Create Embed & View
    embed = _footer(discord.Embed(
        title="🚀 SHx Airdrop!",
        description=f"**{total_amount:,.2f} SHx** total is being airdropped!",
        color=discord.Color.gold()
    ))
    embed.add_field(name="Amount Per Person", value=f"{amount_per_claim:,.2f} SHx", inline=True)
    embed.add_field(name="Max Claims", value=str(max_claims), inline=True)
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    
    embed.set_footer(text=f"Airdrop ID: {airdrop_id} | Click below to claim!")

    view = AirdropView()
    await interaction.followup.send(embed=embed, view=view)


# ── /tip-group ───────────────────────────────────────────────────────────────

@bot.tree.command(name="tip-group", description="Admin: Tip multiple users or a role")
@app_commands.describe(
    amount_per_user="Amount of SHx to send to each user",
    users="Mention users or a role (e.g. @Member or @user1 @user2)",
    reason="Optional reason for the tips",
)
async def tip_group_command(
    interaction: Interaction,
    amount_per_user: float,
    users: str,
    reason: str = None,
):
    await interaction.response.defer(ephemeral=True)

    # Admin check
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ Only admins can perform group tips.", ephemeral=True)
        return

    # 1. Parse users (Mentions and Roles)
    target_users = []
    
    # Check for role mentions
    for role in interaction.guild.roles:
        if str(role.id) in users or role.name in users:
            target_users.extend(role.members)

    # Check for user mentions
    for member in interaction.guild.members:
        if str(member.id) in users or member.mention in users:
            if member not in target_users:
                target_users.append(member)

    if not target_users:
        await interaction.followup.send("❌ No valid users or roles found in the input.", ephemeral=True)
        return

    # Filter out bots and self (unless mods want to tip bots?)
    target_users = [u for u in target_users if not u.bot and u.id != interaction.user.id]

    if not target_users:
        await interaction.followup.send("❌ No eligible human recipients found.", ephemeral=True)
        return

    await interaction.followup.send(f"⏳ Processing tips for {len(target_users)} users...", ephemeral=True)

    success_count = 0
    fail_count = 0
    
    # 2. Execute tips
    gas_shx = await stellar.calculate_gas_shx()
    
    for user in target_users:
        recipient_key = await db.get_user_stellar_key(str(user.id))
        if not recipient_key:
            fail_count += 1
            continue
            
        # Distribute from House supply
        result = await stellar.execute_tip(stellar.HOUSE_ACCOUNT_PUBLIC, recipient_key, amount_per_user, 0.0)
        
        if result["success"]:
            success_count += 1
            # We don't record these in tip_history yet to avoid cluttering or 
            # we can record them as admin distributions.
            await db.record_tip("HOUSE", str(user.id), amount_per_user, 0.0, result["tx_hash"], reason or "Group Tip")
        else:
            fail_count += 1
        
        # Small delay to avoid hammering the node too hard
        await asyncio.sleep(0.5)

    await interaction.followup.send(
        f"✅ Group tip complete!\n- Success: {success_count}\n- Failed: {fail_count} (mostly unlinked wallets)",
        ephemeral=True
    )


# ── /withdraw ─────────────────────────────────────────────────────────────────

@bot.tree.command(name="withdraw", description="Withdraw info — your SHx is in your own wallet")
@app_commands.describe(
    amount="Amount (informational only)", destination="Destination address (informational only)"
)
async def withdraw_command(
    interaction: Interaction, amount: float = 0.0, destination: str = ""
):
    await interaction.response.defer(ephemeral=True)
    public_key = await db.get_user_stellar_key(str(interaction.user.id))
    addr = f"`{public_key[:8]}...{public_key[-8:]}`" if public_key else "Not linked"

    embed = _footer(discord.Embed(
        title="📤 Withdraw SHx",
        description=(
            "This bot is **non-custodial** — your SHx lives in your own wallet.\n\n"
            f"**Your wallet:** {addr}\n\n"
            "Open Freighter, Lobstr, or your preferred wallet app to send SHx."
        ),
        color=EMBED_COLOR,
    ))
    await interaction.followup.send(embed=embed, ephemeral=True)


# ── Admin: /fund ──────────────────────────────────────────────────────────────

@bot.tree.command(name="fund", description="[Admin] Fund a user's linked wallet")
@app_commands.describe(user="Target user", amount="SHx amount")
async def fund_command(interaction: Interaction, user: discord.Member, amount: float):
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(
        f"ℹ️ Funding is handled off-chain. Send SHx directly to the user's linked wallet.",
        ephemeral=True,
    )


# ── Admin: /set-treasury ─────────────────────────────────────────────────────

@bot.tree.command(name="set-treasury", description="[Admin] Update the treasury Stellar address")
@app_commands.describe(address="New treasury Stellar public key (G...)")
async def set_treasury_command(interaction: Interaction, address: str):
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        return
    if not address.startswith("G") or len(address) != 56:
        await interaction.response.send_message("❌ Invalid address.", ephemeral=True)
        return

    # Update runtime value (persists until restart; update .env for permanence)
    stellar.TREASURY_ACCOUNT = address
    await interaction.response.send_message(
        f"✅ Treasury updated to `{address[:8]}...{address[-8:]}`.\n"
        "⚠️ Also update `TREASURY_ACCOUNT` in `.env` and re-initialize the contract.",
        ephemeral=True,
    )
    logger.info(f"Treasury updated by admin {interaction.user.id} to {address}")


# ── Hierarchical Role Management ──────────────────────────────────────────────

@bot.tree.command(name="add-role", description="[Admin/Duke/Knight] Assign a role to a subordinate user")
@app_commands.describe(user="The user to receive the role", role_name="Choice: duke, knight, squire, vanguard, captain")
@app_commands.choices(role_name=[
    app_commands.Choice(name="Duke", value="duke"),
    app_commands.Choice(name="Knight", value="knight"),
    app_commands.Choice(name="Squire", value="squire"),
    app_commands.Choice(name="Vanguard", value="vanguard"),
    app_commands.Choice(name="Captain", value="captain"),
])
async def add_role_command(interaction: Interaction, user: discord.Member, role_name: str):
    sender_id = str(interaction.user.id)
    sender_level = get_role_level(interaction.user)

    if sender_level < 4: # Minimum Knight to manage roles
        await interaction.response.send_message("❌ Only Master (Admin), Dukes, or Knights can manage roles.", ephemeral=True)
        return

    # Check if target role is allowed for sender
    target_role_level = 0
    role_id = 0
    if role_name == "duke":
        target_role_level = 5
        role_id = DUKE_ROLE_ID
    elif role_name == "knight":
        target_role_level = 4
        role_id = KNIGHT_ROLE_ID
    elif role_name == "squire":
        target_role_level = 3
        role_id = SQUIRE_ROLE_ID
    elif role_name == "vanguard":
        target_role_level = 2
        role_id = VANGUARD_ROLE_ID
    elif role_name == "captain":
        target_role_level = 1
        role_id = CAPTAIN_ROLE_ID

    if sender_level <= target_role_level:
        await interaction.response.send_message(f"❌ You cannot assign a role level equal to or higher than your own ({sender_level} vs {target_role_level}).", ephemeral=True)
        return

    if role_id == 0:
        await interaction.response.send_message(f"❌ Role `{role_name}` is not configured in `.env`.", ephemeral=True)
        return

    role = interaction.guild.get_role(role_id)
    if not role:
        await interaction.response.send_message(f"❌ Role ID `{role_id}` not found in this server.", ephemeral=True)
        return

    await user.add_roles(role)
    await interaction.response.send_message(f"✅ Added role `{role.name}` to {user.mention}.", ephemeral=True)
    logger.info(f"ROLE ADD | {interaction.user.name} (Lvl {sender_level}) added {role.name} to {user.name}")

@bot.tree.command(name="remove-role", description="[Admin/Duke/Knight] Remove a role from a subordinate user")
@app_commands.describe(user="The user to remove the role from", role_name="Choice: duke, knight, squire, vanguard, captain")
@app_commands.choices(role_name=[
    app_commands.Choice(name="Duke", value="duke"),
    app_commands.Choice(name="Knight", value="knight"),
    app_commands.Choice(name="Squire", value="squire"),
    app_commands.Choice(name="Vanguard", value="vanguard"),
    app_commands.Choice(name="Captain", value="captain"),
])
async def remove_role_command(interaction: Interaction, user: discord.Member, role_name: str):
    sender_id = str(interaction.user.id)
    sender_level = get_role_level(interaction.user)

    if sender_level < 4:
        await interaction.response.send_message("❌ Only Master (Admin), Dukes, or Knights can manage roles.", ephemeral=True)
        return

    # Check if target role is allowed for sender
    target_role_level = 0
    role_id = 0
    if role_name == "duke":
        target_role_level = 5
        role_id = DUKE_ROLE_ID
    elif role_name == "knight":
        target_role_level = 4
        role_id = KNIGHT_ROLE_ID
    elif role_name == "squire":
        target_role_level = 3
        role_id = SQUIRE_ROLE_ID
    elif role_name == "vanguard":
        target_role_level = 2
        role_id = VANGUARD_ROLE_ID
    elif role_name == "captain":
        target_role_level = 1
        role_id = CAPTAIN_ROLE_ID

    if sender_level <= target_role_level:
        await interaction.response.send_message(f"❌ You cannot remove a role level equal to or higher than your own ({sender_level} vs {target_role_level}).", ephemeral=True)
        return

    role = interaction.guild.get_role(role_id)
    if not role:
        await interaction.response.send_message(f"❌ Role ID `{role_id}` not found in this server.", ephemeral=True)
        return

    await user.remove_roles(role)
    await interaction.response.send_message(f"✅ Removed role `{role.name}` from {user.mention}.", ephemeral=True)
    logger.info(f"ROLE REMOVE | {interaction.user.name} (Lvl {sender_level}) removed {role.name} from {user.name}")


# ── Hierarchical Disbursement ────────────────────────────────────────────────

@bot.tree.command(name="disburse", description="[Hierarchical] Fund a subordinate role/user")
@app_commands.describe(
    amount="Amount of SHx to send",
    target_user="Specific user to fund (must be lower role)",
    target_role="Alternatively, fund all users in this role",
)
@app_commands.choices(target_role=[
    app_commands.Choice(name="Duke", value="duke"),
    app_commands.Choice(name="Knight", value="knight"),
    app_commands.Choice(name="Squire", value="squire"),
    app_commands.Choice(name="Vanguard", value="vanguard"),
    app_commands.Choice(name="Captain", value="captain"),
    app_commands.Choice(name="Member", value="member"),
])
async def disburse_command(
    interaction: Interaction,
    amount: float,
    target_user: discord.Member = None,
    target_role: str = None,
):
    await interaction.response.defer(ephemeral=True)
    
    sender = interaction.user
    if not isinstance(sender, discord.Member):
        await interaction.followup.send("❌ This command must be used in a server.", ephemeral=True)
        return

    sender_level = get_role_level(sender)
    if sender_level == 0:
        await interaction.followup.send("❌ Only Squires and above can use `/disburse`.", ephemeral=True)
        return

    if amount <= 0:
        await interaction.followup.send("❌ Amount must be positive.", ephemeral=True)
        return

    # 1. Identify recipients
    recipients = []
    if target_user:
        if get_role_level(target_user) >= sender_level:
            await interaction.followup.send(f"❌ You can only disburse to users with a lower role than yours.", ephemeral=True)
            return
        recipients.append(target_user)
    elif target_role:
        role_id = 0
        target_level = 0
        if target_role == "duke":
            role_id = DUKE_ROLE_ID
            target_level = 5
        elif target_role == "knight":
            role_id = KNIGHT_ROLE_ID
            target_level = 4
        elif target_role == "squire":
            role_id = SQUIRE_ROLE_ID
            target_level = 3
        elif target_role == "vanguard":
            role_id = VANGUARD_ROLE_ID
            target_level = 2
        elif target_role == "captain":
            role_id = CAPTAIN_ROLE_ID
            target_level = 1
        elif target_role == "member":
            # For "member", we just mean anyone without an elevated role
            target_level = 0
        
        if target_level >= sender_level:
            await interaction.followup.send(f"❌ You can only disburse to roles lower than yours.", ephemeral=True)
            return
            
        if role_id != 0:
            role = interaction.guild.get_role(role_id)
            if role:
                recipients = [m for m in role.members if not m.bot and m.id != sender.id]
        else:
             # Default to all members if role is 0 or member
             recipients = [m for m in interaction.guild.members if not m.bot and get_role_level(m) < sender_level]

    if not recipients:
        await interaction.followup.send("❌ No valid recipients found.", ephemeral=True)
        return

    # 2. Execute transfers
    sender_details = await db.get_user_link_details(str(sender.id))
    sender_key = ""
    if sender_level == 4: # Master/Admin
        sender_key = stellar.HOUSE_ACCOUNT_PUBLIC
    else:
        if not sender_details:
             await interaction.followup.send("❌ You must link your wallet first.", ephemeral=True)
             return
        sender_key = sender_details["stellar_public_key"]

    success_count = 0
    fail_reasons = []

    for rec in recipients:
        rec_key = await db.get_user_stellar_key(str(rec.id))
        if not rec_key:
            fail_reasons.append(f"{rec.display_name} (Not linked)")
            continue
            
        # Execute tip (0.0 fee for disbursements)
        result = await stellar.execute_tip(sender_key, rec_key, amount, 0.0)
        if result["success"]:
            success_count += 1
        else:
            fail_reasons.append(f"{rec.display_name} ({result['error']})")

    msg = f"✅ Disbursed {amount} SHx to {success_count} user(s)."
    if fail_reasons:
        msg += f"\n⚠️ Failed for {len(fail_reasons)} user(s): {', '.join(fail_reasons[:5])}"
        if len(fail_reasons) > 5: msg += "..."

    await interaction.followup.send(msg, ephemeral=True)
    logger.info(f"DISBURSE | {sender.name} (Lvl {sender_level}) funded {success_count} users")


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
