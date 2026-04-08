def get_dashboard_html():
    return r'''<!DOCTYPE html>
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
      background-image: url('https://cdn.prod.website-files.com/5e9a1cde22bbc0a89dba7f5b/60c9649cf8fb48e5c883950e_Stronghold%20Logo%20Mark%20Blue.png');
      background-repeat: no-repeat;
      background-position: center;
      background-size: 70%;
      opacity: 0.32;
      z-index: -1;
      filter: blur(1px) brightness(1.1);
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
      gap: 1rem;
      font-family: 'Outfit', sans-serif;
      font-weight: 700;
      font-size: 1.6rem;
      color: #3b82f6;
      line-height: 1;
    }

    .logo img { 
      width: 44px; 
      height: 44px; 
      object-fit: contain;
      filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.4));
    }

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
    .user-subtitle { font-size: 0.85rem; color: var(--muted); margin-top: 0.25rem; }
    .status-badge-inline { display: inline-flex; align-items: center; gap: 0.5rem; font-weight: 600; }

    .status {
      padding: 1rem; border-radius: 0.75rem; margin-bottom: 1.5rem; font-size: 0.95rem; font-weight: 500;
    }
    .status.success { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .status.error { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    
    /* Unified Profile & Stats */
    .profile-section { 
      display: flex; justify-content: space-between; align-items: flex-end;
      padding-bottom: 2rem; border-bottom: 1px solid var(--border); margin-bottom: 2rem;
    }
    .profile-info { display: flex; align-items: center; gap: 1rem; }
    .profile-avatar { width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg, var(--accent), #2563eb); display: flex; align-items: center; justify-content: center; font-family: 'Outfit'; font-weight: 700; font-size: 1.5rem; border: 2px solid var(--border); }
    
    .stats-row { display: flex; align-items: center; gap: 2.5rem; }
    .stat-item { position: relative; }
    .stat-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 0.4rem; }
    .stat-value { font-family: 'Outfit'; font-size: 1.5rem; font-weight: 700; color: #fff; }
    .stat-value.accent { color: var(--accent); }
    
    .stat-divider { width: 1px; height: 32px; background: var(--border); }
    
    /* Elegant Info/Tooltip */
    .info-trigger {
      width: 14px; height: 14px; border-radius: 50%; background: rgba(255,255,255,0.1);
      display: inline-flex; align-items: center; justify-content: center;
      font-size: 9px; color: var(--text-muted); cursor: help; border: 1px solid var(--border);
    }
    .info-trigger:hover { background: var(--accent); color: white; border-color: var(--accent); }

    .tooltip {
      position: absolute; bottom: calc(100% + 15px); left: 50%; transform: translateX(-50%) translateY(10px);
      width: 320px; background: #0f172a; color: #fff; padding: 1.5rem; border-radius: 1.25rem;
      font-size: 0.85rem; line-height: 1.6; border: 1px solid var(--accent);
      box-shadow: 0 20px 50px rgba(0,0,0,0.9); opacity: 0; pointer-events: none; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      z-index: 1000; font-weight: 400; text-align: left;
    }
    .tooltip b { color: var(--accent); font-weight: 600; }
    .tooltip ol { margin-top: 0.75rem; padding-left: 1.2rem; }
    .tooltip li { margin-bottom: 0.6rem; }
    .tooltip::after {
      content: ""; position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
      border-width: 8px; border-style: solid; border-color: var(--accent) transparent transparent transparent;
    }
    .info-trigger:hover + .tooltip, .tooltip:hover { opacity: 1; pointer-events: auto; transform: translateX(-50%) translateY(0); }
    
    .guide-box {
      margin-top: 1.5rem; padding: 1.25rem; border-radius: 1rem;
      background: rgba(59, 130, 246, 0.03); border: 1px dashed var(--border);
    }
    .guide-box h4 { font-family: 'Outfit'; font-size: 0.95rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 1rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      transition: all 0.3s ease;
    }
    .badge-error {
      background: rgba(239, 68, 68, 0.1);
      color: #ef4444;
      border: 1px solid rgba(239, 68, 68, 0.2);
    }
    .badge-success {
      background: rgba(16, 185, 129, 0.1);
      color: #10b981;
      border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .hidden { display: none !important; }

    #swk-button-wrapper {
      display: inline-block;
      min-width: 160px;
      text-align: right;
    }
    
    /* Ensure the Stellar Wallets Kit button is styled correctly in the nav */
    #swk-button-wrapper button {
      background: var(--accent) !important;
      border-radius: 0.75rem !important;
      padding: 0.6rem 1.2rem !important;
      font-weight: 600 !important;
      font-size: 0.85rem !important;
      border: none !important;
      color: white !important;
      transition: all 0.2s ease !important;
    }
    #swk-button-wrapper button:hover {
      background: #2563eb !important;
      transform: translateY(-1px);
    }
    .btn-hero {
      background: linear-gradient(135deg, var(--accent) 0%, #1d4ed8 100%);
      padding: 1rem 2rem;
      font-size: 1.1rem;
      margin-top: 1.5rem;
      box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
    }
    .btn-hero:hover {
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 15px 30px rgba(59, 130, 246, 0.5);
    }

    /* --- MOBILE RESPONSIVENESS --- */
    @media (max-width: 640px) {
      .container { padding: 1rem; }
      nav { margin-bottom: 1rem; flex-direction: column; gap: 1rem; align-items: flex-start; }
      #swk-button-wrapper { width: 100%; text-align: left; }
      .hero { padding: 2rem 0; }
      .hero h1 { font-size: 2rem; line-height: 1.2; }
      .card { padding: 1.25rem; border-radius: 1rem; }
      .profile-section { flex-direction: column; align-items: flex-start; gap: 1.5rem; }
      .stats-row { flex-direction: column; gap: 1rem; width: 100%; }
      .stat-divider { display: none; }
      .stat-item { width: 100%; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }
      .stat-item:last-child { border-bottom: none; }
      .btn { min-height: 48px; width: 100%; justify-content: center; }
      .tooltip { width: calc(100vw - 2rem); left: 50%; }
    }
  </style>
</head>
<body>
  <div class="background-castle"></div>

  <div class="container">
    <nav>
      <div class="logo">
        <img src="https://cdn.prod.website-files.com/5e9a1cde22bbc0a89dba7f5b/60c9649cf8fb48e5c883950e_Stronghold%20Logo%20Mark%20Blue.png" alt="SHx">
        <span style="letter-spacing: -0.02em;">SHx Community</span>
      </div>
      <div>
        <div id="swk-button-wrapper"></div>
      </div>
    </nav>

    <div class="hero">
      <h1>Community Portal <span class="text-xs" style="vertical-align: middle; opacity: 0.5;">v1.8</span></h1>
      <p>Securely link your Discord and manage claims.</p>
      
        <div id="connection-status-area" class="mt-4">
          <div id="connection-status-badge" class="badge badge-error">Wallet: Not Connected</div>
        </div>
    </div>

    <div class="card">
      <!-- Unified Portfolio Section -->
      <div class="profile-section">
        <div class="profile-info">
          <div class="profile-avatar">{{USER_INITIAL}}</div>
          <div>
            <h2 style="font-size: 1.25rem;">{{DISCORD_USER}}</h2>
            <div id="link-status-badge" class="badge badge-success text-xs mt-1">Status: Linked ✅</div>
          </div>
        </div>
        
        <div class="stats-row">
          <!-- Discord Stat -->
          <div class="stat-item">
            <div class="stat-label">
              Discord Balance
              <div class="info-trigger">?</div>
              <div class="tooltip">
                <b>Internal Tipping Account</b>
                <p class="text-xs text-muted mb-2">Move SHx from your wallet here for instant, gas-free tipping:</p>
                <ol>
                  <li>Type <b>/deposit</b> in Discord to get the address.</li>
                  <li>Send SHx with Memo ID: <b>{{MEMO}}</b></li>
                </ol>
              </div>
            </div>
            <div class="stat-value accent">
              <span id="internal-balance-val">{{INTERNAL_BALANCE}}</span> <span class="text-xs">SHx</span>
            </div>
          </div>
          
          <div class="stat-divider"></div>
          
          <!-- Stellar Stat -->
          <div class="stat-item">
            <div class="stat-label">Wallet Balance</div>
            <div class="stat-value">
              <span id="external-balance-val">0.00</span> <span class="text-xs">SHx</span>
            </div>
          </div>
        </div>
      </div>
      
      <p id="reset-session-link" class="mb-4 text-xs text-accent" style="cursor:pointer; text-decoration: underline;" onclick="resetSession()">Trouble connecting? Reset Session</p>
      <div id="link-notify" class="status hidden"></div>
      <button id="btn-link" class="btn btn-primary w-full justify-center" disabled>Verify & Link Wallet</button>
      
      <!-- Unlink Action (Visible only when linked) -->
      <div id="unlink-container" class="mt-4 text-center hidden">
          <button id="btn-unlink-action" class="btn btn-secondary w-full justify-center">Unlink Current Wallet</button>
      </div>
      
      <!-- Trustline Warning -->
      <div id="trustline-warning" class="status error hidden text-sm mt-4">
        ⚠️ <b>Missing SHx Trustline</b><br>
        Your wallet is not set up to receive SHx. Please click "Verify & Link Wallet" above to fix this.
      </div>

      <!-- Blockchain Proof Section -->
      <div class="mt-6 pt-4 border-t border-opacity-10" style="border-top: 1px solid var(--border);">
        <h4 class="text-xs text-muted mb-2 uppercase tracking-widest">Network Verification Proof</h4>
        <div class="grid grid-cols-2 gap-2" style="display:grid; grid-template-columns: 1fr 1fr; gap:0.5rem;">
          <div class="bg-dark-overlay p-2 rounded text-xs">
            <span class="text-muted">Network:</span> <span class="text-white text-bold">{{NETWORK}}</span>
          </div>
          <div class="bg-dark-overlay p-2 rounded text-xs">
            <span class="text-muted">Status:</span> <span id="rpc_status" class="text-success text-bold">Connected</span>
          </div>
          <div class="bg-dark-overlay p-2 rounded text-xs col-span-2" style="grid-column: span 2;">
            <span class="text-muted">Contract:</span> <span id="contract_label" class="text-accent text-bold">{{SOROBAN_CONTRACT_ID}}</span>
          </div>
        </div>
        
        <div id="footer-branding" class="mt-6 pt-4 text-center border-t border-white border-opacity-5">
           <p class="text-[11px] text-muted">
             <span class="status-badge-inline" style="opacity: 0.8;">
               <span style="width: 6px; height: 6px; border-radius: 50%; background: #10b981; display: inline-block;"></span>
               Authenticated via <a href="https://stellarwallets.dev" target="_blank" class="text-accent hover:underline">Stellar Wallets Kit</a>
             </span>
           </p>
        </div>
    </div>

    <!-- Claim Card -->
    <div id="claim-card" class="card">
      <h2>Pending Withdrawals</h2>
      <p class="text-sm text-muted mb-4">You have pending SHx withdrawal tickets created from Discord. Select one to claim to your linked wallet.</p>
      
      <div id="withdrawal-list" class="mb-4">
        <!-- Dynamic list of withdrawals goes here -->
        <div class="text-center py-4 text-muted">Scanning for active tickets...</div>
      </div>
      
      <div id="claim-notify" class="status hidden"></div>
      
      <div id="active-claim-view" class="hidden bg-dark-overlay mt-4">
        <h3 class="mb-2">Claiming Ticket: <span id="active-ticket-id" class="text-accent"></span></h3>
        <p class="mb-4">Amount: <span id="active-ticket-amount" class="text-bold text-accent"></span> SHx</p>
        <button id="btn-claim-action" class="btn btn-primary bg-success w-full justify-center" disabled>Confirm & Claim on Stellar</button>
        <button id="btn-claim-cancel" class="btn btn-secondary w-full justify-center mt-4">Cancel & Refund to Discord</button>
        <p class="text-xs text-center mt-4 text-muted" onclick="showList()" style="cursor:pointer; text-decoration: underline;">← Back to List</p>
      </div>
    </div>


  </div>

  <!-- Stellar SDK + Axios from CDN, SWK UMD from local bundle -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/stellar-sdk/13.3.0/stellar-sdk.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
  <script src="/wallet-kit-bundle.umd.js"></script>

  <script>
    // ══════════════════════════════════════════════════════════════
    // SHx Community Portal — SWK v2 Static API Integration
    // Uses: StellarKit.StellarWalletsKit.init() / .authModal() / etc.
    // ══════════════════════════════════════════════════════════════

    // ── GLOBAL MODAL HELPER ──
    window.openKitModal = async () => {
        console.log("DASHBOARD | openKitModal() called. Kit ready:", kitInitialized);
        if (!kitInitialized) {
            console.warn("DASHBOARD | Kit not initialized yet. Attempting init...");
            if (typeof initKit === 'function') await initKit();
        }
        try {
            console.log("DASHBOARD | Opening auth modal...");
            const { address } = await window.StellarKit.StellarWalletsKit.authModal();
            console.log("DASHBOARD | Auth modal returned address:", address);
            if (address) {
                userAddress = address;
                window.userAddress = address;
                updateUI(address);
            }
        } catch (e) {
            if (e && e.code === -1 && e.message && e.message.includes('closed')) {
                console.log("DASHBOARD | User closed the modal.");
            } else {
                console.error("DASHBOARD | authModal error:", e);
                alert("Wallet connection error: " + (e.message || e));
            }
        }
    };

    // ── INJECTED CONSTANTS (de-duplicated) ──
    const urlParams = new URLSearchParams(window.location.search);
    const TOKEN = urlParams.get('token') || "{{TOKEN}}";
    let CLAIM_ID = urlParams.get('claim_id') || "{{CLAIM_ID}}";
    let PENDING_IDS = {{PENDING_IDS}};
    const NETWORK = "{{NETWORK}}";
    const NETWORK_PASSPHRASE = "{{NETWORK_PASSPHRASE}}";
    const WC_PROJECT_ID = "{{WC_PROJECT_ID}}";
    const APP_VERSION = "{{APP_VERSION}}";
    const SHX_ASSET_CODE = "{{SHX_ASSET_CODE}}";
    const SHX_ISSUER_VAL = "{{SHX_ISSUER}}";
    const HORIZON_URL = "{{HORIZON_URL}}";
    const SOROBAN_URL = "{{SOROBAN_URL}}";
    const API_BASE = window.location.origin;

    console.log("DASHBOARD | Network:", NETWORK, "| Asset:", SHX_ASSET_CODE, "@", SHX_ISSUER_VAL);

    // ── BALANCE REFRESH ──
    async function fetchStellarBalance(address) {
        if (!address) return;
        try {
            console.log("Refreshing Stellar Balance for:", address);
            const server = new window.StellarSdk.Horizon.Server(HORIZON_URL);
            const acc = await server.loadAccount(address);
            const shxBal = acc.balances.find(b => b.asset_code === SHX_ASSET_CODE && b.asset_issuer === SHX_ISSUER_VAL);
            const val = shxBal ? parseFloat(shxBal.balance).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "0.00";
            const el = document.getElementById('external-balance-val');
            if (el) el.innerText = val;
        } catch (e) {
            console.warn("Could not fetch Stellar balance:", e);
            const el = document.getElementById('external-balance-val');
            if (el) el.innerText = "Check Trustline";
        }
    }

    const setStatus = (msg, isError = false) => {
        const el = document.getElementById('link-status-text');
        if (!el) return;
        
        // If it's a success message, we might want to split or style it
        if (msg === "Connected ✅" || msg === "Linked ✅") {
            el.innerText = msg;
            el.className = "text-success text-bold";
        } else {
            el.innerText = (isError ? "❌ " : "") + msg;
            el.className = isError ? "text-error" : "text-muted";
        }
    };

    const fetchBalance = async () => {
        try {
            const res = await axios.get(`${API_BASE}/api/balance?token=${TOKEN}&claim_id=${CLAIM_ID}`);
            if (res.data.success) {
                currentBalance = res.data.balance;
                const balanceEl = document.getElementById('internal-balance-val');
                if (balanceEl) balanceEl.innerText = currentBalance;
                
                const statusEl = document.getElementById('link-status-text');
                if (statusEl && (statusEl.innerText === "Syncing..." || statusEl.innerText.includes("Connected") || statusEl.innerText.includes("Linked"))) {
                    setStatus("Connected ✅");
                }
                
                if (res.data.pending_withdrawals && res.data.pending_withdrawals.length > 0) {
                    PENDING_IDS = res.data.pending_withdrawals.map(w => w.id);
                    renderWithdrawals(res.data.pending_withdrawals);
                } else {
                    document.getElementById('withdrawal-list').innerHTML = '<div class="text-center py-4 text-muted">No pending withdrawal tickets found.</div>';
                }

                // If wallet already connected, refresh on-chain balance too
                if (userAddress) {
                    fetchStellarBalance(userAddress);
                }
            }
        } catch (e) {
            console.error("Failed to fetch data:", e);
        }
    };

    const renderWithdrawals = (withdrawals) => {
        const listEl = document.getElementById('withdrawal-list');
        const claimCard = document.getElementById('claim-card');
        if (!listEl || !claimCard) return;
        
        if (!withdrawals || withdrawals.length === 0) {
            listEl.innerHTML = '<div class="text-center py-4 text-muted">No pending tickets.</div>';
            return;
        }

        let html = '';
        withdrawals.forEach(w => {
            const date = new Date(w.created_at * 1000).toLocaleDateString();
            html += `
            <div class="bg-dark-overlay mb-2 p-3 rounded-lg border border-opacity-10" style="display:flex; justify-content:space-between; align-items:center;">
              <div style="flex:1;">
                <p class="text-bold text-accent">${w.amount} SHx</p>
                <p class="text-xs text-muted">Ticket: ...${w.id.slice(-6)} • ${date}</p>
                <span onclick="handleCancel('${w.id}')" class="text-error text-xs" style="cursor:pointer; text-decoration: underline; margin-top: 5px; display: inline-block;">Cancel & Refund</span>
              </div>
              <button onclick="selectTicket('${w.id}', '${w.amount}')" class="btn btn-primary text-xs px-4 py-2">Select to Claim</button>
            </div>`;
        });
        listEl.innerHTML = html;
    };

    const selectTicket = (id, amount) => {
        CLAIM_ID = id;
        document.getElementById('withdrawal-list').classList.add('hidden');
        document.getElementById('active-claim-view').classList.remove('hidden');
        document.getElementById('active-ticket-id').innerText = `...${id.slice(-8)}`;
        document.getElementById('active-ticket-amount').innerText = amount;
        
        // Ensure buttons are visible if they were hidden by a previous action
        document.getElementById('btn-claim-action').classList.remove('hidden');
        document.getElementById('btn-claim-cancel').classList.remove('hidden');
        
        notify('claim-notify', "Ticket selected. Ready to claim on-chain.");
    };

    const showList = () => {
        document.getElementById('withdrawal-list').classList.remove('hidden');
        document.getElementById('active-claim-view').classList.add('hidden');
        document.getElementById('claim-notify').classList.add('hidden');
        fetchBalance();
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

    const DISCORD_ID = "{{DISCORD_ID}}";
    const SHX_SAC_CONTRACT_ID = "{{SHX_SAC_CONTRACT_ID}}";
    const SOROBAN_CONTRACT_ID = "{{SOROBAN_CONTRACT_ID}}";

    let userAddress = null;
    let kitInitialized = false;

    /**
     * Defensive helper to prevent 'Unsupported address type: undefined' errors.
     */
    const parseAddress = (val, name) => {
        if (!val || typeof val !== 'string' || val.includes('{{')) {
            const msg = `FATAL: Invalid or unrendered Address [${name}]: ${val || 'undefined'}`;
            console.error(msg);
            throw new Error(msg);
        }
        if (val.length < 56) {
             console.warn(`Warning: Address [${name}] seems short (${val.length} chars): ${val}`);
        }
        return val;
    };

    const updateUI = (address) => {
      console.log("updateUI called with address:", address);
      userAddress = address;
      window.userAddress = address;

      const heroBadge = document.getElementById('connection-status-badge');
      const profileBadge = document.getElementById('link-status-badge');
      const linkBtn = document.getElementById('btn-link');
      
      if (address) {
        const addrText = `<span style="width: 8px; height: 8px; background: #10b981; border-radius: 50%; display: inline-block; margin-right: 4px;"></span> Verified: ${address.slice(0,6)}...${address.slice(-4)}`;
        
        if (heroBadge) {
            heroBadge.innerHTML = addrText;
            heroBadge.classList.replace('badge-error', 'badge-success');
        }
        if (profileBadge) {
            profileBadge.innerHTML = addrText;
            profileBadge.classList.replace('badge-error', 'badge-success');
        }

        setStatus("Ready ✅");
        fetchStellarBalance(address);
        
        if (linkBtn) {
            linkBtn.disabled = false;
            linkBtn.innerText = "Verify & Link Wallet";
        }
        
        const claimBtn = document.getElementById('btn-claim-action');
        if (claimBtn) claimBtn.disabled = false;
        
        const existing = "{{EXISTING_KEY_VAL}}";
        if (existing && existing.startsWith('G') && existing.length === 56) {
            document.getElementById('unlink-container')?.classList.remove('hidden');
            if (linkBtn) linkBtn.innerText = "Switch / Change Linked Wallet";
        }
      } else {
        if (heroBadge) {
            heroBadge.innerText = "Wallet: Not Connected";
            heroBadge.classList.replace('badge-success', 'badge-error');
        }
        if (profileBadge) {
            profileBadge.innerText = "Status: Wallet Disconnected";
            profileBadge.classList.replace('badge-success', 'badge-error');
        }
        const linkBtn = document.getElementById('btn-link');
        if (linkBtn) linkBtn.disabled = true;
        const claimBtn = document.getElementById('btn-claim-action');
        if (claimBtn) claimBtn.disabled = true;
      }
    };

    const notify = (id, msg, isError = false) => {
        const div = document.getElementById(id);
        div.classList.remove('hidden', 'success', 'error');
        div.classList.add(isError ? 'error' : 'success');
        div.innerText = msg;
    };

    let kitInitInProgress = false;
    async function initKit() {
        if (kitInitialized || kitInitInProgress) return;
        kitInitInProgress = true;
        
        try {
            if (!window.StellarKit || !window.StellarKit.StellarWalletsKit) {
                console.warn("DASHBOARD | StellarKit global not found. Retrying in 500ms...");
                setTimeout(() => {
                    kitInitInProgress = false;
                    initKit();
                }, 500);
                return;
            }
            
            const { StellarWalletsKit, KitEventType, SwkAppDarkTheme, defaultModules, WalletConnectModule } = window.StellarKit;
            
            // Build module list
            const modules = [...defaultModules()];
            
            // Add WalletConnect if project ID is available
            if (WalletConnectModule && WC_PROJECT_ID && !WC_PROJECT_ID.includes('{{')) {
                try {
                    modules.push(new WalletConnectModule({
                        projectId: WC_PROJECT_ID,
                        metadata: {
                            name: "SHx Tip Bot",
                            description: "SHx Community Portal",
                            url: window.location.origin,
                            icons: ["https://shxtipbotv1.vercel.app/stronghold_logo_watermark.svg"]
                        }
                    }));
                    console.log("DASHBOARD | WalletConnect module added.");
                } catch (wcErr) {
                    console.warn("DASHBOARD | WalletConnect module failed to load (non-fatal):", wcErr);
                }
            }

            // ── SWK v2: Static init ──
            StellarWalletsKit.init({
                theme: SwkAppDarkTheme,
                modules: modules,
                network: NETWORK_PASSPHRASE
            });
            
            console.log("DASHBOARD | SWK v2 initialized for network:", NETWORK);

            // ── Create the built-in connect button ──
            const buttonWrapper = document.getElementById('swk-button-wrapper');
            if (buttonWrapper) {
                StellarWalletsKit.createButton(buttonWrapper);
                console.log("DASHBOARD | SWK button created.");
            }

            // ── Listen to STATE_UPDATED events ──
            StellarWalletsKit.on(KitEventType.STATE_UPDATED, (event) => {
                console.log("DASHBOARD | STATE_UPDATED:", event);
                const addr = event && event.payload ? event.payload.address : null;
                if (addr) {
                    userAddress = addr;
                    window.userAddress = addr;
                    updateUI(addr);
                }
            });

            // ── Listen to DISCONNECT events ──
            StellarWalletsKit.on(KitEventType.DISCONNECT, () => {
                console.log("DASHBOARD | DISCONNECT event.");
                userAddress = null;
                window.userAddress = null;
                updateUI(null);
            });
            
            // ── Try to restore previously connected wallet ──
            try {
               const { address: currentAddr } = await StellarWalletsKit.getAddress();
               if (currentAddr) {
                   userAddress = currentAddr;
                   window.userAddress = currentAddr;
                   updateUI(currentAddr);
                   console.log("DASHBOARD | Restored address:", currentAddr);
               }
            } catch(e) {
                // No wallet previously connected — this is normal
                console.log("DASHBOARD | No previously connected wallet.");
            }
            
            kitInitialized = true;
            kitInitInProgress = false;
            console.log("DASHBOARD | Kit Ready ✓");
        } catch (err) {
            console.error("DASHBOARD | SWK INIT FAILED:", err);
            kitInitInProgress = false;
            setStatus("Connection Error", true);
        }
    };

    // ── APP LOGIC ──
    async function handleLink() {
        console.log("handleLink() triggered. Current userAddress:", userAddress);
        
        // Fallback: try to pull address from kit if global is missing
        if (!userAddress && window.StellarKit && window.StellarKit.StellarWalletsKit) {
            try {
                const { address } = await window.StellarKit.StellarWalletsKit.getAddress();
                if (address) userAddress = address;
                console.log("Synced address from kit:", userAddress);
            } catch (e) {
                console.warn("Could not sync state from kit:", e);
            }
        }

        if (!userAddress || userAddress.length < 56) {
            alert("Wallet not recognized. Please click the 'Connect Wallet' button (top right) and select your wallet first.");
            return;
        }
        
        try {
            notify('link-notify', "Signing Link Request...");
            const server = new window.StellarSdk.Horizon.Server(HORIZON_URL);
            const account = await server.loadAccount(userAddress);
            const tx = new window.StellarSdk.TransactionBuilder(account, { fee: "1000", networkPassphrase: NETWORK_PASSPHRASE })
                .addOperation(window.StellarSdk.Operation.manageData({ name: "link_discord", value: DISCORD_ID }))
                .setTimeout(300).build();

            notify('link-notify', "Awaiting wallet signature...");
            console.log("Linking TX XDR:", tx.toXDR());
            console.log("Requesting signature from address:", userAddress);
            
            const result = await window.StellarKit.StellarWalletsKit.signTransaction(tx.toXDR(), {
                networkPassphrase: NETWORK_PASSPHRASE,
                address: userAddress,
            });
            
            const signedTxXdr = result.signedTxXdr;
            console.log("Received signed TX XDR:", signedTxXdr);

            notify('link-notify', "Verifying on server...");
            const res = await axios.post(`${API_BASE}/api/link`, {
                token: TOKEN, public_key: userAddress, signature_xdr: signedTxXdr, is_approved: true
            });
            if (res.data.success) {
                notify('link-notify', "✅ Wallet linked successfully!");
                setStatus("Linked ✅");
                document.getElementById('unlink-container')?.classList.remove('hidden');
                
                // Show/hide trustline warning
                const trustWarning = document.getElementById('trustline-warning');
                if (res.data.has_shx_trustline) {
                    trustWarning?.classList.add('hidden');
                } else {
                    trustWarning?.classList.remove('hidden');
                }

                // Show withdraw card immediately after link
                document.getElementById('withdraw-card')?.classList.remove('hidden');
                
                fetchBalance(); // Refresh balance after link
            }
        } catch (e) {
            const msg = e.response?.data?.detail || e.message || String(e);
            if (msg.includes('User rejected') || msg.includes('Request rejected')) {
                notify('link-notify', "Linking cancelled in wallet.", true);
            } else {
                notify('link-notify', msg, true); 
            }
        }
    }

    async function handleClaim() {
        console.log("handleClaim() triggered for userAddress:", userAddress, "CLAIM_ID:", CLAIM_ID);
        if (!userAddress || typeof userAddress !== 'string' || userAddress.length < 56) {
            alert(`No wallet connected or invalid address: ${userAddress}`);
            return;
        }
        try {
            console.log("--- Starting Claim Flow ---");
            console.log("userAddress:", userAddress);
            console.log("CLAIM_ID:", CLAIM_ID);
            
            notify('claim-notify', "Fetching withdrawal details...");
            const res = await axios.get(`${API_BASE}/api/withdrawal/${CLAIM_ID}`);
            if (!res.data.success) throw new Error(res.data.message || "Failed to fetch withdrawal details.");
            
            const { amount, nonce, signature } = res.data;
            console.log("Ticket data:", { amount, nonce, signature });

            const server = new window.StellarSdk.Horizon.Server(HORIZON_URL);
            // Detect correct Soroban server class
            const SorobanServerClass = window.StellarSdk.rpc?.Server || window.StellarSdk.SorobanServer;
            const sorobanServer = new SorobanServerClass(SOROBAN_URL, { allowHttp: true });
            
            notify('claim-notify', "Loading account information...");
            const account = await server.loadAccount(userAddress);
            console.log("Account loaded successfully. Seq:", account.sequenceNumber());
            
            const sigBytes = Uint8Array.from(atob(signature), c => c.charCodeAt(0));
            const amountStroops = BigInt(Math.round(amount * 10000000));
            
            notify('claim-notify', "Building proof of claim...");
            
            // Safer ScVal construction
            let userAddressVal;
            try {
                userAddressVal = window.StellarSdk.nativeToScVal(userAddress, { type: 'address' });
            } catch (addrErr) {
                console.warn("Standard 'address' type failed, falling back to manual ScVal construction:", addrErr);
                // Fallback for older SDKs or specific environments
                userAddressVal = window.StellarSdk.xdr.ScVal.scvAddress(
                    window.StellarSdk.Address.fromString(userAddress).toScAddress()
                );
            }

            const args = [
                userAddressVal,
                window.StellarSdk.nativeToScVal(amountStroops, { type: 'i128' }),
                window.StellarSdk.nativeToScVal(BigInt(nonce), { type: 'u64' }),
                window.StellarSdk.nativeToScVal(sigBytes, { type: 'bytes' })
            ];
            
            console.log("Prepared Soroban Args (Raw):", args);
            args.forEach((arg, i) => console.log(`Arg ${i} XDR:`, arg.toXDR('base64')));
            
            console.log("Preparing Transaction for network:", NETWORK, "Passphrase:", NETWORK_PASSPHRASE);
            
            let tx;
            try {
                const contractIdStr = String(parseAddress(SOROBAN_CONTRACT_ID, 'Contract'));
                console.log("Using Contract ID:", contractIdStr);
                
                notify('claim-notify', "Building Soroban operation...");
                
                // Use the Contract class to build the operation safely
                const contract = new window.StellarSdk.Contract(contractIdStr);
                const op = contract.call("claim_withdrawal", ...args);

                tx = new window.StellarSdk.TransactionBuilder(account, { 
                    fee: "100000", 
                    networkPassphrase: NETWORK_PASSPHRASE 
                })
                .addOperation(op)
                .setTimeout(300)
                .build();
                
                console.log("Transaction built successfully.");
            } catch (txError) {

                console.error("FAILED TO BUILD TRANSACTION:", txError);
                throw new Error(`Transaction build error: ${txError.message || txError}`);
            }

            notify('claim-notify', "Simulating on network...");
            let sim;
            try {
                sim = await sorobanServer.simulateTransaction(tx);
                console.log("Simulation result:", sim);
            } catch (simError) {
                console.error("SIMULATION FAIL (Network/RPC):", simError);
                throw new Error(`Simulation failed (RPC): ${simError.message || simError}`);
            }
            
            if (sim.error) {
                console.error("Simulation failed (Contract level). Full Response:", sim);
                // Extract more descriptive error if possible from events or diagnostic data
                let errorDetails = sim.error;
                if (sim.diagnosticEvents) {
                    console.warn("Diagnostic Events:", sim.diagnosticEvents);
                }
                throw new Error(`Contract rejected: ${errorDetails}. This often happens if the signature is invalid or you already claimed this nonce.`);
            }
            
            notify('claim-notify', "Simulation successful. Preparing footprint...");
            const preparedTx = await sorobanServer.prepareTransaction(tx, sim);
            
            notify('claim-notify', "Awaiting signature from your wallet...");
            const preparedXdr = preparedTx.toXDR();
            console.log("Prepared Soroban TX XDR:", preparedXdr);
            console.log("Signing claim with address:", userAddress);

            let signResult;
            try {
                signResult = await window.StellarKit.StellarWalletsKit.signTransaction(preparedXdr, {
                    networkPassphrase: NETWORK_PASSPHRASE,
                    address: userAddress,
                });
            } catch (signErr) {
                console.error("SIGNING FAILED:", signErr);
                if (signErr.message?.includes("xBull")) {
                    throw new Error("xBull signing failed. Please ensure your xBull wallet is unlocked and the correct account is selected.");
                }
                throw signErr;
            }
            
            const { signedTxXdr } = signResult;
            console.log("Successfully received signed Soroban TX.");

            notify('claim-notify', "Submitting to network...");
            const resp = await sorobanServer.sendTransaction(window.StellarSdk.TransactionBuilder.fromXDR(signedTxXdr, NETWORK_PASSPHRASE));
            
            if (resp.status === "ERROR") {
                throw new Error(`Submission failed: ${resp.error_result_xdr}`);
            }
            
            const txHash = resp.hash;
            const networkPrefix = (NETWORK === 'mainnet' || NETWORK === 'public') ? 'public' : 'testnet';
            const explorerUrl = `https://stellar.expert/explorer/${networkPrefix}/tx/${txHash}`;

            // Polling for confirmation
            notify('claim-notify', "Confirming on network...");
            let txResult = await sorobanServer.getTransaction(txHash);
            let attempts = 0;
            while ((txResult.status === "NOT_FOUND" || txResult.status === "PENDING") && attempts < 30) {
                await new Promise(r => setTimeout(r, 2000));
                txResult = await sorobanServer.getTransaction(txHash);
                attempts++;
            }

            if (txResult.status !== "SUCCESS") {
                throw new Error(`Transaction failed with status: ${txResult.status}`);
            }

            // Sync with backend
            notify('claim-notify', "Finalizing withdrawal...");
            await axios.post(`${API_BASE}/api/withdrawal/${CLAIM_ID}/complete`, { tx_hash: txHash });
            
            const notifyEl = document.getElementById('claim-notify');
            notifyEl.classList.remove('hidden', 'error');
            notifyEl.classList.add('success');
            notifyEl.innerHTML = `✅ Claim Successful!<br><a href="${explorerUrl}" target="_blank" style="color:var(--accent); text-decoration: underline; margin-top: 0.5rem; display: inline-block;">View on Stellar.Expert</a><p style="font-size: 0.8rem; opacity: 0.7; margin-top: 1rem;">Closing in 10 seconds...</p>`;
            
            document.getElementById('btn-claim-action').classList.add('hidden');
            document.getElementById('btn-claim-cancel').classList.add('hidden');
            
            // After 10s, refresh and show the list again
            setTimeout(() => {
                showList();
                fetchBalance();
            }, 10000);
        } catch (e) {
            console.error("CLAIM FLOW FAILED:", e);
            const msg = e.response?.data?.detail || e.message || String(e);
            if (msg.includes('User rejected') || msg.includes('Request rejected')) {
                notify('claim-notify', "Claim rejected by user.", true);
            } else {
                notify('claim-notify', msg, true); 
            }
        }
    }


    async function handleCancel(id) {
        if (id && typeof id === 'string') CLAIM_ID = id;
        if (!confirm("Are you sure you want to cancel this withdrawal and refund the SHx to your Discord balance?")) return;
        try {
            notify('claim-notify', "Cancelling withdrawal...");
            if (id) {
                // If called from the list, we might need to show the notification
                document.getElementById('claim-card').classList.remove('hidden');
                notify('claim-notify', "Cancelling withdrawal...");
            }
            const res = await axios.post(`${API_BASE}/api/withdrawal/${CLAIM_ID}/cancel`, { token: TOKEN });
            if (res.data.success) {
                notify('claim-notify', "✅ Withdrawal cancelled. Funds refunded to Discord.");
                document.getElementById('btn-claim-action').classList.add('hidden');
                document.getElementById('btn-claim-cancel').classList.add('hidden');
                
                // Refresh list after refund
                setTimeout(showList, 1500);
            }
        } catch (e) {
            const msg = e.response?.data?.detail || e.message || String(e);
            notify('claim-notify', msg, true);
        }
    }


    window.onload = () => {
        fetchBalance(); 

        const existing = "{{EXISTING_KEY_VAL}}";
        // Check if existing is a valid G-address (starts with G, length 56)
        if (existing && existing.startsWith("G") && existing.length === 56) {
            setStatus("Linked ✅");
            document.getElementById('unlink-container')?.classList.remove('hidden');
            document.getElementById('btn-link').innerText = "Switch / Change Linked Wallet";
        }

        if (CLAIM_ID && CLAIM_ID.length > 5 && CLAIM_ID !== "{{CLAIM_ID}}") {
            // If we came from a direct link, show the ticket directly
            selectTicket(CLAIM_ID, "{{CLAIM_AMOUNT}}");
        }
        
        // Connectivity test removed per user request
    };
    
    // Initialize kit immediately on script load
    initKit();
    
    const linkBtnEl = document.getElementById('btn-link');
    if (linkBtnEl) linkBtnEl.onclick = handleLink;
    const claimActionEl = document.getElementById('btn-claim-action');
    if (claimActionEl) claimActionEl.onclick = handleClaim;
    const claimCancelEl = document.getElementById('btn-claim-cancel');
    if (claimCancelEl) claimCancelEl.onclick = handleCancel;
    
    const unlinkHandler = async () => {
        if (!confirm("Are you sure you want to unlink your wallet? This will remove the connection between your Discord and this Stellar address.")) return;
        try {
            await axios.post(`${API_BASE}/api/unlink`, { token: TOKEN });
            location.reload();
        } catch (e) {
            alert("Failed to unlink: " + (e.response?.data?.detail || e.message));
        }
    };
    
    if (document.getElementById('btn-unlink-action')) {
        document.getElementById('btn-unlink-action').onclick = unlinkHandler;
    }

    // Self-test removed per user request
  </script>
</body>
</html>'''
