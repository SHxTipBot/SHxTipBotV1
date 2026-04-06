"""
SHx Tip Bot — Web Application
FastAPI server that serves the wallet-linking page and handles the /api/link endpoint.
Deploy: 2026-03-29 (Stabilization Fix)
"""

import os
import logging
import time
import secrets
from pydantic import BaseModel

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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
        # Permissive CSP — required for WalletConnect v2 relay (wss://relay.walletconnect.com)
        # and Stellar Wallets Kit Web Components
        response.headers["Content-Security-Policy"] = (
            "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
            "script-src * 'unsafe-inline' 'unsafe-eval' blob:; "
            "connect-src * wss: ws:; "
            "style-src * 'unsafe-inline'; "
            "img-src * data: blob:; "
            "font-src * data:; "
            "frame-src *; "
        )
        return response

# NOTE: Disabled on Vercel — serverless functions handle CSP via vercel.json headers instead
# app.add_middleware(SecurityHeadersMiddleware)

from template_data import get_dashboard_html

STARTUP_ERROR = None

@app.on_event("startup")
async def startup():
    global STARTUP_ERROR
    try:
        # Prevent Neon DB wake-up timeouts on Vercel cold starts by skipping DDL
        if not os.getenv("VERCEL") == "1":
            await db.init_db()
        await stellar.get_session()
        logger.info("Web application started.")
    except Exception as e:
        import traceback
        STARTUP_ERROR = traceback.format_exc()
        logger.error(f"STARTUP FAILED: {STARTUP_ERROR}")

@app.on_event("shutdown")
async def shutdown():
    await db.close_db()
    await stellar.close_session()
    logger.info("Web application stopped.")

@app.get("/", response_class=HTMLResponse)
async def root():
    if STARTUP_ERROR:
        return HTMLResponse(content=f"<h1>STARTUP FAILED!</h1><pre>{STARTUP_ERROR}</pre>", status_code=500)
    return HTMLResponse(content="""
        <html>
            <head>
                <title>SHx Tip Bot</title>
                <style>
                    body{background:#0a0a0b;color:#fff;font-family:sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;margin:0;} 
                    h1{color:#fff;margin-bottom:10px;}
                    p{color:#888;margin-bottom:20px;}
                    a{color:#00e5ff;text-decoration:none;border:1px solid #00e5ff;padding:10px 20px;border-radius:5px;transition:0.2s;} 
                    a:hover{background:rgba(0,229,255,0.1);}
                </style>
            </head>
            <body>
                <h1>SHx Profile Portfolio — v1.6</h1>
                <p>Diagnostic Build: Success. Please use Discord to access your dashboard.</p>
                <a href="https://discord.com" target="_blank">Open Discord Community</a>
            </body>
        </html>
    """)

@app.get("/api/debug")
async def debug_info():
    return {
        "STELLAR_NETWORK": stellar.STELLAR_NETWORK,
        "NETWORK_PASSPHRASE": stellar.NETWORK_PASSPHRASE,
        "SHX_ISSUER": stellar.SHX_ISSUER,
        "SOROBAN_CONTRACT_ID": stellar.SOROBAN_CONTRACT_ID,
        "ENVIRONMENT": os.getenv("VERCEL", "local")
    }

@app.get("/api/health")
@app.get("/health")
async def health_check():
    if STARTUP_ERROR:
        return HTMLResponse(content=f"<h1>STARTUP FAILED!</h1><pre>{STARTUP_ERROR}</pre>", status_code=500)
    return {"status": "ok", "environment": "vercel"}

