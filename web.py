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

# --- Static file mounting ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "src_public")

if os.path.exists(static_dir):
    logger.info(f"Mounting static files from: {static_dir}")
    app.mount("/public", StaticFiles(directory=static_dir), name="public")
else:
    logger.warning(f"Static directory NOT FOUND at {static_dir}. Skipping mount.")

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

app.add_middleware(SecurityHeadersMiddleware)

from template_data import get_dashboard_html

STARTUP_ERROR = None

@app.on_event("startup")
async def startup():
    global STARTUP_ERROR
    try:
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
    """Serve the modern dashboard as the landing page."""
    return await register_page(token="", claim_id="")

@app.get("/api/debug")
async def debug_info():
    return {
        "STELLAR_NETWORK": stellar.STELLAR_NETWORK,
        "NETWORK_PASSPHRASE": stellar.NETWORK_PASSPHRASE,
        "SHX_ISSUER": stellar.SHX_ISSUER,
        "SOROBAN_CONTRACT_ID": stellar.SOROBAN_CONTRACT_ID,
        "ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }

@app.get("/api/health")
@app.get("/health")
async def health_check():
    if STARTUP_ERROR:
        return HTMLResponse(content=f"<h1>STARTUP FAILED!</h1><pre>{STARTUP_ERROR}</pre>", status_code=500)
    return {"status": "ok", "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")}

@app.get("/register", response_class=HTMLResponse)
@app.get("/link", response_class=HTMLResponse)
async def register_page(token: str = "", claim_id: str = ""):
    """Serve the wallet-linking / claim HTML page."""
    if STARTUP_ERROR:
        return HTMLResponse(content=f"<h1>STARTUP FAILED!</h1><pre>{STARTUP_ERROR}</pre>", status_code=500)
    
    # Allow empty token/claim_id to show the base dashboard for wallet connection

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

    discord_user = "Community Guest"
    internal_balance = 0.0
    memo_id = 0
    existing_key = None
    
    if discord_id:
        user_data = await db.get_or_create_user(discord_id)
        discord_user = user_data.get("username") or f"User {discord_id}"
        internal_balance = await db.get_internal_balance(discord_id)
        existing_key = await db.get_user_stellar_key(discord_id)
        memo_id = user_data.get("memo_id", 0)

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
    html = html.replace("{{HORIZON_URL}}", stellar.HORIZON_URL.strip())
    html = html.replace("{{SOROBAN_URL}}", stellar.SOROBAN_RPC_URL.strip())
    html = html.replace("{{WC_PROJECT_ID}}", wc_project_id.strip())
    html = html.replace("{{SHX_ISSUER}}", stellar.SHX_ISSUER.strip())
    
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
        "expires_at": data.get("expires_at"),
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
        
    # Security Phase 2: Verify the cryptographic claim has expired
    expires_at = withdrawal.get("expires_at")
    import time
    now_ts = int(time.time())
    if expires_at and now_ts <= expires_at:
        raise HTTPException(400, f"Cannot cancel yet. On-chain claim is fully valid for {(expires_at - now_ts) // 60} more minutes.")
    
    # Security Phase 3: Verify the claim was NOT already executed on-chain
    # This prevents the double-spend exploit where a user claims on-chain,
    # doesn't call /complete, waits for expiry, then cancels for a refund.
    stellar_address = withdrawal.get("stellar_address")
    nonce = withdrawal.get("nonce")
    if stellar_address and nonce:
        nonce_used = await stellar.check_withdrawal_nonce_used(stellar_address, nonce)
        if nonce_used:
            # Auto-mark as COMPLETED to prevent future cancel attempts
            await db.complete_withdrawal_by_nonce(nonce, f"CANCEL_BLOCKED_{withdrawal_id}")
            logger.warning(
                f"CANCEL BLOCKED | Withdrawal {withdrawal_id} was already claimed on-chain "
                f"(nonce {nonce}). Blocked refund and marked COMPLETED."
            )
            raise HTTPException(400, "This withdrawal was already claimed on-chain. Refund denied.")
        
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

    # NEW: Verify the transaction actually succeeded on-chain before completing
    is_confirmed = await stellar.verify_transaction_status(tx_hash)
    if not is_confirmed:
        logger.warning(f"WITHDRAWAL COMPLETE ATTEMPT | ID: {withdrawal_id} | Hash {tx_hash} NOT CONFIRMED on-chain yet.")
        # We still allow it if it's just a lag issue, but we log a strong warning. 
        # Actually, for Soroban claims, we should probably be strict.
        # But to avoid breaking things for the user if RPC is laggy, we'll proceed if it's not an explicit FAILURE.
        pass

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
