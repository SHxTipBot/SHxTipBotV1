# SHx Tip Bot

A production-ready Discord tipping bot for the **Stronghold Community** that lets members tip each other using the **SHx token** on the Stellar network.

> ⚠️ **WARNING**: This bot handles real cryptocurrency. Before deploying to mainnet, conduct a thorough security audit. Start with **testnet** first.

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  Discord     │────▶│  Bot (Python) │────▶│  Soroban Contract   │
│  Slash Cmds  │     │  discord.py   │     │  tip (gas reimb.)   │
└─────────────┘     └──────┬───────┘     └─────────┬───────────┘
                           │                       │
                    ┌──────┴───────┐     ┌─────────▼───────────┐
                    │  SQLite DB   │     │  Stellar Network     │
                    │  (mappings)  │     │  (SHx SAC + Horizon) │
                    └──────────────┘     └─────────────────────┘
                           │
                    ┌──────┴───────┐
                    │  Web App     │
                    │  (FastAPI)   │
                    │  /register   │
                    └──────────────┘
```

**Non-custodial**: The bot never stores private keys. Users link their public key via the web app and grant the Soroban contract an allowance to spend SHx on their behalf.

**Gas Reimbursement**: Instead of a fixed fee, the bot deducts a small SHX amount from each tip to cover the XLM gas cost (~0.05 XLM). This SHX is sent to the **House Account** to replenish its XLM via the Stellar DEX.

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers))
- A Stellar account with XLM (house account — pays network fees)
- Rust + `soroban-cli` (for deploying the contract)

### 2. Clone & Install

```bash
cd "SHx Tip Bot"
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your values (see Environment Variables below)
```

### 4. Deploy the Soroban Contract

```bash
cd soroban_tipping_contract
cargo build --release --target wasm32-unknown-unknown

# Deploy to testnet
soroban contract deploy \
  --wasm target/wasm32-unknown-unknown/release/shx_tipping_contract.wasm \
  --network testnet \
  --source <YOUR_SECRET_KEY>

# Initialize the contract
soroban contract invoke \
  --id <DEPLOYED_CONTRACT_ID> \
  --network testnet \
  --source <ADMIN_SECRET> \
  -- initialize \
  --admin <ADMIN_PUBLIC_KEY> \
  --shx_contract <SHX_SAC_CONTRACT_ID> \
  --treasury <TREASURY_PUBLIC_KEY>
```

Set the deployed contract ID as `SOROBAN_CONTRACT_ID` in `.env`.

### 5. Run

```bash
python run.py
```

This starts both the Discord bot and the web server (default port 8080).

## Deployment

### 1. GitHub (Source Control)

First, push your code to a **private** GitHub repository.

```bash
git init
git add .
git commit -m "Initial commit: SHx Tip Bot"
# Create a private repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### 2. Vercel (Web/Link Page)

The web component is configured for **Vercel**.

- Connect your GitHub repo to Vercel.
- Vercel will detect `vercel.json` and `api/index.py`.
- **Environment Variables**: In Vercel, add all the variables from your `.env` file (except the bot-only ones if you prefer, but adding all is safest).
- Once deployed, update `WEB_BASE_URL` in your bot's `.env` to your Vercel production URL.

### 3. Bot Hosting (Continuous)