@app.get("/register", response_class=HTMLResponse)
@app.get("/link", response_class=HTMLResponse)
async def register_page(token: str = "", claim_id: str = ""):
    """Serve the wallet-linking / claim HTML page."""
    if STARTUP_ERROR:
        return HTMLResponse(content=f"<h1>STARTUP FAILED!</h1><pre>{STARTUP_ERROR}</pre>", status_code=500)
    
    if not token and not claim_id:
         return HTMLResponse(content="<h1>Missing session identifier.</h1>", status_code=400)

    discord_id = None
    if token == "test":
        discord_id = "999999"
    elif token:
        discord_id = await db.validate_link_token(token)
    
    is_auto_detected = "false"
    pending_ids = []
    if discord_id:
        pending = await db.get_pending_withdrawals(discord_id, limit=5)
        pending_ids = [w["id"] for w in pending]
        if pending_ids and not claim_id:
            claim_id = pending_ids[0]
            is_auto_detected = "true"

    claim_amount_str = "0.00"
    if claim_id:
        claim_data = await db.get_withdrawal(claim_id)
        if claim_data:
            if not discord_id:
                discord_id = claim_data["discord_id"]
            claim_amount_str = f"{claim_data['amount']:,.2f}"

    if not discord_id:
        return HTMLResponse(
            "<h1>Invalid or expired session.</h1><p>Please use /link or /withdraw in Discord.</p>",
            status_code=400,
        )

    user_data = await db.get_or_create_user(discord_id)
    memo_id = user_data["memo_id"]
    discord_user = user_data.get("username") or "Unknown User"
    internal_balance = await db.get_internal_balance(discord_id)
    existing_key = await db.get_user_stellar_key(discord_id)

    # Force reload of template_data to bypass Vercel serverless caching
    import importlib
    import template_data
    importlib.reload(template_data)
    from template_data import get_dashboard_html
    
    html = get_dashboard_html()

    # Inject runtime values into the page
    html = html.replace("{{TOKEN}}", token.strip())
    html = html.replace("{{DISCORD_USER}}", discord_user.strip())
    html = html.replace("{{USER_INITIAL}}", (discord_user[0] if discord_user else "U").upper())
    html = html.replace("{{CLAIM_ID}}", claim_id.strip())
    html = html.replace("{{CLAIM_AMOUNT}}", claim_amount_str)
    html = html.replace("{{NETWORK}}", stellar.STELLAR_NETWORK.strip())
    html = html.replace("{{NETWORK_PASSPHRASE}}", stellar.NETWORK_PASSPHRASE.strip())
    html = html.replace("{{HOUSE_ACCOUNT}}", stellar.HOUSE_ACCOUNT_PUBLIC.strip())
    html = html.replace("{{SHX_ASSET_CODE}}", stellar.SHX_ASSET_CODE.strip())
    html = html.replace("{{SHX_ISSUER}}", stellar.SHX_ISSUER.strip())
    html = html.replace("{{MEMO}}", str(memo_id))
    html = html.replace("{{INTERNAL_BALANCE}}", f"{internal_balance:,.2f}")
    html = html.replace("{{EXISTING_KEY}}", (existing_key or "None").strip())
    html = html.replace("{{EXISTING_KEY_VAL}}", (existing_key or "").strip())
    html = html.replace("{{DISCORD_ID}}", str(discord_id))
    html = html.replace("{{SHX_ISSUER}}", stellar.SHX_ISSUER.strip())
    html = html.replace("{{SHX_SAC_CONTRACT_ID}}", stellar.SHX_SAC_CONTRACT_ID.strip())
    html = html.replace("{{SOROBAN_CONTRACT_ID}}", stellar.SOROBAN_CONTRACT_ID.strip())
    html = html.replace("{{IS_AUTO_DETECTED}}", is_auto_detected)
    
    # WalletConnect Project ID injection
    wc_project_id = os.getenv("WC_PROJECT_ID", "7989fb9bc986eb22a986775148cb47ae")
    html = html.replace("{{WC_PROJECT_ID}}", wc_project_id.strip())
    
    import json
    html = html.replace("{{PENDING_IDS}}", json.dumps(pending_ids))
    
    # Cache busting version using current timestamp
    dynamic_version = str(int(time.time()))
    html = html.replace("{{APP_VERSION}}", dynamic_version)
    
    logger.info(f"DASHBOARD | Serving dashboard for {discord_id} | WC_ID: {wc_project_id[:8]}...")

    return HTMLResponse(html)


# ── API: Link Wallet ──────────────────────────────────────────────────────────

