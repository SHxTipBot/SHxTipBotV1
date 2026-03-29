# 🧪 How to Test SHx Withdrawals on Testnet

Hey everyone! We need to verify that tipping and withdrawing works flawlessly before moving to Mainnet. The bot currently operates on the **Stellar Testnet**, so you will be using fake "test" SHx and XLM to verify the functionality.

To test the `/withdraw` command and actually receive the SHX in your wallet, please follow these exact steps:

## 1. Get a Testnet Wallet

If you don't already do dev testing, the easiest way to test is by installing the **Freighter** browser extension.

1. Open Freighter, go to **Settings** (gear icon) → **Preferences**.
2. Turn ON **Enable Testnet**.
3. Under the network dropdown at the upper right of the wallet, switch to **Testnet**.
4. At the bottom of the main screen, click **Fund with Friendbot** to get 10,000 free test XLM (needed for the next step).

## 2. Add the Testnet SHx Token (Trustline)

You cannot receive SHx to your wallet until you explicitly "trust" the token. Since we are on Testnet, you must add the custom Testnet SHx issuer.

1. In your Freighter wallet to go **Manage Assets** (or Add Asset).
2. Choose **Add Custom Asset**.
3. Enter the following details:
   - **Asset Code:** `SHX`
   - **Asset Issuer:** `GC6S55K5ZGJTG6HDNQC42RLAQDRSLCJD7KFPKOOFM2JR4NNPV32SOIDF`
4. Click **Add Asset** and sign the transaction (costs miniscule amount of your free XLM).

## 3. Link Your Wallet to the Bot

1. In this channel, type `/link` and hit enter.
2. The bot will give you an ephemeral message with a secure link.
3. Click the link to open the SHx Dashboard, look under **Withdrawal Setup**, and paste your Freighter Wallet's Public Address (starts with a `G`).
4. Click **Link Wallet Address**.

## 4. Withdraw

1. Make sure you actually have internal tipping balance. (Use `/balance` to check). If you have zero, ask a Tipper/Admin to `/tip` you some test SHx!
2. Once you have a balance, type `/withdraw`
3. Enter the `amount` you want to withdraw (e.g., `100`)
4. Enter the `destination` address (your exact Freighter `G...` address).
5. The bot will initiate the Soroban Smart Contract and move your internal balance to your real Testnet wallet!

Let us know your results!
