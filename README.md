# SHx Tip Bot (v1.6) 🚀

A professional, production-ready Discord tipping bot for the **Stronghold Community**. This bot enables **instant, gasless SHx tipping** between members using a 1:1 custodial internal ledger, with a non-custodial, on-chain withdrawal system powered by **Stellar Soroban**.

---

## 🏗️ Architecture Overview

The SHx Tip Bot utilizes a **Hybrid Custodial Model** to maximize speed and eliminate community transaction costs while maintaining on-chain security for large movements.

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Discord     │────▶│  Discord Bot │────▶│  Postgres   │
│  Slash Cmds  │     │  (run_all.py)│     │  (Database) │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────┴───────┐     ┌──────────────┐
                    │ Web Dashboard│     │  House Acc.  │
                    │ (Vercel/Web) │     │ (Master Wal.)│
                    └──────┬───────┘     └───────┬──────┘
                           │                     │
                    ┌──────┴───────────┐         │
                    │ Soroban Contract │◄────────┘
                    │ (Claim/Authorize)│
                    └────────┬─────────┘
                             │
                      ┌──────▼───────┐
                      │ User Wallet  │
                      │ (Receives SHX)│
                      └──────────────┘
```

1.  **Instant Tipping**: Users tip each other (`/tip`) instantly within Discord. The bot manages these totals in a localized **Postgres** database. No Stellar network fees apply for internal tips.
2.  **On-Chain Deposits**: Users can fund their Discord wallet by sending SHx to the **House Account** with their unique Memo ID. The bot's background stream detects these and credits their balance.
3.  **Non-Custodial Withdrawals**: Users withdraw their funds via `/withdraw`. The bot issues a cryptographically signed **"Claim Ticket"**. The user signs a transaction with their own wallet (Lobstr, Freighter, etc.) on the **Web Dashboard** to claim the funds from the Smart Contract.

---

## 🌟 Key Features

*   **Nuclear Reliability Core**: Single orchestrator (`run_all.py`) for managing Bot and Web services.
*   **Stellar SDK 13.x Protocol**: Robust ID extraction and 512-bit ED25519 alignment (scval tagging) to ensure 100% on-chain success rates.
*   **Automated Payouts**: The Smart Contract (`soroban_tipping_contract`) handles the multi-hop authorization of SHx from the House Account to the user.
*   **Universal Wallet Support**: Integrated **Stellar Wallets Kit (SWK)** with **WalletConnect v2** support.
*   **Administrative Suite**: Real-time role allocation, automated allowance granting, and community airdrop management.

---

## 🛠️ Quick Start

### 1. Installation
```bash
git clone https://github.com/SHxTipBot/SHxTipBotV1.git
cd SHxTipBotV1
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env` and provide your credentials (Discord Token, House Account Secret, Database URL).

### 3. Automated Deployment
Use the included automation suite to prepare the network:
```bash
# 1. Fresh Contract Deploy & Init
python deploy_and_init.py

# 2. Grant House Account Allowance (Required for withdrawals)
python setup_allowance.py
```

### 4. Run Locally
```bash
python run_all.py
```

---

## 📟 Command Reference

| Command | User Level | Description |
| :--- | :--- | :--- |
| `/link` | All | Connect your Stellar wallet to Discord. |
| `/balance` | All | Check internal balance and pending withdrawals. |
| `/tip @user` | All | Instant, zero-fee community tip. |
| `/withdraw` | All | Move SHx to your personal Stellar wallet. |
| `/airdrop` | Admin | Create a claimable SHx pool in a channel. |
| `/tip-group` | Tipper | Tip an entire role or group simultaneously. |
| `/distribute` | Admin | Fund a specific user's internal balance. |

---

## 🚀 Mainnet Readiness

When moving to Mainnet:
1.  Set `STELLAR_NETWORK=public` in `.env`.
2.  Use the official SHx Issuer: `GDSTRSHXHGJ7ZIVRBXEYE5Q74XUVCUSEKEBR7UCHEUUEK72N7I7KJ6JH`.
3.  Deploy the contract to Mainnet using `deploy_and_init.py`.
4.  Ensure `WC_PROJECT_ID` is set for WalletConnect functionality.

---

## 🔒 Security
*   **Non-Custodial Architecture**: The bot never handles user private keys.
*   **Signature Enforcement**: All claims require a one-time signature from the House Account, preventing unauthorized withdrawals.
*   **Nonce Protection**: Prevents double-claiming of the same withdrawal ticket.

---

## 📄 License
MIT. Created for the Stronghold Community. This software handles real assets; ensure thorough testing on Testnet before deploying to Production.