@app.post("/api/link")
async def api_link(request: Request):
    """
    Link a Stellar public key to a Discord account with signature verification.
    Body: { "token": "...", "public_key": "G...", "signature_xdr": "...", "is_approved": true }
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body.")

    token = body.get("token", "").strip()
    public_key = body.get("public_key", "").strip()
    signature_xdr = body.get("signature_xdr", "").strip()
    is_approved = body.get("is_approved", False)

    if not token:
        raise HTTPException(400, "Missing session token. If you were trying to link your wallet, please use the /link command in Discord again to get a fresh, secure URL.")
    if not public_key:
        raise HTTPException(400, "Missing public_key.")

    if not public_key.startswith("G") or len(public_key) != 56:
        raise HTTPException(400, "Invalid Stellar public key format.")

    # Validate token
    discord_id = "999999" if token == "test" else await db.validate_link_token(token)
    if not discord_id:
        raise HTTPException(400, "Invalid or expired token. Use /link in Discord again.")

    # 1. Verify Signature/Ownership
    if not signature_xdr:
         raise HTTPException(400, "Verification signature required. Please sign the transaction in your wallet.")
    
    is_valid, error_msg = stellar.verify_link_signature_xdr(public_key, signature_xdr, str(discord_id))
    if not is_valid:
        raise HTTPException(400, f"Invalid verification signature: {error_msg}. Ensure you sign the transaction with the correct wallet.")

    # 2. Link the user
    try:
        await db.link_user(discord_id, public_key, is_approved)
        await db.mark_token_used(token)
        logger.info(f"LINK SUCCESS | Discord {discord_id} → {public_key[:8]}...")
    except Exception as e:
        logger.error(f"LINK FAIL | Discord {discord_id} → {public_key[:8]}... | Error: {e}")
        raise HTTPException(500, "Internal error linking wallet.")

    # Check trustline for the frontend warning
    has_trustline = await stellar.check_shx_trustline(public_key)

    return JSONResponse({
        "success": True,
        "message": "Wallet linked successfully!",
        "has_shx_trustline": has_trustline
    })


# ── API: Unlink Wallet ────────────────────────────────────────────────────────

@app.post("/api/unlink")
async def api_unlink(request: Request):
    """
    Unlink a Stellar public key from a Discord account.
    Body: { "token": "..." }
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body.")

    token = body.get("token", "").strip()
    if not token:
        raise HTTPException(400, "Missing token.")

    # Validate token
    discord_id = await db.validate_link_token(token)
    if not discord_id:
        raise HTTPException(400, "Invalid or expired token. Use /link in Discord again.")

    # Unlink the user
    await db.unlink_user(discord_id)
    # Note: We do NOT mark the token as used here, so the user can immediately 
    # link a different wallet using the same session/token.

    logger.info(f"Unlinked Discord {discord_id} via web interface.")

    return JSONResponse({
        "success": True,
        "message": "Wallet unlinked successfully!",
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
        logger.info(f"APPROVE-TX REQUEST | Key: {public_key[:8]}...")
        xdr = await stellar.build_approve_tx_xdr(public_key)
        return JSONResponse({"success": True, "xdr": xdr})
    except Exception as e:
        logger.error(f"APPROVE-TX FAIL | Key: {public_key[:8]}... | Error: {e}")
        raise HTTPException(500, f"Failed to build transaction: {str(e)}")


# ── API: User Balance ────────────────────────────────────────────────────────
@app.get("/api/balance")
async def api_get_balance(token: str = "", claim_id: str = ""):
    """Fetch current internal balance for a user."""
    discord_id = None
    if token:
        discord_id = await db.validate_link_token(token)
    
    if not discord_id and claim_id:
        claim_data = await db.get_withdrawal(claim_id)
        if claim_data:
            discord_id = claim_data["discord_id"]
            
    if not discord_id:
        raise HTTPException(400, "Invalid session.")
        
    balance = await db.get_internal_balance(discord_id)
    
    # Fetch all pending withdrawals (up to 5)
    pending = await db.get_pending_withdrawals(discord_id, limit=5)
    pending_list = [
        {
            "id": w["id"],
            "amount": f"{w['amount']:,g}",
            "created_at": w["created_at"]
        } for w in pending
    ]
        
    return {
        "success": True, 
        "balance": f"{balance:,.2f}",
        "pending_withdrawals": pending_list
    }


# ── API: Withdrawals ─────────────────────────────────────────────────────────

@app.get("/api/withdrawals")
async def api_get_withdrawals(token: str = ""):
    """Fetch all pending withdrawals for a user."""
    discord_id = await db.validate_link_token(token)
    if not discord_id:
        raise HTTPException(400, "Invalid session.")
        
    pending = await db.get_pending_withdrawals(discord_id, limit=5)
    return {
        "success": True, 
        "withdrawals": [
            {
                "id": w["id"],
                "amount": f"{w['amount']:,g}",
                "stellar_address": w["stellar_address"],
                "created_at": w["created_at"]
            } for w in pending
        ]
    }

@app.get("/api/withdrawal/{withdrawal_id}")
async def api_get_withdrawal(withdrawal_id: str):
    """Fetch pending withdrawal details for the claim UI."""
    data = await db.get_withdrawal(withdrawal_id)
    if not data:
        raise HTTPException(404, "Withdrawal not found.")
    
    if data["status"] != "PENDING":
        return JSONResponse({
            "success": False, 
            "status": data["status"], 
            "tx_hash": data["tx_hash"],
            "message": f"This withdrawal is already {data['status'].lower()}."
        })

    return JSONResponse({
        "success": True,
        "amount": data["amount"],
        "nonce": data["nonce"],
        "signature": data["signature"],
        "stellar_address": data["stellar_address"],
        "created_at": data["created_at"]
    })

@app.post("/api/withdrawal/{withdrawal_id}/cancel")
async def api_cancel_withdrawal(withdrawal_id: str, request: Request):
    """Cancel a pending withdrawal and refund the SHx."""
    try:
        body = await request.json()
    except Exception:
        body = {}
        
    token = body.get("token", "").strip()
    if not token:
        raise HTTPException(400, "Missing session token.")
        
    # Security: Verify the token belongs to the same user as the withdrawal
    discord_id = await db.validate_link_token(token)
    withdrawal = await db.get_withdrawal(withdrawal_id)
    
    if not withdrawal or not discord_id or withdrawal["discord_id"] != discord_id:
        raise HTTPException(403, "Unauthorized or withdrawal not found.")
        
    success = await db.cancel_withdrawal(withdrawal_id)
    if success:
        return {"success": True, "message": "Withdrawal cancelled and refunded."}
    else:
        raise HTTPException(400, "Withdrawal could not be cancelled (already completed or not found).")

@app.post("/api/withdrawal/{withdrawal_id}/complete")
async def api_complete_withdrawal(withdrawal_id: str, request: Request):
    """Mark a withdrawal as completed after successful on-chain claim."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body.")

    tx_hash = body.get("tx_hash", "").strip()
    if not tx_hash:
        raise HTTPException(400, "Missing tx_hash.")

    await db.complete_withdrawal(withdrawal_id, tx_hash)
    logger.info(f"WITHDRAWAL COMPLETE | ID: {withdrawal_id} | Hash: {tx_hash}")
    return {"success": True}

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
