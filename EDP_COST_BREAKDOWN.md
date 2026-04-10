# SHx Tip Bot: Infrastructure & Cost Breakdown

This document provides a comprehensive overview of the architecture, build investment, and monthly maintenance costs associated with running the **SHx Tip Bot**. It is structured for submission to the Stronghold Ecosystem Development Program (EDP).

---

## 🏗️ One-Time Build & Hardware Costs

These are the initial upfront investments required to design, develop, and host the foundation of the final product.

| Item / Resource | Description | Estimated Value / Cost |
| :--- | :--- | :--- |
| **Raspberry Pi 4 Kit** | Used as the dedicated, 24/7 localized hosting server for the Discord bot backend. Includes the board, power supply, case, and SD card. | **~$100.00** |
| **Initial Development Time** | Comprehensive engineering of the Python Discord bot, Soroban smart contracts (Rust), Stellar Wallet Kit frontend dashboard, and extensive Protocol 22 testing. | **~120 - 150 Hours** |

> [!NOTE]
> The exact monetary value of the initial development time will depend on the internal hourly rate assigned to the developer(s) building this. At a standard web3 development rate of $75/hr, this represents a ~$9,000 - $11,250 infrastructural investment.

---

## 🔄 Monthly Recurring Maintenance Costs

The recurring costs required to keep the bot operational, handle server hosting, AI integration, and on-chain transactions.

| Service | Purpose | Monthly Cost (Current) |
| :--- | :--- | :--- |
| **Antigravity Subscription** | AI pair programming agent utilized for continuous code maintenance, bug patching, server troubleshooting, and rapid feature implementation. | **$20.00 / month** |
| **Vercel Hosting** | Cloud hosting for the Web Dashboard interface used by users to link wallets and withdraw SHx. Currently running on the Hobby/Free tier. | **$0.00 / month** |
| **Stellar Network Fees (XLM)**| Base transaction fees and Soroban smart contract invocation compute costs. Paid from the House Account. Extremely efficient. | **~$2.00 - $5.00 / month** |
| **Routine Maintenance Dev Time**| Monthly allocation for server updates (Raspberry Pi OS/Packages), monitoring, user support, and minor bot modifications. | **~10 Hours / month** |

### **💵 Grand Tally (Current Monthly Cash Outlay)**: **~$25.00 / month** 
*(Excluding internal hourly compensation for the 10 hrs of maintenance).*

---

> [!WARNING]
> ### 📈 Disclaimer: Scalability and Future Cost Increases
> 
> The current infrastructure is highly optimized and budget-friendly, but costs **will increase** as network demand and user adoption grow. Please anticipate the following scaling triggers:
> 
> 1. **Vercel Pro Upgrade (~$20+/mo)**: As traffic to the web dashboard naturally scales, Vercel will eventually require an upgrade to their Pro tier to handle higher bandwidth, longer Serverless Function execution times, and concurrent connections without rate-limiting users.
> 2. **Dedicated Cloud Server (~$15 - $40/mo)**: While the Raspberry Pi 4 is excellent for current volume, massive discord server adoption may eventually require migrating the Python Bot to a dedicated VPS (Virtual Private Server) like AWS EC2, DigitalOcean, or Railway for better uptime SLAs and internet bandwidth redundancy.
> 3. **Increased XLM Network/Compute Fees**: Soroban smart contract invocations incur compute/resource fees. While cheap on Stellar, processing tens of thousands of tips and withdrawals will proportionally increase the monthly XLM burn rate for the House Account.
> 4. **Increased Development Hours**: As community demand grows, feature requests will naturally expand (e.g., deeper metrics, new mini-games, multi-asset tipping), which will require a larger monthly allotment of development hours.
