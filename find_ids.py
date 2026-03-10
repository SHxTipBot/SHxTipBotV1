"""Quick helper to find Discord guild IDs (no members intent needed)."""
import sys, io, os
from dotenv import load_dotenv
import discord

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
load_dotenv()

intents = discord.Intents.default()
# Do NOT request members intent - just get guild list
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot online as {client.user} (ID: {client.user.id})")
    print(f"\nGuilds the bot is in:")
    for g in client.guilds:
        print(f"  {g.name} -> Guild ID: {g.id} ({g.member_count} members)")
    print("\nDone.")
    await client.close()

client.run(os.getenv("DISCORD_TOKEN"), log_handler=None)
