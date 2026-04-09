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
      overflow-x: hidden;
      width: 100%;
    }
    
    html {
      overflow-x: hidden;
      width: 100%;
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
    .break-word { word-break: break-all; overflow-wrap: break-word; }
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
          <div class="bg-dark-overlay p-2 rounded text-xs col-span-2" style="grid-column: span 2; overflow: hidden;">
            <span class="text-muted">Contract:</span> <span id="contract_label" class="text-accent text-bold break-word" style="font-size: 0.7rem;">{{SOROBAN_CONTRACT_ID}}</span>
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
  <script src="https://cdn.jsdelivr.net/npm/stellar-sdk@12.3.0/dist/stellar-sdk.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
  <script src="/wallet-kit-bundle.umd.js"></script>

  <script>
    // ── SDK READINESS HELPER ──
    const getSdk = () => {
        if (window.StellarSdk) return window.StellarSdk;
        if (window.Stellar) return window.Stellar;
        return null;
    };

    const checkSdkReady = () => {
        const sdk = getSdk();
        if (!sdk) {
            console.warn("DASHBOARD | Stellar SDK not ready yet...");
            return false;
        }
        return true;
    };

    // ── GLOBAL MODAL HELPER ──
    window.openKitModal = async () => {
        if (!kitInitialized) {
            if (typeof initKit === 'function') await initKit();
        }
        try {
            const { address } = await window.StellarKit.StellarWalletsKit.authModal();
            if (address) {
                userAddress = address;
                window.userAddress = address;
                updateUI(address);
            }
        } catch (e) {
            if (!(e && e.code === -1 && e.message && e.message.includes('closed'))) {
                console.error("DASHBOARD | authModal error:", e);
                alert("Wallet connection error: " + (e.message || e));
            }
        }
    };

    // ── INJECTED CONSTANTS ──
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

    // ── BALANCE REFRESH ──
    async function fetchStellarBalance(address) {
        if (!address || !checkSdkReady()) return;
        try {
            const sdk = getSdk();
            // In v12, Server is under Horizon
            const ServerClass = sdk.Horizon?.Server || sdk.Server;
            const server = new ServerClass(HORIZON_URL);
            
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
        const el = document.getElementById('link-status-badge');
        if (!el) return;
        if (msg.includes("✅")) {
            el.innerText = "Status: " + msg;
            el.classList.replace('badge-error', 'badge-success');
        } else {
            el.innerText = "Status: " + msg;
            if (isError) el.classList.replace('badge-success', 'badge-error');
        }
    };

    const fetchBalance = async () => {
        try {
            const res = await axios.get(`${API_BASE}/api/balance?token=${TOKEN}&claim_id=${CLAIM_ID}`);
            if (res.data.success) {
                const balanceEl = document.getElementById('internal-balance-val');
                if (balanceEl) balanceEl.innerText = res.data.balance;
                
                if (res.data.pending_withdrawals && res.data.pending_withdrawals.length > 0) {
                    PENDING_IDS = res.data.pending_withdrawals.map(w => w.id);
                    renderWithdrawals(res.data.pending_withdrawals);
                } else {
                    document.getElementById('withdrawal-list').innerHTML = '<div class="text-center py-4 text-muted">No pending tickets found.</div>';
                }
                if (userAddress) fetchStellarBalance(userAddress);
            }
        } catch (e) { console.error("Data fetch failed:", e); }
    };

    const renderWithdrawals = (withdrawals) => {
        const listEl = document.getElementById('withdrawal-list');
        if (!listEl) return;
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
        const view = document.getElementById('active-claim-view');
        view.classList.remove('hidden');
        document.getElementById('active-ticket-id').innerText = `...${id.slice(-8)}`;
        document.getElementById('active-ticket-amount').innerText = amount;
        document.getElementById('btn-claim-action').classList.remove('hidden');
        document.getElementById('btn-claim-cancel').classList.remove('hidden');
        notify('claim-notify', "Ticket selected. Ready to claim.");
    };

    const showList = () => {
        document.getElementById('withdrawal-list').classList.remove('hidden');
        document.getElementById('active-claim-view').classList.add('hidden');
        document.getElementById('claim-notify').classList.add('hidden');
        fetchBalance();
    };

    const resetSession = () => {
        if (!confirm("Clear wallet cache and reload?")) return;
        localStorage.clear();
        location.reload();
    };

    const DISCORD_ID = "{{DISCORD_ID}}";
    const SOROBAN_CONTRACT_ID = "{{SOROBAN_CONTRACT_ID}}";
    let userAddress = null;
    let kitInitialized = false;

    const updateUI = (address) => {
      userAddress = address;
      window.userAddress = address;
      const heroBadge = document.getElementById('connection-status-badge');
      const profileBadge = document.getElementById('link-status-badge');
      const linkBtn = document.getElementById('btn-link');
      const existingKey = "{{EXISTING_KEY_VAL}}";
      const isAlreadyLinked = (existingKey && existingKey.length === 56 && existingKey === address);

      if (address) {
        const addrText = `<span style="width: 8px; height: 8px; background: #10b981; border-radius: 50%; display: inline-block; margin-right: 4px;"></span> Verified: ${address.slice(0,6)}...${address.slice(-4)}`;
        if (heroBadge) {
            heroBadge.innerHTML = addrText;
            heroBadge.classList.replace('badge-error', 'badge-success');
        }
        if (profileBadge) {
            profileBadge.innerHTML = isAlreadyLinked ? "Status: Linked ✅" : "Status: Wallet Not Linked";
            profileBadge.classList.replace(isAlreadyLinked ? 'badge-error' : 'badge-success', isAlreadyLinked ? 'badge-success' : 'badge-error');
        }
        fetchStellarBalance(address);
        if (linkBtn) {
            linkBtn.disabled = address === existingKey;
            linkBtn.innerText = address === existingKey ? "Linked ✅" : (existingKey ? "Switch to this Wallet" : "Verify & Link Wallet");
            if (address === existingKey) linkBtn.classList.replace('btn-primary', 'btn-secondary');
        }
        const claimBtn = document.getElementById('btn-claim-action');
        if (claimBtn) claimBtn.disabled = false;
        if (existingKey && existingKey.length === 56) document.getElementById('unlink-container')?.classList.remove('hidden');
      } else {
        if (heroBadge) heroBadge.innerText = "Wallet: Not Connected";
        if (profileBadge) profileBadge.innerText = "Status: Wallet Disconnected";
        if (linkBtn) { linkBtn.disabled = true; linkBtn.innerText = "Verify & Link Wallet"; }
      }
    };

    const notify = (id, msg, isError = false) => {
        const div = document.getElementById(id);
        if (!div) return;
        div.classList.remove('hidden', 'success', 'error');
        div.classList.add(isError ? 'error' : 'success');
        div.innerText = msg;
    };

    async function initKit() {
        if (kitInitialized) return;
        try {
            if (!window.StellarKit) { setTimeout(initKit, 500); return; }
            const { StellarWalletsKit, KitEventType, SwkAppDarkTheme, defaultModules, WalletConnectModule } = window.StellarKit;
            const modules = [...defaultModules()];
            if (WalletConnectModule && WC_PROJECT_ID && !WC_PROJECT_ID.includes('{{')) {
                modules.push(new WalletConnectModule({
                    projectId: WC_PROJECT_ID,
                    metadata: { name: "SHx Tip Bot", url: window.location.origin }
                }));
            }
            StellarWalletsKit.init({ theme: SwkAppDarkTheme, modules, network: NETWORK_PASSPHRASE });
            const wrapper = document.getElementById('swk-button-wrapper');
            if (wrapper) StellarWalletsKit.createButton(wrapper);
            StellarWalletsKit.on(KitEventType.STATE_UPDATED, (e) => updateUI(e?.payload?.address));
            StellarWalletsKit.on(KitEventType.DISCONNECT, () => updateUI(null));
            try { const { address: a } = await StellarWalletsKit.getAddress(); if (a) updateUI(a); } catch(e) {}
            kitInitialized = true;
        } catch (err) { console.error("Kit Init Fail:", err); }
    };

    async function handleLink() {
        if (!checkSdkReady()) { alert("Please wait for Stellar SDK to load..."); return; }
        if (!userAddress) { try { const { address: a } = await window.StellarKit.StellarWalletsKit.getAddress(); userAddress = a; } catch(e){} }
        if (!userAddress) { alert("Connect wallet first."); return; }
        
        try {
            const sdk = getSdk();
            notify('link-notify', "Building request...");
            const ServerClass = sdk.Horizon?.Server || sdk.Server;
            const server = new ServerClass(HORIZON_URL);
            const account = await server.loadAccount(userAddress);
            const tx = new sdk.TransactionBuilder(account, { fee: "1000", networkPassphrase: NETWORK_PASSPHRASE })
                .addOperation(sdk.Operation.manageData({ name: "link_discord", value: DISCORD_ID }))
                .setTimeout(300).build();

            notify('link-notify', "Awaiting signature...");
            const res = await window.StellarKit.StellarWalletsKit.signTransaction(tx.toXDR(), { networkPassphrase: NETWORK_PASSPHRASE, address: userAddress });
            notify('link-notify', "Verifying...");
            const apiRes = await axios.post(`${API_BASE}/api/link`, { token: TOKEN, public_key: userAddress, signature_xdr: res.signedTxXdr, is_approved: true });
            if (apiRes.data.success) location.reload();
        } catch (e) { notify('link-notify', e.message || String(e), true); }
    }

    async function handleClaim() {
        if (!checkSdkReady() || !userAddress) { alert("Check wallet/SDK connection."); return; }
        try {
            const sdk = getSdk();
            notify('claim-notify', "Fetching ticket...");
            const res = await axios.get(`${API_BASE}/api/withdrawal/${CLAIM_ID}`);
            const { amount, nonce, signature } = res.data;
            const ServerClass = sdk.Horizon?.Server || sdk.Server;
            const server = new ServerClass(HORIZON_URL);
            const SorobanClass = sdk.rpc?.Server || sdk.SorobanServer || sdk.Server;
            const soroban = new SorobanClass(SOROBAN_URL);
            const account = await server.loadAccount(userAddress);
            const sigBytes = Uint8Array.from(atob(signature), c => c.charCodeAt(0));
            const uVal = sdk.nativeToScVal(userAddress, { type: 'address' });
            const args = [uVal, sdk.nativeToScVal(BigInt(Math.round(amount*1M7)), { type: 'i128' }), sdk.nativeToScVal(BigInt(nonce), { type: 'u64' }), sdk.nativeToScVal(sigBytes, { type: 'bytes' })];
            const contract = new sdk.Contract(SOROBAN_CONTRACT_ID);
            const tx = new sdk.TransactionBuilder(account, { fee: "100000", networkPassphrase: NETWORK_PASSPHRASE }).addOperation(contract.call("claim_withdrawal", ...args)).setTimeout(300).build();
            notify('claim-notify', "Simulating...");
            const sim = await soroban.simulateTransaction(tx);
            if (sim.error) throw new Error(sim.error);
            const prepared = await soroban.prepareTransaction(tx, sim);
            notify('claim-notify', "Signing...");
            const sig = await window.StellarKit.StellarWalletsKit.signTransaction(prepared.toXDR(), { networkPassphrase: NETWORK_PASSPHRASE, address: userAddress });
            notify('claim-notify', "Submitting...");
            const resp = await soroban.sendTransaction(sdk.TransactionBuilder.fromXDR(sig.signedTxXdr, NETWORK_PASSPHRASE));
            if (resp.status === "ERROR") throw new Error(resp.error_result_xdr);
            notify('claim-notify', "Confirming...");
            let txR = null; let att = 0;
            while(att<30) { txR = await soroban.getTransaction(resp.hash); if(txR.status==="SUCCESS") break; await new Promise(r=>setTimeout(r,2000)); att++; }
            await axios.post(`${API_BASE}/api/withdrawal/${CLAIM_ID}/complete`, { tx_hash: resp.hash });
            notify('claim-notify', "✅ Success!");
            setTimeout(location.reload, 5000);
        } catch (e) { notify('claim-notify', e.message || String(e), true); }
    }

    async function handleCancel(id) {
        if (!confirm("Cancel and refund?")) return;
        try {
            const res = await axios.post(`${API_BASE}/api/withdrawal/${id || CLAIM_ID}/cancel`, { token: TOKEN });
            if (res.data.success) { notify('claim-notify', "✅ Refunded!"); setTimeout(showList, 1500); }
        } catch (e) { notify('claim-notify', e.message || String(e), true); }
    }

    window.onload = () => {
        fetchBalance(); 
        const e = "{{EXISTING_KEY_VAL}}";
        if (e && e.length === 56) setStatus("Linked ✅");
        initKit();
    };
    
    document.getElementById('btn-link').onclick = handleLink;
    document.getElementById('btn-claim-action').onclick = handleClaim;
    document.getElementById('btn-claim-cancel').onclick = handleCancel;
    document.getElementById('btn-unlink-action').onclick = async () => {
        if (confirm("Unlink wallet?")) {
            await axios.post(`${API_BASE}/api/unlink`, { token: TOKEN });
            localStorage.clear();
            location.reload();
        }
    };
  </script>
</body>
</html>'''
