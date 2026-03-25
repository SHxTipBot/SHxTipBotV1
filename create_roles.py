import discord
import os
from dotenv import load_dotenv

# Load Current ENVs
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
guild_id = int(os.getenv("DISCORD_GUILD_ID"))

ROLES_TO_CREATE = [
    ("Duke", 0x5865F2),     # Level 5
    ("Knight", 0x2ECC71),   # Level 4
    ("Squire", 0xF1C40F),   # Level 3
    ("Vanguard", 0xE67E22), # Level 2
    ("Captain", 0xE74C3C)   # Level 1
]

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        guild = self.get_guild(guild_id)
        if not guild:
            print("Guild not found.")
            await self.close()
            return

        print(f"Checking roles in {guild.name}...")
        
        # New IDs for .env
        role_ids = {}

        # Scan for existing or create new
        for role_name, role_color in ROLES_TO_CREATE:
            existing_role = discord.utils.get(guild.roles, name=role_name)
            if existing_role:
                print(f"Role '{role_name}' already exists with ID: {existing_role.id}")
                role_ids[role_name.upper()] = existing_role.id
            else:
                try:
                    new_role = await guild.create_role(name=role_name, color=discord.Color(role_color), reason="Automated setup for SHx Tip Bot")
                    print(f"Created role '{role_name}' with ID: {new_role.id}")
                    role_ids[role_name.upper()] = new_role.id
                except Exception as e:
                    print(f"Failed to create role '{role_name}': {e}")

        # Summary for .env update
        print("\n--- NEW CONFIGURATION ---")
        for name, rid in role_ids.items():
            print(f"{name}_ROLE_ID={rid}")
        
        await self.close()

# Requires MANAGE_ROLES permission!
intents = discord.Intents.default()
client = MyClient(intents=intents)
client.run(token)
