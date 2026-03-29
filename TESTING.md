# SHx Tip Bot Operations & Testing Guide

This document outlines everything you need to know to manually test the core features of the SHx Tip Bot safely on your Discord server, leveraging its brand new Tip.cc-inspired instant custodial architecture.

Feel free to modify or update this document as the bot evolves!

---

## 🏛️ How the Bot Works Now (The Tip.cc Model)

- **Tipping is Instant and Off-Chain**: The `/tip` command interacts strictly with the bot's internal Postgres database. Users **do not** need to link their Stellar wallet or establish a trustline to receive or hold tips.
- **The Only Blockchain Interaction**: The bot relies on the Stellar Network *only* when a user types `/withdraw` (to pull SHx out of the Discord ecosystem) or when the House account processes a live `/deposit`.

---

## 🛠️ Testing Core Workflows

### 1. Generating Free Test Money (Admin Only)

Because the bot is now strictly balance-enforced, you must have an internal balance to tip people. As an Admin, you can "print" money in two ways to facilitate testing:
- **Manual Funding**: Type `/fund @username 1000` to instantly drop 1,000 SHx into anyone's internal database balance (including your own).
- **Auto-Funding (Admin QoL)**: If you type `/tip @username 100` but your balance is 0.0, the bot will invisibly grant you 5,000 SHx before the tip executes so you never run out of test ammo during live events.

### 2. Testing Internal Tips

- **Command**: `/tip @username amount [reason/memo]`
- **What to look for**: A success embed should appear instantly in the channel. Check both your balance and the recipient's balance using `/balance` to verify the math is accurate and the 1.0 SHx fee was assessed.
- **Validations**: Try to tip a bot, try to tip yourself, or try tipping a negative number to watch the error handlers gracefully block the action.

### 3. Testing the Wallet Linking Flow

- **Command**: `/link`
- **What to look for**: A unique 15-minute token URL should be delivered via an ephemeral message. Clicking the link should route your browser to your Vercel dashboard to pair a Stellar wallet securely.
- **Why it matters**: A linked Stellar wallet is strictly required before a user allows the bot to execute a `/withdraw` command.

### 4. Testing Airdrops

- **Command**: `/airdrop total_amount max_claims`
- **What to look for**: A button-based embed is spawned in the channel. The total amount is divided among the maximum number of claims. Any user who clicks the button will instantly receive their share internally.

### 5. Testing Withdrawals (On-Chain)

- **Command**: `/withdraw amount stellar_address`
- **What to look for**: The bot deducts the amount from your internal database balance, then builds and signs a physical Stellar Payment from the `HOUSE_ACCOUNT` to the selected address. The bot will provide a Stellar Expert URL to track the live on-chain transaction.

---

## 🖥️ Monitoring & Debugging

If an edge case breaks, you can view the real-time bot terminal output or open `shx_tip_bot.log`.
- Every major action (linking, transferring, withdrawing, funding) generates an `INFO` log footprint.
- Look out for `discord.app_commands.errors` if a slash command hangs—this means the bot caught a Python exception before it could respond to the Discord client.
