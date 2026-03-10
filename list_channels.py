import os
import asyncio
from dotenv import load_dotenv
import discord

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

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

        print("--- Existing Channels ---")
        for channel in guild.text_channels:
            print(f"- {channel.name} (ID: {channel.id})")
        print("-------------------------")

        await self.close()

if __name__ == "__main__":
    client = SetupClient()
    client.run(TOKEN)
