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
from discord.ext import commands, tasks
import secrets
from typing import Optional, List, Dict, Any

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
AIRDROP_RESERVE = "AIRDROP_RESERVE"

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
            await interaction.followup.send("❌ This airdrop is no longer active.", ephemeral=True)
            return
            
        if await db.has_user_claimed(self.airdrop_id, user_id):
            await interaction.followup.send("❌ You have already entered this airdrop.", ephemeral=True)
            return
            
        await db.get_or_create_user(user_id)
        await db.add_airdrop_claim(self.airdrop_id, user_id)
        
        # Calculate time remaining
        expires_at = ad.get("expires_at")
        rem_str = "soon"
        if expires_at:
            delta = int(expires_at - time.time())
            if delta > 60:
                rem_str = f"in {delta // 60} minutes"
            elif delta > 0:
                rem_str = f"in {delta} seconds"
        
        await interaction.followup.send(f"✅ **Entry Confirmed!** You will receive your share of the pool {rem_str}. Keep an eye on the channel!", ephemeral=True)



async def parse_amount(input_str: str) -> float | None:
    """Parse a string to an SHx float. Handles raw SHx or fiat ($ USD). Returns None on failure."""
    result = await parse_amount_full(input_str)
    return result["shx"] if result else None

async def parse_amount_full(input_str: str) -> dict | None:
    """
    Parse an amount string and return full conversion details.
    Returns dict: {shx: float, was_usd: bool, usd_input: float|None, rate: float|None}
    Returns None on failure.
    """
    input_str = str(input_str).strip().lower()
    is_usd = input_str.startswith('$') or input_str.endswith('usd')
    clean_str = input_str.replace('$', '').replace('usd', '').strip()
    
    last_comma = clean_str.rfind(',')
    last_dot = clean_str.rfind('.')
    
    if last_comma != -1 and last_dot != -1:
        if last_comma > last_dot:
            clean_str = clean_str.replace('.', '').replace(',', '.')
        else:
            clean_str = clean_str.replace(',', '')
    elif last_comma != -1:
        if clean_str.count(',') > 1 or len(clean_str) - last_comma - 1 == 3:
            clean_str = clean_str.replace(',', '')
        else:
            clean_str = clean_str.replace(',', '.')
    else:
        if clean_str.count('.') > 1:
            clean_str = clean_str.replace('.', '')
    try:
        val = float(clean_str)
        if val <= 0: return None
        if is_usd:
            usd_price = await stellar.get_shx_usd_price()
            if not usd_price or usd_price <= 0: return None
            shx_amount = round(val / usd_price, 7)
            return {"shx": shx_amount, "was_usd": True, "usd_input": val, "rate": usd_price}
        return {"shx": val, "was_usd": False, "usd_input": None, "rate": None}
    except ValueError:
        return None


async def get_unique_users_from_string(guild: discord.Guild, input_str: str, exclude_id: str = None) -> list[discord.Member]:
    """Extract unique Members from a string containing mentions of users and roles."""
    import re
    user_ids = set(re.findall(r'<@!?(\d+)>', input_str))
    role_ids = set(re.findall(r'<@&(\d+)>', input_str))
    
    unique_members = {}
    
    # Process user mentions
    for uid_str in user_ids:
        uid = int(uid_str)
        if str(uid) == exclude_id: continue
        member = guild.get_member(uid)
        if not member:
            try: member = await guild.fetch_member(uid)
            except: continue
        if member and not member.bot:
            unique_members[member.id] = member
            
    # Process role mentions
    for rid_str in role_ids:
        rid = int(rid_str)
        role = guild.get_role(rid)
        if role:
            # Ensure guild is chunked for role.members
            if not role.members and not guild.chunked:
                try: await guild.chunk(cache=True)
                except: pass
            
            members = role.members
            if not members:
                try:
                    # fetch_members is heavy, use with caution but necessary if cache fails
                    async for m in guild.fetch_members(limit=None):
                        if role in m.roles and not m.bot and str(m.id) != exclude_id:
                            unique_members[m.id] = m
                except Exception as e:
                    logger.warning(f"Failed to fetch members for role {role.name}: {e}")
            else:
                for m in members:
                    if not m.bot and str(m.id) != exclude_id:
                        unique_members[m.id] = m
                        
    return list(unique_members.values())

async def parse_multiple_each_input(guild: discord.Guild, input_str: str, exclude_id: str = None) -> list[tuple[discord.Member, float]]:
    """Parse a string like '@user1 10, @user2 $5' into (Member, SHx_amount) pairs."""
    import re
    # Pattern: <@!?ID> followed by an optional $ and numbers/commas/decimals/usd
    pattern = r'(<@!?\d+>)\s*[:=]?\s*([\$]?(?:[\d,]*\.)?[\d,]+(?:usd)?)'
    matches = re.findall(pattern, input_str, re.IGNORECASE)
    
    results = []
    seen_ids = set()
    
    for mention, amt_str in matches:
        uid = int(re.search(r'\d+', mention).group())
        if str(uid) == exclude_id or uid in seen_ids: continue
        
        member = guild.get_member(uid)
        if not member:
            try: member = await guild.fetch_member(uid)
            except: continue
            
        if member and not member.bot:
            parsed_amt = await parse_amount(amt_str)
            if parsed_amt and parsed_amt > 0:
                results.append((member, parsed_amt))
                seen_ids.add(uid)
                
    return results

# ── Select Menu & Modal for Multi-Tip ──────────────────────────────────────────

