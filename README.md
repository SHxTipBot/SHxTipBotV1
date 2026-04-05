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

1. **Instant Tipping**: Users tip each other (`/tip`) instantly. The bot moves SHx in a localized **Postgres (Neon)** ledger. **Internal community tipping is 100% free with zero gas fees.**
2. **On-Chain Deposits**: Users deposit SHx to the **House Account** with a unique Memo ID. The bot automatically detects these deposits and credits the user's internal balance.
3. **Non-Custodial Withdrawals**: When a user wants their funds on-chain, they use `/withdraw`. The bot signs a **"Claim Ticket"**. The user then visits the **Web Dashboard** and executes a `claim_withdrawal` function.
   * **User Pays Gas**: The user pays the small XLM network fee directly to the Stellar network during the claim process. This ensures the bot remains free and sustainable to operate at scale.

---

## 📟 Comprehensive Command Reference

### 👤 Standard User Commands

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/link` | *None* | Start the wallet verification process to enable withdrawals. |
| `/balance` | *None* | Check your current available SHx and any pending withdrawal tickets. |
| `/deposit` | *None* | View the Bot's deposit address and your **Unique Memo ID**. |
| `/tip` | `@user`, `amount`, `[reason]` | Send SHx instantly and for free to another server member. |
| `/withdraw` | `amount`, `[destination]` | Prepare an on-chain withdrawal. Amount can be a number, `$USD`, or `all`. |

### 👥 Group & Role Tipping (Tipper Level)

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/tip-role` | `@role`, `amount` | **Split** a total amount equally among all members of a role. |
| `/tip-role-each` | `@role`, `amount` | Send a fixed amount to **every** member of a specific role. |
| `/tip-multiple` | `targets`, `amount` | Mention multiple users/roles to **split** an amount among them. |
| `/tip-multiple-each` | `targets`, `amount` | Send different amounts to different users in a single command. |
| `/airdrop` | `amount`, `duration` | Create an interactable claim button for a community pool. |

### 🛡️ Administrative Commands

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/create-role` | `name`, `color` | Create a new Discord role with a specific HEX color. |
| `/assign-role` | `@user`, `@role` | Assign a role to a member. |
| `/bot-sync` | *None* | Force-refresh the bot's slash command tree with Discord's API. |
| `/distribute` | `@user`, `amount` | Fund a user's internal balance from the House reserve. |

---

## 🌟 Key Features

* **Nuclear Reliability Core**: Single orchestrator (`run_all.py`) for managing Bot and Web services.
* **Stellar SDK 13.x Protocol**: Robust ID extraction and 512-bit ED25519 alignment (scval tagging) to ensure 100% on-chain success rates.
* **Automated Payouts**: The Smart Contract (`soroban_tipping_contract`) handles the multi-hop authorization of SHx from the House Account to the user.
* **Universal Wallet Support**: Integrated **Stellar Wallets Kit (SWK)** with **WalletConnect v2** support.

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

### 2. Automated Deployment

Use the included automation suite to prepare the network:

```bash
# 1. Fresh Contract Deploy & Init
python deploy_and_init.py

# 2. Grant House Account Allowance (Required for withdrawals)
python setup_allowance.py
```

### 3. Launch

```bash
python run_all.py
```

---

## 🚀 Mainnet Readiness

When moving to Mainnet:

1. **Set `STELLAR_NETWORK=public` in `.env`.**
2. **Use the official SHx Issuer: `GDSTRSHXHGJ7ZIVRBXEYE5Q74XUVCUSEKEBR7UCHEUUEK72N7I7KJ6JH`.**
3. **Deploy the contract to Mainnet using `deploy_and_init.py`.**

---

## 🔒 Security

* **Non-Custodial Payouts**: The bot never handles user private keys.
* **Signature Enforcement**: All claims require a one-time signature from the House Account.
* **Nonce Protection**: Prevents double-claiming of the same withdrawal ticket.

---

## 📄 License

MIT. Created for the Stronghold Community.
