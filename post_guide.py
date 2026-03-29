import os
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

CONTENT = """📌 **SHx Tip Bot — Command Reference**

**💰 For Everyone**
> `/balance` — Check your internal SHx balance.
> `/tip @user <amount>` — Instantly send SHx to any server member. Amount can be SHx (e.g. `100`) or USD (e.g. `$5`). No wallet needed to receive.
> `/deposit` — Get the bot's deposit address + your unique Memo ID to load SHx from an external wallet.

**🔗 Withdrawals (Requires Wallet Setup)**
> `/link` — Get a secure 15-minute link to connect your Stellar wallet address to your Discord account.
> `/withdraw <amount> <G...address>` — Move SHx from your bot balance to your Stellar wallet. Your wallet must be linked first.

**🎭 Role Tipping**
> `/tip-role @role <amount>` — Split a total SHx amount equally among all members of a role. Example: `/tip-role @Community 500` splits 500 SHx evenly across every member.

**🪂 Airdrops**
> `/airdrop <total> <claims> [duration]` — Post a "Claim SHx" button in the channel. The total is split among whoever clicks first. Optional: `duration_minutes`, `duration_hours`, `duration_days`.

**🔧 Admin Only**
> `/create-role <name> <hex_color>` — Create a new Discord role (e.g. `/create-role Tippers 0xFF4500`).
> `/assign-role @user @role` — Assign a Discord role to a user.

> 💡 **Note:** Tipping is instant and off-chain — no gas fees or wallet needed to send or receive. Wallets are only required for `/withdraw`."""


class Broadcaster(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}")
        guild = self.get_guild(GUILD_ID)
        if not guild:
            print("Could not find guild.")
            await self.close()
            return

        print(f"Available channels: {[c.name for c in guild.text_channels]}")

        # Find #general (or first channel with 'general' in the name)
        target_channel = discord.utils.find(
            lambda c: "general" in c.name.lower(), guild.text_channels
        )
        if not target_channel and guild.text_channels:
            target_channel = guild.text_channels[0]
            print(f"No #general found, falling back to #{target_channel.name}")

        if target_channel:
            msg = await target_channel.send(CONTENT)
            try:
                await msg.pin()
                print(f"SUCCESS: Posted and pinned in #{target_channel.name}")
            except discord.Forbidden:
                print(f"SUCCESS: Posted to #{target_channel.name} (bot lacks Manage Messages to pin — pin manually)")
        else:
            print("ERROR: No text channels found!")

        await self.close()


intents = discord.Intents.default()
client = Broadcaster(intents=intents)
client.run(TOKEN, log_handler=None)
