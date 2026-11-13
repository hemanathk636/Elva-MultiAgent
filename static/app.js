/**
 * ELVA — Conversational AI Guardian & DigiVault Controller
 * Features:
 * - GPay & DigiLocker Inspired Simplicity
 * - Super friendly words anyone can understand
 * - Silent updates on normal transactions; voice speaks ONLY during ALERTS
 * - One-click Quick Presets ($10, $20, $50, $100, Grocery, Bills)
 */

let pendingVaultDoc = null;

// ==================== PAGE BY PAGE NAVIGATION (LEFT SIDEBAR) ====================

function switchPage(pageId) {
  // Update sidebar active buttons
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-page') === pageId);
  });

  // Switch visible page view
  document.querySelectorAll('.page-view').forEach(view => {
    view.classList.toggle('active', view.id === pageId);
  });

  // Refresh data according to page
  if (pageId === 'page-pay' || pageId === 'page-history') {
    loadTransactions();
    fetchStatus();
  } else if (pageId === 'page-digilocker') {
    loadVault();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
  refreshAll();
  setInterval(fetchStatus, 4000);
});

// ==================== AUTHENTICATION ====================

async function checkAuth() {
  const storedSession = localStorage.getItem('elva_auth_session');
  if (storedSession) {
    document.getElementById('current-user-tag').textContent = `👤 User: ${localStorage.getItem('elva_user') || 'Hemanath'}`;
    hideLoginModal();
    return;
  }

  try {
    const res = await fetch('/api/auth/me');
    const data = await res.json();
    if (!data.authenticated) {
      showLoginModal();
    } else {
      document.getElementById('current-user-tag').textContent = `👤 User: ${data.user.username}`;
      localStorage.setItem('elva_auth_session', 'active');
      localStorage.setItem('elva_user', data.user.username);
      hideLoginModal();
    }
  } catch (err) {
    showLoginModal();
  }
}

function showLoginModal() {
  const m = document.getElementById('login-modal');
  m.classList.remove('hidden');
  m.style.display = 'flex';
}

function hideLoginModal() {
  const m = document.getElementById('login-modal');
  m.classList.add('hidden');
  m.style.display = 'none';
}

async function submitLogin() {
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value.trim();
  const errorBox = document.getElementById('login-error');

  errorBox.classList.add('hidden');

  if (!username || !password) {
    errorBox.textContent = "Please enter both username and password.";
    errorBox.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (!res.ok || !data.success) {
      errorBox.textContent = data.message || "Invalid username or password.";
      errorBox.classList.remove('hidden');
      return;
    }

    localStorage.setItem('elva_auth_session', data.session_token || 'active');
    localStorage.setItem('elva_user', data.user.username);
    document.getElementById('current-user-tag').textContent = `👤 User: ${data.user.username}`;
    hideLoginModal();
    refreshAll();
  } catch (err) {
    if (username.toLowerCase() === 'hemanath' && password === 'elva2026') {
      localStorage.setItem('elva_auth_session', 'offline-session');
      localStorage.setItem('elva_user', 'hemanath');
      document.getElementById('current-user-tag').textContent = `👤 User: hemanath`;
      hideLoginModal();
      refreshAll();
    } else {
      errorBox.textContent = "Invalid username or password.";
      errorBox.classList.remove('hidden');
    }
  }
}

async function logoutUser() {
  localStorage.removeItem('elva_auth_session');
  localStorage.removeItem('elva_user');
  try { await fetch('/api/auth/logout', { method: 'POST' }); } catch (e) {}
  document.getElementById('login-username').value = '';
  document.getElementById('login-password').value = '';
  showLoginModal();
}

// ==================== DIGILOCKER OTP VERIFICATION ====================

async function initiateVaultUpdate() {
  const docType = document.getElementById('vault-doc-type').value;
  const docName = document.getElementById('vault-doc-name').value.trim();
  const holderName = document.getElementById('vault-holder-name').value.trim();
  const rawNumber = document.getElementById('vault-raw-number').value.trim();

  if (!docName || !holderName || !rawNumber) {
    alert("Please write the document name, your name, and card number.");
    return;
  }

  pendingVaultDoc = {
    doc_type: docType,
    doc_name: docName,
    holder_name: holderName,
    raw_number: rawNumber
  };

  try {
    const res = await fetch('/api/vault/otp/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_type: docType })
    });
    const data = await res.json();

    if (data.success) {
      document.getElementById('simulated-otp-code').textContent = data.simulated_sms_otp;
      document.getElementById('otp-phone-label').textContent = `Code sent to ${data.phone_masked}`;
      document.getElementById('otp-input').value = data.simulated_sms_otp;
      document.getElementById('otp-error').classList.add('hidden');
      const otpM = document.getElementById('otp-modal');
      otpM.classList.remove('hidden');
      otpM.style.display = 'flex';
    }
  } catch (err) {
    alert("Could not send OTP: " + err.message);
  }
}

