const tabs = document.querySelectorAll('.mode-tabs button');
const panels = document.querySelectorAll('.panel');
const errorEl = document.getElementById('error');
const metaEl = document.getElementById('result-meta');
const tbody = document.querySelector('#results tbody');
const themeToggle = document.getElementById('theme-toggle');
const clearBtn = document.getElementById('clear-results');
const resultsTable = document.getElementById('results');

const resultsBar = document.querySelector('.results-bar');
const tableWrap = document.querySelector('.table-wrap');

const MAX_ROWS = 500;
const EMPTY_ROW = '<tr class="empty-row"><td colspan="9"><i data-lucide="inbox"></i>No results yet — run a calculation.</td></tr>';

// ---- Per-mode state: each calculator keeps its own table + meta + error ----
const MODES = ['flsm', 'vlsm', 'ipv6', 'nth'];
let activeMode = 'flsm';
const modeResults = {
  flsm: { rows: [], label: '' },
  vlsm: { rows: [], label: '' },
  ipv6: { rows: [], label: '' },
};
const modeErrors = { flsm: '', vlsm: '', ipv6: '', nth: '' };

function fmtCount(n) {
  return Number(n).toLocaleString('en-US');
}

function refreshIcons() {
  if (window.lucide) window.lucide.createIcons();
}

// ---- Theme (dark default, persisted) ----
function applyTheme(theme) {
  const next = theme === 'light' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  const toLight = next === 'dark';
  themeToggle.innerHTML = `<i data-lucide="${toLight ? 'sun' : 'moon'}"></i><span>${toLight ? 'Light' : 'Dark'}</span>`;
  themeToggle.setAttribute('aria-label', toLight ? 'Switch to light mode' : 'Switch to dark mode');
  try {
    localStorage.setItem('subnet-theme', next);
  } catch (e) {
    // Private mode etc: theme still applies for this session.
  }
  refreshIcons();
}

function initTheme() {
  let stored = 'dark';
  try {
    stored = localStorage.getItem('subnet-theme') || 'dark';
  } catch (e) {
    stored = 'dark';
  }
  applyTheme(stored);
}

themeToggle.addEventListener('click', () => {
  applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
});

// ---- Tabs ----
function clearResults() {
  if (activeMode === 'nth') {
    const resultEl = document.getElementById('nth-result');
    resultEl.hidden = true;
    resultEl.innerHTML = '';
    modeErrors.nth = '';
    showError('');
    clearBtn.disabled = true;
    refreshIcons();
    return;
  }
  modeResults[activeMode] = { rows: [], label: '' };
  modeErrors[activeMode] = '';
  paintTable([], '');
  showError('');
  clearBtn.disabled = true;
  refreshIcons();
}

clearBtn.addEventListener('click', clearResults);

function restoreMode(mode) {
  if (!MODES.includes(mode)) mode = 'flsm';
  activeMode = mode;
  tabs.forEach((b) => b.classList.toggle('active', b.dataset.mode === mode));
  panels.forEach((p) => p.classList.toggle('active', p.id === `panel-${mode}`));
  // Nth IP uses its own inline answer, not the shared table.
  const isNth = mode === 'nth';
  if (resultsBar) resultsBar.hidden = isNth;
  if (tableWrap) tableWrap.hidden = isNth;
  if (!isNth) {
    const state = modeResults[mode];
    paintTable(state.rows, state.label);
    clearBtn.disabled = state.rows.length === 0;
  } else {
    clearBtn.disabled = document.getElementById('nth-result').hidden;
  }
  const err = modeErrors[mode] || '';
  errorEl.innerHTML = err ? '<i data-lucide="circle-alert"></i>' : '';
  errorEl.append(err || '');
  refreshIcons();
}

tabs.forEach((btn) => {
  btn.addEventListener('click', () => restoreMode(btn.dataset.mode));
});

// ---- Results ----
function showError(msg) {
  modeErrors[activeMode] = msg || '';
  errorEl.innerHTML = msg ? '<i data-lucide="circle-alert"></i>' : '';
  errorEl.append(msg || '');
  refreshIcons();
}

function setMeta(msg) {
  metaEl.textContent = msg || '';
}

function setBusy(btn, busy, idleLabel) {
  btn.disabled = busy;
  btn.innerHTML = busy
    ? '<i data-lucide="loader-circle"></i>Working…'
    : `<i data-lucide="${btn.dataset.icon || 'calculator'}"></i>${idleLabel}`;
  refreshIcons();
}

function renderTable(mode, subnets, label) {
  modeResults[mode] = { rows: subnets || [], label: label || '' };
  if (mode !== activeMode) return;
  paintTable(modeResults[mode].rows, modeResults[mode].label);
}