class MultiTipEachModal(discord.ui.Modal):
    def __init__(self, members: list[discord.Member], reason: str = None):
        super().__init__(title="Enter Tip Amounts")
        self.members = members
        self.reason = reason
        self.inputs = []

        for member in members:
            text_input = discord.ui.TextInput(
                label=f"Amount for {member.display_name}",
                placeholder="e.g. 100 or $5",
                min_length=1,
                max_length=20,
                required=True
            )
            self.add_item(text_input)
            self.inputs.append((member, text_input))

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        sender_id = str(interaction.user.id)
        
        tips = []
        for member, text_input in self.inputs:
            amount = await parse_amount(text_input.value)
            if amount is None:
                await interaction.followup.send(f"❌ Invalid amount for {member.display_name}: `{text_input.value}`", ephemeral=True)
                return
            tips.append((member, amount))

        total_needed = sum(a for _, a in tips)
        sender_bal = await db.get_internal_balance(sender_id)
        if sender_bal < total_needed:
            await interaction.followup.send(f"❌ Total required: **{total_needed:,.2f} SHx**, but you only have **{sender_bal:,.2f} SHx**.", ephemeral=True)
            return

        success_list = []
        for member, amount in tips:
            recipient_id = str(member.id)
            await db.get_or_create_user(recipient_id)
            success = await db.transfer_internal(sender_id, recipient_id, amount, 0.0, self.reason or "Multi-tip selection")
            if success:
                success_list.append(f"{member.mention}: {amount:,.2f} SHx")

        embed = _footer(discord.Embed(title="📊 Multi-Tip Selection Summary", color=SUCCESS_COLOR))
        embed.add_field(name="Total Sent", value=f"**{total_needed:,.2f} SHx**", inline=False)
        if success_list:
            embed.add_field(name="✅ Successful Tips", value="\n".join(success_list), inline=False)
        if self.reason:
            embed.add_field(name="Reason", value=self.reason, inline=False)
        
        await interaction.followup.send(embed=embed)

