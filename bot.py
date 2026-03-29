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
    pattern = r'(<@!?\d+>)\s*[:=]?\s*([\$]?[\d,]+(?:\.\d+)?(?:usd)?)'
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

    embed.set_image(url=f"https://quickchart.io/qr?text={stellar.HOUSE_ACCOUNT_PUBLIC}&size=150")

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

    # User MUST be linked to withdraw on-chain
    user_key = await db.get_user_stellar_key(discord_id)
    if not user_key:
        await interaction.followup.send("❌ Your Stellar wallet is not linked. Use `/link` first or use the dashboard.", ephemeral=True)
        return

    # Generate claim ticket
    withdrawal_id = secrets.token_hex(16)
    nonce = int(time.time() * 1000)
    
    try:
        signature = stellar.sign_withdrawal(user_key, amount_f, nonce)
    except Exception as e:
        logger.error(f"Failed to sign withdrawal for {discord_id}: {e}")
        await interaction.followup.send("❌ System error generating withdrawal ticket.", ephemeral=True)
        return

    # Atomic DB: Deduct balance + create pending withdrawal
    # We use a special transfer to a 'LOCK' account or similar, 
    # but for simplicity we'll just deduct it and record the withdrawal.
    await db.add_deposit(discord_id, f"WD_PENDING_{withdrawal_id}", -amount_f)
    await db.create_withdrawal(withdrawal_id, discord_id, user_key, amount_f, nonce, signature)

    claim_url = f"{WEB_BASE_URL}/?claim_id={withdrawal_id}"

    embed = _footer(discord.Embed(
        title="🎟️ Withdrawal Ticket Created",
        description=(
            f"You have prepared a withdrawal of **{amount_f:,.2f} SHx**.\n\n"
            "To complete this, you must claim it on the dashboard using your Stellar wallet.\n\n"
            "⚠️ **NETWORK FEES**: Since you are withdrawing to your own wallet, you will need a small amount of **XLM** to pay the Stellar network fee."
        ),
        color=SUCCESS_COLOR
    ))
    
    embed.add_field(name="Next Step", value=f"**[→ Click here to Claim your SHx]({claim_url})**", inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)


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


# ── /tip-multiple ─────────────────────────────────────────────────────────────