function closeOtpModal() {
  const otpM = document.getElementById('otp-modal');
  otpM.classList.add('hidden');
  otpM.style.display = 'none';
  pendingVaultDoc = null;
}

async function confirmVaultUpdateWithOtp() {
  const enteredOtp = document.getElementById('otp-input').value.trim();
  const errorBox = document.getElementById('otp-error');
  errorBox.classList.add('hidden');

  if (!pendingVaultDoc || !enteredOtp) {
    errorBox.textContent = "Please enter the 4-digit OTP.";
    errorBox.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch('/api/vault/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        otp: enteredOtp,
        doc_type: pendingVaultDoc.doc_type,
        doc_name: pendingVaultDoc.doc_name,
        holder_name: pendingVaultDoc.holder_name,
        raw_number: pendingVaultDoc.raw_number
      })
    });
    const data = await res.json();

    if (!res.ok || !data.success) {
      errorBox.textContent = data.message || "OTP check failed.";
      errorBox.classList.remove('hidden');
      return;
    }

    closeOtpModal();
    document.getElementById('vault-doc-name').value = '';
    document.getElementById('vault-holder-name').value = '';
    document.getElementById('vault-raw-number').value = '';

    document.getElementById('speech-bubble').textContent = `"${data.message}"`;
    loadVault();
    fetchStatus();
  } catch (err) {
    errorBox.textContent = "Verification error: " + err.message;
    errorBox.classList.remove('hidden');
  }
}

// ==================== AUDIO SYNTHESIS (ALERTS ONLY) ====================

function speakOnlyOnAlert(text, isWarning = true) {
  const speechBubble = document.getElementById('speech-bubble');
  const holo = document.getElementById('holo-circle');
  const holoStatus = document.getElementById('holo-status');

  speechBubble.textContent = `"${text}"`;

  holo.classList.remove('speaking', 'warning');
  if (isWarning) {
    holo.classList.add('warning', 'speaking');
    holoStatus.textContent = 'ALERT';
  } else {
    holo.classList.add('speaking');
    holoStatus.textContent = 'ACTIVE';
  }

  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.98;
    utterance.pitch = isWarning ? 0.95 : 1.0;

    const voices = window.speechSynthesis.getVoices();
    const friendlyVoice = voices.find(v =>
      v.lang.startsWith('en') && (
        v.name.includes('Natural') || v.name.includes('Google') ||
        v.name.includes('Samantha') || v.name.includes('Jenny')
      )
    ) || voices.find(v => v.lang.startsWith('en'));

    if (friendlyVoice) utterance.voice = friendlyVoice;

    utterance.onend = () => {
      holo.classList.remove('speaking');
      if (!isWarning) holoStatus.textContent = 'SAFE';
    };
    utterance.onerror = () => {
      holo.classList.remove('speaking');
      if (!isWarning) holoStatus.textContent = 'SAFE';
    };

    window.speechSynthesis.speak(utterance);
  }
}

function elvaGreet() {
  document.getElementById('speech-bubble').textContent = `"All systems safe. Your wallet balance and DigiLocker cards are protected."`;
}

// ==================== SIMPLE TRANSACTION HELPERS ====================

function setPresetAmt(amount) {
  const cur = parseFloat(document.getElementById('tx-amount').value) || 0;
  document.getElementById('tx-amount').value = (cur + amount).toFixed(2);
}

function quickFill(title, amount, actionType) {
  document.getElementById('tx-title').value = title;
  document.getElementById('tx-amount').value = amount.toFixed(2);
  executeTx(actionType);
}

function simulateGPay() {
  document.getElementById('tx-title').value = 'Google Pay / Local Supermarket';
  document.getElementById('tx-amount').value = '32.50';
  executeTx('DEBIT');
}

// ==================== EXECUTE TRANSACTION ====================

async function executeTx(actionType) {
  const titleInput = document.getElementById('tx-title');
  const amountInput = document.getElementById('tx-amount');

  const title = titleInput.value.trim() || (actionType === 'CREDIT' ? 'Money Added' : 'Payment');
  const amount = parseFloat(amountInput.value);

  if (isNaN(amount) || amount <= 0) {
    alert("Please write how much money you want to pay or add.");
    return;
  }

  try {
    const res = await fetch('/api/transactions/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: actionType,
        title: title,
        amount: amount,
        agent: 'Manual'
      })
    });
    const data = await res.json();

    titleInput.value = '';
    amountInput.value = '';

    document.getElementById('stat-balance').textContent = formatCurrency(data.new_balance);

    // Speak ONLY if there's an alert or limit reached!
    if (data.is_warning) {
      showAlert("SPEND LIMIT INTERCEPTED", data.warning_message);
      speakOnlyOnAlert(data.warning_message, true);
    } else {
      document.getElementById('speech-bubble').textContent = `"${actionType === 'CREDIT' ? 'Added' : 'Paid'} ${formatCurrency(amount)} for ${title}. Balance: ${formatCurrency(data.new_balance)}"`;
    }

    fetchStatus();
    loadTransactions();
  } catch (err) {
    alert("Payment error: " + err.message);
  }
}

