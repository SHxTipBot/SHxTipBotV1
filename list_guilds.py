import discord
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        print("Guilds the bot is in:")
        for guild in self.guilds:
            print(f"Name: {guild.name} | ID: {guild.id}")
        await self.close()

client = MyClient(intents=discord.Intents.default())
client.run(token)
