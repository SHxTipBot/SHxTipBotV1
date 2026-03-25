import discord
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
guild_id = int(os.getenv("DISCORD_GUILD_ID"))

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        guild = self.get_guild(guild_id)
        if guild:
            print(f"Roles in {guild.name}:")
            for role in guild.roles:
                print(f"Role: {role.name} | ID: {role.id}")
        else:
            print("Guild not found.")
        await self.close()

client = MyClient(intents=discord.Intents.default())
client.run(token)
