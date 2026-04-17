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
      background-size: min(70vw, 80vh);
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
      width: 56px; 
      height: 56px; 
      object-fit: contain;
      border-radius: 50%;
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

    /* Utilities */
    .hidden { display: none !important; }

    #swk-button-wrapper { display: inline-block; min-width: 160px; text-align: right; }
    #swk-button-wrapper button {
      background: var(--accent) !important; border-radius: 0.75rem !important;
      padding: 0.6rem 1.2rem !important; font-weight: 600 !important;
      font-size: 0.85rem !important; border: none !important; color: white !important;
      transition: all 0.2s ease !important; cursor: pointer !important;
    }
    #swk-button-wrapper button:hover { background: #2563eb !important; transform: translateY(-1px); }

        /* Language Selector */
    #lang-selector {
      background: rgba(17, 24, 39, 0.8);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 0.4rem 0.8rem;
      border-radius: 0.5rem;
      font-family: 'Inter', sans-serif;
      font-size: 0.85rem;
      cursor: pointer;
      outline: none;
      margin-right: 1rem;
    }
    #lang-selector:focus { border-color: var(--accent); }
    #lang-selector option { background: #0f172a; }

    /* Responsive */
    @media (max-width: 640px) {
      .profile-section { flex-direction: column; align-items: flex-start; gap: 1.5rem; }
      .stats-row { flex-direction: column; align-items: flex-start; gap: 1rem; width: 100%; }
      .stat-divider { display: none; }
      .hero h1 { font-size: 2rem; }
      nav { flex-direction: column; gap: 1rem; align-items: center; }
      #swk-button-wrapper { text-align: center; }
      
      /* Fix Tooltip cutoff on mobile */
      .tooltip { left: -10px; transform: translateY(10px); width: 280px; }
      .tooltip::after { left: 17px; transform: translateX(-50%); }
      .info-trigger:hover + .tooltip, .tooltip:hover { transform: translateY(0); }
    }
  </style>