The Discord bot needs a persistent server (Vercel is serverless and won't keep the bot alive).

- Use **Render**, **Railway**, or a **VPS**.
- Run the bot using: `python run.py` (which starts both) or a dedicated bot script.
- Ensure the server has the `.env` file and `shx_tip_bot.db`.

---

## Discord Commands

| Command | Description |
|---------|------------|
| `/link` | Get a unique URL to connect your Stellar wallet |
| `/register` | Alias for `/link` |
| `/balance` | Check your SHx balance |
| `/tip @user amount [reason]` | Tip a user with SHx |
| `/withdraw` | Info about withdrawing (non-custodial) |
| **Admin** | |
| `/fund @user amount` | Funding info |
| `/tip @user amount [reason]` | Tip a user with SHx (recipients pay gas) |
| `/distribute @user amount` | Admin: Send SHx from supply to a mod/user |
| `/airdrop total max [reason]` | Admin: Start an airdrop in the channel |
| `/tip-group amount user/role` | Admin: Batch tip multiple users or a role |
| `/withdraw` | Info about your non-custodial wallet |

---

## Linking Flow

1. User types `/link` in Discord → gets a unique URL (expires in 15 min).
2. User opens the URL → connects Freighter, Lobstr, or pastes their public key.
3. User signs an `approve` transaction granting the tipping contract an allowance.
4. Backend stores `discord_id → public_key` in SQLite.
5. User can now send and receive tips via `/tip`.

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Discord bot token | ✅ |
| `DISCORD_GUILD_ID` | Target guild (server) ID | ✅ |
| `ADMIN_DISCORD_IDS` | Comma-separated admin Discord IDs | ✅ |
| `STELLAR_NETWORK` | `testnet` or `public` | ✅ |
| `HORIZON_URL` | Stellar Horizon URL | ✅ |
| `SOROBAN_RPC_URL` | Soroban RPC endpoint | ✅ |
| `SHX_ASSET_CODE` | Asset code (`SHX`) | ✅ |
| `SHX_ISSUER` | SHx issuer address | ✅ |
| `SOROBAN_CONTRACT_ID` | Deployed tipping contract ID | ✅ |
| `SHX_SAC_CONTRACT_ID` | SHx Stellar Asset Contract ID | ✅ |
| `HOUSE_ACCOUNT_SECRET` | House account secret key (pays XLM fees) | ✅ |
| `HOUSE_ACCOUNT_PUBLIC` | House account public key | ✅ |
| `WEB_BASE_URL` | Public URL of the web app (e.g. Vercel URL) | ✅ |
| `FALLBACK_GAS_SHX` | Fallback gas reimbursement in SHx | |
| `ESTIMATED_XLM_FEE` | Estimated XLM cost per Soroban invoke | |
| `RATE_LIMIT_TIPS_PER_MINUTE` | Max tips per user per minute | |
| `DB_PATH` | SQLite database path | |
| `LOG_FILE` | Log file path | |
| `LOG_LEVEL` | Logging level | |

---

## Project Structure

```
SHx Tip Bot/
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
├── run.py                       # Entry point (bot + web)
├── bot.py                       # Discord bot + slash commands
├── web.py                       # FastAPI web server
├── database.py                  # SQLite database layer
├── stellar_utils.py             # Stellar/Soroban utilities
├── Dockerfile                   # Container deployment
├── web_static/
│   └── index.html               # Wallet linking page
└── soroban_tipping_contract/
    ├── Cargo.toml               # Rust manifest
    └── src/
        └── lib.rs               # Soroban tipping contract
```

---

## Security Notes

- **No private keys stored** — the bot is non-custodial; only public keys are in the database.
- **House account** pays XLM network fees; keep it funded but with limited balance.
- **Rate limiting** — 5 tips/minute/user by default (configurable).
- **Trustline validation** — verifies recipient has an SHx trustline before tipping.
- **Ephemeral responses** — sensitive info (balances, errors) is shown only to the user.
- **Link tokens expire** — 15-minute TTL, single-use.
- All secrets via environment variables — never hard-coded or logged.

---

## Mainnet Checklist

- [ ] Set `STELLAR_NETWORK=public` in `.env`
- [ ] Update `HORIZON_URL` and `SOROBAN_RPC_URL` to mainnet endpoints
- [ ] Deploy contract to mainnet
- [ ] Fund house account with XLM on mainnet
- [ ] Configure a real `WEB_BASE_URL` with HTTPS
- [ ] Security audit of all contract and bot code
- [ ] Set up monitoring and alerting
- [ ] Back up the SQLite database regularly

---

## License

MIT — use at your own risk. This software handles real cryptocurrency; the authors are not liable for any losses.
