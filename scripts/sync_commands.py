import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))

if not TOKEN or not GUILD_ID:
    print("❌ ERROR: DISCORD_TOKEN or DISCORD_GUILD_ID not found in .env")
    exit(1)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    guild = discord.Object(id=GUILD_ID)
    
    try:
        print(f"Syncing commands for guild {GUILD_ID}...")
        
        # Import the command tree from your main bot file to avoid re-defining them
        # (Though in this case, we'll just import the tree from bot.py if possible)
        from bot import bot as main_bot
        
        # Copy global commands to guild
        main_bot.tree.copy_global_to(guild=guild)
        synced = await main_bot.tree.sync(guild=guild)
        print(f"✅ Successfully synced {len(synced)} guild commands.")
        
        # Clear global to avoid duplicates
        # main_bot.tree.clear_commands(guild=None)
        # await main_bot.tree.sync()
        # print("✅ Global command cache cleared.")
        
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    finally:
        await bot.close()

async def main():
    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
