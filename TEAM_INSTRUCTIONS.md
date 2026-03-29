# 🚀 SHx Tip Bot: Team Handover Guide

This guide summarizes how the SHx Tip Bot works, why it was designed this way, and how to get it running in minutes.

---

## 💡 What is the SHx Tip Bot?

The SHx Tip Bot is a high-performance Discord community tool that allows users to send and receive **SHx** instantly and without gas fees. It uses a **Hybrid Custodial Architecture**:

1. **Internal Tipping**: Tips between members happen on an internal database ledger. They are **instant and free**.
2. **On-Chain Claims**: When a user wants their SHx in their real Stellar wallet, they generate a "Claim Ticket" and withdraw via a custom **Soroban Smart Contract**.

---

## 🌟 Why this is better than tip.cc

While `tip.cc` is a popular general-purpose bot, it often fails or becomes expensive for specific tokens like SHx due to high network fees or centralized congestion. Our custom design offers several mission-critical advantages:

| Feature | tip.cc (Generic) | **SHx Tip Bot (Custom)** |
| :--- | :--- | :--- |
| **Transaction Fees** | Bot often pays fees; can run out of XLM. | **User-Paid**: The user pays the small XLM gas when claiming. |
| **Speed** | Can be delayed by network congestion. | **Instant**: Internal tips move in milliseconds. |
| **Security** | Fully custodial (they hold 100% of keys). | **Signed Claims**: The bot authorizes, but the user executes the contract. |
| **Sustainability** | Relies on bot owner to fund withdrawal gas. | **Self-Sustaining**: The bot never needs a massive XLM treasury. |

---

## 🛠️ How it Works (The Flow)

1. **Deposit**: A user sends SHx to the central "House Account" with their unique **Memo ID**. The bot detects this and credits their balance.
2. **Tip**: A user types `/tip @user 100`. The bot instantly moves 100 SHx from the sender to the recipient in the database.
3. **Withdraw**: A user types `/withdraw 50`. The bot creates a cryptographically signed ticket.
4. **Claim**: The user visits the Web Dashboard, connects **Freighter/Lobstr**, and signs the claim. The SHx is moved from the House Account directly to their wallet.

---

## ⚡ Quick Start: 5-Minute Setup

If you are taking over this project, follow these steps to go live:

### **1. Configure the Environment**

Update the `.env` file with your credentials:

- `DISCORD_TOKEN`: Your bot token from the Discord Dev Portal.
- `HOUSE_ACCOUNT_SECRET`: The "Master Wallet" that will hold the community SHx pool.
- `SHX_SAC_CONTRACT_ID`: The official SHx contract ID on Stellar.

### **2. Deploy the Smart Contract (Automated)**

We have made on-chain setup "one-click" simple. Just run:

```bash
python deploy_and_init.py
```

*This script automatically installs the WASM, deploys the contract, and updates your `.env`.*

### **3. Start the Services**

Run the unified runner to start both the Discord Bot and the Web Dashboard:

```bash
python run_all.py
```

---

## 🛡️ Security Best Practices

- 🔐 **Protect the `HOUSE_ACCOUNT_SECRET`**: This key signs all withdrawal tickets. It is the most sensitive part of the system.
- 🔐 **Funding**: Keep a small amount of XLM (5–10) in the House Account to keep it active.
- 🔐 **Backups**: Ensure you have a backup of the `shx_tip_bot.db` file; it contains all user internal balances.

> [!TIP]
> **Pro-Tip for Admins**: Use the `/airdrop` command to create interactive claim messages for the community!
