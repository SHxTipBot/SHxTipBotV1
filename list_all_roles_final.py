import discord
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        for guild in self.guilds:
            print(f"\nGuild: {guild.name} ({guild.id})")
            print("Roles:")
            for role in guild.roles:
                print(f"  - {role.name} (ID: {role.id})")
        await self.close()

client = MyClient(intents=discord.Intents.default())
client.run(token)