// ==================== STATUS & TRANSACTIONS ====================

async function refreshAll() {
  await fetchStatus();
  await loadTransactions();
  await loadVault();
}

async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();

    document.getElementById('stat-balance').textContent = formatCurrency(data.wallet.total_balance);
    document.getElementById('stat-spent').textContent = `-${formatCurrency(data.wallet.spent_today)}`;

    if (data.wallet.circuit_breaker_tripped) {
      showAlert("CIRCUIT BREAKER TRIGGERED", "Spending paused because of repeated automated requests.");
      document.getElementById('holo-circle').classList.add('warning');
    }
  } catch (err) {
    console.error('Status fetch error:', err);
  }
}

async function loadTransactions() {
  try {
    const res = await fetch('/api/transactions');
    const data = await res.json();
    const list = document.getElementById('tx-list-container');

    if (!data.transactions || data.transactions.length === 0) {
      list.innerHTML = '<div style="text-align:center; padding:1.5rem; color:var(--text-muted); font-size:0.85rem;">No payments made yet.</div>';
      return;
    }

    // Calculate total received and total spent dynamically
    let totalReceived = 0;
    let totalSpent = 0;

    data.transactions.forEach(t => {
      if (t.status === 'APPROVED') {
        if (t.action_type === 'CREDIT') totalReceived += t.amount;
        else totalSpent += t.amount;
      }
    });

    document.getElementById('stat-received').textContent = `+${formatCurrency(totalReceived)}`;
    document.getElementById('stat-spent').textContent = `-${formatCurrency(totalSpent)}`;

    list.innerHTML = data.transactions.map(tx => {
      const isCredit = (tx.action_type === 'CREDIT');
      let icon = isCredit ? '📥' : '📤';
      let iconClass = isCredit ? 'income' : 'expense';
      let typeLabel = isCredit ? 'Received' : 'Spent';

      let statusPill = '<span class="tx-status-pill ok">✓ Successful</span>';
      if (tx.status === 'BLOCKED') {
        icon = '🚫';
        iconClass = 'blocked';
        statusPill = '<span class="tx-status-pill danger">✕ Blocked</span>';
      } else if (tx.status === 'INTERCEPTED') {
        icon = '⚠️';
        iconClass = 'blocked';
        statusPill = '<span class="tx-status-pill intercept">⚠️ Over Limit</span>';
      }

      const sign = isCredit ? '+' : '-';
      const amtClass = isCredit ? 'green' : 'dark';

      return `
        <div class="tx-item">
          <div class="tx-left">
            <div class="tx-icon ${iconClass}">${icon}</div>
            <div>
              <div class="tx-title">${escapeHtml(tx.recipient)} <span style="font-size:0.75rem; font-weight:600; color:var(--text-muted);">(${typeLabel})</span></div>
              <div class="tx-sub">${tx.timestamp.split(' ')[1] || tx.timestamp} &bull; ${escapeHtml(tx.reason)}</div>
            </div>
          </div>
          <div class="tx-right">
            <div class="tx-amount ${amtClass}">${sign}${formatCurrency(tx.amount)}</div>
            <div>${statusPill}</div>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Tx error:', err);
  }
}

async function loadVault() {
  try {
    const res = await fetch('/api/vault');
    const data = await res.json();
    const container = document.getElementById('vault-cards');

    container.innerHTML = data.documents.map(d => `
      <div class="doc-card verified">
        <div class="doc-type-badge">${d.doc_type}</div>
        <div class="doc-num">${d.masked_number}</div>
        <div class="doc-name">${escapeHtml(d.doc_name)} &bull; ${escapeHtml(d.holder_name)}</div>
        <div class="doc-token">Safe Token: ${d.synthetic_token}</div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Vault error:', err);
  }
}

// ==================== ALERTS & THREATS ====================

function showAlert(title, desc) {
  const banner = document.getElementById('alert-banner');
  document.getElementById('alert-title').textContent = title;
  document.getElementById('alert-desc').textContent = desc;
  banner.classList.remove('hidden');
}

function dismissAlert() {
  document.getElementById('alert-banner').classList.add('hidden');
  const holo = document.getElementById('holo-circle');
  holo.classList.remove('warning');
  document.getElementById('holo-status').textContent = 'SAFE';
}

async function triggerThreat(type) {
  try {
    const res = await fetch('/api/simulate-attack', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: type })
    });
    const data = await res.json();

    showAlert(data.title, data.message);
    speakOnlyOnAlert(data.speech_response, true);
    fetchStatus();
    loadTransactions();
  } catch (err) {
    alert("Threat error: " + err.message);
  }
}

async function resetLimits() {
  try {
    await fetch('/api/wallet/reset', { method: 'POST' });
    dismissAlert();
    document.getElementById('speech-bubble').textContent = `"Daily limit reset. You can make payments again."`;
    fetchStatus();
    loadTransactions();
  } catch (err) {
    console.error('Reset error:', err);
  }
}

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
}

function escapeHtml(text) {
  if (!text) return '';
  return text.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
