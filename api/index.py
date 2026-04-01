import os
import sys

# Add the api/ directory to Python's path so we can import sibling modules
api_dir = os.path.dirname(os.path.abspath(__file__))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

import traceback

try:
    # Import app using absolute import (NOT relative - Vercel doesn't support it)
    from web import app
except Exception as e:
    import logging
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse
    
    app = FastAPI()
    error_msg = traceback.format_exc()
    
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    async def catch_all(request: Request, path_name: str):
        return HTMLResponse(content=f"<h1>Startup Error</h1><pre>{error_msg}</pre>", status_code=500)

# Export for Vercel
app = app
