# SHx Tip Bot — Handover Guide

Complete setup guide for the Stronghold team to deploy and manage the SHx Tip Bot.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Account Setup (Stellar)](#account-setup-stellar)
4. [Discord Bot Setup](#discord-bot-setup)
5. [Environment Configuration](#environment-configuration)
6. [Deploying on Vercel](#deploying-on-vercel)
7. [Running the Discord Bot](#running-the-discord-bot)
8. [Admin Commands](#admin-commands)
9. [How Tipping Works](#how-tipping-works)
10. [Security Best Practices](#security-best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Deploying on Railway](#deploying-on-railway)

---

## Architecture Overview

```text
Stronghold  ──/distribute──►  Mod Wallets (SHX supply)
                                    │
                                    ▼
Discord Mod  ──/tip──►  Discord Bot (bot.py)
                              │
                              ▼
                     Soroban Smart Contract
                     (tipping_contract)
                              │
                     ┌────────┴────────┐
                     ▼                 ▼
              Sender Wallet     Recipient Wallet
              (mod's own)       (user's own)
                                    │
                                    ▼
                              Small SHX → XLM swap
                              (covers gas fee)

Discord User  ──/link──►  Web App (web.py + index.html)
                              │
                              ▼
                     Links Discord ID → Stellar wallet
```

**Key principles**:

- **Non-custodial** — users hold their own Stellar wallets
- **No fees collected** — Stronghold supplies SHX to mods for distribution
- **Recipient pays gas** — a tiny portion of the received SHX is swapped to XLM to cover the Stellar transaction fee

### Components

| Component | File(s) | Purpose |
| --------- | ------- | ------- |
| Discord Bot | `bot.py` | Slash commands: /tip, /link, /balance, etc. |
| Web App | `web.py`, `web_static/index.html` | Wallet linking page served via FastAPI |
| Stellar Utils | `stellar_utils.py` | Balance queries, fee calc, transaction execution |
| Database | `database.py`, `shx_tip_bot.db` | SQLite DB linking Discord IDs to Stellar keys |
| Unified Runner | `run_all.py` | Starts both Bot and Web server for 24/7 hosting |
| Soroban Contract | `soroban_tipping_contract/` | On-chain tipping logic |

---

## Prerequisites

- **Python 3.10+** with pip
- **Node.js/npm** (for Vercel CLI, optional)
- A **Stellar account** for the bot to submit transactions (the "house account")
- A **Stronghold SHX supply wallet** for mods to distribute from
- A **Discord Bot Token** from [Discord Developer Portal](https://discord.com/developers/applications)

---

## Account Setup (Stellar)

You need **2 Stellar accounts** for production:

### 1. House Account (submits transactions)

- The bot uses this account to submit Soroban contract calls to the network
- Fund with **20–50 XLM** initially (gas costs ~0.05 XLM per tip)
- The XLM cost is reimbursed by the recipient (see "How Tipping Works" below)
- Keep the secret key secure (it's used by the bot to sign transactions)

### 2. Stronghold Supply Wallet (SHX distribution)

- Stronghold loads this wallet with SHX to be distributed
- Mods use `/tip` to distribute SHX to community members
- **No treasury or fee collection** — SHX flows one way: Stronghold → mods → users

### SHx Asset (Mainnet)

- **For mainnet**: Use the official Stronghold SHx issuer: `GDSTRSHXHGJ7ZIVRBXEYE5Q74XUVCUSEKEBR7UCHEUUEK72N7I7KJ6JH`
- **For testnet**: The setup script (`setup_testnet.py`) creates a custom test issuer

### Soroban Contracts

Two contract IDs are needed:

- **SOROBAN_CONTRACT_ID**: The deployed tipping contract
- **SHX_SAC_CONTRACT_ID**: The SHx Stellar Asset Contract (SAC) — wraps the SHx classic asset for Soroban

To redeploy on mainnet, build and deploy the contract from `soroban_tipping_contract/`.

---

## Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application → **Bot** section
3. Copy the **Bot Token**
4. Enable these intents:
   - ✅ `SERVER MEMBERS INTENT` (recommended for richer UX)
5. Generate an invite URL with scopes: `bot`, `applications.commands`
   - Permissions: `Send Messages`, `Use Slash Commands`, `Embed Links`
6. Invite the bot to your Discord server
7. Copy the **Guild ID** (right-click server → Copy Server ID, with Developer Mode on)
8. Copy **Admin Discord IDs** (right-click your user → Copy User ID)

---

## Environment Configuration

Copy `.env.example` to `.env` and fill in all values:

```env
# ── Discord ───────────────────────────────────────
DISCORD_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_server_id_here
ADMIN_DISCORD_IDS=admin_user_id_1,admin_user_id_2

# ── Stellar Network ──────────────────────────────
# Change to "public" for mainnet
STELLAR_NETWORK=testnet
HORIZON_URL=https://horizon-testnet.stellar.org
SOROBAN_RPC_URL=https://soroban-testnet.stellar.org

# For mainnet, use:
# HORIZON_URL=https://horizon.stellar.org
# SOROBAN_RPC_URL=https://soroban.stellar.org

# ── SHx Token ────────────────────────────────────
SHX_ASSET_CODE=SHX
SHX_ISSUER=your_shx_issuer_public_key

# ── Soroban Contracts ────────────────────────────
SOROBAN_CONTRACT_ID=your_tipping_contract_id
SHX_SAC_CONTRACT_ID=your_shx_sac_contract_id

# ── Bot House Account (submits transactions) ────
HOUSE_ACCOUNT_SECRET=your_house_secret_key
HOUSE_ACCOUNT_PUBLIC=your_house_public_key

# ── Gas Fee Configuration ────────────────────────
# Estimated XLM cost of a Soroban invocation
ESTIMATED_XLM_FEE=0.05

# ── Rate Limiting ────────────────────────────────
RATE_LIMIT_TIPS_PER_MINUTE=5

# ── Web Application ─────────────────────────────
WEB_HOST=0.0.0.0
WEB_PORT=8080
WEB_BASE_URL=https://your-domain.vercel.app

# ── Logging ──────────────────────────────────────
LOG_FILE=shx_tip_bot.log
LOG_LEVEL=INFO
DB_PATH=shx_tip_bot.db
```

### Critical: Switching to Mainnet

When switching from testnet to mainnet, update:

1. `STELLAR_NETWORK=public`
2. `HORIZON_URL=https://horizon.stellar.org`
3. `SOROBAN_RPC_URL=https://soroban.stellar.org`
4. `SHX_ISSUER=GDSTRSHXHGJ7ZIVRBXEYE5Q74XUVCUSEKEBR7UCHEUUEK72N7I7KJ6JH` (official Stronghold issuer)
5. Deploy the Soroban contract to mainnet and update both contract IDs
6. Fund the house account with real XLM

---

## Deploying on Vercel

The **web component** (wallet linking page) can be deployed to Vercel. The Discord bot must run on a separate server (VPS/Docker).

### Web App on Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Create a `vercel.json` in the project root:

```json
{
  "builds": [
    {
      "src": "web.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/web_static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/web.py"
    }
  ]
}
```

1. Set environment variables in Vercel dashboard (same as `.env`)
2. Deploy: `vercel --prod`
3. Update `WEB_BASE_URL` in `.env` to your Vercel URL (e.g., `https://shx-tip-bot.vercel.app`)

### Discord Bot on a VPS

The Discord bot needs to run persistently. Options:

- **Docker**: Use the included `Dockerfile`

  ```bash
  docker build -t shx-tip-bot .
  docker run -d --env-file .env --name shx-tip-bot shx-tip-bot
  ```

- **Systemd service** (Linux VPS):

  ```bash
  # Create service file
  sudo nano /etc/systemd/system/shx-tip-bot.service
  # Start and enable
  sudo systemctl start shx-tip-bot
  sudo systemctl enable shx-tip-bot
  ```

- **PM2** (Node process manager):

  ```bash
  pm2 start "python run_all.py" --name shx-tip-bot
  ```

---

## Deploying on Railway

Railway is our **recommended** platform for 24/7 persistent hosting. It handles Docker deployments automatically from GitHub.

### Step 1: Prepare Repository

Ensure your latest code (including `Dockerfile` and `run_all.py`) is pushed to GitHub.

### Step 2: Create Railway Project

1. Log in to [Railway.app](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select your `SHxTipBotV1` repository.

### Step 3: Configure Environment Variables

1. Go to the **Variables** tab in your Railway service.
2. Click **Bulk Import** and paste the contents of your `.env` file.
3. Ensure `WEB_PORT` is set to `8080` (Railway will automatically map this to a public URL).

### Step 4: Health Checks (Optional but Recommended)

1. Go to **Settings** → **Healthchecks**.
2. Set the path to `/health`.
3. Railway will now monitor your bot and restart it automatically if it becomes unresponsive.

### Step 5: Network (Public URL)

1. Go to **Settings** → **Networking**.
2. Click **Generate Domain**. This will be your new `WEB_BASE_URL`.
3. Important: Update the `WEB_BASE_URL` variable in Railway to match this new domain.


---

## House Account and Role-Based Funding

To prepare for mainnet and maintain a strict 1:1 custodial backing of SHx, the bot uses a "House Account" model.
- The **House Account** is simply any Discord user designated as an Admin (`ADMIN_DISCORD_IDS` in `.env`).
- To fund the House Account, you must make a real Stellar deposit to the bot's deposit address (obtainable via the `/deposit` command) using the Admin's Discord ID as the memo. This credits the Admin's internal balance with real SHx.
- Once funded, the House Account can distribute SHx to other Discord members (usually "Tippers") so they have a balance to tip regular users.

### Linking Profiles to Roles & Tipping

You can manage roles natively via Discord Server Settings, or use the bot's built-in commands:

1. Use `/create-role` to create a new role (e.g., "Tippers").
2. Use `/assign-role` to give this role to specific Discord profiles.
3. Once users are assigned to a role, they unlock the ability to run `/tip-role`. Any user with an assigned role can tip **every** member of another configured role, using their own SHx balance!


---

## Admin Commands

| Command                     | Description                                            |
| --------------------------- | ------------------------------------------------------ |
| `/create-role name hex_color`| Create a new Discord role (Admin only).                |
| `/assign-role @user @role` | Assign a role to a Discord user (Admin only). |
| `/airdrop total max mins` | Create an airdrop message with a "Claim SHx" button. |

*Note: Only users whose Discord IDs are in `ADMIN_DISCORD_IDS` can use the admin commands listed above (except airdrop if configured otherwise).*

---

## House Account Tipping Commands

Any Discord user that is a **House Account** or **Tipper** (meaning they are assigned to any Discord role) can use:

| Command                  | Description                                            |
| ------------------------ | ------------------------------------------------------ |
| `/tip-role @role amount` | Tip a specific amount of SHx to *each* member of a role. |


## How Tipping Works

1. Mod types `/tip @recipient 10 Great work!`
2. Bot checks: sender linked? recipient linked? balance sufficient? rate limit ok?
3. Bot calculates gas fee equivalent in SHX (based on SHx/XLM DEX price)
4. Bot calls the Soroban tipping contract:
   - Transfers `amount` SHx from sender → recipient
   - A small SHX portion from the tip is swapped to XLM via the Stellar DEX to cover the network gas fee
5. The **recipient** effectively pays the gas (deducted from the tip they receive)
6. **No fees go to a treasury** — Stronghold supplies SHX, mods distribute it
7. Bot posts success embed with Stellar Expert link

### Airdrops & Group Tipping

#### `/airdrop` (Community Airdrops)

1. Mod creates an airdrop via `/airdrop total_amount:100 max_claims:10`.
2. A message is posted with a **"Claim SHx"** button.
3. Users click the button to claim their share on-demand.
4. Gas is deducted from each claim, and the airdrop id is tracked in the DB.

#### `/tip-group` (Batch Tipping)

1. Mod tips a group via `/tip-group amount:5 users:@AlphaMod @MemberRole`.
2. The bot iterates through each unique, linked user in the mentioned users/roles.
3. Each user receives the specified amount as a separate transaction.

### User Approval Flow

- Users must approve the tipping contract to spend SHx on their behalf
- This happens during `/link` → web page → "Sign & Link Wallet"
- The approval grants the contract a 1M SHx allowance
- If a user links manually, run `approve_contract.py <SECRET_KEY>` separately

---

## Security Best Practices

- 🔐 **Never commit `.env`** — it contains secret keys
- 🔐 **Never commit `testnet_secrets.env` or `testnet_accounts.json`**
- 🔐 The **HOUSE_ACCOUNT_SECRET** is the most sensitive value — it signs all tip transactions
- 🔐 Use environment variables in production (Vercel dashboard, Docker `--env-file`)
- 🔐 Rotate the house account secret key if compromised
- 🔐 Keep the house account XLM balance modest (50–100 XLM) to limit exposure
- 🔐 The bot is non-custodial — you never hold user SHx

---

## Troubleshooting

| Issue                       | Solution                                                   |
| --------------------------- | ---------------------------------------------------------- |
| Slash commands don't appear | Restart bot — commands sync on startup                     |
| "Wallet not linked" | User needs to use `/link` and complete the web flow |
| "Not enough allowance" | Run `approve_contract.py <USER_SECRET_KEY>` |
| "Transaction timed out" | Testnet can be slow — check Stellar Expert for the TX hash |
| "DEX price unavailable" | Normal on testnet — uses fallback fee of 5 SHx |
| House account out of XLM | Send more XLM to the house account |
| Port 8080 in use | Kill old process: `netstat -ano \| findstr :8080` then `taskkill /PID <PID> /F` |

---

## File Reference

```text
SHx Tip Bot/
├── .env                    # Configuration (DO NOT COMMIT)
├── .env.example            # Template for .env
├── bot.py                  # Discord bot (slash commands)
├── web.py                  # FastAPI web server
├── web_static/
│   └── index.html          # Wallet linking page
├── stellar_utils.py        # Stellar/Soroban transaction logic
├── database.py             # SQLite database operations
├── run_all.py              # Entry point (starts bot + web)
├── setup_testnet.py        # Testnet account setup
├── test_e2e.py             # E2E testnet preparation
├── approve_contract.py     # Submit approve TX for a user
├── create_test_account.py  # Generate & fund a test account
├── Dockerfile              # Docker deployment (optimized for Railway)
├── requirements.txt        # Python dependencies
└── soroban_tipping_contract/
    └── ...                 # Rust Soroban smart contract
```