function paintTable(subnets, label) {
  tbody.innerHTML = '';
  const rows = subnets || [];
  const isV6 = rows.length > 0 && rows.every((s) => !s.subnet_mask && !s.broadcast_address);
  resultsTable.classList.toggle('ipv6', isV6);
  if (!rows.length) {
    tbody.innerHTML = EMPTY_ROW;
    setMeta('');
    clearBtn.disabled = true;
    refreshIcons();
    return;
  }
  const total = rows.length;
  const shown = rows.slice(0, MAX_ROWS);
  const noun = total === 1 ? 'subnet' : 'subnets';
  setMeta(
    total > MAX_ROWS
      ? `${label} — showing first ${fmtCount(MAX_ROWS)} of ${fmtCount(total)} ${noun} — narrow the prefix range`
      : `${label} — ${fmtCount(total)} ${noun}`
  );
  clearBtn.disabled = false;
  for (const s of shown) {
    const tr = document.createElement('tr');
    const cidr = `${s.network_address}/${s.prefix_length}`;
    const cells = [
      { value: s.name || '', addr: false },
      { value: s.network_address, addr: true },
      { value: `/${s.prefix_length}`, addr: false },
      { value: s.subnet_mask || '-', addr: false },
      { value: s.first_usable || '-', addr: true },
      { value: s.last_usable || '-', addr: true },
      { value: s.broadcast_address || '-', addr: false },
      { value: fmtCount(s.usable_count), addr: false },
    ];
    for (const c of cells) {
      const td = document.createElement('td');
      td.textContent = String(c.value);
      if (c.addr) {
        td.className = 'addr';
        td.title = String(c.value);
      }
      tr.appendChild(td);
    }
    const actionTd = document.createElement('td');
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.title = `Copy ${cidr}`;
    copyBtn.setAttribute('aria-label', `Copy ${cidr}`);
    copyBtn.innerHTML = '<i data-lucide="copy"></i>';
    copyBtn.addEventListener('click', () => copyText(cidr, copyBtn));
    actionTd.appendChild(copyBtn);
    tr.appendChild(actionTd);
    tbody.appendChild(tr);
  }
  refreshIcons();
}

async function copyText(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
  } catch (e) {
    // Fallback for environments without async clipboard.
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
    } catch (ignored) {
      showError(`Copy failed — select manually: ${text}`);
      ta.remove();
      return;
    }
    ta.remove();
  }
  if (btn) {
    btn.innerHTML = '<i data-lucide="check"></i>';
    refreshIcons();
    setTimeout(() => {
      btn.innerHTML = '<i data-lucide="copy"></i>';
      refreshIcons();
    }, 1200);
  }
}

async function callBackend(payload) {
  showError('');
  try {
    const res = await window.subnetApi.request(payload);
    if (!res.ok) {
      showError(res.error);
      return null;
    }
    return res;
  } catch (err) {
    showError(`Backend unreachable: ${err.message}`);
    return null;
  }
}

async function runWithButton(btn, idleLabel, fn) {
  setBusy(btn, true);
  try {
    await fn();
  } finally {
    setBusy(btn, false, idleLabel);
  }
}

// ---- FLSM ----
const flsmBtn = document.getElementById('flsm-go');
flsmBtn.dataset.icon = 'calculator';
flsmBtn.addEventListener('click', () => runWithButton(flsmBtn, 'Calculate', async () => {
  const network = document.getElementById('flsm-network').value.trim();
  const prefixRaw = document.getElementById('flsm-prefix').value;
  const countRaw = document.getElementById('flsm-count').value.trim();
  if (!network) {
    showError('Network CIDR is required.');
    return;
  }
  let payload;
  if (countRaw) {
    payload = { action: 'flsm', network, subnet_count: Number(countRaw) };
  } else {
    payload = { action: 'flsm', network, new_prefix: Number(prefixRaw) };
  }
  const res = await callBackend(payload);
  if (res) renderTable('flsm', res.subnets, `FLSM from ${network}`);
}));

// ---- VLSM ----
const vlsmBtn = document.getElementById('vlsm-go');
vlsmBtn.dataset.icon = 'play';
vlsmBtn.addEventListener('click', () => runWithButton(vlsmBtn, 'Allocate', async () => {
  const network = document.getElementById('vlsm-network').value.trim();
  if (!network) {
    showError('Base network is required.');
    return;
  }
  const raw = document.getElementById('vlsm-reqs').value;
  const requirements = raw
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [name, hosts] = line.split(':').map((p) => p.trim());
      return { name: name || 'Net', hosts_needed: Number(hosts) };
    });
  if (!requirements.length) {
    showError('Add at least one requirement as name:hosts.');
    return;
  }
  const res = await callBackend({ action: 'vlsm', network, requirements });
  if (res) renderTable('vlsm', res.subnets, `VLSM from ${network}`);
}));

// ---- IPv6 ----
const ipv6Btn = document.getElementById('ipv6-go');
ipv6Btn.dataset.icon = 'calculator';
ipv6Btn.addEventListener('click', () => runWithButton(ipv6Btn, 'Calculate', async () => {
  const network = document.getElementById('ipv6-network').value.trim();
  if (!network) {
    showError('IPv6 network is required.');
    return;
  }
  const new_prefix = Number(document.getElementById('ipv6-prefix').value);
  const res = await callBackend({ action: 'ipv6', network, new_prefix });
  if (res) renderTable('ipv6', res.subnets, `IPv6 from ${network}`);
}));

// ---- Nth IP ----
const nthBtn = document.getElementById('nth-go');
nthBtn.dataset.icon = 'search';
nthBtn.addEventListener('click', () => runWithButton(nthBtn, 'Find IP', async () => {
  const network = document.getElementById('nth-network').value.trim();
  const n = Number(document.getElementById('nth-n').value);
  const resultEl = document.getElementById('nth-result');
  resultEl.hidden = true;
  if (!network) {
    showError('Subnet CIDR is required.');
    return;
  }
  if (!Number.isInteger(n) || n < 1) {
    showError('Position n must be a positive integer.');
    return;
  }
  const res = await callBackend({ action: 'nth', network, n });
  if (res) {
    resultEl.innerHTML = '';
    const icon = document.createElement('i');
    icon.setAttribute('data-lucide', 'check');
    resultEl.append(icon, `#${n} usable IP: ${res.ip}`);
    resultEl.hidden = false;
    refreshIcons();
  }
}));

// Enter key submits the visible panel.
document.querySelectorAll('.panel').forEach((panel) => {
  panel.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.matches('input')) {
      panel.querySelector('button').click();
    }
  });
});

// ---- Boot ----
initTheme();
restoreMode('flsm');
refreshIcons();
