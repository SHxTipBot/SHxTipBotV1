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
            
            # Also list members to see their roles
            print("\nMembers and their roles:")
            # Note: requires members intent
            async for member in guild.fetch_members(limit=100):
                roles = [r.name for r in member.roles if r.name != "@everyone"]
                print(f"Member: {member.name} ({member.id}) | Roles: {', '.join(roles)}")
        else:
            print("Guild not found.")
        await self.close()

# Try with all intents
intents = discord.Intents.all()
client = MyClient(intents=intents)
client.run(token)