class RoleMemberView(discord.ui.View):
    def __init__(self, role: discord.Role, reason: str = None):
        super().__init__(timeout=180)
        self.role = role
        self.reason = reason
        
        # Get members of the role (filter bots)
        members = [m for m in role.members if not m.bot][:25]
        if not members:
            return

        options = [
            discord.SelectOption(label=m.display_name, value=str(m.id), description=f"ID: {m.id}") 
            for m in members
        ]
        
        self.select = discord.ui.Select(
            placeholder=f"Select up to 5 members of {role.name}...",
            min_values=1,
            max_values=min(5, len(members)),
            options=options
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        selected_ids = self.select.values
        selected_members = [interaction.guild.get_member(int(uid)) for uid in selected_ids]
        selected_members = [m for m in selected_members if m]
        
        if not selected_members:
            await interaction.response.send_message("❌ Error identifying members. Try again.", ephemeral=True)
            return

        modal = MultiTipEachModal(selected_members, self.reason)
        await interaction.response.send_modal(modal)

# ══════════════════════════════════════════════════════════════════════════════
# COMMANDS — define ALL commands BEFORE on_ready so they exist in the tree
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

    # Sync username on link request to ensure dashboard shows it
    await db.get_or_create_user(discord_id, username=interaction.user.display_name)
    token = await db.create_link_token(discord_id)
    link_url = f"{WEB_BASE_URL}/register?token={token}"

    embed = _footer(discord.Embed(
        title="🔗 Verify Your Stellar Wallet",
        description=(
            "To withdraw your tips, you must verify your Stellar address using **Freighter**, **LOBSTR**, or **xBull**.\n\n"
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
        await db.get_or_create_user(discord_id, username=interaction.user.display_name)
        balance = await db.get_internal_balance(discord_id)

        embed = _footer(discord.Embed(title="💰 Your SHx Tip Balance", color=EMBED_COLOR))
        embed.add_field(name="Available Balance", value=f"**{balance:,.2f} SHx**", inline=False)
        
        # Show USD equivalent
        usd_price = await stellar.get_shx_usd_price()
        if usd_price and usd_price > 0:
            usd_equiv = balance * usd_price
            embed.add_field(name="USD Value", value=f"~**${usd_equiv:,.2f}** (@ ${usd_price:.6f}/SHx)", inline=False)
        
        embed.add_field(
            name="Tip others",
            value="Use `/tip @user amount` to send SHx. You can also use `$5` to tip in USD!",
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

    embed.set_image(url=f"https://quickchart.io/qr?text={stellar.HOUSE_ACCOUNT_PUBLIC}&size=150")

    await interaction.followup.send(
        content="⚠️ **IMPORTANT**: You MUST include the Memo ID or your deposit will be lost.",
        embed=embed, ephemeral=True
    )

# ── /withdraw ─────────────────────────────────────────────────────────────────
@bot.tree.command(name="withdraw", description="Prepare a withdrawal of SHx to your external Stellar wallet")
@app_commands.describe(
    amount="Amount of SHx, USD, or 'all' (e.g. 100, $5.00, or all)", 
    destination="Optional: Your Stellar address (defaults to your linked wallet)"
)
async def withdraw_command(interaction: Interaction, amount: str, destination: str = None):
    logger.info(f"COMMAND | /withdraw | User: {interaction.user} ({interaction.user.id}) | Amount: {amount} | Dest: {destination}")
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)

    # 1. Resolve Destination
    linked_key = await db.get_user_stellar_key(discord_id)
    if not destination:
        if not linked_key:
            await interaction.followup.send("❌ Your Stellar wallet is not linked AND you didn't provide a destination. Use `/link` first (supports **Freighter**, **LOBSTR**, or **xBull**) or specify an address manually.", ephemeral=True)
            return
        destination = linked_key
    elif not (destination.startswith("G") and len(destination) == 56):
        await interaction.followup.send("❌ Invalid Stellar address provided. Must start with 'G' and be 56 characters.", ephemeral=True)
        return

    # 2. Resolve Amount
    current_bal = await db.get_internal_balance(discord_id)
    if amount.lower().strip() == "all":
        if current_bal <= 0:
            await interaction.followup.send("❌ Your balance is 0 SHx. Nothing to withdraw.", ephemeral=True)
            return
        amount_f = current_bal
    else:
        parsed_amount = await parse_amount(amount)
        if parsed_amount is None or parsed_amount <= 0:
            await interaction.followup.send("❌ Invalid amount. Enter a positive number, a fiat string (like `$5`), or type `all`.", ephemeral=True)
            return
        amount_f = parsed_amount

    if amount_f > current_bal:
        await interaction.followup.send(f"❌ Insufficient balance. You have **{current_bal:,.2f} SHx**.", ephemeral=True)
        return

    # 2.5 Check House Account Liquidity
    house_bal = await stellar.get_shx_balance(stellar.HOUSE_ACCOUNT_PUBLIC)
    if house_bal is not None and house_bal < amount_f:
        logger.error(f"HOUSE ACCOUNT LOW LIQUIDITY | Needs {amount_f} but has {house_bal}")
        await interaction.followup.send("❌ The bot's House Account is currently low on liquidity. Please notify an admin or try a smaller amount.", ephemeral=True)
        return

    # 2.6 Check House Account Allowance
    allowance = await stellar.check_shx_allowance(stellar.HOUSE_ACCOUNT_PUBLIC, stellar.SOROBAN_CONTRACT_ID)
    if allowance < amount_f:
        logger.info(f"HOUSE ACCOUNT LOW ALLOWANCE | Needs {amount_f} but has {allowance}. Attempting auto-approve...")
        # Auto-approve a large buffer (1M SHx) to minimize future calls
        approve_res = await stellar.approve_shx(stellar.HOUSE_ACCOUNT_SECRET, amount=1_000_000)
        if approve_res.get("success"):
            logger.info(f"AUTO-APPROVE SUCCESS | Hash: {approve_res.get('hash')}")
            # Quick sleep to allow the ledger to update before the next check/transaction
            await asyncio.sleep(3)
            # Re-check allowance just to be safe
            allowance = await stellar.check_shx_allowance(stellar.HOUSE_ACCOUNT_PUBLIC, stellar.SOROBAN_CONTRACT_ID)
            if allowance < amount_f:
                 await interaction.followup.send("❌ Auto-approval failed to propagate in time. Please try again in a few seconds.", ephemeral=True)
                 return
        else:
            logger.error(f"AUTO-APPROVE FAILED | {approve_res.get('error')}")
            await interaction.followup.send("❌ The bot's House Account has technical permission issues (low allowance). Please notify an admin.", ephemeral=True)
            return

    withdrawal_id = secrets.token_hex(16)
    nonce = int(time.time() * 1000)
    expires_at = int(time.time()) + (15 * 60) # 15 minutes expiration
    
    try:
        # We sign specifically for the target destination
        signature = stellar.sign_withdrawal(destination, amount_f, nonce, expires_at)
    except Exception as e:
        logger.error(f"Failed to sign withdrawal for {discord_id}: {e}")
        await interaction.followup.send("❌ System error generating withdrawal ticket.", ephemeral=True)
        return

    # 4. Atomic Balance Deduction
    await db.get_or_create_user(discord_id, username=interaction.user.display_name)
    await db.add_deposit(discord_id, f"WD_PENDING_{withdrawal_id}", -amount_f)
    await db.create_withdrawal(withdrawal_id, discord_id, destination, amount_f, nonce, signature, expires_at)

    logger.info(f"WITHDRAWAL TICKET | User: {interaction.user.id} | Amt: {amount_f} | Nonce: {nonce} | ID: {withdrawal_id}")

    # 5. Build and Send Response
    token = await db.create_link_token(discord_id)
    claim_url = f"{WEB_BASE_URL}/register?claim_id={withdrawal_id}&token={token}"
    
    embed = _footer(discord.Embed(
        title="🎟️ Withdrawal Ticket Created",
        description=(
            f"You have prepared a withdrawal of **{amount_f:,.2f} SHx**.\n\n"
            f"**Destination**: `{destination[:8]}...{destination[-4:]}`\n\n"
            "To complete this, you must claim it on the dashboard using your Stellar wallet.\n\n"
            "⚠️ **NETWORK FEES**: You will need a small amount of **XLM** in your wallet to pay the Stellar network fee."
        ),
        color=SUCCESS_COLOR
    ))
    embed.add_field(name="Next Step", value=f"**[→ Click here to Claim your SHx]({claim_url})**", inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@withdraw_command.autocomplete('destination')
async def withdraw_destination_autocomplete(interaction: Interaction, current: str):
    discord_id = str(interaction.user.id)
    linked_key = await db.get_user_stellar_key(discord_id)
    choices = []
    if linked_key:
        choices.append(app_commands.Choice(name=f"Verified Wallet (LOBSTR/Freighter/xBull): {linked_key[:8]}...{linked_key[-4:]}", value=linked_key))
    
    return [c for c in choices if current.lower() in c.value.lower()][:25]

# ── /tip ──────────────────────────────────────────────────────────────────────

@bot.tree.command(name="tip", description="Tip another user with SHx (supports $ amounts, e.g. $5)")
@app_commands.describe(
    user="The user to tip",
    amount="Amount in SHx or USD (e.g. 100, $5, 2.50usd)",
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
        
    result = await parse_amount_full(amount)
    if result is None:
        await interaction.followup.send("❌ Invalid amount. Use a number like `100` for SHx or `$5` for USD equivalent.", ephemeral=True)
        return
    parsed_amount = result["shx"]


    # Ensure recipient exists in DB (cannot get display_name easily for mention unless in cache, but we try)
    await db.get_or_create_user(recipient_id, username=user.display_name)
    # Also sync sender username
    await db.get_or_create_user(sender_id, username=interaction.user.display_name)


    success = await db.transfer_internal(sender_id, recipient_id, parsed_amount, 0.0, actual_reason)

    if success:
        embed = _footer(discord.Embed(title="\u2705 Tip Sent!", color=SUCCESS_COLOR))
        embed.add_field(name="From", value=interaction.user.mention, inline=True)
        embed.add_field(name="To", value=user.mention, inline=True)
        # Show conversion details if USD was used
        if result["was_usd"]:
            embed.add_field(name="Amount", value=f"**${result['usd_input']:.2f}** = **{parsed_amount:,.2f} SHx**", inline=True)
            embed.add_field(name="Rate", value=f"1 SHx = ${result['rate']:.6f}", inline=True)
        else:
            embed.add_field(name="Amount", value=f"**{parsed_amount:,.2f} SHx**", inline=True)
        if actual_reason:
            embed.add_field(name="Reason", value=actual_reason, inline=False)
        await interaction.followup.send(embed=embed)
        logger.info(f"INTERNAL TIP OK | {sender_id}\u2192{recipient_id} | {parsed_amount} SHx")
    else:
        # PRIVACY FIX: Explicitly scrub balances from the rejection log so nothing is shown in chat!
        await interaction.followup.send(
            f"\u274c Transaction failed due to insufficient funds.\n"
            f"Please type `/balance` to privately check your available SHx.",
            ephemeral=True
        )


# ── /tip-multiple ─────────────────────────────────────────────────────────────

@bot.tree.command(name="tip-multiple", description="Split a total amount among multiple users/roles (supports $)")
@app_commands.describe(
    targets="Mention users and/or roles (e.g. @user1 @role1)",
    amount="Total SHx or USD to split equally (e.g. 100 or $5)",
    reason="Optional reason"
)
async def tip_multiple_command(interaction: Interaction, targets: str, amount: str, reason: Optional[str] = None):
    logger.info(f"COMMAND | /tip-multiple | User: {interaction.user} Targets: {targets} Amount: {amount}")
    await interaction.response.defer()
    
    sender_id = str(interaction.user.id)
    # Role check (standard for role-based tipping features)
    if not isinstance(interaction.user, discord.Member):
        if sender_id not in ADMIN_DISCORD_IDS:
            await interaction.followup.send("❌ This command must be used in a server.", ephemeral=True)
            return
    elif len(interaction.user.roles) <= 1 and sender_id not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ Only users with an assigned role can use `/tip-multiple`.", ephemeral=True)
        return

    result = await parse_amount_full(amount)
    if result is None:
        await interaction.followup.send("❌ Invalid amount. Use `100` for SHx or `$5` for USD equivalent.", ephemeral=True)
        return
    parsed_amount = result["shx"]

    members = await get_unique_users_from_string(interaction.guild, targets, exclude_id=sender_id)
    if not members:
        await interaction.followup.send("❌ No valid recipient users or roles found in the input. Ensure you mention them properly.", ephemeral=True)
        return

    amount_per_member = round(parsed_amount / len(members), 7)
    if amount_per_member < 0.0000001:
        await interaction.followup.send(f"❌ Total amount too small to split among {len(members)} users.", ephemeral=True)
        return

    sender_bal = await db.get_internal_balance(sender_id)
    if sender_bal < parsed_amount:
        await interaction.followup.send(f"❌ Insufficient balance. You need **{parsed_amount:,.2f} SHx**, but you only have **{sender_bal:,.2f} SHx**.", ephemeral=True)
        return

    success_count = 0
    # Sync sender username
    await db.get_or_create_user(sender_id, username=interaction.user.display_name)
    for member in members:
        recipient_id = str(member.id)
        await db.get_or_create_user(recipient_id, username=member.display_name)
        success = await db.transfer_internal(sender_id, recipient_id, amount_per_member, 0.0, reason or "Multi-tip split")
        if success:
            success_count += 1
            
    embed = _footer(discord.Embed(title="\U0001f465 Multi-Tip Split Complete!", color=SUCCESS_COLOR))
    if result["was_usd"]:
        embed.add_field(name="Total Split", value=f"**${result['usd_input']:.2f}** = **{parsed_amount:,.2f} SHx**", inline=True)
        embed.add_field(name="Rate", value=f"1 SHx = ${result['rate']:.6f}", inline=True)
    else:
        embed.add_field(name="Total Split", value=f"**{parsed_amount:,.2f} SHx**", inline=True)
    embed.add_field(name="Recipients", value=f"**{len(members)}**", inline=True)
    embed.add_field(name="Amount Each", value=f"**{amount_per_member:,.4f} SHx**", inline=True)
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    
    await interaction.followup.send(embed=embed)
    logger.info(f"MULTI-TIP OK | {sender_id} split {parsed_amount} among {success_count} users")


# ── /tip-multiple-each ────────────────────────────────────────────────────────

@bot.tree.command(name="tip-multiple-each", description="Send different SHx amounts to multiple users at once")
@app_commands.describe(
    user="Format: @user1 amount, @user2 amount (e.g. @Naugl 10, @Friend $5)",
    role="Select a role to pick specific members to tip",
    reason="Optional reason"
)
async def tip_multiple_each_command(interaction: Interaction, user: Optional[str] = None, role: Optional[discord.Role] = None, reason: Optional[str] = None):
    logger.info(f"COMMAND | /tip-multiple-each | User: {interaction.user} Role: {role.name if role else 'N/A'}")
    
    if not user and not role:
        await interaction.response.send_message("❌ Please provide either a `user` list OR select a `role` to pick members from.", ephemeral=True)
        return

    sender_id = str(interaction.user.id)
    # Role check
    if not isinstance(interaction.user, discord.Member):
        if sender_id not in ADMIN_DISCORD_IDS:
            await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)
            return
    elif len(interaction.user.roles) <= 1 and sender_id not in ADMIN_DISCORD_IDS:
        await interaction.response.send_message("❌ Only users with an assigned role can use `/tip-multiple-each`.", ephemeral=True)
        return

    # Flow A: Role selection
    if role:
        # Ensure guild is chunked for role.members
        if not role.members and not interaction.guild.chunked:
            await interaction.response.defer(ephemeral=True)
            try: await interaction.guild.chunk(cache=True)
            except: pass
        
        view = RoleMemberView(role, reason)
        if not view.children:
            await interaction.response.send_message(f"❌ No valid (non-bot) members found in role {role.name}.", ephemeral=True)
            return
        
        await interaction.response.send_message(f"👥 Select members from **{role.name}** to tip:", view=view, ephemeral=True)
        return

    # Flow B: String parsing (user parameter)
    await interaction.response.defer()
    tips = await parse_multiple_each_input(interaction.guild, user, exclude_id=sender_id)
    if not tips:
        await interaction.followup.send("❌ No valid tips found. Ensure format is `@user 100, @user2 50`", ephemeral=True)
        return

    total_amount = sum(amt for _, amt in tips)
    sender_bal = await db.get_internal_balance(sender_id)
    if sender_bal < total_amount:
        await interaction.followup.send(f"❌ Insufficient balance for all tips. Total required: **{total_amount:,.2f} SHx**, but you have **{sender_bal:,.2f} SHx**.", ephemeral=True)
        return

    success_list = []
    fail_list = []
    
    for member, amount in tips:
        recipient_id = str(member.id)
        await db.get_or_create_user(recipient_id)
        success = await db.transfer_internal(sender_id, recipient_id, amount, 0.0, reason or "Multi-tip each")
        if success:
            success_list.append(f"{member.mention}: {amount:,.2f} SHx")
        else:
            fail_list.append(f"{member.mention}: {amount:,.2f} SHx (Insufficient funds?)")

    embed = _footer(discord.Embed(title="📊 Multi-Tip Each Summary", color=SUCCESS_COLOR))
    success_total = sum(amt for m, amt in tips if any(m.mention in s for s in success_list))
    embed.add_field(name="Total Sent", value=f"**{success_total:,.2f} SHx**", inline=False)
    
    if success_list:
        embed.add_field(name="✅ Successful Tips", value="\n".join(success_list[:15]) + ("\n..." if len(success_list) > 15 else ""), inline=False)
    if fail_list:
        embed.add_field(name="❌ Failed Tips", value="\n".join(fail_list), inline=False)
        embed.color = ERROR_COLOR
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)

    await interaction.followup.send(embed=embed)
    logger.info(f"MULTI-TIP-EACH OK | {sender_id} sent {success_total} SHx to {len(success_list)} users")




# ── /create-role ──────────────────────────────────────────────────────────────

@bot.tree.command(name="create-role", description="[Admin] Create a new Discord role")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(name="Name of the role", hex_color="Hex color code (e.g. 0x5865F2)")
async def create_role_command(interaction: Interaction, name: str, hex_color: str):
    logger.info(f"COMMAND | /create-role | User: {interaction.user} Name: {name} Color: {hex_color}")
    await interaction.response.defer(ephemeral=True)
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ You do not have permission to use this command.", ephemeral=True)
        return
    
    try:
        color_int = int(hex_color.replace("#", ""), 16)
        role = await interaction.guild.create_role(name=name, color=discord.Color(color_int), reason="Created via bot command")
        await interaction.followup.send(f"✅ Role {role.mention} created successfully.", ephemeral=True)
    except ValueError:
        await interaction.followup.send("❌ Invalid hex color. Please use format like `0x5865F2` or `#5865F2`.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ Failed to create role. The bot lacks `Manage Roles` permissions.", ephemeral=True)
    except Exception as e:
        logger.error(f"Failed to create role: {e}")
        await interaction.followup.send(f"❌ Failed to create role: {str(e)}", ephemeral=True)


# ── /assign-role ──────────────────────────────────────────────────────────────

@bot.tree.command(name="assign-role", description="[Admin] Assign a role to a user")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user="The user to assign", role="The role to assign")
async def assign_role_command(interaction: Interaction, user: discord.Member, role: discord.Role):
    logger.info(f"COMMAND | /assign-role | User: {interaction.user} Target: {user} Role: {role.name}")
    await interaction.response.defer(ephemeral=True)
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ You do not have permission to use this command.", ephemeral=True)
        return
        
    try:
        await user.add_roles(role, reason="Assigned via bot command")
        await interaction.followup.send(f"✅ Role {role.mention} assigned to {user.mention}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ Failed to assign role. Ensure the bot's role is positioned *higher* than the role being assigned in server settings.", ephemeral=True)
    except Exception as e:
        logger.error(f"Failed to assign role: {e}")
        await interaction.followup.send(f"❌ Failed to assign role: {str(e)}", ephemeral=True)


# ── /tip-role ─────────────────────────────────────────────────────────────────

async def get_role_members(interaction: Interaction, role: discord.Role, sender_id: str) -> List[discord.Member]:
    """Helper to fetch valid, non-bot members of a role (excluding sender)."""
    members = role.members
    # Fallback 1: guild not yet chunked
    if not members and not interaction.guild.chunked:
        try:
            await interaction.guild.chunk(cache=True)
            members = role.members
        except Exception as ce:
            logger.warning(f"Guild chunk failed: {ce}")

    # Fallback 2: fetch members directly from the API
    if not members:
        try:
            fetched = [m async for m in interaction.guild.fetch_members(limit=None)]
            members = [m for m in fetched if role in m.roles]
        except Exception as fe:
            logger.error(f"Failed to fetch members via API: {fe}")

    return [m for m in members if not m.bot and str(m.id) != sender_id]


# ── /tip-role ─────────────────────────────────────────────────────────────────

@bot.tree.command(name="tip-role", description="Divide a total amount equally among all members of a role (supports $)")
@app_commands.describe(role="The role to tip", amount="Total SHx or USD to split equally (e.g. 100 or $5)")
async def tip_role_command(interaction: Interaction, role: discord.Role, amount: str):
    logger.info(f"COMMAND | /tip-role | User: {interaction.user} Role: {role.name} Total: {amount}")
    await interaction.response.defer()
    
    sender_id = str(interaction.user.id)
    if not isinstance(interaction.user, discord.Member):
        if sender_id not in ADMIN_DISCORD_IDS:
            await interaction.followup.send("❌ This command must be used in a server.", ephemeral=True)
            return
    elif len(interaction.user.roles) <= 1 and sender_id not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ Only users with an assigned role can use this command.", ephemeral=True)
        return

    result = await parse_amount_full(amount)
    if result is None or result["shx"] <= 0:
        await interaction.followup.send("❌ Invalid amount. Use `100` for SHx or `$5` for USD equivalent.", ephemeral=True)
        return
    parsed_amount = result["shx"]

    valid_members = await get_role_members(interaction, role, sender_id)
    if not valid_members:
        await interaction.followup.send(f"❌ No valid recipient members found in the **{role.name}** role (bots and yourself are excluded).", ephemeral=True)
        return

    amount_per_member = round(parsed_amount / len(valid_members), 7)
    if amount_per_member < 0.0000001:
        await interaction.followup.send(f"❌ Total amount too small to split among {len(valid_members)} members.", ephemeral=True)
        return

    sender_bal = await db.get_internal_balance(sender_id)
    if sender_bal < parsed_amount:
        await interaction.followup.send(f"❌ Insufficient balance. You need **{parsed_amount:,.2f} SHx**, but only have **{sender_bal:,.2f} SHx**.", ephemeral=True)
        return

    success_count = 0
    for member in valid_members:
        recipient_id = str(member.id)
        await db.get_or_create_user(recipient_id)
        if await db.transfer_internal(sender_id, recipient_id, amount_per_member, 0.0, f"Role Split: {role.name}"):
            success_count += 1
            
    embed = _footer(discord.Embed(title="\U0001f3ad Role Split Tip Complete!", color=SUCCESS_COLOR))
    embed.add_field(name="Role Tipped", value=role.mention, inline=False)
    if result["was_usd"]:
        embed.add_field(name="Total Distributed", value=f"**${result['usd_input']:.2f}** = **{parsed_amount:,.2f} SHx**", inline=True)
    else:
        embed.add_field(name="Total Distributed", value=f"**{parsed_amount:,.2f} SHx**", inline=True)
    embed.add_field(name="Amount Each", value=f"**{amount_per_member:,.4f} SHx**", inline=True)
    embed.add_field(name="Members Tipped", value=f"**{success_count}**", inline=True)
    
    await interaction.followup.send(embed=embed)
    logger.info(f"ROLE SPLIT OK | {sender_id}\u2192{role.name} | {amount_per_member} SHx x {success_count}")


# ── /tip-role-each ────────────────────────────────────────────────────────────

@bot.tree.command(name="tip-role-each", description="Send a specific amount to every member of a role (supports $)")
@app_commands.describe(role="The role to tip", amount="Amount per member in SHx or USD (e.g. 10 or $1)")
async def tip_role_each_command(interaction: Interaction, role: discord.Role, amount: str):
    logger.info(f"COMMAND | /tip-role-each | User: {interaction.user} Role: {role.name} Each: {amount}")
    await interaction.response.defer()
    
    sender_id = str(interaction.user.id)
    if not isinstance(interaction.user, discord.Member):
        if sender_id not in ADMIN_DISCORD_IDS:
            await interaction.followup.send("❌ This command must be used in a server.", ephemeral=True)
            return
    elif len(interaction.user.roles) <= 1 and sender_id not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ Only users with an assigned role can use this command.", ephemeral=True)
        return

    result = await parse_amount_full(amount)
    if result is None or result["shx"] <= 0:
        await interaction.followup.send("❌ Invalid amount. Use `10` for SHx or `$1` for USD equivalent.", ephemeral=True)
        return
    parsed_single_amount = result["shx"]

    valid_members = await get_role_members(interaction, role, sender_id)
    num_members = len(valid_members)
    if not valid_members:
        await interaction.followup.send(f"❌ No valid recipient members found in the **{role.name}** role.", ephemeral=True)
        return

    total_needed = parsed_single_amount * num_members
    sender_bal = await db.get_internal_balance(sender_id)
    if sender_bal < total_needed:
        await interaction.followup.send(f"❌ Insufficient balance. You need **{total_needed:,.2f} SHx** ({parsed_single_amount:,.2f} x {num_members} members), but only have **{sender_bal:,.2f} SHx**.", ephemeral=True)
        return

    success_count = 0
    for member in valid_members:
        recipient_id = str(member.id)
        await db.get_or_create_user(recipient_id)
        if await db.transfer_internal(sender_id, recipient_id, parsed_single_amount, 0.0, f"Role Each: {role.name}"):
            success_count += 1
            
    embed = _footer(discord.Embed(title="\U0001f3ad Role Tipping Each Complete!", color=SUCCESS_COLOR))
    embed.add_field(name="Role Tipped", value=role.mention, inline=False)
    if result["was_usd"]:
        embed.add_field(name="Amount Per Member", value=f"**${result['usd_input']:.2f}** = **{parsed_single_amount:,.2f} SHx**", inline=True)
    else:
        embed.add_field(name="Amount Per Member", value=f"**{parsed_single_amount:,.2f} SHx**", inline=True)
    embed.add_field(name="Members Tipped", value=f"**{success_count}**", inline=True)
    embed.add_field(name="Total Spent", value=f"**{(parsed_single_amount * success_count):,.2f} SHx**", inline=False)
    
    await interaction.followup.send(embed=embed)
    logger.info(f"ROLE EACH OK | {sender_id}\u2192{role.name} | {parsed_single_amount} SHx x {success_count}")

# ── /price ────────────────────────────────────────────────────────────────────

@bot.tree.command(name="price", description="Check the current SHx price and convert amounts")
@app_commands.describe(amount="Optional: Amount to convert (e.g. $10, 500shx)")
async def price_command(interaction: Interaction, amount: str = None):
    logger.info(f"COMMAND | /price | User: {interaction.user} | Amount: {amount}")
    await interaction.response.defer(ephemeral=True)
    
    usd_price = await stellar.get_shx_usd_price()
    xlm_price = await stellar.get_shx_xlm_price()
    
    if not usd_price or usd_price <= 0:
        await interaction.followup.send("\u274c Could not fetch SHx price. Oracle unavailable.", ephemeral=True)
        return
    
    embed = _footer(discord.Embed(title="\U0001f4b9 SHx Price", color=EMBED_COLOR))
    embed.add_field(name="USD Price", value=f"**1 SHx = ${usd_price:.6f}**", inline=True)
    if xlm_price and xlm_price > 0:
        embed.add_field(name="XLM Price", value=f"**1 SHx = {xlm_price:.7f} XLM**", inline=True)
    
    # Quick reference conversions
    ref_lines = []
    for usd_val in [1, 5, 10, 25, 50, 100]:
        shx_equiv = round(usd_val / usd_price, 2)
        ref_lines.append(f"${usd_val} = **{shx_equiv:,.2f} SHx**")
    embed.add_field(name="Quick Reference", value="\n".join(ref_lines), inline=False)
    
    # Optional conversion
    if amount:
        result = await parse_amount_full(amount)
        if result:
            if result["was_usd"]:
                embed.add_field(
                    name="\U0001f504 Your Conversion", 
                    value=f"**${result['usd_input']:.2f}** = **{result['shx']:,.2f} SHx**", 
                    inline=False
                )
            else:
                usd_equiv = result["shx"] * usd_price
                embed.add_field(
                    name="\U0001f504 Your Conversion", 
                    value=f"**{result['shx']:,.2f} SHx** = **${usd_equiv:.2f} USD**", 
                    inline=False
                )
    
    embed.set_footer(text="SHx Tip Bot \u2022 Prices via CoinGecko / Stellar DEX")
    await interaction.followup.send(embed=embed, ephemeral=True)

# ── /airdrop ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="airdrop", description="Create an SHx airdrop in the current channel")
@app_commands.describe(
    total_amount="Total SHx or USD (e.g. 100 or $10)", 
    duration_minutes="Optional expiration time in minutes",
    duration_hours="Optional expiration time in hours",
    duration_days="Optional expiration time in days",
    claims="Legacy parameter (ignored)"
)
async def airdrop_command(
    interaction: Interaction, 
    total_amount: str, 
    duration_minutes: Optional[int] = None,
    duration_hours: Optional[int] = None,
    duration_days: Optional[int] = None,
    claims: Optional[int] = None
):
    logger.info(f"COMMAND | /airdrop | User: {interaction.user} Total: {total_amount} Mins: {duration_minutes} Hrs: {duration_hours} Days: {duration_days}")
    await interaction.response.defer()
    creator_id = str(interaction.user.id)
    
    parsed_amount = await parse_amount(total_amount)
    if parsed_amount is None or parsed_amount <= 0:
        await interaction.followup.send("❌ Invalid amount. Must be > 0.", ephemeral=True)
        return
        
    # Check balance
    bal = await db.get_internal_balance(creator_id)
    if bal < parsed_amount:
        await interaction.followup.send(f"❌ Insufficient balance. You have **{bal:,.2f} SHx**.", ephemeral=True)
        return
        
    # Deduct upfront to "reserve" the funds (System account 'AIRDROP_RESERVE')
    success = await db.transfer_internal(creator_id, AIRDROP_RESERVE, parsed_amount, 0.0, f"Airdrop Pool Funding")
    if not success:
        await interaction.followup.send("❌ Error reserving funds for airdrop.", ephemeral=True)
        return

    total_mins = 0
    if duration_minutes: total_mins += duration_minutes
    if duration_hours: total_mins += duration_hours * 60
    if duration_days: total_mins += duration_days * 1440
    # Default to 24 hours if none provided
    if total_mins == 0: 
        total_mins = 1440
        duration_days = 1
    
    airdrop_id = secrets.token_hex(4)
    await db.create_airdrop(
        airdrop_id, creator_id, parsed_amount, "Channel Airdrop", total_mins
    )
    
    expires_str = ""
    expires_parts = []
    if duration_days: expires_parts.append(f"{duration_days} day(s)")
    if duration_hours: expires_parts.append(f"{duration_hours} hour(s)")
    if duration_minutes: expires_parts.append(f"{duration_minutes} minute(s)")
    
    if expires_parts:
        expires_str = f"\n⏳ *Expires in {', '.join(expires_parts)}*"
    
    embed = _footer(discord.Embed(
        title="🪂 SHx Airdrop!",
        description=f"{interaction.user.mention} is dropping **{parsed_amount:,.2f} SHx**!\n" +
                    f"The total pool will be **split equally** among everyone who clicks below!{expires_str}",
        color=0xFF00AA
    ))
    embed.add_field(name="Total Pool", value=f"**{parsed_amount:,.2f} SHx**", inline=True)
    embed.add_field(name="Duration", value=f"**{', '.join(expires_parts)}**", inline=True)
    
    view = AirdropView(airdrop_id)
    msg = await interaction.followup.send(embed=embed, view=view)
    await db.update_airdrop_message(airdrop_id, str(msg.channel.id), str(msg.id))


# ── Background Task: Airdrop Processing ──────────────────────────────────────────

@tasks.loop(seconds=60)
async def process_airdrops():
    """Background task to distribute funds for expired airdrops."""
    try:
        expired = await db.get_expired_airdrops()
        if not expired:
            return

        for ad in expired:
            airdrop_id = ad["id"]
            creator_id = ad["creator_discord_id"]
            total_amount = ad["total_amount"]
            
            participants = await db.get_airdrop_participants(airdrop_id)
            count = len(participants)
            
            # Use channel ID if available, otherwise fallback to system log
            # For simplicity, we assume the bot can find the channel from cache or ID
            # In index.html/bot.py context, we usually have a guild-only bot
            guild = bot.get_guild(DISCORD_GUILD_ID)
            
            if count > 0:
                share = round(total_amount / count, 2)
                # Ensure we don't over-distribute due to rounding up
                if share * count > total_amount:
                    share = total_amount / count # True precision
                
                success_count = 0
                for uid in participants:
                    # Transfer from System Hold to user
                    if await db.transfer_internal(AIRDROP_RESERVE, uid, share, 0.0, f"Airdrop {airdrop_id} Split"):
                        success_count += 1
                
                logger.info(f"AIRDROP | {airdrop_id} | Distributed {total_amount} SHx among {count} users.")
                
                # Try to announce in the channel
                # We don't store channel_id in airdrops table currently, but we can try to find the 
                # original message if we had stored it. For now, let's log and optionally broadcast
                # to a general channel if DISCORD_GUILD_ID is set.
                if guild:
                    # Look for a system/announcement channel or use a common one
                    # For now, let's just log. If we want to post to the specific channel,
                    # we would need to have stored channel_id in the airdrops table.
                    pass
            else:
                # Refund creator if 0 participants
                await db.transfer_internal(AIRDROP_RESERVE, creator_id, total_amount, 0.0, f"Airdrop {airdrop_id} Refund (0 participants)")
                logger.info(f"AIRDROP | {airdrop_id} | Refunded {total_amount} SHx to {creator_id} (No participants)")

            # Edit the original discord message to show it is expired
            cid = ad.get("channel_id")
            mid = ad.get("message_id")
            if cid and mid and guild:
                channel = guild.get_channel(int(cid))
                if channel:
                    try:
                        msg = await channel.fetch_message(int(mid))
                        if msg:
                            embed = msg.embeds[0] if msg.embeds else discord.Embed(title="Airdrop")
                            # Add information that it is expired
                            embed.color = discord.Color.dark_gray()
                            
                            class ExpiredView(discord.ui.View):
                                def __init__(self):
                                    super().__init__(timeout=None)
                                    btn = discord.ui.Button(label="Expired", style=discord.ButtonStyle.secondary, disabled=True, custom_id="expired_btn")
                                    self.add_item(btn)
                                    
                            await msg.edit(embed=embed, view=ExpiredView())
                    except Exception as e:
                        logger.warning(f"Could not edit expired airdrop message: {e}")

            # Close the airdrop
            await db.close_airdrop(airdrop_id)

    except Exception as e:
        logger.error(f"Error in process_airdrops task: {e}", exc_info=True)

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

    # Chunk the guild so role.members is populated in cache
    guild = bot.get_guild(DISCORD_GUILD_ID)
    if guild and not guild.chunked:
        try:
            await guild.chunk(cache=True)
            logger.info(f"Guild member cache populated ({guild.member_count} members).")
        except Exception as e:
            logger.warning(f"Guild chunk failed (non-fatal): {e}")

    try:
        # Simplified Sync: Copy global commands and sync to our specific guild
        # This resolves duplicate registrations and ensures immediate updates
        guild_obj = discord.Object(id=DISCORD_GUILD_ID)
        bot.tree.copy_global_to(guild=guild_obj)
        await bot.tree.sync(guild=guild_obj)
        logger.info(f"Slash command tree synchronized to guild {DISCORD_GUILD_ID}.")
    except Exception as e:
        logger.error(f"Command registration/sync failed: {e}", exc_info=True)

    # Start background tasks
    if not process_airdrops.is_running():
        process_airdrops.start()
        logger.info("Background task process_airdrops started.")
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
                tx_url = stellar.get_explorer_url(tx_hash)
                embed = _footer(discord.Embed(
                    title="💰 Deposit Confirmed",
                    description=f"Your account has been credited with **{amount_shx:,.2f} SHx**.\n\n[View on Stellar Expert]({tx_url})",
                    color=SUCCESS_COLOR
                ))
                try:
                    await user.send(embed=embed)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error processing deposit {tx_hash}: {e}")

    # Start the live monitor (now with automatic startup sweep)
    logger.info(f"DASHBOARD | Starting deposit monitor for {stellar.HOUSE_ACCOUNT_PUBLIC[:8]}...")
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



# ── Admin Sync ────────────────────────────────────────────────────────────────

@bot.tree.command(name="bot-sync", description="[Admin] Sync the bot's command tree with Discord")
@app_commands.default_permissions(administrator=True)
async def bot_sync_command(interaction: Interaction):
    logger.info(f"COMMAND | /bot-sync | User: {interaction.user}")
    await interaction.response.defer(ephemeral=True)
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ You do not have permission to use this command.", ephemeral=True)
        return
    
    try:
        # Sync globally
        synced = await bot.tree.sync()
        await interaction.followup.send(f"✅ Successfully synced {len(synced)} commands with Discord. New UI changes (like /withdraw autocomplete) should be visible soon.", ephemeral=True)
    except Exception as e:
        logger.error(f"Failed to sync command tree: {e}")
        await interaction.followup.send(f"❌ Failed to sync: {str(e)}", ephemeral=True)


# ── /distribute ───────────────────────────────────────────────────────────────

@bot.tree.command(name="distribute", description="[Admin] Manually fund a user's internal SHx balance")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user="The user to fund", amount="Amount of SHx to grant")
async def distribute_command(interaction: Interaction, user: discord.User, amount: str):
    logger.info(f"COMMAND | /distribute | User: {interaction.user} Target: {user} Amount: {amount}")
    await interaction.response.defer(ephemeral=True)
    if str(interaction.user.id) not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ You do not have permission to use this command.", ephemeral=True)
        return
        
    parsed_amt = await parse_amount(amount)
    if not parsed_amt or parsed_amt <= 0:
        await interaction.followup.send("❌ Invalid amount.", ephemeral=True)
        return
        
    try:
        await db.get_or_create_user(str(user.id))
        await db.admin_fund_internal(str(user.id), parsed_amt)
        
        embed = _footer(discord.Embed(title="💳 Internal Funding Complete", color=SUCCESS_COLOR))
        embed.add_field(name="Recipient", value=user.mention, inline=True)
        embed.add_field(name="Amount Granted", value=f"**{parsed_amt:,.2f} SHx**", inline=True)
        embed.set_description(f"Successfully funded {user.display_name}'s internal balance from the House reserve.")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        # Notify the user too!
        try:
            await user.send(f"🏦 An admin has credited your account with **{parsed_amt:,.2f} SHx**!")
        except:
            pass
    except Exception as e:
        logger.error(f"Distribute command error: {e}")
        await interaction.followup.send(f"❌ Failed to distribute funds: {str(e)}", ephemeral=True)


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
