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
    .btn-danger { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }
    .btn-danger:hover { background: #ef4444; color: white; transform: translateY(-1px); }
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

    #swk-button-wrapper { display: inline-block; min-width: 160px; text-align: right; }
    #swk-button-wrapper button {
      background: var(--accent) !important; border-radius: 0.75rem !important;
      padding: 0.6rem 1.2rem !important; font-weight: 600 !important;
      font-size: 0.85rem !important; border: none !important; color: white !important;
      transition: all 0.2s ease !important; cursor: pointer !important;
    }
    #swk-button-wrapper button:hover { background: #2563eb !important; transform: translateY(-1px); }
  </style>
</head>
<body>
  <div class="background-castle"></div>
  <div class="container">
    <nav>
      <div class="logo">
        <img src="https://cdn.prod.website-files.com/5e9a1cde22bbc0a89dba7f5b/60c9649cf8fb48e5c883950e_Stronghold%20Logo%20Mark%20Blue.png" alt="SHx">
        <span>SHx Community</span>
      </div>
      <div id="swk-button-wrapper"></div>
    </nav>

    <div class="hero">
      <h1>Community Portal <span class="text-xs" style="opacity: 0.5;">v2.0</span></h1>
      <p>Securely link your Discord and manage claims.</p>
      <div id="connection-status-badge" class="badge badge-error mt-4">Wallet: Not Connected</div>
    </div>

    <div class="card">
      <div class="profile-section">
        <div class="profile-info">
          <div class="profile-avatar">{{USER_INITIAL}}</div>
          <div>
            <h2 style="font-size: 1.25rem;">{{DISCORD_USER}}</h2>
            <div id="link-status-badge" class="badge badge-error text-xs mt-1">Status: Checking...</div>
          </div>
        </div>
        <div class="stats-row">
          <div class="stat-item">
            <div class="stat-label">Discord Balance <div class="info-trigger">?</div>
              <div class="tooltip">
                <b>Internal Tipping Account</b><p class="text-xs text-muted mb-2">Move SHx from your wallet here for tipping:</p>
                <ol><li>Type <b>/deposit</b> in Discord.</li><li>Send SHx with Memo ID: <b>{{MEMO}}</b></li></ol>
              </div>
            </div>
            <div class="stat-value accent"><span id="internal-balance-val">{{INTERNAL_BALANCE}}</span> <span class="text-xs">SHx</span></div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-label">Wallet Balance</div>
            <div class="stat-value"><span id="external-balance-val">0.00</span> <span class="text-xs">SHx</span></div>
          </div>
        </div>
      </div>
      
      <p class="mb-4 text-xs text-accent" style="cursor:pointer; text-decoration: underline;" onclick="resetSession()">Trouble connecting? Reset Session</p>
      <div id="link-notify" class="status hidden"></div>
      <button id="btn-link" class="btn btn-primary w-full justify-center" disabled>Verify & Link Wallet</button>
      <div id="unlink-container" class="mt-4 text-center hidden"><button id="btn-unlink-action" class="btn btn-secondary w-full justify-center">Unlink Current Wallet</button></div>
    </div>

    <div id="claim-card" class="card">
      <h2>Pending Withdrawals</h2>
      <p class="text-sm text-muted mb-4">Tickets created from Discord. Select one to claim.</p>
      <div id="withdrawal-list" class="mb-4"><div class="text-center py-4 text-muted">Scanning tickets...</div></div>
      <div id="claim-notify" class="status hidden"></div>
      <div id="active-claim-view" class="hidden bg-dark-overlay mt-4">
        <h3 class="mb-2">Claiming: <span id="active-ticket-id" class="text-accent"></span></h3>
        <p class="mb-4">Amount: <span id="active-ticket-amount" class="text-bold text-accent"></span> SHx</p>
        <button id="btn-claim-action" class="btn btn-primary bg-success w-full justify-center" disabled>Confirm & Claim on Stellar</button>
        <button id="btn-claim-cancel" class="btn btn-danger w-full justify-center mt-4">Cancel Ticket & Refund to Discord</button>
        <p class="text-xs text-center mt-4 text-muted" onclick="showList()" style="cursor:pointer; text-decoration: underline;">← Back to List</p>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/stellar-sdk@12.3.0/dist/stellar-sdk.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
  <script src="/wallet-kit-bundle.umd.js"></script>

  <script>
    const getSdk = () => window.StellarSdk || window.Stellar;
    const checkSdkReady = () => !!getSdk();

    const urlParams = new URLSearchParams(window.location.search);
    const TOKEN_RAW = urlParams.get('token') || "{{TOKEN}}";
    const TOKEN = (TOKEN_RAW.includes("{{") || !TOKEN_RAW) ? "" : TOKEN_RAW;
    let CLAIM_ID_RAW = urlParams.get('claim_id') || "{{CLAIM_ID}}";
    let CLAIM_ID = (CLAIM_ID_RAW.includes("{{") || !CLAIM_ID_RAW) ? "" : CLAIM_ID_RAW;
    let PENDING_IDS = {{PENDING_IDS}};
    const NETWORK = "{{NETWORK}}";
    const STELLAR_EXPERT_BASE = `https://stellar.expert/explorer/${NETWORK === 'public' ? 'public' : 'testnet'}`;
    const NETWORK_PASSPHRASE = "{{NETWORK_PASSPHRASE}}";
    const SHX_ASSET_CODE = "{{SHX_ASSET_CODE}}";
    const SHX_ISSUER_VAL = "{{SHX_ISSUER}}";
    const HORIZON_URL = "{{HORIZON_URL}}";
    const SOROBAN_URL = "{{SOROBAN_URL}}";
    const API_BASE = window.location.origin;

    async function fetchStellarBalance(address) {
        if (!address || !checkSdkReady()) return;
        try {
            const sdk = getSdk();
            const server = new (sdk.Horizon?.Server || sdk.Server)(HORIZON_URL);
            const acc = await server.loadAccount(address);
            const b = acc.balances.find(x => x.asset_code === SHX_ASSET_CODE && x.asset_issuer === SHX_ISSUER_VAL);
            document.getElementById('external-balance-val').innerText = b ? parseFloat(b.balance).toLocaleString(undefined, {minimumFractionDigits:2}) : "0.00";
        } catch (e) { document.getElementById('external-balance-val').innerText = "Check Trustline"; }
    }

    const setStatus = (msg, isError = false) => {
        const el = document.getElementById('link-status-badge');
        if (!el) return;
        el.innerText = "Status: " + msg;
        el.className = `badge text-xs mt-1 ${msg.includes('✅') ? 'badge-success' : 'badge-error'}`;
    };

    const fetchBalance = async () => {
        if (!TOKEN && !CLAIM_ID) {
            document.getElementById('withdrawal-list').innerHTML = '<div class="text-center py-4 text-muted">Guest Mode: Use <b>/link</b> in Discord to see your tickets.</div>';
            return;
        }
        try {
            const res = await axios.get(`${API_BASE}/api/balance?token=${TOKEN}&claim_id=${CLAIM_ID}`);
            if (res.data.success) {
                document.getElementById('internal-balance-val').innerText = res.data.balance;
                if (res.data.pending_withdrawals?.length > 0) renderWithdrawals(res.data.pending_withdrawals);
                else document.getElementById('withdrawal-list').innerHTML = '<div class="text-center py-4 text-muted">No pending tickets found.</div>';
                if (userAddress) fetchStellarBalance(userAddress);
            }
        } catch (e) { 
            console.warn("Balance fetch failed:", e); 
            document.getElementById('withdrawal-list').innerHTML = '<div class="text-center py-4 text-muted">Wait for a fresh link from Discord...</div>';
        }
    };

    const renderWithdrawals = (ws) => {
        const el = document.getElementById('withdrawal-list');
        let html = '';
        ws.forEach(w => {
            html += `<div class="bg-dark-overlay mb-2 p-3 rounded-lg border border-opacity-10" style="display:flex; justify-content:space-between; align-items:center;">
              <div><p class="text-bold text-accent">${w.amount} SHx</p><p class="text-xs text-muted">Ticket: ...${w.id.slice(-6)}</p><span onclick="handleCancel('${w.id}')" class="text-error text-xs" style="cursor:pointer; text-decoration: underline; margin-top: 4px; display: inline-block;">Cancel & Refund</span></div>
              <button onclick="selectTicket('${w.id}', '${w.amount}')" class="btn btn-primary text-xs px-4 py-2">Select to Claim</button>
            </div>`;
        });
        el.innerHTML = html;
    };

    const selectTicket = (id, amt) => {
        CLAIM_ID = id;
        document.getElementById('withdrawal-list').classList.add('hidden');
        document.getElementById('active-claim-view').classList.remove('hidden');
        document.getElementById('active-ticket-id').innerText = `...${id.slice(-8)}`;
        document.getElementById('active-ticket-amount').innerText = amt;
        document.getElementById('btn-claim-action').disabled = !userAddress;
        
        // Ensure the cancel button is visible and active
        const cBtn = document.getElementById('btn-claim-cancel');
        if (cBtn) { cBtn.classList.remove('hidden'); cBtn.onclick = () => handleCancel(id); }
        
        notify('claim-notify', "Review details and confirm below.");
    };

    const showList = () => {
        document.getElementById('withdrawal-list').classList.remove('hidden');
        document.getElementById('active-claim-view').classList.add('hidden');
        fetchBalance();
    };

    const resetSession = () => { if(confirm("Reset session?")) { localStorage.clear(); location.reload(); } };

    const DISCORD_ID = "{{DISCORD_ID}}";
    const SOROBAN_CONTRACT_ID = "{{SOROBAN_CONTRACT_ID}}";
    let userAddress = null;
    let kitInitialized = false;

    const updateUI = (address) => {
      userAddress = address;
      const hero = document.getElementById('connection-status-badge');
      const profile = document.getElementById('link-status-badge');
      const linkBtn = document.getElementById('btn-link');
      const existing = "{{EXISTING_KEY_VAL}}";
      const linked = (existing && existing === address);

      if (address) {
        hero.innerText = `Verified: ${address.slice(0,6)}...${address.slice(-4)}`;
        hero.className = "badge badge-success mt-4";
        profile.innerText = linked ? "Status: Linked ✅" : "Status: Wallet Not Linked";
        profile.className = `badge text-xs mt-1 ${linked ? 'badge-success' : 'badge-error'}`;
        fetchStellarBalance(address);
        linkBtn.disabled = linked;
        linkBtn.innerText = linked ? "Linked ✅" : (existing && existing.length === 56 ? "Switch to this Wallet" : "Verify & Link Wallet");
        document.getElementById('btn-claim-action').disabled = false;
        if(existing && existing.length === 56) document.getElementById('unlink-container').classList.remove('hidden');
      } else {
        hero.innerText = "Wallet: Not Connected";
        hero.className = "badge badge-error mt-4";
        linkBtn.disabled = true;
      }
    };

    const notify = (id, msg, isError = false) => {
        const div = document.getElementById(id);
        if (!div) return;
        div.className = `status ${isError ? 'error' : 'success'}`;
        div.innerHTML = msg;
        div.classList.remove('hidden');
    };

    async function initKit() {
        if (kitInitialized) return;
        console.log("DASHBOARD | Initializing Wallet Kit...");
        try {
            if (!window.StellarKit) { setTimeout(initKit, 500); return; }
            const { StellarWalletsKit, KitEventType, SwkAppDarkTheme, defaultModules } = window.StellarKit;
            StellarWalletsKit.init({ theme: SwkAppDarkTheme, modules: defaultModules(), network: NETWORK_PASSPHRASE });
            StellarWalletsKit.createButton(document.getElementById('swk-button-wrapper'));
            StellarWalletsKit.on(KitEventType.STATE_UPDATED, (e) => updateUI(e?.payload?.address));
            StellarWalletsKit.on(KitEventType.DISCONNECT, () => updateUI(null));
            const { address } = await StellarWalletsKit.getAddress();
            if (address) updateUI(address);
            kitInitialized = true;
            console.log("DASHBOARD | Wallet Kit Ready.");
        } catch (err) { console.error("Kit Init Fail:", err); }
    };

    async function handleLink() {
        if (!userAddress) return alert("Connect wallet first.");
        if (!TOKEN) return alert("Guest Mode: Please navigate here using the /link command from Discord to verify your wallet.");
        try {
            const sdk = getSdk();
            notify('link-notify', "Awaiting signature...");
            const server = new (sdk.Horizon?.Server || sdk.Server)(HORIZON_URL);
            const account = await server.loadAccount(userAddress);
            const tx = new sdk.TransactionBuilder(account, { fee: "1000", networkPassphrase: NETWORK_PASSPHRASE })
                .addOperation(sdk.Operation.manageData({ name: "link_discord", value: DISCORD_ID }))
                .setTimeout(300).build();
            const res = await window.StellarKit.StellarWalletsKit.signTransaction(tx.toXDR(), { networkPassphrase: NETWORK_PASSPHRASE, address: userAddress });
            await axios.post(`${API_BASE}/api/link`, { token: TOKEN, public_key: userAddress, signature_xdr: res.signedTxXdr, is_approved: true });
            location.reload();
        } catch (e) {
            const errorMsg = e.response?.data?.detail || e.message || String(e);
            notify('link-notify', errorMsg, true);
        }
    }

    async function handleClaim() {
        if (!userAddress) return alert("Connect wallet first.");
        try {
            const sdk = getSdk();
            notify('claim-notify', "Preparing claim...");
            const res = await axios.get(`${API_BASE}/api/withdrawal/${CLAIM_ID}`);
            const { amount, nonce, signature } = res.data;
            const soroban = new (sdk.rpc?.Server || sdk.SorobanServer || sdk.Server)(SOROBAN_URL);
            const account = await (new (sdk.Horizon?.Server || sdk.Server)(HORIZON_URL)).loadAccount(userAddress);
            const uVal = sdk.nativeToScVal(userAddress, { type: 'address' });
            const args = [uVal, sdk.nativeToScVal(BigInt(Math.round(amount*10000000)), { type: 'i128' }), sdk.nativeToScVal(BigInt(nonce), { type: 'u64' }), sdk.nativeToScVal(Uint8Array.from(atob(signature), c => c.charCodeAt(0)), { type: 'bytes' })];
            const tx = new sdk.TransactionBuilder(account, { fee: "100000", networkPassphrase: NETWORK_PASSPHRASE }).addOperation((new sdk.Contract(SOROBAN_CONTRACT_ID)).call("claim_withdrawal", ...args)).setTimeout(300).build();
            const sim = await soroban.simulateTransaction(tx);
            const prepared = await soroban.prepareTransaction(tx, sim);
            const sig = await window.StellarKit.StellarWalletsKit.signTransaction(prepared.toXDR(), { networkPassphrase: NETWORK_PASSPHRASE, address: userAddress });
            const resp = await soroban.sendTransaction(sdk.TransactionBuilder.fromXDR(sig.signedTxXdr, NETWORK_PASSPHRASE));
            notify('claim-notify', "Confirming...");
            let txR = null; let att = 0;
            while(att<15) { txR = await soroban.getTransaction(resp.hash); if(txR.status==="SUCCESS") break; await new Promise(r=>setTimeout(r,2000)); att++; }
            await axios.post(`${API_BASE}/api/withdrawal/${CLAIM_ID}/complete`, { tx_hash: resp.hash });
            const txUrl = `${STELLAR_EXPERT_BASE}/tx/${resp.hash}`;
            notify('claim-notify', `✅ Success! <a href="${txUrl}" target="_blank" style="color:var(--accent); text-decoration:underline;">View on Explorer</a>`);
            setTimeout(() => location.reload(), 4500);
        } catch (e) {
            const errorMsg = e.response?.data?.detail || e.message || String(e);
            notify('claim-notify', errorMsg, true);
        }
    }

    async function handleCancel(id) {
        if (!confirm("Are you sure you want to cancel this withdrawal and refund the SHx back to your Discord balance?")) return;
        try {
            notify('claim-notify', "Processing refund...");
            const res = await axios.post(`${API_BASE}/api/withdrawal/${id || CLAIM_ID}/cancel`, { token: TOKEN });
            if (res.data.success) { notify('claim-notify', "✅ Refunded back to Discord!"); setTimeout(showList, 1500); }
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
    const cancelBtn = document.getElementById('btn-claim-cancel');
    if (cancelBtn) cancelBtn.onclick = () => handleCancel();
    
    document.getElementById('btn-unlink-action').onclick = async () => {
        if (confirm("Unlink wallet?")) { await axios.post(`${API_BASE}/api/unlink`, { token: TOKEN }); localStorage.clear(); location.reload(); }
    };
  </script>
</html>'''
