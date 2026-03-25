import os
import discord
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

class Broadcaster(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}")
        guild = self.get_guild(GUILD_ID)
        if not guild:
            print("Could not find guild.")
            await self.close()
            return
            
        print("Searching for channel...")
        target_channel = discord.utils.find(lambda c: 'how-to-test' in c.name.lower() or 'test' in c.name.lower(), guild.text_channels)
        if not target_channel and guild.text_channels:
            target_channel = guild.text_channels[0]
            
        if target_channel:
            with open('USER_GUIDE.md', 'r', encoding='utf-8') as f:
                content = f.read()
            await target_channel.send(content)
            print(f"SUCCESS: Posted testing guide to #{target_channel.name}")
        else:
            print("ERROR: Channel not found!")
            
        await self.close()

intents = discord.Intents.default()
client = Broadcaster(intents=intents)
client.run(TOKEN, log_handler=None)
