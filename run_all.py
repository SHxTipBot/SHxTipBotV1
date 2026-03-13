import multiprocessing
import os
import uvicorn
from bot import main as start_bot
from web import app

def run_web():
    """Run the FastAPI web server."""
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)

def run_bot():
    """Run the Discord bot."""
    start_bot()

if __name__ == "__main__":
    # Use multiprocessing to run both bot and web server concurrently
    bot_process = multiprocessing.Process(target=run_bot)
    web_process = multiprocessing.Process(target=run_web)

    bot_process.start()
    web_process.start()

    bot_process.join()
    web_process.join()