</head>
<body>
  <div class="background-castle"></div>
  <div class="container">
    <nav>
      <div class="logo">
        <img src="/bot_avatar.png" alt="SHx Tip Bot Avatar">
        <span data-i18n="nav_title">SHx Tip Bot</span>
      </div>
      <div style="display: flex; align-items: center;">
        <select id="lang-selector">
          <option value="en">English</option>
          <option value="ja">日本語</option>
          <option value="ko">한국어</option>
          <option value="de">Deutsch</option>
          <option value="es">Español</option>
          <option value="fr">Français</option>
          <option value="zh">中文</option>
          <option value="pt">Português</option>
          <option value="ru">Русский</option>
        </select>
        <div id="swk-button-wrapper"></div>
      </div>
    </nav>

    <div class="hero">
      <h1><span data-i18n="hero_title">Community Portal</span> <span class="text-xs" style="opacity: 0.5;">v2.0</span></h1>
      <p data-i18n="hero_desc">Securely link your Discord and manage claims.</p>
      <div id="connection-status-badge" class="badge badge-error mt-4" data-i18n="wallet_not_connected">Wallet: Not Connected</div>
    </div>

    <div class="card">
      <div class="profile-section">
        <div class="profile-info">
          <div class="profile-avatar">{{USER_INITIAL}}</div>
          <div>
            <h2 style="font-size: 1.25rem;">{{DISCORD_USER}}</h2>
            <div id="link-status-badge" class="badge badge-error text-xs mt-1" data-i18n="status_checking">Status: Checking...</div>
          </div>
        </div>
        <div class="stats-row">
          <div class="stat-item">
            <div class="stat-label"><span data-i18n="stat_discord_bal">Discord Balance</span> <div class="info-trigger">?</div>
              <div class="tooltip">
                <b data-i18n="tt_internal_acc">Internal Tipping Account</b><p class="text-xs text-muted mb-2" data-i18n="tt_desc">Move SHx from your wallet here for tipping:</p>
                <ol><li data-i18n="tt_li1">Type <b>/deposit</b> in Discord.</li><li data-i18n="tt_li2">Send SHx with Memo ID: <b>{{MEMO}}</b></li></ol>
              </div>
            </div>
            <div class="stat-value accent"><span id="internal-balance-val">{{INTERNAL_BALANCE}}</span> <span class="text-xs">SHx</span></div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-label" data-i18n="stat_wallet_bal">Wallet Balance</div>
            <div class="stat-value"><span id="external-balance-val">0.00</span> <span class="text-xs">SHx</span></div>
          </div>
        </div>
      </div>
      
      <p class="mb-4 text-xs text-accent" style="cursor:pointer; text-decoration: underline;" onclick="resetSession()" data-i18n="reset_session">Trouble connecting? Reset Session</p>
      <div id="link-notify" class="status hidden"></div>
      <button id="btn-link" class="btn btn-primary w-full justify-center" disabled data-i18n="btn_link">Verify & Link Wallet</button>
      <div id="unlink-container" class="mt-4 text-center hidden"><button id="btn-unlink-action" class="btn btn-secondary w-full justify-center" data-i18n="btn_unlink">Unlink Current Wallet</button></div>
    </div>

    <div id="claim-card" class="card">
      <h2 data-i18n="pending_withdrawals">Pending Withdrawals</h2>
      <p class="text-sm text-muted mb-4" data-i18n="tickets_desc">Tickets created from Discord. Select one to claim.</p>
      <div id="withdrawal-list" class="mb-4"><div class="text-center py-4 text-muted" data-i18n="scanning_tickets">Scanning tickets...</div></div>
      <div id="claim-notify" class="status hidden"></div>
      <div id="active-claim-view" class="hidden bg-dark-overlay mt-4">
        <h3 class="mb-2"><span data-i18n="claiming">Claiming</span>: <span id="active-ticket-id" class="text-accent"></span></h3>
        <p class="mb-4"><span data-i18n="amount">Amount</span>: <span id="active-ticket-amount" class="text-bold text-accent"></span> SHx</p>
        <button id="btn-claim-action" class="btn btn-primary bg-success w-full justify-center" disabled data-i18n="btn_claim">Confirm & Claim on Stellar</button>
        <button id="btn-claim-cancel" class="btn btn-danger w-full justify-center mt-4 hidden" data-i18n="btn_cancel">Cancel Ticket & Refund to Discord</button>
        <p class="text-xs text-center mt-4 text-muted" onclick="showList()" style="cursor:pointer; text-decoration: underline;" data-i18n="back_list">← Back to List</p>
      </div>
    </div>

    <div class="text-center mt-4 text-xs text-muted" style="padding-bottom: 2rem;">
      <span data-i18n="questions">Questions?: Email</span> <a href="mailto:SHxTipBot@Gmail.com" style="color: var(--accent); text-decoration: none;">SHxTipBot@Gmail.com</a>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/@stellar/stellar-sdk@15.0.1/dist/stellar-sdk.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
  <script src="/wallet-kit-bundle.umd.js"></script>

  <script>

    // === MULTILINGUAL i18n SYSTEM ===
    const TRANSLATIONS = {
      en: {
        nav_title: "SHx Tip Bot", hero_title: "Community Portal", hero_desc: "Securely link your Discord and manage claims.",
        wallet_not_connected: "Wallet: Not Connected", status_checking: "Status: Checking...",
        stat_discord_bal: "Discord Balance", tt_internal_acc: "Internal Tipping Account", tt_desc: "Move SHx from your wallet here for tipping:",
        tt_li1: "Type <b>/deposit</b> in Discord.", tt_li2: "Send SHx with Memo ID:", stat_wallet_bal: "Wallet Balance",
        reset_session: "Trouble connecting? Reset Session", btn_link: "Verify & Link Wallet", btn_unlink: "Unlink Current Wallet",
        pending_withdrawals: "Pending Withdrawals", tickets_desc: "Tickets created from Discord. Select one to claim.", scanning_tickets: "Scanning tickets...",
        claiming: "Claiming", amount: "Amount", btn_claim: "Confirm & Claim on Stellar", btn_cancel: "Cancel Ticket & Refund to Discord",
        back_list: "← Back to List", questions: "Questions?: Email",
        js_guest_mode: "Guest Mode: Use <b>/link</b> in Discord to see your tickets.",
        js_wait_fresh: "Wait for a fresh link from Discord...", js_no_tickets: "No pending tickets found.",
        js_ticket: "Ticket:", js_cancel_refund: "Cancel & Refund", js_select_claim: "Select to Claim",
        js_review: "Review details and confirm below.", js_verified: "Verified", js_status_linked: "Status: Linked ✅",
        js_status_not_linked: "Status: Wallet Not Linked", js_switch_wallet: "Switch to this Wallet",
        js_connect_first: "Connect wallet first.", js_guest_alert: "Guest Mode: Please navigate here using the /link command from Discord to verify your wallet.",
        js_awaiting_sig: "Awaiting signature...", js_preparing: "Preparing claim...", js_confirming: "Confirming...",
        js_success: "✅ Success!", js_view_explorer: "View on Explorer", js_refund_prompt: "Are you sure you want to cancel this withdrawal and refund the SHx back to your Discord balance?",
        js_processing: "Processing refund...", js_refunded: "✅ Refunded back to Discord!", js_check_trustline: "Check Trustline",
        js_reset_prompt: "Reset session?", js_unlink_prompt: "Unlink wallet?"
      },
      ja: {
        nav_title: "SHxチップボット", hero_title: "コミュニティポータル", hero_desc: "Discordを安全にリンクし、請求を管理します。",
        wallet_not_connected: "ウォレット：未接続", status_checking: "ステータス：確認中...",
        stat_discord_bal: "Discord残高", tt_internal_acc: "内部チップアカウント", tt_desc: "チップ用にウォレットからSHxを移動：",
        tt_li1: "Discordで<b>/deposit</b>と入力します。", tt_li2: "メモID付きでSHxを送信：", stat_wallet_bal: "ウォレット残高",
        reset_session: "接続の問題？セッションをリセット", btn_link: "ウォレットを検証してリンク", btn_unlink: "現在のウォレットのリンクを解除",
        pending_withdrawals: "保留中の出金", tickets_desc: "Discordから作成されたチケット。請求するものを選択してください。", scanning_tickets: "チケットをスキャン中...",
        claiming: "請求", amount: "金額", btn_claim: "Stellarで確認して請求", btn_cancel: "チケットをキャンセルしてDiscordに返金",
        back_list: "← リストに戻る", questions: "質問がありますか？メール：",
        js_guest_mode: "ゲストモード：チケットを表示するにはDiscordで<b>/link</b>を使用してください。",
        js_wait_fresh: "Discordからの新しいリンクを待っています...", js_no_tickets: "保留中のチケットは見つかりませんでした。",
        js_ticket: "チケット:", js_cancel_refund: "キャンセルして返金", js_select_claim: "選択して請求",
        js_review: "詳細を確認し、以下で承認してください。", js_verified: "検証済み", js_status_linked: "ステータス：リンク済み ✅",
        js_status_not_linked: "ステータス：リンクされていません", js_switch_wallet: "このウォレットに切り替える",
        js_connect_first: "最初にウォレットを接続してください。", js_guest_alert: "ゲストモード：Discordの/linkコマンドを使用してここへ行き、ウォレットを認証してください。",
        js_awaiting_sig: "署名を待っています...", js_preparing: "請求の準備中...", js_confirming: "確認中...",
        js_success: "✅ 成功！", js_view_explorer: "エクスプローラーで表示", js_refund_prompt: "この出金をキャンセルし、SHxをDiscordの残高に返金してもよろしいですか？",
        js_processing: "返金処理中...", js_refunded: "✅ Discordに返金されました！", js_check_trustline: "トラストラインを確認",
        js_reset_prompt: "セッションをリセットしますか？", js_unlink_prompt: "ウォレットのリンクを解除しますか？"
      },
      ko: {
        nav_title: "SHx 팁 봇", hero_title: "커뮤니티 포털", hero_desc: "Discord를 안전하게 연결하고 청구를 관리하세요.",
        wallet_not_connected: "지갑: 연결되지 않음", status_checking: "상태: 확인 중...",
        stat_discord_bal: "Discord 잔고", tt_internal_acc: "내부 팁 계정", tt_desc: "팁을 위해 지갑에서 이곳으로 SHx를 이동하세요:",
        tt_li1: "Discord에서 <b>/deposit</b>을 입력하세요.", tt_li2: "메모 ID와 함께 SHx 보내기:", stat_wallet_bal: "지갑 잔고",
        reset_session: "연결 문제? 세션 초기화", btn_link: "지갑 확인 및 연결", btn_unlink: "현재 지갑 연결 해제",
        pending_withdrawals: "대기 중인 출금", tickets_desc: "Discord에서 생성된 티켓입니다. 청구할 하나를 선택하세요.", scanning_tickets: "티켓 스캔 중...",
        claiming: "청구 중", amount: "금액", btn_claim: "확인 및 Stellar에서 청구", btn_cancel: "티켓 취소 및 Discord로 환불",
        back_list: "← 목록으로 돌아가기", questions: "도움이 필요하신가요? 이메일:",
        js_guest_mode: "게스트 모드: 티켓을 보려면 Discord에서 <b>/link</b>를 사용하세요.",
        js_wait_fresh: "Discord에서 새로운 링크를 기다리는 중...", js_no_tickets: "대기 중인 티켓을 찾을 수 없습니다.",
        js_ticket: "티켓:", js_cancel_refund: "취소 및 환불", js_select_claim: "청구할 항목 선택",
        js_review: "세부 사항을 검토하고 아래에서 확인하세요.", js_verified: "확인됨", js_status_linked: "상태: 연결됨 ✅",
        js_status_not_linked: "상태: 연결되지 않음", js_switch_wallet: "이 지갑으로 전환",
        js_connect_first: "먼저 지갑을 연결하세요.", js_guest_alert: "게스트 모드: 지갑을 확인하려면 Discord의 /link 명령을 사용하세요.",
        js_awaiting_sig: "서명 대기 중...", js_preparing: "청구 준비 중...", js_confirming: "확인 중...",
        js_success: "✅ 성공!", js_view_explorer: "익스플로러에서 보기", js_refund_prompt: "이 출금을 취소하고 SHx를 Discord 잔고로 환불하시겠습니까?",
        js_processing: "환불 처리 중...", js_refunded: "✅ Discord로 환불되었습니다!", js_check_trustline: "트러스트라인 확인",
        js_reset_prompt: "세션을 초기화하시겠습니까?", js_unlink_prompt: "지갑 연결을 해제하시겠습니까?"
      },
      de: {
        nav_title: "SHx Trinkgeld Bot", hero_title: "Community Portal", hero_desc: "Verbinde dein Discord sicher und verwalte Forderungen.",
        wallet_not_connected: "Wallet: Nicht verbunden", status_checking: "Status: Überprüfung...",
        stat_discord_bal: "Discord Guthaben", tt_internal_acc: "Internes Trinkgeld-Konto", tt_desc: "Verschiebe SHx für Trinkgelder hierher:",
        tt_li1: "Tippe <b>/deposit</b> in Discord ein.", tt_li2: "Sende SHx mit Memo ID:", stat_wallet_bal: "Wallet Guthaben",
        reset_session: "Verbindungsprobleme? Sitzung zurücksetzen", btn_link: "Wallet validieren & verbinden", btn_unlink: "Aktuelles Wallet trennen",
        pending_withdrawals: "Ausstehende Auszahlungen", tickets_desc: "In Discord erstellte Tickets. Wähle eins für die Auszahlung.", scanning_tickets: "Tickets werden gescannt...",
        claiming: "Forderung", amount: "Betrag", btn_claim: "Bestätigen & auf Stellar einfordern", btn_cancel: "Ticket stornieren & an Discord erstatten",
        back_list: "← Zurück zur Liste", questions: "Fragen? E-Mail:",
        js_guest_mode: "Gastmodus: Nutze <b>/link</b> in Discord, um deine Tickets zu sehen.",
        js_wait_fresh: "Warte auf einen frischen Link von Discord...", js_no_tickets: "Keine ausstehenden Tickets gefunden.",
        js_ticket: "Ticket:", js_cancel_refund: "Stornieren & Erstatten", js_select_claim: "Für Auszahlung wählen",
        js_review: "Details unten überprüfen und bestätigen.", js_verified: "Verifiziert", js_status_linked: "Status: Verbunden ✅",
        js_status_not_linked: "Status: Wallet nicht verbunden", js_switch_wallet: "Auf dieses Wallet wechseln",
        js_connect_first: "Wallet zuerst verbinden.", js_guest_alert: "Gastmodus: Bitte verwende den /link-Befehl aus Discord, um dein Wallet zu bestätigen.",
        js_awaiting_sig: "Warte auf Signatur...", js_preparing: "Forderung wird vorbereitet...", js_confirming: "Bestätige...",
        js_success: "✅ Erfolg!", js_view_explorer: "Im Explorer ansehen", js_refund_prompt: "Bist du sicher, dass du diese Auszahlung stornieren und SHx auf dein Discord-Guthaben erstatten möchtest?",
        js_processing: "Erstattung wird verarbeitet...", js_refunded: "✅ Zurück an Discord erstattet!", js_check_trustline: "Trustline prüfen",
        js_reset_prompt: "Sitzung zurücksetzen?", js_unlink_prompt: "Wallet trennen?"
      },
      es: {
        nav_title: "SHx Tip Bot", hero_title: "Portal Comunitario", hero_desc: "Vincula de forma segura tu Discord y administra tus reclamos.",
        wallet_not_connected: "Billetera: No conectada", status_checking: "Estado: Comprobando...",
        stat_discord_bal: "Saldo de Discord", tt_internal_acc: "Cuenta interna de propinas", tt_desc: "Mueve SHx desde tu billetera aquí para propinas:",
        tt_li1: "Escribe <b>/deposit</b> en Discord.", tt_li2: "Envía SHx con ID de Memo:", stat_wallet_bal: "Saldo de Billetera",
        reset_session: "¿Problemas para conectar? Reiniciar Sesión", btn_link: "Verificar y Vincular Billetera", btn_unlink: "Desvincular Billetera Actual",
        pending_withdrawals: "Retiros pendientes", tickets_desc: "Tickets creados desde Discord. Selecciona uno para reclamar.", scanning_tickets: "Buscando tickets...",
        claiming: "Reclamando", amount: "Monto", btn_claim: "Confirmar y Reclamar en Stellar", btn_cancel: "Cancelar Ticket y Reembolsar a Discord",
        back_list: "← Volver a la Lista", questions: "¿Preguntas? Correo:",
        js_guest_mode: "Modo invitado: Usa <b>/link</b> en Discord para ver tus tickets.",
        js_wait_fresh: "Esperando un nuevo enlace desde Discord...", js_no_tickets: "No se encontraron tickets pendientes.",
        js_ticket: "Ticket:", js_cancel_refund: "Cancelar y Reembolsar", js_select_claim: "Seleccionar para Reclamar",
        js_review: "Revisa los detalles y confirma a continuación.", js_verified: "Verificado", js_status_linked: "Estado: Vinculado ✅",
        js_status_not_linked: "Estado: Billetera no vinculada", js_switch_wallet: "Cambiar a esta billetera",
        js_connect_first: "Conecta la billetera primero.", js_guest_alert: "Modo Invitado: Utilice el comando /link de Discord para verificar su billetera.",
        js_awaiting_sig: "Esperando firma...", js_preparing: "Preparando reclamo...", js_confirming: "Confirmando...",
        js_success: "✅ ¡Éxito!", js_view_explorer: "Ver en el Explorador", js_refund_prompt: "¿Estás seguro de que deseas cancelar este retiro y reembolsar el SHx a tu saldo de Discord?",
        js_processing: "Procesando reembolso...", js_refunded: "✅ ¡Reembolsado a Discord!", js_check_trustline: "Verifique Trustline",
        js_reset_prompt: "¿Reiniciar sesión?", js_unlink_prompt: "¿Desvincular billetera?"
      },
      fr: {
        nav_title: "SHx Tip Bot", hero_title: "Portail Communautaire", hero_desc: "Liez votre Discord en toute sécurité et gérez vos réclamations.",
        wallet_not_connected: "Portefeuille : Non connecté", status_checking: "Statut : Vérification...",
        stat_discord_bal: "Solde Discord", tt_internal_acc: "Compte de pourboire interne", tt_desc: "Déplacez des SHx de votre portefeuille ici pour les pourboires :",
        tt_li1: "Tapez <b>/deposit</b> dans Discord.", tt_li2: "Envoyer des SHx avec l'ID Memo :", stat_wallet_bal: "Solde du Portefeuille",
        reset_session: "Problèmes de connexion ? Réinitialiser la session", btn_link: "Vérifier et lier le portefeuille", btn_unlink: "Délier le portefeuille actuel",
        pending_withdrawals: "Retraits en attente", tickets_desc: "Billets créés depuis Discord. Sélectionnez-en un à réclamer.", scanning_tickets: "Recherche de billets...",
        claiming: "Réclamation", amount: "Montant", btn_claim: "Confirmer et réclamer sur Stellar", btn_cancel: "Annuler le billet et rembourser à Discord",
        back_list: "← Retour à la liste", questions: "Questions ? Email :",
        js_guest_mode: "Mode invité : Utilisez <b>/link</b> dans Discord pour voir vos billets.",
        js_wait_fresh: "En attente d'un nouveau lien depuis Discord...", js_no_tickets: "Aucun billet en attente trouvé.",
        js_ticket: "Billet :", js_cancel_refund: "Annuler et rembourser", js_select_claim: "Sélectionner pour réclamer",
        js_review: "Passez en revue les détails et confirmez ci-dessous.", js_verified: "Vérifié", js_status_linked: "Statut : Lié ✅",
        js_status_not_linked: "Statut : Portefeuille non lié", js_switch_wallet: "Passer à ce portefeuille",
        js_connect_first: "Connectez le portefeuille d'abord.", js_guest_alert: "Mode invité : Veuillez utiliser la commande /link dans Discord pour vérifier votre portefeuille.",
        js_awaiting_sig: "En attente de signature...", js_preparing: "Préparation de la réclamation...", js_confirming: "Confirmation...",
        js_success: "✅ Succès !", js_view_explorer: "Voir sur l'explorateur", js_refund_prompt: "Êtes-vous sûr de vouloir annuler ce retrait et recréditer les SHx sur votre solde Discord ?",
        js_processing: "Traitement du remboursement...", js_refunded: "✅ Remboursé à Discord !", js_check_trustline: "Vérifier la ligne de confiance",
        js_reset_prompt: "Réinitialiser la session ?", js_unlink_prompt: "Délier le portefeuille ?"
      },
      zh: {
        nav_title: "SHx 提示机器人", hero_title: "社区门户", hero_desc: "安全连接您的 Discord 并管理申领。",
        wallet_not_connected: "钱包：未连接", status_checking: "状态：检查中...",
        stat_discord_bal: "Discord 余额", tt_internal_acc: "内部打赏账户", tt_desc: "从钱包将 SHx 移至此处进行打赏：",
        tt_li1: "在 Discord 中输入 <b>/deposit</b>。", tt_li2: "发送带有 Memo ID 的 SHx：", stat_wallet_bal: "钱包余额",
        reset_session: "连接有问题？重置会话", btn_link: "验证并关联钱包", btn_unlink: "取消关联当前钱包",
        pending_withdrawals: "待处理的提款", tickets_desc: "从 Discord 创建的票务。选择一个进行申领。", scanning_tickets: "正在扫描票务...",
        claiming: "正在申领", amount: "金额", btn_claim: "确认并在 Stellar 上申领", btn_cancel: "取消票务并退还至 Discord",
        back_list: "← 返回列表", questions: "有问题？电子邮件：",
        js_guest_mode: "访客模式：在 Discord 中使用 <b>/link</b> 查看您的票务。",
        js_wait_fresh: "正在等待 Discord 的新链接...", js_no_tickets: "未找到待处理的票务。",
        js_ticket: "票务:", js_cancel_refund: "取消并退款", js_select_claim: "选择以申领",
        js_review: "查看详情并在下方确认。", js_verified: "已验证", js_status_linked: "状态：已关联 ✅",
        js_status_not_linked: "状态：未关联钱包", js_switch_wallet: "切换到此钱包",
        js_connect_first: "请先连接钱包。", js_guest_alert: "访客模式：请使用 Discord 中的 /link 命令到达此处验证您的钱包。",
        js_awaiting_sig: "正在等待签名...", js_preparing: "准备申领中...", js_confirming: "确认中...",
        js_success: "✅ 成功！", js_view_explorer: "在浏览器中查看", js_refund_prompt: "您确定要取消此提款并将 SHx 退还至您的 Discord 余额吗？",
        js_processing: "正在处理退款...", js_refunded: "✅ 已退还至 Discord！", js_check_trustline: "检查信任线",
        js_reset_prompt: "重置会话？", js_unlink_prompt: "解除钱包关联？"
      },
      pt: {
        nav_title: "SHx Tip Bot", hero_title: "Portal da Comunidade", hero_desc: "Vincule o Discord com segurança e gerencie resgates.",
        wallet_not_connected: "Carteira: Não Conectada", status_checking: "Status: Verificando...",
        stat_discord_bal: "Saldo Discord", tt_internal_acc: "Conta de Gorjetas Interna", tt_desc: "Mova SHx da sua carteira para cá para dar gorjetas:",
        tt_li1: "Digite <b>/deposit</b> no Discord.", tt_li2: "Envie SHx com o ID do Memo:", stat_wallet_bal: "Saldo da Carteira",
        reset_session: "Problemas de conexão? Redefinir sessão", btn_link: "Verificar e Vincular Carteira", btn_unlink: "Desvincular Carteira Atual",
        pending_withdrawals: "Saques Pendentes", tickets_desc: "Tickets criados no Discord. Selecione um para resgatar.", scanning_tickets: "Analisando tickets...",
        claiming: "Resgatando", amount: "Quantia", btn_claim: "Verificar e Resgatar na Stellar", btn_cancel: "Cancelar Ticket e Reembolsar ao Discord",
        back_list: "← Voltar à Lista", questions: "Dúvidas? E-mail:",
        js_guest_mode: "Modo Visitante: Use <b>/link</b> no Discord para ver seus tickets.",
        js_wait_fresh: "Aguardando um novo link do Discord...", js_no_tickets: "Nenhum ticket pendente encontrado.",
        js_ticket: "Ticket:", js_cancel_refund: "Cancelar e Reembolsar", js_select_claim: "Selecionar para Resgatar",
        js_review: "Revise os detalhes e confirme abaixo.", js_verified: "Verificado", js_status_linked: "Status: Vinculada ✅",
        js_status_not_linked: "Status: Carteira Não Vinculada", js_switch_wallet: "Mudar para esta carteira",
        js_connect_first: "Conecte a carteira primeiro.", js_guest_alert: "Modo Visitante: Use o comando /link do Discord para verificar sua carteira.",
        js_awaiting_sig: "Aguardando assinatura...", js_preparing: "Preparando resgate...", js_confirming: "Confirmando...",
        js_success: "✅ Sucesso!", js_view_explorer: "Ver no Explorer", js_refund_prompt: "Tem certeza de que deseja cancelar este saque e devolver os SHx ao seu saldo do Discord?",
        js_processing: "Processando reembolso...", js_refunded: "✅ Reembolsado ao Discord!", js_check_trustline: "Verifique a Trustline",
        js_reset_prompt: "Redefinir sessão?", js_unlink_prompt: "Desvincular carteira?"
      },
      ru: {
        nav_title: "SHx Tip Bot", hero_title: "Портал Сообщества", hero_desc: "Безопасно привяжите Discord и управляйте выплатами.",
        wallet_not_connected: "Кошелек: Не подключен", status_checking: "Статус: Проверка...",
        stat_discord_bal: "Баланс Discord", tt_internal_acc: "Внутренний счет чаевых", tt_desc: "Переведите SHx из кошелька сюда для чаевых:",
        tt_li1: "Введите <b>/deposit</b> в Discord.", tt_li2: "Отправьте SHx с Memo ID:", stat_wallet_bal: "Баланс кошелька",
        reset_session: "Проблемы с подключением? Сбросить сессию", btn_link: "Проверить и привязать кошелек", btn_unlink: "Отвязать текущий кошелек",
        pending_withdrawals: "Ожидающие выводы", tickets_desc: "Билеты, созданные в Discord. Выберите один для получения.", scanning_tickets: "Сканирование билетов...",
        claiming: "Получение", amount: "Сумма", btn_claim: "Подтвердить и получить в Stellar", btn_cancel: "Отменить билет и вернуть в Discord",
        back_list: "← Назад к списку", questions: "Вопросы? Эл.почта:",
        js_guest_mode: "Гостевой режим: Используйте <b>/link</b> в Discord для просмотра.",
        js_wait_fresh: "Ожидание новой ссылки из Discord...", js_no_tickets: "Ожидающих билетов не найдено.",
        js_ticket: "Билет:", js_cancel_refund: "Отменить и вернуть", js_select_claim: "Выбрать для вывода",
        js_review: "Проверьте детали и подтвердите ниже.", js_verified: "Проверен", js_status_linked: "Статус: Привязан ✅",
        js_status_not_linked: "Статус: Кошелек не привязан", js_switch_wallet: "Переключить на этот кошелек",
        js_connect_first: "Сначала подключите кошелек.", js_guest_alert: "Гостевой режим: Используйте /link в Discord для привязки кошелька.",
        js_awaiting_sig: "Ожидание подписи...", js_preparing: "Подготовка получения...", js_confirming: "Подтверждение...",
        js_success: "✅ Успешно!", js_view_explorer: "Посмотреть в обозревателе", js_refund_prompt: "Вы уверены, что хотите отменить вывод и вернуть SHx на баланс Discord?",
        js_processing: "Обработка возврата...", js_refunded: "✅ Возвращено в Discord!", js_check_trustline: "Проверьте Линию Доверия",
        js_reset_prompt: "Сбросить сессию?", js_unlink_prompt: "Отвязать кошелек?"
      }
    };
    
    let activeLang = localStorage.getItem('shx_lang') || 'en';
    
    const t = (key) => TRANSLATIONS[activeLang][key] || TRANSLATIONS['en'][key];
    
    const applyLanguage = (lang) => {
      activeLang = lang;
      localStorage.setItem('shx_lang', lang);
      document.querySelector('#lang-selector').value = lang;
      document.querySelectorAll('[data-i18n]').forEach(el => {
         const k = el.getAttribute('data-i18n');
         if(TRANSLATIONS[lang] && TRANSLATIONS[lang][k]) {
           el.innerHTML = TRANSLATIONS[lang][k];
         }
      });
      // Handle dynamic JS UI updates after language switch without hard reloading page if possible
      if (document.getElementById('connection-status-badge').innerText.includes('Not Connected')) {
          document.getElementById('connection-status-badge').innerText = t('wallet_not_connected');
      }
      if (document.getElementById('link-status-badge').innerText.includes('Checking') || document.getElementById('link-status-badge').innerText.includes('確認中') || document.getElementById('link-status-badge').innerText.includes('확인 중')) {
          document.getElementById('link-status-badge').innerText = t('status_checking');
      }
      if (userAddress) updateUI(userAddress);
    };

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelector('#lang-selector').addEventListener('change', (e) => applyLanguage(e.target.value));
        applyLanguage(activeLang);
    });

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
        } catch (e) { document.getElementById('external-balance-val').innerText = t('js_check_trustline'); }
    }

    const setStatus = (msg, isError = false) => {
        const el = document.getElementById('link-status-badge');
        if (!el) return;
        el.innerText = "Status: " + msg;
        el.className = `badge text-xs mt-1 ${msg.includes('✅') ? 'badge-success' : 'badge-error'}`;
    };

    const fetchBalance = async () => {
        if (!TOKEN && !CLAIM_ID) {
            document.getElementById('withdrawal-list').innerHTML = `<div class="text-center py-4 text-muted">${t('js_guest_mode')}</div>`;
            return;
        }
        try {
            const res = await axios.get(`${API_BASE}/api/balance?token=${TOKEN}&claim_id=${CLAIM_ID}`);
            if (res.data.success) {
                document.getElementById('internal-balance-val').innerText = res.data.balance;
                if (res.data.pending_withdrawals?.length > 0) renderWithdrawals(res.data.pending_withdrawals);
                else document.getElementById('withdrawal-list').innerHTML = `<div class="text-center py-4 text-muted">${t('js_no_tickets')}</div>`;
                if (userAddress) fetchStellarBalance(userAddress);
            }
        } catch (e) { 
            console.warn("Balance fetch failed:", e); 
            document.getElementById('withdrawal-list').innerHTML = `<div class="text-center py-4 text-muted">${t('js_wait_fresh')}</div>`;
        }
    };

    const renderWithdrawals = (ws) => {
        const el = document.getElementById('withdrawal-list');
        let html = '';
        ws.forEach(w => {
            html += `<div class="bg-dark-overlay mb-2 p-3 rounded-lg border border-opacity-10" style="display:flex; justify-content:space-between; align-items:center;">
              <div><p class="text-bold text-accent">${w.amount} SHx</p><p class="text-xs text-muted">${t('js_ticket')} ...${w.id.slice(-6)}</p><span onclick="handleCancel('${w.id}')" class="text-error text-xs" style="cursor:pointer; text-decoration: underline; margin-top: 4px; display: inline-block;">${t('js_cancel_refund')}</span></div>
              <button onclick="selectTicket('${w.id}', '${w.amount}')" class="btn btn-primary text-xs px-4 py-2">${t('js_select_claim')}</button>
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
        
        notify('claim-notify', t('js_review'));
    };

    const showList = () => {
        document.getElementById('withdrawal-list').classList.remove('hidden');
        document.getElementById('active-claim-view').classList.add('hidden');
        fetchBalance();
    };

    const resetSession = () => { if(confirm(t('js_reset_prompt'))) { localStorage.clear(); location.reload(); } };

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
        hero.innerText = `${t('js_verified')}: ${address.slice(0,6)}...${address.slice(-4)}`;
        hero.className = "badge badge-success mt-4";
        profile.innerText = linked ? t('js_status_linked') : t('js_status_not_linked');
        profile.className = `badge text-xs mt-1 ${linked ? 'badge-success' : 'badge-error'}`;
        fetchStellarBalance(address);
        linkBtn.disabled = linked;
        linkBtn.innerText = linked ? t('js_status_linked').replace("Status: ", "") : (existing && existing.length === 56 ? t('js_switch_wallet') : t('btn_link'));
        document.getElementById('btn-claim-action').disabled = false;
        if(existing && existing.length === 56) document.getElementById('unlink-container').classList.remove('hidden');
      } else {
        hero.innerText = t('wallet_not_connected');
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
            const { StellarWalletsKit, KitEventType, SwkAppDarkTheme, FreighterModule, LobstrModule, xBullModule, WalletConnectModule } = window.StellarKit;
            
            const wcProjectId = "{{WC_PROJECT_ID}}";
            let modules = [
                new FreighterModule(), 
                new LobstrModule({ projectId: wcProjectId }), 
                new xBullModule()
            ];
            if (wcProjectId) {
                modules.push(new WalletConnectModule({
                    projectId: wcProjectId,
                    metadata: {
                        name: "SHx Tip Bot",
                        description: "SHx Community Tipping Dashboard",
                        url: window.location.origin,
                        icons: ["https://cdn.prod.website-files.com/5e9a1cde22bbc0a89dba7f5b/60c9649cf8fb48e5c883950e_Stronghold%20Logo%20Mark%20Blue.png"]
                    }
                }));
            }
            
            StellarWalletsKit.init({ theme: SwkAppDarkTheme, modules: modules, network: NETWORK_PASSPHRASE });
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
        if (!userAddress) return alert(t('js_connect_first'));
        if (!TOKEN) return alert(t('js_guest_alert'));
        try {
            const sdk = getSdk();
            notify('link-notify', t('js_awaiting_sig'));
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
        if (!userAddress) return alert(t('js_connect_first'));
        try {
            const sdk = getSdk();
            notify('claim-notify', t('js_preparing'));
            const res = await axios.get(`${API_BASE}/api/withdrawal/${CLAIM_ID}`);
            const { amount, nonce, expires_at, signature, stellar_address } = res.data;
            
            // STRICT SECURITY ENFORCEMENT: The connected wallet must physically match the destination bound to the cryptic signature.
            if (userAddress !== stellar_address) {
                throw new Error(`Connected wallet mismatch! Please switch to account ending in ...${stellar_address.slice(-4)}`);
            }
            
            const soroban = new (sdk.rpc?.Server || sdk.SorobanServer || sdk.Server)(SOROBAN_URL);
            const account = await (new (sdk.Horizon?.Server || sdk.Server)(HORIZON_URL)).loadAccount(userAddress);
            const uVal = sdk.nativeToScVal(userAddress, { type: 'address' });
            const expVal = sdk.nativeToScVal(BigInt(expires_at || 0), { type: 'u64' });
            const args = [uVal, sdk.nativeToScVal(BigInt(Math.round(amount*10000000)), { type: 'i128' }), sdk.nativeToScVal(BigInt(nonce), { type: 'u64' }), expVal, sdk.nativeToScVal(Uint8Array.from(atob(signature), c => c.charCodeAt(0)), { type: 'bytes' })];
            const tx = new sdk.TransactionBuilder(account, { fee: "100000", networkPassphrase: NETWORK_PASSPHRASE }).addOperation((new sdk.Contract(SOROBAN_CONTRACT_ID)).call("claim_withdrawal", ...args)).setTimeout(300).build();
            const sim = await soroban.simulateTransaction(tx);
            const prepared = await soroban.prepareTransaction(tx, sim);
            const sig = await window.StellarKit.StellarWalletsKit.signTransaction(prepared.toXDR(), { networkPassphrase: NETWORK_PASSPHRASE, address: userAddress, network: NETWORK.toUpperCase() });
            const resp = await soroban.sendTransaction(sdk.TransactionBuilder.fromXDR(sig.signedTxXdr, NETWORK_PASSPHRASE));
            notify('claim-notify', t('js_confirming'));
            let txR = null; let att = 0;
            while(att<15) { txR = await soroban.getTransaction(resp.hash); if(txR.status==="SUCCESS") break; await new Promise(r=>setTimeout(r,2000)); att++; }
            await axios.post(`${API_BASE}/api/withdrawal/${CLAIM_ID}/complete`, { tx_hash: resp.hash });
            const txUrl = `${STELLAR_EXPERT_BASE}/tx/${resp.hash}`;
            notify('claim-notify', `${t('js_success')} <a href="${txUrl}" target="_blank" style="color:var(--accent); text-decoration:underline;">${t('js_view_explorer')}</a>`);
            setTimeout(() => location.reload(), 4500);
        } catch (e) {
            const errorMsg = e.response?.data?.detail || e.message || String(e);
            notify('claim-notify', errorMsg, true);
        }
    }

    async function handleCancel(id) {
        if (!confirm(t('js_refund_prompt'))) return;
        try {
            notify('claim-notify', t('js_processing'));
            const res = await axios.post(`${API_BASE}/api/withdrawal/${id || CLAIM_ID}/cancel`, { token: TOKEN });
            if (res.data.success) { notify('claim-notify', t('js_refunded')); setTimeout(showList, 1500); }
        } catch (e) { notify('claim-notify', e.response?.data?.detail || e.message || String(e), true); }
    }

    window.onload = () => {
        fetchBalance(); 
        const e = "{{EXISTING_KEY_VAL}}";
        if (e && e.length === 56) setStatus(t("js_status_linked").replace("Status: ", ""));
        initKit();
    };
    
    document.getElementById('btn-link').onclick = handleLink;
    document.getElementById('btn-claim-action').onclick = handleClaim;
    const cancelBtn = document.getElementById('btn-claim-cancel');
    if (cancelBtn) cancelBtn.onclick = () => handleCancel();
    
    document.getElementById('btn-unlink-action').onclick = async () => {
        if (confirm(t('js_unlink_prompt'))) { await axios.post(`${API_BASE}/api/unlink`, { token: TOKEN }); localStorage.clear(); location.reload(); }
    };
  </script>
</html>'''