@bot.tree.command(name="tip-multiple", description="Split a total SHx amount among multiple mentioned users or roles")
@app_commands.describe(
    targets="Mention users and/or roles (e.g. @user1 @role1)",
    amount="Total SHx to split equally among all members (e.g. 100 or $5)",
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

    parsed_amount = await parse_amount(amount)
    if parsed_amount is None:
        await interaction.followup.send("❌ Invalid amount. Enter numbers or a fiat string (e.g. `$5`).", ephemeral=True)
        return

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
    for member in members:
        recipient_id = str(member.id)
        await db.get_or_create_user(recipient_id)
        success = await db.transfer_internal(sender_id, recipient_id, amount_per_member, 0.0, reason or "Multi-tip split")
        if success:
            success_count += 1
            
    embed = _footer(discord.Embed(title="👥 Multi-Tip Split Complete!", color=SUCCESS_COLOR))
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

@bot.tree.command(name="tip-role", description="Split a total SHx amount equally among all members of a role")
@app_commands.describe(role="The role to tip", amount="Total SHx to split equally (e.g. 100 or $5)")
async def tip_role_command(interaction: Interaction, role: discord.Role, amount: str):
    logger.info(f"COMMAND | /tip-role | User: {interaction.user} Role: {role.name} Amount/User: {amount}")
    await interaction.response.defer()
    
    sender_id = str(interaction.user.id)
    
    # Must be in a server to check roles
    if not isinstance(interaction.user, discord.Member):
        if sender_id not in ADMIN_DISCORD_IDS:
            await interaction.followup.send("❌ This command must be used in a server.", ephemeral=True)
            return
    # Must have at least one assigned role (other than @everyone) to use /tip-role
    elif len(interaction.user.roles) <= 1 and sender_id not in ADMIN_DISCORD_IDS:
        await interaction.followup.send("❌ Only users with an assigned role can use `/tip-role`. Users without a role can only tip other individual users using `/tip`.", ephemeral=True)
        return

    parsed_amount = await parse_amount(amount)
    if parsed_amount is None:
        await interaction.followup.send("❌ Invalid amount. Enter numbers or a fiat string (e.g. `$5`).", ephemeral=True)
        return

    members = role.members
    # Fallback 1: guild not yet chunked — request chunking now
    if not members and not interaction.guild.chunked:
        try:
            await interaction.guild.chunk(cache=True)
            members = role.members
        except Exception as ce:
            logger.warning(f"Guild chunk failed in tip-role: {ce}")

    # Fallback 2: still empty — fetch members directly from the API
    if not members:
        try:
            fetched = [m async for m in interaction.guild.fetch_members(limit=None)]
            members = [m for m in fetched if role in m.roles]
            logger.info(f"tip-role: fetched {len(members)} members via API for role {role.name}")
        except Exception as fe:
            logger.error(f"Failed to fetch members for tip-role: {fe}")

    if not members:
        await interaction.followup.send(f"❌ There are no members found in the **{role.name}** role.", ephemeral=True)
        return

    valid_members = [m for m in members if not m.bot and str(m.id) != sender_id]
    if not valid_members:
        await interaction.followup.send(f"❌ There are no valid recipient members in the {role.name} role (bots and yourself are excluded).", ephemeral=True)
        return

    amount_per_member = round(parsed_amount / len(valid_members), 7)
    if amount_per_member < 0.0000001:
        await interaction.followup.send(f"❌ Total amount too small to split among {len(valid_members)} members.", ephemeral=True)
        return

    sender_bal = await db.get_internal_balance(sender_id)
    if sender_bal < parsed_amount:
        await interaction.followup.send(f"❌ Insufficient balance. You need **{parsed_amount:,.2f} SHx** to split among {len(valid_members)} members, but you only have **{sender_bal:,.2f} SHx**.", ephemeral=True)
        return

    success_count = 0
    for member in valid_members:
        recipient_id = str(member.id)
        await db.get_or_create_user(recipient_id)
        success = await db.transfer_internal(sender_id, recipient_id, amount_per_member, 0.0, f"Role tip: {role.name}")
        if success:
            success_count += 1
            
    embed = _footer(discord.Embed(title="🎭 Role Tip Complete!", color=SUCCESS_COLOR))
    embed.add_field(name="Role Tipped", value=role.mention, inline=False)
    embed.add_field(name="Each Member Received", value=f"**{amount_per_member:,.4f} SHx**", inline=True)
    embed.add_field(name="Members Tipped", value=f"**{success_count}** out of {len(valid_members)}", inline=True)
    embed.add_field(name="Total Distributed", value=f"**{(amount_per_member * success_count):,.4f} SHx**", inline=False)
    
    await interaction.followup.send(embed=embed)
    logger.info(f"ROLE TIP OK | {sender_id}→{role.name} | {amount_per_member} SHx x {success_count} members | Total: {amount_per_member * success_count}")

# ── /airdrop ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="airdrop", description="Create an SHx airdrop in the current channel")
@app_commands.describe(
    total_amount="Total SHx or USD (e.g. 100 or $10)", 
    claims="Number of people who can claim", 
    duration_minutes="Optional expiration time in minutes",
    duration_hours="Optional expiration time in hours",
    duration_days="Optional expiration time in days"
)
async def airdrop_command(
    interaction: Interaction, 
    total_amount: str, 
    claims: int, 
    duration_minutes: Optional[int] = None,
    duration_hours: Optional[int] = None,
    duration_days: Optional[int] = None
):
    logger.info(f"COMMAND | /airdrop | User: {interaction.user} Total: {total_amount} Claims: {claims} Mins: {duration_minutes} Hrs: {duration_hours} Days: {duration_days}")
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
        
    total_mins = 0
    if duration_minutes: total_mins += duration_minutes
    if duration_hours: total_mins += duration_hours * 60
    if duration_days: total_mins += duration_days * 1440
    total_mins = total_mins if total_mins > 0 else None
    
    airdrop_id = secrets.token_hex(4)
    await db.create_airdrop(
        airdrop_id, creator_id, parsed_amount, amount_per_claim, claims, "Channel Airdrop", total_mins
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
        description=f"{interaction.user.mention} is dropping **{parsed_amount:,.2f} SHx**!" + expires_str,
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

    # Chunk the guild so role.members is populated in cache
    guild = bot.get_guild(DISCORD_GUILD_ID)
    if guild and not guild.chunked:
        try:
            await guild.chunk(cache=True)
            logger.info(f"Guild member cache populated ({guild.member_count} members).")
        except Exception as e:
            logger.warning(f"Guild chunk failed (non-fatal): {e}")

    try:
        # Sync the globally defined commands to our specific guild first
        bot.tree.copy_global_to(guild=guild_obj)
        await bot.tree.sync(guild=guild_obj)
        logger.info(f"Synced guild slash commands to {DISCORD_GUILD_ID}.")
        
        # To fix the "duplicate commands" issue, we temporarily clear the global tree 
        # and sync it to Discord. This removes the "Global" copies that appear everywhere.
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        logger.info("Cleared global slash command cache (fixes duplicates).")
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
