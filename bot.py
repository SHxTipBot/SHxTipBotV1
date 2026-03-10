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
    await db.init_db()
    
    # Register persistent views
    bot.add_view(AirdropView())
    
    try:
        bot.tree.copy_global_to(guild=guild_obj)
        synced = await bot.tree.sync(guild=guild_obj)
        logger.info(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        logger.error(f"Command sync failed: {e}")


# ── /link ─────────────────────────────────────────────────────────────────────

@bot.tree.command(name="link", description="Link your Stellar wallet to your Discord account")
async def link_command(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)

    existing = await db.get_user_stellar_key(discord_id)
    relink_note = ""
    if existing:
        relink_note = (
            f"\n\n⚠️ You are already linked to `{existing[:8]}...{existing[-8:]}`. "
            "Using this link will **replace** your current wallet."
        )

    token = await db.create_link_token(discord_id)
    link_url = f"{WEB_BASE_URL}/register?token={token}"

    embed = _footer(discord.Embed(
        title="🔗 Link Your Stellar Wallet",
        description=(
            "Click below to connect your wallet (Freighter or Lobstr) "
            "and authorise the SHx Tip Bot.\n\n"
            f"**[→ Connect Wallet]({link_url})**\n\n"
            "⏰ Link expires in **15 minutes**.{relink}"
        ).replace("{relink}", relink_note),
        color=EMBED_COLOR,
    ))

    await interaction.followup.send(embed=embed, ephemeral=True)


# ── /register (alias) ────────────────────────────────────────────────────────

@bot.tree.command(name="register", description="Alias for /link — connect your Stellar wallet")
async def register_command(interaction: Interaction):
    await link_command.callback(interaction)


# ── /balance ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="balance", description="Check your SHx balance")
async def balance_command(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)

    public_key = await db.get_user_stellar_key(discord_id)
    if not public_key:
        embed = _footer(discord.Embed(
            title="❌ Wallet Not Linked",
            description="Use `/link` to connect your Stellar wallet first.",
            color=ERROR_COLOR,
        ))
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    balance = await stellar.get_shx_balance(public_key)
    if balance is None:
        embed = _footer(discord.Embed(
            title="⚠️ Could Not Fetch Balance",
            description="Horizon may be down. Please try again later.",
            color=WARN_COLOR,
        ))
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    embed = _footer(discord.Embed(title="💰 Your SHx Balance", color=EMBED_COLOR))
    embed.add_field(name="Balance", value=f"**{balance:,.7f} SHx**", inline=False)
    embed.add_field(
        name="Address",
        value=f"`{public_key[:8]}...{public_key[-8:]}`",
        inline=False,
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


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

    # ── Validation ────────────────────────────────────────────────────────
    if user.bot and stellar.STELLAR_NETWORK != "testnet":
        await interaction.followup.send("❌ Cannot tip bots.", ephemeral=True)
        return
    if sender_id == recipient_id:
        await interaction.followup.send("❌ Cannot tip yourself.", ephemeral=True)
        return
    if amount <= 0 or amount > 1_000_000:
        await interaction.followup.send(
            "❌ Amount must be between 0 and 1,000,000 SHx.", ephemeral=True
        )
        return

    # ── Rate limit ────────────────────────────────────────────────────────
    since = time.time() - 60
    if await db.get_user_tip_count_since(sender_id, since) >= RATE_LIMIT_TIPS:
        await interaction.followup.send(
            f"⏳ Rate limit: max {RATE_LIMIT_TIPS} tips/min.", ephemeral=True
        )
        return

    # ── Wallet checks ────────────────────────────────────────────────────
    sender_key = await db.get_user_stellar_key(sender_id)
    if not sender_key:
        await interaction.followup.send(
            "❌ Your wallet is not linked. Use `/link` first.", ephemeral=True
        )
        return

    recipient_key = await db.get_user_stellar_key(recipient_id)
    if not recipient_key:
        await interaction.followup.send(
            f"❌ {user.mention} hasn't linked their wallet yet.", ephemeral=True
        )
        return

    # ── Trustline check ──────────────────────────────────────────────────
    if not await stellar.check_shx_trustline(recipient_key):
        await interaction.followup.send(
            f"❌ {user.mention}'s wallet lacks an SHx trustline.", ephemeral=True
        )
        return

    # ── SHX Gas Reimbursement + balance check ────────────────────────────
    gas_shx = await stellar.calculate_gas_shx()
    total = amount + gas_shx

    sender_balance = await stellar.get_shx_balance(sender_key)
    if sender_balance is None or sender_balance < total:
        bal_str = f"{sender_balance:,.7f}" if sender_balance is not None else "unknown"
        await interaction.followup.send(
            f"❌ Insufficient balance.\n"
            f"Need **{total:,.7f} SHx** (tip {amount:,.7f} + gas {gas_shx:,.7f})\n"
            f"Have **{bal_str} SHx**",
            ephemeral=True,
        )
        return

    # ── Execute ──────────────────────────────────────────────────────────
    # Note: stellar.execute_tip still uses a 'fee' parameter which the contract sends to the house account
    result = await stellar.execute_tip(sender_key, recipient_key, amount, gas_shx)

    if result["success"]:
        await db.record_tip(sender_id, recipient_id, amount, gas_shx, result["tx_hash"], reason)

        embed = _footer(discord.Embed(title="✅ Tip Sent!", color=SUCCESS_COLOR))
        embed.add_field(name="From", value=interaction.user.mention, inline=True)
        embed.add_field(name="To", value=user.mention, inline=True)
        embed.add_field(name="Amount", value=f"**{amount:,.7f} SHx**", inline=True)
        embed.add_field(name="Gas Reimbursement", value=f"{gas_shx:,.7f} SHx", inline=True)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(
            name="Transaction",
            value=f"[View on Stellar Expert]({result['tx_url']})",
            inline=False,
        )
        await interaction.followup.send(embed=embed)
        logger.info(
            f"TIP OK | {sender_id}→{recipient_id} | {amount} SHx | gas {gas_shx} | {result['tx_hash']}"
        )
    else:
        embed = _footer(discord.Embed(
            title="❌ Tip Failed",
            description=result["error"],
            color=ERROR_COLOR,
        ))
        if result.get("tx_url"):
            embed.add_field(name="TX", value=f"[View]({result['tx_url']})")
        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.error(f"TIP FAIL | {sender_id}→{recipient_id} | {result['error']}")


# ── /distribute ───────────────────────────────────────────────────────────────

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
