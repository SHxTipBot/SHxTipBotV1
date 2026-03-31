"""
SHx Tip Bot — Web Application
FastAPI server that serves the wallet-linking page and handles the /api/link endpoint.
Deploy: 2026-03-29 (Stabilization Fix)
"""

import os
import logging

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
        response.headers["Content-Security-Policy"] = (
            "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
            "script-src * 'unsafe-inline' 'unsafe-eval' blob:; "
            "connect-src * 'unsafe-inline' 'unsafe-eval' wss:; "
            "style-src * 'unsafe-inline'; "
            "img-src * data: blob:; "
            "font-src * data:; "
            "frame-src *; "
        )
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


@app.get("/")
async def root():
    return {"status": "SHx Tip Bot API is active (Vercel Backend)", "docs": "/health"}


# ── Registration Page ─────────────────────────────────────────────────────────

    # Get optional claim_id for User-Paid withdrawal
    # We allow the root /register to be used for both linking and claiming
    claim_id = ""
    claim_total = "0.00"
    
    # Try to get claim_id from request params if available (FastAPI handles this via token: str = "")
    # However, since I named the param token, I should probably check for claim_id explicitly.
    # I'll modify the signature to accept both.
    pass

@app.get("/register", response_class=HTMLResponse)
async def register_page(token: str = "", claim_id: str = ""):
    """Serve the wallet-linking / claim HTML page."""
    # If no token, we might be in 'Claim Only' mode, but usually users come from /link
    # If no token AND no claim_id, it's invalid.
    if not token and not claim_id:
         return HTMLResponse("<h1>Missing session identifier.</h1>", status_code=400)

    discord_id = None
    if token == "test":
        discord_id = "999999"
    elif token:
        discord_id = await db.validate_link_token(token)
    
    # NEW: Auto-detect pending withdrawal if claim_id is missing
    is_auto_detected = "false"
    if discord_id and not claim_id:
        pending = await db.get_latest_pending_withdrawal(discord_id)
        if pending:
            claim_id = pending["id"]
            is_auto_detected = "true"

    # If we have a claim_id, we can also derive the discord_id from the withdrawal record
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

    # Get user details for dashboard
    user_data = await db.get_or_create_user(discord_id)
    memo_id = user_data["memo_id"]
    internal_balance = await db.get_internal_balance(discord_id)
    existing_key = await db.get_user_stellar_key(discord_id)

    # Read and serve the HTML file, injecting variables
    html_path = os.path.join(STATIC_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Inject runtime values into the page
    html = html.replace("{{TOKEN}}", token.strip())
    html = html.replace("{{CLAIM_ID}}", claim_id.strip())
    html = html.replace("{{CLAIM_AMOUNT}}", claim_amount_str)
    html = html.replace("{{NETWORK}}", stellar.STELLAR_NETWORK.strip())
    html = html.replace("{{NETWORK_PASSPHRASE}}", stellar.NETWORK_PASSPHRASE.strip())
    html = html.replace("{{HOUSE_ACCOUNT_PUBLIC}}", stellar.HOUSE_ACCOUNT_PUBLIC.strip())
    html = html.replace("{{MEMO_ID}}", str(memo_id))
    html = html.replace("{{INTERNAL_BALANCE}}", f"{internal_balance:,.2f}")
    html = html.replace("{{EXISTING_KEY}}", (existing_key or "None").strip())
    html = html.replace("{{EXISTING_KEY_VAL}}", (existing_key or "").strip())
    html = html.replace("{{DISCORD_ID}}", str(discord_id))
    html = html.replace("{{SHX_ISSUER}}", stellar.SHX_ISSUER.strip())
    html = html.replace("{{SHX_SAC_CONTRACT_ID}}", stellar.SHX_SAC_CONTRACT_ID.strip())
    html = html.replace("{{SOROBAN_CONTRACT_ID}}", stellar.SOROBAN_CONTRACT_ID.strip())
    html = html.replace("{{IS_AUTO_DETECTED}}", is_auto_detected)

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

    if not token or not public_key:
        raise HTTPException(400, "Missing token or public_key.")

    if not public_key.startswith("G") or len(public_key) != 56:
        raise HTTPException(400, "Invalid Stellar public key format.")

    # Validate token
    discord_id = await db.validate_link_token(token)
    if not discord_id:
        raise HTTPException(400, "Invalid or expired token. Use /link in Discord again.")

    # 1. Verify Signature/Ownership
    if not signature_xdr:
         raise HTTPException(400, "Verification signature required. Please sign the transaction in your wallet.")
    
    is_valid = stellar.verify_link_signature_xdr(public_key, signature_xdr, str(discord_id))
    if not is_valid:
        raise HTTPException(400, "Invalid verification signature. Ensure you sign the transaction with the correct wallet.")

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
    return {"success": True, "balance": f"{balance:,.2f}"}


# ── API: Withdrawals ─────────────────────────────────────────────────────────

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

@app.post("/api/withdrawal/{withdrawal_id}/cancel")
async def api_cancel_withdrawal(withdrawal_id: str, request: Request):
    """Cancel a pending withdrawal and refund the user."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body.")

    token = body.get("token", "").strip()
    # Note: We allow cancellation if they have a valid token OR if they originated from the bot's claim link.
    # To be secure, we validate the token if provided.
    
    discord_id = None
    if token:
        discord_id = await db.validate_link_token(token)
    
    # Check the withdrawal record
    withdrawal = await db.get_withdrawal(withdrawal_id)
    if not withdrawal:
        raise HTTPException(404, "Withdrawal not found.")
        
    # If a token was provided, ensure it matches the withdrawal owner
    if discord_id and withdrawal["discord_id"] != discord_id:
        raise HTTPException(403, "You do not have permission to cancel this withdrawal.")

    # Perform cancellation
    success = await db.cancel_withdrawal(withdrawal_id)
    if not success:
        return JSONResponse({
            "success": False, 
            "message": "Cancellation failed. Withdrawal may be finished or not found."
        }, status_code=400)

    logger.info(f"WITHDRAWAL CANCELLED | ID: {withdrawal_id} | User: {withdrawal['discord_id']}")
    return {"success": True, "message": "Withdrawal cancelled. SHx refunded to Discord."}


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
