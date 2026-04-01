DASHBOARD_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SHx Tip Bot | Web Dashboard</title>
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  
  <style>
    :root {
      --bg: #030712;
      --card-bg: rgba(17, 24, 39, 0.7);
      --border: rgba(59, 130, 246, 0.2);
      --border-hover: rgba(59, 130, 246, 0.5);
      --text: #f9fafb;
      --text-muted: #9ca3af;
      --accent: #3b82f6;
      --error: #ef4444;
      --success: #10b981;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    .background-castle {
      position: fixed;
      top: 0; left: 0; width: 100%; height: 100%;
      background-image: url('/stronghold_logo_watermark.svg');
      background-repeat: no-repeat;
      background-position: center;
      background-size: 60%;
      opacity: 0.15;
      z-index: -1;
      filter: blur(2px);
    }

    .container {
      max-width: 1000px;
      margin: 0 auto;
      padding: 1.5rem;
      flex: 1;
    }

    nav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 0;
      margin-bottom: 2rem;
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-family: 'Outfit', sans-serif;
      font-weight: 700;
      font-size: 1.5rem;
      color: #3b82f6;
    }

    .logo img { width: 32px; height: 32px; }

    .hero {
      text-align: center;
      padding: 3rem 0;
      margin-bottom: 2rem;
    }

    .hero h1 {
      font-family: 'Outfit', sans-serif;
      font-size: 3rem;
      margin-bottom: 0.5rem;
      background: linear-gradient(135deg, #fff 0%, #3b82f6 100%);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .hero p { color: var(--text-muted); }

    .card {
      background: var(--card-bg);
      -webkit-backdrop-filter: blur(12px);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 1.5rem;
      padding: 2rem;
      margin-bottom: 1.5rem;
      transition: border-color 0.3s ease;
    }

    .card h2 { margin-bottom: 0.5rem; font-family: 'Outfit'; }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.875rem 1.75rem;
      border-radius: 0.75rem;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      border: none;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      color: white;
    }

    .btn-primary { background-color: var(--accent); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
    .btn-primary:hover { background-color: #2563eb; transform: translateY(-1px); }
    .btn-secondary { background: rgba(59, 130, 246, 0.1); color: var(--accent); border: 1px solid var(--border); }
    .btn-secondary:hover { border-color: var(--accent); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

    /* Utility Helpers */
    .w-full { width: 100%; }
    .text-center { text-align: center; }
    .text-right { text-align: right; }
    .justify-center { justify-content: center; }
    .mt-4 { margin-top: 1rem; }
    .mb-6 { margin-bottom: 1.5rem; }
    .text-sm { font-size: 0.85rem; }
    .text-xs { font-size: 0.8rem; }
    .text-bold { font-weight: 600; }
    .text-accent { color: var(--accent); }
    .text-error { color: var(--error); }
    .text-success { color: var(--success); }
    .text-white { color: #fff; }
    .bg-success { background: var(--success) !important; }
    .bg-dark-overlay { background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 0.75rem; border: 1px solid var(--border); }
    .break-word { overflow-wrap: break-word; display: block; }

    .status {
      padding: 1rem; border-radius: 0.75rem; margin-bottom: 1.5rem; font-size: 0.95rem; font-weight: 500;
    }
    .status.success { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .status.error { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }

    .hidden { display: none !important; }

    #swk-button-wrapper {
      display: inline-block;
    }
  </style>
</head>
<body>
  <div class="background-castle"></div>

  <div class="container">
    <nav>
      <div class="logo">
        <img src="/stronghold_logo_watermark.svg" alt="SHx">
        <span>SHx Tip Bot</span>
      </div>
      <div>
        <div id="swk-button-wrapper"></div>
        <div id="wallet-display" class="hidden text-right">
          <code id="address-short" class="text-accent text-bold">G...</code>
        </div>
      </div>
    </nav>

    <div class="hero">
      <h1>Community Portal</h1>
      <p>Securely link your Discord and manage claims.</p>
    </div>

    <!-- Link Card -->
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
        <div>
          <h2>Discord Status</h2>
          <p id="link-status-text" class="text-muted">Syncing...</p>
        </div>
        <div id="discord-balance-card" class="text-right">
          <p class="text-xs text-muted">Discord Wallet</p>
          <p class="text-xl text-bold text-accent"><span id="internal-balance-val">{{INTERNAL_BALANCE}}</span> <span class="text-xs">SHx</span></p>
        </div>
      </div>
      
      <p id="reset-session-link" class="mb-4 text-xs text-accent" style="cursor:pointer; text-decoration: underline;" onclick="resetSession()">Trouble connecting? Reset Session</p>
      <div id="link-notify" class="status hidden"></div>
      <button id="btn-link" class="btn btn-primary w-full justify-center" disabled>Verify & Link Wallet</button>
      <p id="btn-unlink" class="text-error mt-4 text-center text-sm hidden">Unlink Wallet</p>
    </div>

    <!-- Claim Card -->
    <div id="claim-card" class="card hidden">
      <h2>Pending Withdrawal</h2>
      <div id="claim-notify" class="status hidden"></div>
      <button id="btn-claim-action" class="btn btn-primary bg-success w-full justify-center" disabled>Claim SHx Rewards</button>
      <button id="btn-claim-cancel" class="btn btn-secondary w-full justify-center mt-4">Cancel & Refund to Discord</button>
    </div>

    <!-- Withdraw Card -->
    <div id="withdraw-card" class="card hidden">
      <h2>Web Withdrawal</h2>
      <p class="text-sm text-muted mb-6">Withdraw SHx directly from your Discord balance to your linked wallet.</p>
      <div style="margin-bottom: 1rem;">
        <input type="number" id="withdraw-amount-input" placeholder="Amount (e.g. 1000)" style="width: 100%; padding: 0.75rem; border-radius: 0.5rem; border: 1px solid var(--border); background: rgba(0,0,0,0.5); color: white; margin-bottom: 0.5rem;">
      </div>
      <div id="withdraw-notify" class="status hidden"></div>
      <button id="btn-web-withdraw" class="btn btn-primary w-full justify-center" disabled>Prepare Withdrawal</button>
    </div>

  </div>

  <script src="/stellar-sdk.js?v={{APP_VERSION}}"></script>
  <script src="/axios.js?v={{APP_VERSION}}"></script>
  <script src="/wallet-kit-bundle.umd.js?v={{APP_VERSION}}"></script>

  <script>
    const urlParams = new URLSearchParams(window.location.search);
    const TOKEN = urlParams.get('token') || "{{TOKEN}}";
    let CLAIM_ID = urlParams.get('claim_id') || "{{CLAIM_ID}}";
    const NETWORK = "{{NETWORK}}";
    const WC_PROJECT_ID = "{{WC_PROJECT_ID}}";
    const APP_VERSION = "{{APP_VERSION}}";
    const NETWORK_PASSPHRASE = (NETWORK === 'mainnet' || NETWORK === 'public') ? 'Public Global Stellar Network ; September 2015' : 'Test SDF Network ; September 2015';
    
    // Initial balance from template injection
    let currentBalance = "{{INTERNAL_BALANCE}}";

    const setStatus = (msg, isError = false) => {
        const el = document.getElementById('link-status-text');
        if (!el) return;
        el.innerText = (isError ? "❌ " : "") + msg;
        el.className = isError ? "text-error" : "text-muted";
    };

    const fetchBalance = async () => {
        try {
            const res = await axios.get(`${API_BASE}/api/balance?token=${TOKEN}&claim_id=${CLAIM_ID}`);
            if (res.data.success) {
                currentBalance = res.data.balance;
                const el = document.getElementById('internal-balance-val');
                if (el) el.innerText = currentBalance;
            }
        } catch (e) {
            console.error("Failed to fetch balance:", e);
        }
    };

    const resetSession = () => {
        if (!confirm("This will clear your local wallet connection cache and reload the page. Continue?")) return;
        setStatus("Clearing session...");
        for (let key in localStorage) {
            if (key.includes('wc@2') || key.includes('walletconnect')) {
                localStorage.removeItem(key);
            }
        }
        location.reload();
    };

    window.onerror = (msg) => setStatus("Error: " + msg, true);
    window.onunhandledrejection = (event) => setStatus("Async Error: " + (event.reason?.message || event.reason || "Unknown"), true);

    const SOROBAN_CONTRACT_ID = "{{SOROBAN_CONTRACT_ID}}";
    const DISCORD_ID = "{{DISCORD_ID}}";
    const API_BASE = window.location.origin;
    const HORIZON_URL = (NETWORK === 'mainnet' || NETWORK === 'public') ? 'https://horizon.stellar.org' : 'https://horizon-testnet.stellar.org';
    const SOROBAN_URL = (NETWORK === 'mainnet' || NETWORK === 'public') ? 'https://soroban.stellar.org' : 'https://soroban-testnet.stellar.org';

    let userAddress = null;
    let kitInitialized = false;

    const updateUI = (address) => {
      userAddress = address;
      if (address) {
        document.getElementById('wallet-display').classList.remove('hidden');
        document.getElementById('address-short').innerText = `${address.substring(0,5)}...${address.substring(51)}`;
        document.getElementById('btn-link').disabled = false;
        const claimBtn = document.getElementById('btn-claim-action');
        if (claimBtn) claimBtn.disabled = false;
        const withdrawBtn = document.getElementById('btn-web-withdraw');
        if (withdrawBtn) withdrawBtn.disabled = false;
        setStatus("Connected ✅");
      } else {
        document.getElementById('wallet-display').classList.add('hidden');
        document.getElementById('address-short').innerText = 'G...';
        document.getElementById('btn-link').disabled = true;
        const claimBtn = document.getElementById('btn-claim-action');
        if (claimBtn) claimBtn.disabled = true;
        const withdrawBtn = document.getElementById('btn-web-withdraw');
        if (withdrawBtn) withdrawBtn.disabled = true;
      }
    };

    const notify = (id, msg, isError = false) => {
        const div = document.getElementById(id);
        div.classList.remove('hidden', 'success', 'error');
        div.classList.add(isError ? 'error' : 'success');
        div.innerText = msg;
    };

    try {
        if (!kitInitialized) {
            const { StellarWalletsKit, KitEventType, SwkAppDarkTheme, defaultModules, WalletConnectModule } = window.StellarKit;
            const modules = defaultModules();
            
            if (WalletConnectModule && WC_PROJECT_ID) {
                modules.push(new WalletConnectModule({
                    projectId: WC_PROJECT_ID,
                    projectID: WC_PROJECT_ID, 
                    network: NETWORK,
                    metadata: {
                        name: "SHx Tip Bot",
                        description: "Securely link your Discord account",
                        url: window.location.origin,
                        icons: ["https://shxtipbotv1.vercel.app/stronghold_logo_watermark.svg"]
                    }
                }));
            }

            // Initialize SWK using the static init method (standard for this UMD bundle)
            StellarWalletsKit.init({
                theme: SwkAppDarkTheme,
                modules: modules,
                network: NETWORK === 'mainnet' ? 'public' : 'testnet'
            });

            // Create the built-in wallet connect button
            const buttonWrapper = document.getElementById('swk-button-wrapper');
            StellarWalletsKit.createButton(buttonWrapper);

            // Listen for wallet state changes
            StellarWalletsKit.on(KitEventType.STATE_UPDATED, (event) => {
                updateUI(event.payload.address || null);
            });
            
            kitInitialized = true;
        }
    } catch (err) {
        console.error("SWK INIT FAILED:", err);
        setStatus("Connection Error: " + (err.message || "Kit not found"), true);
    }

    // ── APP LOGIC ──
    async function handleLink() {
        if (!userAddress) return;
        try {
            notify('link-notify', "Signing Link Request...");
            const server = new window.StellarSdk.Horizon.Server(HORIZON_URL);
            const account = await server.loadAccount(userAddress);
            const tx = new window.StellarSdk.TransactionBuilder(account, { fee: "1000", networkPassphrase: NETWORK_PASSPHRASE })
                .addOperation(window.StellarSdk.Operation.manageData({ name: "link_discord", value: DISCORD_ID }))
                .setTimeout(300).build();

            notify('link-notify', "Awaiting wallet signature...");
            const { signedTxXdr } = await window.StellarKit.StellarWalletsKit.signTransaction(tx.toXDR(), {
                networkPassphrase: NETWORK_PASSPHRASE,
                address: userAddress,
            });

            notify('link-notify', "Verifying on server...");
            const res = await axios.post(`${API_BASE}/api/link`, {
                token: TOKEN, public_key: userAddress, signature_xdr: signedTxXdr, is_approved: true
            });
            if (res.data.success) {
                notify('link-notify', "✅ Wallet linked successfully!");
                setStatus("Linked ✅");
                document.getElementById('btn-unlink').classList.remove('hidden');
                document.getElementById('discord-balance-card').classList.remove('hidden');
                fetchBalance(); // Refresh balance after link
            }
        } catch (e) {
            const msg = e.response?.data?.detail || e.message || String(e);
            notify('link-notify', msg, true); 
        }
    }

    async function handleClaim() {
        if (!userAddress) return;
        try {
            notify('claim-notify', "Preparing withdrawal...");
            const res = await axios.get(`${API_BASE}/api/withdrawal/${CLAIM_ID}`);
            if (!res.data.success) throw new Error(res.data.message);
            const { amount, nonce, signature } = res.data;

            const server = new window.StellarSdk.Horizon.Server(HORIZON_URL);
            const sorobanServer = new window.StellarSdk.rpc.Server(SOROBAN_URL, { allowHttp: true });
            const account = await server.loadAccount(userAddress);
            
            const sigBytes = Uint8Array.from(atob(signature), c => c.charCodeAt(0));
            const amountStroops = BigInt(Math.round(amount * 10000000));

            const tx = new window.StellarSdk.TransactionBuilder(account, { fee: "100000", networkPassphrase: NETWORK_PASSPHRASE })
                .addOperation(window.StellarSdk.Operation.invokeContractFunction({
                    contractId: SOROBAN_CONTRACT_ID,
                    function: "claim_withdrawal",
                    args: [
                        window.StellarSdk.nativeToScVal(userAddress, { type: 'address' }),
                        window.StellarSdk.nativeToScVal(amountStroops, { type: 'i128' }),
                        window.StellarSdk.nativeToScVal(BigInt(nonce), { type: 'u64' }),
                        window.StellarSdk.xdr.ScVal.scvBytes(sigBytes)
                    ]
                })).setTimeout(300).build();

            notify('claim-notify', "Simulating Transaction...");
            const sim = await sorobanServer.simulateTransaction(tx);
            const preparedTx = await sorobanServer.prepareTransaction(tx, sim);

            notify('claim-notify', "Awaiting wallet signature...");
            const { signedTxXdr } = await window.StellarKit.StellarWalletsKit.signTransaction(preparedTx.toXDR(), {
                networkPassphrase: NETWORK_PASSPHRASE,
                address: userAddress,
            });

            notify('claim-notify', "Submitting to network...");
            const resp = await sorobanServer.sendTransaction(window.StellarSdk.TransactionBuilder.fromXDR(signedTxXdr, NETWORK_PASSPHRASE));
            
            const txHash = resp.hash;
            const networkPrefix = NETWORK === 'mainnet' || NETWORK === 'public' ? 'public' : 'testnet';
            const explorerUrl = `https://stellar.expert/explorer/${networkPrefix}/tx/${txHash}`;
            
            const notifyEl = document.getElementById('claim-notify');
            notifyEl.classList.remove('hidden', 'error');
            notifyEl.classList.add('success');
            notifyEl.innerHTML = `✅ Claim Successful!<br><a href="${explorerUrl}" target="_blank" style="color:var(--accent); text-decoration: underline; margin-top: 0.5rem; display: inline-block;">View on Stellar.Expert</a>`;
            
            document.getElementById('btn-claim-action').classList.add('hidden');
            fetchBalance();
        } catch (e) {
            const msg = e.response?.data?.detail || e.message || String(e);
            notify('claim-notify', msg, true); 
        }
    }

    async function handleCancel() {
        if (!confirm("Are you sure you want to cancel this withdrawal and refund the SHx to your Discord balance?")) return;
        try {
            notify('claim-notify', "Cancelling withdrawal...");
            const res = await axios.post(`${API_BASE}/api/withdrawal/${CLAIM_ID}/cancel`, { token: TOKEN });
            if (res.data.success) {
                notify('claim-notify', "✅ Withdrawal cancelled. Funds refunded to Discord.");
                document.getElementById('btn-claim-action').classList.add('hidden');
                document.getElementById('btn-claim-cancel').classList.add('hidden');
                
                // Refresh balance after refund
                setTimeout(fetchBalance, 1000);
            }
        } catch (e) {
            const msg = e.response?.data?.detail || e.message || String(e);
            notify('claim-notify', msg, true);
        }
    }

    async function handleWebWithdraw() {
        if (!userAddress) return;
        const amountEl = document.getElementById('withdraw-amount-input');
        const amount = amountEl.value;
        if (!amount || amount <= 0) {
            notify('withdraw-notify', "Please enter a valid amount.", true);
            return;
        }

        try {
            document.getElementById('btn-web-withdraw').disabled = true;
            notify('withdraw-notify', "Initializing withdrawal. Please wait...");
            
            const res = await axios.post(`${API_BASE}/api/web-withdraw`, { token: TOKEN, amount: amount });
            if (!res.data.success) throw new Error("Failed to initialize withdrawal");
            
            CLAIM_ID = res.data.id;
            
            document.getElementById('withdraw-card').classList.add('hidden');
            document.getElementById('claim-card').classList.remove('hidden');
            
            notify('claim-notify', "Withdrawal ticket ready. Awaiting your wallet signature to claim...");
            handleClaim();
        } catch (e) {
            document.getElementById('btn-web-withdraw').disabled = false;
            const msg = e.response?.data?.detail || e.message || String(e);
            notify('withdraw-notify', msg, true); 
        }
    }

    window.onload = () => {
        fetchBalance(); // Always fetch latest balance

        const existing = "{{EXISTING_KEY_VAL}}";
        if (existing && existing.length > 10 && existing !== "{{EXISTING_KEY_VAL}}") {
            setStatus("Linked ✅");
            document.getElementById('btn-unlink').classList.remove('hidden');
        }

        if (CLAIM_ID && CLAIM_ID.length > 5 && CLAIM_ID !== "{{CLAIM_ID}}") {
            document.getElementById('claim-card').classList.remove('hidden');
        } else if (existing && existing.length > 10 && existing !== "{{EXISTING_KEY_VAL}}") {
            // Unhide withdraw card only if no pending claim
            document.getElementById('withdraw-card').classList.remove('hidden');
        }
    };
    
    document.getElementById('btn-link').onclick = handleLink;
    document.getElementById('btn-claim-action').onclick = handleClaim;
    document.getElementById('btn-claim-cancel').onclick = handleCancel;
    const webWithdrawBtn = document.getElementById('btn-web-withdraw');
    if (webWithdrawBtn) webWithdrawBtn.onclick = handleWebWithdraw;
    
    document.getElementById('btn-unlink').onclick = async () => {
        if (!confirm("Unlink wallet?")) return;
        await axios.post(`${API_BASE}/api/unlink`, { token: TOKEN });
        location.reload();
    };
  </script>
</body>
</html>'''
