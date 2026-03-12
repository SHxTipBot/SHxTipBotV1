import os
import asyncio
from dotenv import load_dotenv
import discord

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

# The content of TESTER_GUIDE.md (hardcoded for simplicity in this one-off script)
GUIDE_CONTENT = """# 🧪 SHx Tip Bot — Tester Guide

Welcome to the SHx Tip Bot testnet pilot! Follow these steps to get set up and start testing.

---

### 1️⃣ Set Up a Wallet (Testnet)

You'll need a Stellar wallet that supports **Testnet**. We recommend **Freighter** (browser) or **Lobstr** (mobile/web).

* **Freighter**: Go to Settings > Network and switch to **Testnet**.
* **Lobstr**: Go to Settings > Network and switch to **Testnet**.

### 2️⃣ Link Your Wallet

In any channel, use the following command:
`/link`

The bot will DM you a private link. Open it and connect your wallet to link your Discord ID to your Stellar address.

### 3️⃣ Add the SHX Trustline (Required)

To receive SHX, your wallet must explicitly "trust" the SHX asset.

* **Asset Code**: `SHX`
* **Issuer Address**: `GC6S55K5ZGJTG6HDNQC42RLAQDRSLCJD7KFPKOOFM2JR4NNPV32SOIDF`

In your wallet, find the "Add Asset" or "Trustline" section and search for this issuer or add it manually.

### 4️⃣ Get Some Test XLM

You need a small amount of XLM to pay for your trustline.

* Go to the [Stellar Laboratory Friendbot](https://stellar.org/laboratory/#account-creator?network=testnet) and paste your address to get 10,000 test XLM.

---

### 🚀 Now You're Ready to Test

* **Tip Someone**: `/tip @username amount:10`
* **Check Balance**: `/balance`
* **Claim Airdrops**: Keep an eye out for airdrop messages with a **"Claim SHx"** button!

> [!NOTE]
> This is a **Testnet** environment. No real funds are used. If you run into issues, please report them to the alpha team!
"""

class SetupClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        guild = self.get_guild(GUILD_ID)
        if not guild:
            print(f"Could not find guild with ID {GUILD_ID}")
            await self.close()
            return

        print(f"Connected to guild: {guild.name}")

        # 1. Create channel if it doesn't exist
        channel_name = "how-to-test"
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        
        if not channel:
            print(f"Creating channel #{channel_name}...")
            # Try to create it at the top of the list
            channel = await guild.create_text_channel(channel_name, position=0)
            print(f"Channel created: {channel.name}")
        else:
            print(f"Channel #{channel_name} already exists.")

        # 2. Clear existing messages (optional, but good for a fresh guide)
        # await channel.purge(limit=10)

        # 3. Post the guide
        print("Posting tester guide...")
        # Discord has a 2000 char limit. Our guide is ~1600.
        await channel.send(GUIDE_CONTENT)
        print("Guide posted successfully!")

        await self.close()

if __name__ == "__main__":
    client = SetupClient()
    client.run(TOKEN)
