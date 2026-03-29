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
7. [Deploying on Railway](#deploying-on-railway)
8. [Ownership Transfer (Step-by-Step)](#ownership-transfer-step-by-step)
9. [Admin Commands](#admin-commands)
10. [House Account Tipping Commands](#house-account-tipping-commands)
11. [How Tipping Works (Custodial Architecture)](#how-tipping-works-custodial-architecture)
12. [Security Best Practices](#security-best-practices)
13. [Troubleshooting](#troubleshooting)
14. [File Reference](#file-reference)

---

## Architecture Overview

```text
Stronghold  ──/distribute──►  House Account (SHX pool)
                                     │
                                     ▼
Discord User  ──/withdraw──►  Discord Bot (bot.py)
                                     │
                                     ▼
                        Generates signed "Claim Ticket"
                                     │
                                     ▼
Discord User  ──/claim─────►  Web Dashboard (Freighter)
                                     │
                                     ▼
                          Soroban Smart Contract
                          (claim_withdrawal)
                                     │
                      ┌──────────────┴──────────────┐
                      ▼                             ▼
               User Wallet                   House Account 
               (Pays XLM Fee)                (Sends SHX)
```

**Key principles**:

- **Hybrid Custodial Model** — Bot uses an internal database ledger for instant, gasless community tipping.
- **User-Paid Withdrawals** — On-chain Stellar network fees are paid by the user (XLM) when they "Claim" their funds.
- **Master Wallet Storage** — All community SHx is held in a single secure House Account authorized by the Bot.

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

- The bot uses this account to authorize withdrawals and tipping operations.
- The House Account **no longer pays network fees** for user withdrawals (the user pays the XLM gas when claiming).
- Fund with a base amount of XLM (1-2 XLM) to keep the account active.
- Keep the secret key secure (it's used to sign "Claim Tickets").

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

#### Automated Deployment (Recommended)

To deploy and initialize the contract in one step, ensure your `.env` file has the correct `HOUSE_ACCOUNT_SECRET` and `SHX_SAC_CONTRACT_ID`, then run:

```bash
python deploy_and_init.py
```

This script will:

1. Install the `soroban_tipping_contract.wasm` on-chain.
2. Deploy a new contract instance.
3. Initialize the contract with your SHx token and House Account.
4. Correctly authorize the bot to sign withdrawals.
5. Automatically update your `.env` with the new `SOROBAN_CONTRACT_ID`.

To redeploy on mainnet, simply change your `STELLAR_NETWORK` to `public` in `.env` and run the script again.

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

# ── Bot House Account (Master Wallet) ───
# The House Account secret is used to sign "Withdrawal Claim Tickets"
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

## Ownership Transfer (Step-by-Step)

To handover the bot to a new team or individual, follow these steps:

### 1. Identify the New Admin

The person "accepting" the admin role needs to find their unique **Discord User ID**:

1. Open Discord → **User Settings** → **Advanced**.
2. Enable **Developer Mode**.
3. Right-click their profile → **Copy User ID**.

### 2. Update the Admin List

Open the `.env` file (or update the environment variables in Railway/Vercel) and add the new User ID to the `ADMIN_DISCORD_IDS` list:

```env
ADMIN_DISCORD_IDS=1234567890,9876543210
```

This grants that user full access to `/create-role`, `/assign-role`, and `/airdrop`.

### 3. Link the Master Wallet (House Account)

The "Master Wallet" is the Stellar account that holds the SHx and XLM for the community.

1. Generate or import a Stellar secret key (starts with 'S').
2. Update the `HOUSE_ACCOUNT_SECRET` and `HOUSE_ACCOUNT_PUBLIC` in the `.env` file.
3. Fund this wallet with **XLM** (for gas) and **SHx** (for the tip pool).
4. Restart the bot.

---

## How Tipping Works (Custodial Architecture)

Unlike most bots that require on-chain transactions for every micro-tip, this bot uses a **1:1 Custodial Internal Balance** system. This makes tipping instant and free for your community.

1. **Deposits**: Users deposit SHx to the Bot's House Account with a unique **memo ID**.
2. **Internal Ledger**: The bot detects the deposit and credits the user's **Internal Balance** in the database.
3. **Tipping**: When a user types `/tip @recipient 10`, the bot instantly moves 10 SHx from the sender's balance to the recipient's balance in the database. There are **no on-chain gas fees** for internal tips.
4. **Withdrawals**: When a user wants their SHx on-chain, they use the `/withdraw` command. The bot deducts their internal balance and provides a **"Claim Ticket"** (link to dashboard). The user then visits the dashboard and signs a transaction with their own wallet (Freighter/Lobstr). **The user pays the Stellar network fee (XLM)** for this transaction.

### Why this is better

- **Instant**: Community tipping is limited only by Discord's speed, not the Stellar network.
- **Gasless**: Users don't need XLM to tip each other.
- **Simplified Setup**: You only need to fund the single Master Wallet (House Account) with XLM for withdrawals.

---

## Admin Commands

| Command                       | Description                                          |
| ----------------------------- | ---------------------------------------------------- |
| `/create-role name hex_color` | Create a new Discord role (Admin only).              |
| `/assign-role @user @role`    | Assign a role to a Discord user (Admin only).        |
| `/airdrop total max mins`     | Create an airdrop message with a "Claim SHx" button. |

*Note: Only users whose Discord IDs are in `ADMIN_DISCORD_IDS` can use the admin commands listed above (except airdrop if configured otherwise).*

---

## House Account Tipping Commands

Any Discord user that is a **House Account** or **Tipper** (meaning they are assigned to any Discord role) can use:

| Command                  | Description                                              |
| ------------------------ | -------------------------------------------------------- |
| `/tip-role @role amount` | Tip a specific amount of SHx to *each* member of a role. |

### 2. Verification Link Flow

1. User types `/link`.
2. Bot generates a unique, time-limited token.
3. User visits the dashboard, chooses their wallet, and signs a "Link" transaction (or provides their address).
4. The Master Wallet (`HOUSE_ACCOUNT_SECRET`) validates the request and saves the link to the DB.

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
- 🔐 The **HOUSE_ACCOUNT_SECRET** is the most sensitive value — it signs all "Claim Tickets" which authorize on-chain transfers.
- 🔐 Use environment variables in production (Vercel dashboard, Docker `--env-file`)
- 🔐 Rotate the house account secret key if compromised
- 🔐 Keep the house account XLM balance modest (50–100 XLM) to limit exposure
- 🔐 The bot uses a 1:1 custodial model — ensure internal balances match real SHx in the Master Wallet

---

## Troubleshooting

| Issue                       | Solution                                                                        |
| --------------------------- | ------------------------------------------------------------------------------- |
| Slash commands don't appear | Restart bot — commands sync on startup                                          |
| "Wallet not linked"         | User needs to use `/link` and complete the web flow                             |
| "Not enough allowance"      | Run `approve_contract.py <USER_SECRET_KEY>`                                     |
| "Transaction timed out"     | Testnet can be slow — check Stellar Expert for the TX hash                      |
| "DEX price unavailable"     | Normal on testnet — uses fallback fee of 5 SHx                                  |
| House account out of XLM    | Send more XLM to the house account                                              |
| Port 8080 in use            | Kill old process: `netstat -ano \| findstr :8080` then `taskkill /PID <PID> /F` |

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
