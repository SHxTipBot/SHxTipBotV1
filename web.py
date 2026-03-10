"""
SHx Tip Bot — Web Application
FastAPI server that serves the wallet-linking page and handles the /api/link endpoint.
"""

import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import database as db
import stellar_utils as stellar

load_dotenv()

logger = logging.getLogger("shx_tip_bot.web")

app = FastAPI(title="SHx Tip Bot — Wallet Linking", docs_url=None, redoc_url=None)

# ── Security Middleware ──────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to specific domains if needed
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' https: data:;"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Serve static files (index.html, etc.)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "web_static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
async def startup():
    await db.init_db()
    await stellar.get_session()
    logger.info("Web application started.")

@app.on_event("shutdown")
async def shutdown():
    await db.close_db()
    await stellar.close_session()
    logger.info("Web application stopped.")


# ── Registration Page ─────────────────────────────────────────────────────────

@app.get("/register", response_class=HTMLResponse)
async def register_page(token: str = ""):
    """Serve the wallet-linking HTML page."""
    if not token:
        return HTMLResponse("<h1>Missing token parameter.</h1>", status_code=400)

    # Validate token exists and is not expired
    discord_id = await db.validate_link_token(token)
    if not discord_id:
        return HTMLResponse(
            "<h1>Invalid or expired link.</h1><p>Please use /link in Discord to get a new one.</p>",
            status_code=400,
        )

    # Read and serve the HTML file, injecting the token
    html_path = os.path.join(STATIC_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Inject runtime values into the page
    html = html.replace("{{TOKEN}}", token)
    html = html.replace("{{NETWORK}}", stellar.STELLAR_NETWORK)
    html = html.replace("{{NETWORK_PASSPHRASE}}", stellar.NETWORK_PASSPHRASE)
    html = html.replace("{{SHX_SAC_CONTRACT_ID}}", stellar.SHX_SAC_CONTRACT_ID)
    html = html.replace("{{SOROBAN_CONTRACT_ID}}", stellar.SOROBAN_CONTRACT_ID)

    return HTMLResponse(html)


# ── API: Link Wallet ──────────────────────────────────────────────────────────

@app.post("/api/link")
async def api_link(request: Request):
    """
    Link a Stellar public key to a Discord account.
    Body: { "token": "...", "public_key": "G..." }
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body.")

    token = body.get("token", "").strip()
    public_key = body.get("public_key", "").strip()

    if not token or not public_key:
        raise HTTPException(400, "Missing token or public_key.")

    if not public_key.startswith("G") or len(public_key) != 56:
        raise HTTPException(400, "Invalid Stellar public key format.")

    # Validate token
    discord_id = await db.validate_link_token(token)
    if not discord_id:
        raise HTTPException(400, "Invalid or expired token. Use /link in Discord again.")

    # Optional: verify the account exists and has an SHx trustline
    has_trustline = await stellar.check_shx_trustline(public_key)

    # Link the user
    await db.link_user(discord_id, public_key)
    await db.mark_token_used(token)

    logger.info(f"Linked Discord {discord_id} → {public_key[:8]}...")

    return JSONResponse({
        "success": True,
        "message": "Wallet linked successfully!",
        "has_shx_trustline": has_trustline,
        "discord_id": discord_id,
    })


# ── API: Build Approve TX ────────────────────────────────────────────────────

@app.post("/api/approve-tx")
async def api_approve_tx(request: Request):
    """
    Build an unsigned approve transaction XDR for the user to sign.
    Body: { "public_key": "G..." }
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body.")

    public_key = body.get("public_key", "").strip()
    if not public_key or not public_key.startswith("G") or len(public_key) != 56:
        raise HTTPException(400, "Invalid public key.")

    try:
        xdr = await stellar.build_approve_tx_xdr(public_key)
        return JSONResponse({"success": True, "xdr": xdr})
    except Exception as e:
        logger.error(f"Error building approve TX: {e}")
        raise HTTPException(500, f"Failed to build transaction: {str(e)}")


# ── Health Check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "network": stellar.STELLAR_NETWORK}


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8080"))
    uvicorn.run("web:app", host=host, port=port, reload=True)
