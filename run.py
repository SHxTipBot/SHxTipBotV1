"""
SHx Tip Bot — Entry Point
Runs both the Discord bot and the FastAPI web server concurrently.
"""

import os
import sys
import io
import asyncio
import threading
import logging

# Force UTF-8 on Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("shx_tip_bot.run")


def start_web_server():
    """Run the FastAPI web server in a separate thread."""
    import uvicorn
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8080"))
    uvicorn.run("web:app", host=host, port=port, log_level="info")


def start_bot():
    """Run the Discord bot (blocking)."""
    from bot import main as bot_main
    bot_main()


def main():
    print("=" * 50)
    print("  SHx Tip Bot — Stronghold Community")
    print(f"  Network: {os.getenv('STELLAR_NETWORK', 'testnet')}")
    print("=" * 50)

    # Validate critical env vars
    required = ["DISCORD_TOKEN", "DISCORD_GUILD_ID", "HOUSE_ACCOUNT_SECRET"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        print(f"\nERROR: Missing required environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and configure all values.")
        sys.exit(1)

    # Start web server in background thread
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    print(f"\n[OK] Web server starting on {os.getenv('WEB_HOST', '0.0.0.0')}:{os.getenv('WEB_PORT', '8080')}")

    # Start Discord bot (blocks main thread)
    print("[OK] Starting Discord bot...\n")
    start_bot()


if __name__ == "__main__":
    main()
