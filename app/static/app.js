/* Mailroom operator UI. Zero dependencies, zero build step. */

const API = "/api";

const PAGES = {
  overview: {
    title: "Overview",
    sub: "One control room for approvals, inbox rotation and delivery.",
    icon: "overview",
  },
  approvals: {
    title: "Approvals",
    sub: "Every email waits for your decision. Nothing sends without an approve.",
    icon: "approvals",
  },
  campaigns: {
    title: "Campaigns",
    sub: "Separate lead pools, separate schedules, one operating system.",
    icon: "campaigns",
  },
  leads: {
    title: "Leads",
    sub: "The single sheet. Filter by campaign, status or search.",
    icon: "leads",
  },
  suppression: {
    title: "Suppression",
    sub: "Permanent stop addresses. Checked before queueing and before send.",
    icon: "shield",
  },
  inboxes: {
    title: "Inboxes & domains",
    sub: "Connect domains and mailboxes. Rotation spreads volume across the pool.",
    icon: "inboxes",
  },
  deliverability: {
    title: "Deliverability",
    sub: "Volume, caps and DNS checks. No reputation scoring in this phase.",
    icon: "deliverability",
  },
  warmup: {
    title: "Warmup",
    sub: "Closed-pool warmup across your own domains. Cross-domain only, slow ramp.",
    icon: "target",
  },
  queue: {
    title: "Send queue",
    sub: "Coordinated sends, spaced by mailbox and domain.",
    icon: "queue",
  },
  activity: {
    title: "Activity",
    sub: "Every approval, queue move and send is recorded.",
    icon: "activity",
  },
  sheets: {
    title: "Google Sheets",
    sub: "Two-way sync for leads and campaigns, with conflict detection.",
    icon: "layers",
  },
  settings: {
    title: "Settings",
    sub: "Sender identity, safety switches and the agent hook.",
    icon: "settings",
  },
};

const NAV_GROUPS = [
  {
    label: "Workspace",
    items: [
      ["overview", "Overview", "overview"],
      ["approvals", "Approvals", "approvals"],
      ["campaigns", "Campaigns", "campaigns"],
      ["leads", "Leads", "leads"],
      ["suppression", "Suppression", "shield"],
    ],
  },
  {
    label: "Sending",
    items: [
      ["inboxes", "Inboxes & domains", "inboxes"],
      ["deliverability", "Deliverability", "deliverability"],
      ["warmup", "Warmup", "target"],
      ["queue", "Send queue", "queue"],
    ],
  },
  {
    label: "System",
    items: [
      ["activity", "Activity", "activity"],
      ["sheets", "Google Sheets", "layers"],
      ["settings", "Settings", "settings"],
    ],
  },
];

const ICONS = {
  overview: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  approvals: '<path d="M4 5.5h16v13H4z"/><path d="M4 7l8 6 8-6"/><path d="m14.5 16.5 1.8 1.8 3.2-3.6"/>',
  campaigns: '<path d="M4 11v2a1 1 0 0 0 1 1h2l4 3V7L7 10H5a1 1 0 0 0-1 1Z"/><path d="M14 9a3 3 0 0 1 0 6"/><path d="M17 7a6 6 0 0 1 0 10"/>',
  leads: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  inboxes: '<rect x="3" y="4" width="18" height="6" rx="2"/><rect x="3" y="14" width="18" height="6" rx="2"/><path d="M7 7h.01M7 17h.01"/>',
  deliverability: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
  queue: '<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4Z"/>',
  activity: '<path d="M3 12h4l2 7 4-14 2 7h6"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2 2-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V20h-3v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1-2-2 .1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H4v-3h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1 2-2 .1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5V4h3v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1 2 2-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.5 1H20v3h-.2a1.7 1.7 0 0 0-1.5 1Z"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  x: '<path d="m6 6 12 12M18 6 6 18"/>',
  chevron: '<path d="m6 9 6 6 6-6"/>',
  arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  refresh: '<path d="M20 11a8 8 0 0 0-14.8-4L3 9"/><path d="M3 4v5h5"/><path d="M4 13a8 8 0 0 0 14.8 4L21 15"/><path d="M21 20v-5h-5"/>',
  download: '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
  upload: '<path d="M12 21V9"/><path d="m7 14 5-5 5 5"/><path d="M5 3h14"/>',
  play: '<path d="m7 4 13 8-13 8V4Z"/>',
  pause: '<path d="M8 5v14M16 5v14"/>',
  trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 15H6L5 6"/><path d="M10 11v6M14 11v6"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/>',
  alert: '<path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.6 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0Z"/>',
  checkCircle: '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  zap: '<path d="m13 2-9 12h7l-1 8 9-12h-7l1-8Z"/>',
  layers: '<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
  send: '<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4Z"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 4.6 1.4c-.6.8-1.6 1.2-1.6 2.4"/><path d="M12 17h.01"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
};

const STATUS = {
  new: ["New", "gray"],
  drafted: ["Drafted", "gray"],
  pending_approval: ["Awaiting approval", "amber"],
  approved: ["Approved", "violet"],
  queued: ["Queued", "blue"],
  sending: ["Sending", "blue"],
  sent: ["Sent", "green"],
  denied: ["Denied", "red"],
  failed: ["Failed", "red"],
  replied: ["Replied", "green"],
  bounced: ["Bounced", "red"],
  suppressed: ["Suppressed", "gray"],
  pending: ["Pending", "amber"],
  leased: ["Sending", "blue"],
  cancelled: ["Cancelled", "gray"],
  off: ["Off", "gray"],
  ramping: ["Ramping", "violet"],
  active: ["Active", "green"],
  paused: ["Paused", "amber"],
};

const ACTIVITY_META = {
  message_sent: ["Message sent", "green"],
  draft_approved: ["Draft approved", "violet"],
  draft_denied: ["Draft denied", "red"],
  draft_queued: ["Draft queued", "blue"],
  draft_edited: ["Draft edited", "amber"],
  draft_agent_generated: ["Agent draft generated", "violet"],
  draft_regenerated: ["Draft regenerated", "gray"],
  leads_imported: ["Leads imported", "green"],
  drafts_generated: ["Drafts generated", "violet"],
  campaign_created: ["Campaign created", "violet"],
  campaign_updated: ["Campaign updated", "gray"],
  mailbox_created: ["Mailbox added", "violet"],
  mailbox_updated: ["Mailbox updated", "gray"],
  mailbox_tested: ["Mailbox tested", "blue"],
  mailbox_paused: ["Mailbox paused", "amber"],
  mailbox_resumed: ["Mailbox resumed", "green"],
  domain_created: ["Domain added", "violet"],
  domain_updated: ["Domain updated", "gray"],
  dns_checked: ["DNS checked", "blue"],
  queue_cancelled: ["Queue cancelled", "amber"],
  queue_send_now: ["Send now requested", "blue"],
  send_retry: ["Send retry", "amber"],
  send_failed: ["Send failed", "red"],
  settings_updated: ["Settings updated", "gray"],
  suppression_added: ["Suppression added", "red"],
  suppression_removed: ["Suppression removed", "amber"],
  google_sheets_configured: ["Google Sheets configured", "violet"],
  warmup_thread_created: ["Warmup thread created", "violet"],
  warmup_message_sent: ["Warmup message sent", "violet"],
  warmup_opened: ["Warmup opened", "blue"],
  warmup_replied: ["Warmup replied", "green"],
  warmup_task_retry: ["Warmup retry", "amber"],
  warmup_task_failed: ["Warmup failed", "red"],
  warmup_started: ["Warmup started", "violet"],
  warmup_paused: ["Warmup paused", "amber"],
  warmup_resumed: ["Warmup resumed", "green"],
  warmup_stopped: ["Warmup stopped", "gray"],
  warmup_off: ["Warmup off", "gray"],
  warmup_ramping: ["Warmup ramping", "violet"],
  warmup_active: ["Warmup active", "green"],
  warmup_settings_updated: ["Warmup settings updated", "gray"],
  demo_seeded: ["Demo seeded", "violet"],
};

const state = {
  page: "overview",
  campaigns: [],
  campaignId: null,
  overview: null,
  approvals: { items: [], total: 0, pools: {} },
  approvalQuery: "",
  approvalRequest: 0,
  selectedApproval: null,
  approvalChecked: new Set(),
  approvalBusy: false,
  leadDraft: null,
  leads: { items: [], total: 0, page: 1, page_size: 50, pages: 1 },
  leadRequest: 0,
  leadFilters: { q: "", status: "", page: 1, pageSize: 50 },
  inboxes: [],
  domains: [],
  deliverability: null,
  warmup: null,
  queue: null,
  activity: [],
  sheets: null,
  settings: {},
  renderToken: 0,
};

/* ----------------------------- utilities ----------------------------- */

function $(selector, root = document) {
  return root.querySelector(selector);
}

function $$(selector, root = document) {
  return Array.from(root.querySelectorAll(selector));
}

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function safeHref(value) {
  try {
    const url = new URL(value, location.origin);
    return ["http:", "https:"].includes(url.protocol) ? value : "";
  } catch {
    return "";
  }
}

function icon(name, size = 18) {
  const path = ICONS[name] || ICONS.overview;
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${path}</svg>`;
}

function initials(name) {
  const parts = String(name || "?")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function avatarTone(name) {
  const tones = ["", "green", "amber", "blue", "red"];
  let hash = 0;
  for (const char of String(name || "")) hash = (hash * 31 + char.charCodeAt(0)) % 997;
  return tones[hash % tones.length];
}

function fmtNumber(value) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

function fmtDate(value, withYear = false) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    ...(withYear ? { year: "numeric" } : {}),
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function fmtTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("en-US", { hour: "2-digit", minute: "2-digit" }).format(date);
}

function fmtRelative(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  const abs = Math.abs(seconds);
  const units = [
    [60, "second"],
    [60, "minute"],
    [24, "hour"],
    [7, "day"],
  ];
  let amount = seconds;
  let unit = "second";
  for (const [size, name] of units) {
    if (Math.abs(amount) < size) {
      unit = name;
      break;
    }
    amount = Math.round(amount / size);
    unit = name === "second" ? "minute" : name === "minute" ? "hour" : name === "hour" ? "day" : "week";
  }
  const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  return formatter.format(amount, unit);
}

function todayLabel(dateValue) {
  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) return dateValue || "";
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(date);
}

function statusChip(status) {
  const meta = STATUS[status] || [status || "Unknown", "gray"];
  return `<span class="chip ${meta[1]}"><span class="dot"></span>${esc(meta[0])}</span>`;
}

function transportChip(transport) {
  if (transport === "smtp") return '<span class="chip blue">SMTP</span>';
  if (transport === "gas") return '<span class="chip violet">Apps Script</span>';
  return '<span class="chip green">Mock</span>';
}

function dnsChip(label, status) {
  const safe = ["pass", "missing", "error"].includes(status) ? status : "";
  return `<span class="dns-pill ${safe}">${esc(label)} ${esc(status === "pass" ? "PASS" : status === "missing" ? "MISS" : status === "error" ? "ERR" : "?")}</span>`;
}

function campaignName(id) {
  const campaign = state.campaigns.find((item) => Number(item.id) === Number(id));
  return campaign ? campaign.name : "Campaign";
}

function campaignOptions(selected = "") {
  return [
    '<option value="">All campaigns</option>',
    ...state.campaigns.map(
      (campaign) =>
        `<option value="${campaign.id}" ${String(selected) === String(campaign.id) ? "selected" : ""}>${esc(campaign.name)}</option>`,
    ),
  ].join("");
}

function debounce(fn, delay = 280) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

async function api(path, options = {}) {
  const response = await fetch(API + path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (response.status === 204) return null;
  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }
  if (!response.ok) {
    const detail = data?.detail || data?.error || response.statusText || "Request failed";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function toast(message, type = "success") {
  const wrap = $("#toast-wrap");
  if (!wrap) return;
  const node = document.createElement("div");
  node.className = `toast ${type}`;
  node.innerHTML = `${icon(type === "error" ? "alert" : "checkCircle", 17)}<span>${esc(message)}</span><button class="close" aria-label="Dismiss">${icon("x", 14)}</button>`;
  node.querySelector(".close").addEventListener("click", () => node.remove());
  wrap.appendChild(node);
  setTimeout(() => node.remove(), 4800);
}

function emptyState(title, sub, iconName = "inbox") {
  return `<div class="empty"><div class="empty-icon">${icon(iconName, 20)}</div><div class="empty-title">${esc(title)}</div><div class="empty-sub">${esc(sub)}</div></div>`;
}

function progress(value, cap, tone = "") {
  const percent = cap ? Math.min(100, Math.round((Number(value) / Number(cap)) * 100)) : 0;
  return `<div class="progress ${tone}" title="${percent}% of ${esc(cap)}"><span style="width:${percent}%"></span></div>`;
}

function activityMeta(kind) {
  return ACTIVITY_META[kind] || [String(kind || "Event").replaceAll("_", " "), "gray"];
}

function activityDetail(item) {
  try {
    const data = JSON.parse(item.detail || "{}");
    if (data.from && data.to) return `${data.from} → ${data.to}`;
    return (
      data.email ||
      data.mailbox ||
      data.name ||
      data.reason ||
      data.source ||
      (data.count ? `${data.count} record(s)` : "") ||
      Object.entries(data)
        .slice(0, 2)
        .map(([key, value]) => `${key}: ${value}`)
        .join(" · ")
    );
  } catch {
    return item.detail || "";
  }
}

/* ----------------------------- shell ----------------------------- */

async function loadCampaigns() {
  const data = await api("/campaigns");
  state.campaigns = data.items || [];
  if (state.campaignId && !state.campaigns.some((item) => Number(item.id) === Number(state.campaignId))) {
    state.campaignId = null;
  }
}

function campaignSelectValue() {
  return state.campaignId ? String(state.campaignId) : "";
}

function renderCampaignOptions() {
  const select = $("#campaign-select");
  if (!select) return;
  select.innerHTML = campaignOptions(campaignSelectValue());
  select.value = campaignSelectValue();
}

function renderShell() {
  const app = $("#app");
  app.className = "";
  app.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand">
          <div class="brand-mark">${icon("mail", 17)}</div>
          <div><div class="brand-name">Mailroom</div><div class="brand-sub">Outbound control room</div></div>
        </div>
        <div class="workspace">
          <div class="workspace-avatar">DY</div>
          <div><div class="workspace-name">Dynamisers</div><div class="workspace-plan">Local workspace</div></div>
          <span class="chev">${icon("chevron", 13)}</span>
        </div>
        <div class="campaign-select-wrap">
          <label for="campaign-select">Campaign view</label>
          <select id="campaign-select" class="select">${campaignOptions(campaignSelectValue())}</select>
          <div class="campaign-hint">Filters approvals, leads and the queue.</div>
        </div>
        <div class="sidebar-scroll">
          ${NAV_GROUPS.map(
            (group) => `
              <div class="nav-group">
                <div class="nav-label">${esc(group.label)}</div>
                ${group.items
                  .map(
                    ([page, label, iconName]) => `
                      <a class="nav-item" href="#/${page}" data-page="${page}" title="${esc(label)}" aria-label="${esc(label)}">
                        <span class="nav-icon">${icon(iconName, 17)}</span>
                        <span class="label">${esc(label)}</span>
                        ${page === "approvals" ? '<span class="nav-badge" id="approval-badge">0</span>' : ""}
                      </a>
                    `,
                  )
                  .join("")}
              </div>
            `,
          ).join("")}
        </div>
        <div class="sidebar-footer">
          <div class="mock-card">
            <span class="mock-dot"></span>
            <div><div class="mock-title">Mock mode</div><div class="mock-sub">No email leaves this Mac</div></div>
          </div>
        </div>
      </aside>
      <div class="main">
        <header class="topbar">
          <div class="breadcrumb">Workspace <span>/</span> <strong id="crumb-page">Overview</strong></div>
          <div class="topbar-search">
            ${icon("search", 15)}
            <input id="global-search" type="search" aria-label="Search leads" placeholder="Search leads by name, email or company..." autocomplete="off" />
          </div>
          <div class="topbar-actions">
            <button class="icon-btn" data-action="help" title="How Mailroom works" aria-label="Help">${icon("help", 17)}</button>
            <button class="btn primary sm" data-action="new-campaign">${icon("plus", 15)} New campaign</button>
            <div class="avatar">AM</div>
          </div>
        </header>
        <main id="page" class="content"></main>
      </div>
    </div>
    <div id="modal-root"></div>
    <div class="toast-wrap" id="toast-wrap" aria-live="polite" aria-atomic="false"></div>
  `;

  $("#campaign-select").addEventListener("change", (event) => {
    state.campaignId = event.target.value ? Number(event.target.value) : null;
    localStorage.setItem("mailroom.campaign", state.campaignId ? String(state.campaignId) : "");
    state.leadFilters.page = 1;
    state.selectedApproval = null;
    renderPage();
  });
  $("#global-search").addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const value = event.target.value.trim();
    state.leadFilters.q = value;
    state.leadFilters.page = 1;
    if (state.page !== "leads") location.hash = "#/leads";
    else renderPage();
  });
  updateNav();
}

function updateNav() {
  $$(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.page === state.page);
  });
  const crumb = $("#crumb-page");
  if (crumb) crumb.textContent = PAGES[state.page]?.title || "Overview";
}

function setApprovalBadge(total) {
  const badge = $("#approval-badge");
  if (!badge) return;
  const value = Number(total || 0);
  badge.textContent = value > 99 ? "99+" : String(value);
  badge.classList.toggle("hot", value > 0);
}

async function refreshApprovalBadge() {
  try {
    const data = await api("/approvals?page_size=1");
    setApprovalBadge(data.total);
  } catch {
    /* The badge is not critical. */
  }
}

async function route() {
  closeModal();
  const raw = location.hash.replace(/^#\/?/, "").split("?")[0] || "overview";
  state.page = PAGES[raw] ? raw : "overview";
  updateNav();
  await renderPage();
}

function pageSkeleton(title, sub, action = "") {
  return `
    <div class="page-head">
      <div>
        <div class="skeleton skel-line" style="width:190px;height:24px"></div>
        <div class="skeleton skel-line" style="width:420px;max-width:100%;margin-top:10px"></div>
      </div>
      <div class="page-actions">${action}</div>
    </div>
    <div class="skeleton skel-block" style="height:92px"></div>
    <div class="skeleton skel-block" style="height:340px"></div>
  `;
}

async function renderPage() {
  const token = ++state.renderToken;
  const page = $("#page");
  if (!page) return;
  page.innerHTML = pageSkeleton();
  try {
    if (state.page === "overview") await renderOverview(token);
    else if (state.page === "approvals") await renderApprovals(token);
    else if (state.page === "campaigns") await renderCampaigns(token);
    else if (state.page === "leads") await renderLeads(token);
    else if (state.page === "suppression") await renderSuppression(token);
    else if (state.page === "inboxes") await renderInboxes(token);
    else if (state.page === "deliverability") await renderDeliverability(token);
    else if (state.page === "warmup") await renderWarmup(token);
    else if (state.page === "queue") await renderQueue(token);
    else if (state.page === "activity") await renderActivity(token);
    else if (state.page === "sheets") await renderSheets(token);
    else if (state.page === "settings") await renderSettings(token);
  } catch (error) {
    if (token !== state.renderToken) return;
    page.innerHTML = `
      <div class="page-head"><div><h1 class="page-title">${esc(PAGES[state.page].title)}</h1></div></div>
      <div class="card card-body">
        <div class="notice red">${esc(error.message || "Could not load this page")}</div>
        <button class="btn mt-12" data-action="refresh">${icon("refresh", 15)} Retry</button>
      </div>`;
    toast(error.message || "Could not load this page", "error");
  }
}

/* ----------------------------- overview ----------------------------- */

async function renderOverview(token) {
  const data = await api("/overview");
  if (token !== state.renderToken) return;
  state.overview = data;
  setApprovalBadge(data.stats?.pending_count || 0);
  const stats = data.stats || {};
  const campaigns = data.campaigns || [];
  const queue = data.queue_preview || [];
  const activity = data.activity || [];
  const daily = buildDailySeries(data.daily || []);
  const maxDaily = Math.max(1, ...daily.map((item) => Number(item.sent || 0)));

  const topCampaigns = campaigns.slice(0, 3);
  const health = data.mailbox_health || [];

  $("#page").innerHTML = `
    <div class="page-head">
      <div>
        <h1 class="page-title">Overview</h1>
        <div class="page-sub">${esc(PAGES.overview.sub)}</div>
      </div>
      <div class="page-actions">
        <button class="btn" data-action="refresh">${icon("refresh", 15)} Refresh</button>
        <a class="btn" href="#/warmup">${icon("target", 15)} Warmup</a>
        <a class="btn primary" href="#/approvals">${icon("approvals", 15)} Review approvals</a>
      </div>
    </div>

    ${stats.sending_paused ? `<div class="notice red" style="margin-bottom:14px"><strong>Sending is paused globally.</strong> New approvals are blocked and queued items will not send. Warmup runs separately. <a href="#/settings" style="text-decoration:underline">Change in Settings</a>.</div>` : ""}
    ${data.mock_only ? `<div class="notice green" style="margin-bottom:14px">Mock mode is on. ${fmtNumber(stats.active_mailboxes)} inboxes and ${fmtNumber(stats.active_domains)} domains are ready, and no message can leave this Mac.</div>` : `<div class="notice violet" style="margin-bottom:14px">At least one real transport is configured. Review mailbox caps and DNS before activating a campaign.</div>`}

    <div class="grid stat-grid">
      <div class="card stat-card">
        <div class="stat-label">${icon("approvals", 14)} Awaiting approval</div>
        <div class="stat-value">${fmtNumber(stats.pending_count)}</div>
        <div class="stat-foot"><span class="chip amber">Needs a decision</span></div>
        <div class="stat-icon violet">${icon("approvals", 15)}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">${icon("send", 14)} Queued sends</div>
        <div class="stat-value">${fmtNumber(stats.queued_count)}</div>
        <div class="stat-foot">${fmtNumber(stats.failed_queue)} failed in queue</div>
        <div class="stat-icon blue">${icon("queue", 15)}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">${icon("mail", 14)} Sent today</div>
        <div class="stat-value">${fmtNumber(stats.sent_today)}</div>
        <div class="stat-foot">${fmtNumber(stats.sent_total)} sent all time</div>
        <div class="stat-icon green">${icon("checkCircle", 15)}</div>
        <div class="spark">${daily.map((item) => `<span class="${Number(item.sent) ? "on" : ""}" style="height:${Math.max(3, Math.round((Number(item.sent || 0) / maxDaily) * 24))}px"></span>`).join("")}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">${icon("inboxes", 14)} Active inboxes</div>
        <div class="stat-value">${fmtNumber(stats.active_mailboxes)}</div>
        <div class="stat-foot">${fmtNumber(stats.active_domains)} domains in rotation</div>
        <div class="stat-icon amber">${icon("inboxes", 15)}</div>
      </div>
    </div>

    <div class="grid dashboard-grid mt-16">
      <div class="grid" style="gap:14px">
        <div class="card">
          <div class="card-head">
            <div><div class="card-title">Campaigns</div><div class="card-sub">Separate lead pools, one queue.</div></div>
            <div class="right"><a class="btn ghost sm" href="#/campaigns">View all ${icon("arrow", 13)}</a></div>
          </div>
          <div class="card-body">
            ${topCampaigns.length ? topCampaigns.map((campaign) => campaignMini(campaign)).join("") : emptyState("No campaigns yet", "Create a campaign to start collecting approvals.", "campaigns")}
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div><div class="card-title">Sending plan</div><div class="card-sub">Next slots from every active mailbox.</div></div>
            <div class="right"><a class="btn ghost sm" href="#/queue">Open queue ${icon("arrow", 13)}</a></div>
          </div>
          <div class="card-body flush" style="padding:6px 17px 10px">
            ${queue.length ? queue.map((item) => `
              <div class="queue-row">
                <div class="queue-when">${esc(fmtTime(item.scheduled_at))}</div>
                <div class="queue-main"><div class="name">${esc(item.name)} · ${esc(item.company)}</div><div class="sub">${esc(item.campaign_name)} · ${esc(item.email)}</div></div>
                <div class="queue-mailbox">${esc(item.mailbox_email)}</div>
              </div>
            `).join("") : emptyState("Nothing queued", "Approved emails will appear here with a mailbox and a send time.", "queue")}
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div><div class="card-title">Recent activity</div><div class="card-sub">The audit trail, newest first.</div></div>
            <div class="right"><a class="btn ghost sm" href="#/activity">All activity ${icon("arrow", 13)}</a></div>
          </div>
          <div class="card-body">
            ${activity.length ? `<div class="timeline">${activity.slice(0, 6).map((item) => {
              const meta = activityMeta(item.kind);
              return `<div class="timeline-item ${meta[1]}"><div class="timeline-title">${esc(meta[0])}</div><div class="timeline-sub">${esc(activityDetail(item))}</div><div class="timeline-time">${esc(fmtRelative(item.created_at))}</div></div>`;
            }).join("")}</div>` : emptyState("No activity yet", "Approve a draft or send a message to populate the log.", "activity")}
          </div>
        </div>
      </div>

      <div class="grid" style="gap:14px">
        <div class="card">
          <div class="card-head">
            <div><div class="card-title">Inbox health</div><div class="card-sub">Today's volume against daily caps.</div></div>
            <div class="right"><a class="btn ghost sm" href="#/inboxes">Manage ${icon("arrow", 13)}</a></div>
          </div>
          <div class="card-body">
            ${health.length ? health.map((mailbox) => `
              <div class="bar-row">
                <div class="truncate" title="${esc(mailbox.email)}">${esc(mailbox.display_name || mailbox.email.split("@")[0])}</div>
                <div class="bar"><span style="width:${Math.min(100, Math.round((Number(mailbox.sent_today || 0) / Math.max(1, Number(mailbox.daily_limit || 25))) * 100))}%"></span></div>
                <div class="value">${fmtNumber(mailbox.sent_today)}/${fmtNumber(mailbox.daily_limit)}</div>
              </div>
            `).join("") : emptyState("No inboxes", "Add a domain and a mailbox to start rotation.", "inboxes")}
          </div>
        </div>

        <div class="card">
          <div class="card-head"><div><div class="card-title">Today at a glance</div><div class="card-sub">Current operating state.</div></div></div>
          <div class="card-body">
            <div class="cap-row"><div class="main"><div class="name">Approval required</div><div class="sub">Manual campaigns wait for you</div></div><span class="chip violet">On</span></div>
            <div class="cap-row"><div class="main"><div class="name">Transport</div><div class="sub">${data.mock_only ? "Mock outbox only" : "Real transport configured"}</div></div><span class="chip ${data.mock_only ? "green" : "amber"}">${data.mock_only ? "Safe" : "Live"}</span></div>
            <div class="cap-row"><div class="main"><div class="name">Warmup</div><div class="sub">${fmtNumber(stats.warmup_active)} active · ${fmtNumber(stats.warmup_sent_today)} sent · ${fmtNumber(stats.warmup_replies_today)} replies today</div></div><a class="chip violet" href="#/warmup">Open</a></div>
            <div class="cap-row"><div class="main"><div class="name">Suppression list</div><div class="sub">Permanent stop addresses</div></div><span class="chip">${fmtNumber(stats.suppressed)}</span></div>
            <div class="cap-row"><div class="main"><div class="name">Worker</div><div class="sub">Checks the queue every 2 seconds</div></div><span class="chip green">Running</span></div>
          </div>
        </div>

        <div class="card">
          <div class="card-head"><div><div class="card-title">Next steps</div><div class="card-sub">The shortest path through the control room.</div></div></div>
          <div class="card-body flush" style="padding:4px 17px 10px">
            <a class="cap-row" href="#/approvals"><div class="main"><div class="name">Review approvals</div><div class="sub">${fmtNumber(stats.pending_count)} waiting for a decision</div></div>${icon("arrow", 13)}</a>
            <a class="cap-row" href="#/warmup"><div class="main"><div class="name">${stats.warmup_active ? "Check warmup" : "Start warmup"}</div><div class="sub">${stats.warmup_active ? `${fmtNumber(stats.warmup_active)} profiles active` : "25 mailboxes ready in the mock pool"}</div></div>${icon("arrow", 13)}</a>
            <a class="cap-row" href="#/sheets"><div class="main"><div class="name">${stats.sheets_configured ? "Open Google Sheets" : "Connect Google Sheets"}</div><div class="sub">${stats.sheets_configured ? "Two-way sync is configured" : "Two-way leads and campaigns"}</div></div>${icon("arrow", 13)}</a>
          </div>
        </div>

        <div class="card card-body">
          <div class="row"><div class="stat-icon violet" style="position:static;margin:0">${icon("zap", 15)}</div><div><div class="card-title">Approval first</div><div class="card-sub" style="margin-top:3px">A denial is terminal. An approval reserves a mailbox and a send slot.</div></div></div>
        </div>
      </div>
    </div>
  `;
}

function campaignMini(campaign) {
  const pending = Number(campaign.pending_count || 0);
  const sent = Number(campaign.sent_count || 0);
  const leads = Number(campaign.lead_count || 0);
  return `
    <div class="campaign-mini">
      <div class="top">
        <div style="min-width:0;flex:1"><div class="name">${esc(campaign.name)}</div><div class="meta">${esc(campaign.status)} · ${fmtNumber(campaign.mailbox_count)} inboxes · ${esc(campaign.approval_mode)} approval</div></div>
        ${campaign.status === "active" ? '<span class="chip green">Active</span>' : '<span class="chip gray">Paused</span>'}
      </div>
      <div class="numbers">
        <div class="num"><strong>${fmtNumber(leads)}</strong><span>Leads</span></div>
        <div class="num"><strong>${fmtNumber(pending)}</strong><span>Pending</span></div>
        <div class="num"><strong>${fmtNumber(sent)}</strong><span>Sent</span></div>
        <div class="num"><strong>${fmtNumber(campaign.sent_today)}</strong><span>Today</span></div>
      </div>
      <div class="mt-8">${progress(campaign.sent_today, campaign.daily_limit, "green")}</div>
    </div>
  `;
}

/* ----------------------------- approvals ----------------------------- */

async function renderApprovals(token) {
  $("#page").innerHTML = `
    <div class="page-head">
      <div><h1 class="page-title">Approvals</h1><div class="page-sub">${esc(PAGES.approvals.sub)}</div></div>
      <div class="page-actions">
        <div class="search">${icon("search", 15)}<input id="approval-search" type="search" aria-label="Search approvals" placeholder="Search name, email, company..." value="${esc(state.approvalQuery)}" /></div>
        <button class="btn" data-action="refresh">${icon("refresh", 15)} Refresh</button>
      </div>
    </div>
    <div class="approval-layout">
      <div class="card approval-list" id="approval-list-card"></div>
      <div class="card approval-detail" id="approval-detail-card"></div>
    </div>
  `;
  $("#approval-search").addEventListener(
    "input",
    debounce((event) => {
      state.approvalQuery = event.target.value.trim();
      state.selectedApproval = null;
      state.approvalChecked = new Set();
      loadApprovals();
    }, 280),
  );
  await loadApprovals(token);
}

async function loadApprovals(token = state.renderToken) {
  const request = ++state.approvalRequest;
  const query = new URLSearchParams({ page_size: "100" });
  if (state.campaignId) query.set("campaign_id", state.campaignId);
  if (state.approvalQuery) query.set("q", state.approvalQuery);
  const data = await api(`/approvals?${query.toString()}`);
  if (token !== state.renderToken || request !== state.approvalRequest) return;
  state.approvals = data;
  const ids = new Set(data.items.map((item) => item.draft_id));
  state.approvalChecked = new Set([...state.approvalChecked].filter((id) => ids.has(id)));
  if (!ids.has(state.selectedApproval)) state.selectedApproval = data.items[0]?.draft_id || null;
  setApprovalBadge(data.total);
  renderApprovalList();
  renderApprovalDetail();
}

function renderApprovalList() {
  const container = $("#approval-list-card");
  if (!container) return;
  const items = state.approvals.items || [];
  const checked = state.approvalChecked.size;
  container.innerHTML = `
    <div class="approval-list-head">
      <div><div class="card-title">Review queue</div><div class="count">${fmtNumber(state.approvals.total)} waiting${state.campaignId ? ` in ${esc(campaignName(state.campaignId))}` : ""} · ${fmtNumber(items.length)} shown${state.campaignId ? ` · <a href="#" data-action="clear-campaign" style="text-decoration:underline">Show all</a>` : ""}</div></div>
      <div class="right" style="margin-left:auto">${items.length ? `<label class="checkline small"><input type="checkbox" id="approval-select-all" ${checked && checked === items.length ? "checked" : ""}/> Select shown</label>` : ""}</div>
    </div>
    ${checked ? `<div style="display:flex;gap:6px;padding:9px 12px;border-bottom:1px solid var(--line);background:#fbfaff"><span class="chip violet">${checked} selected</span><button class="btn xs success" data-action="bulk-approve">Approve selected</button><button class="btn xs danger" data-action="bulk-deny">Deny selected</button></div>` : ""}
    <div id="approval-list-rows">
      ${items.length ? items.map((item) => {
        const active = Number(item.draft_id) === Number(state.selectedApproval);
        const checkedItem = state.approvalChecked.has(item.draft_id);
        return `
          <div class="approval-card ${active ? "active" : ""}" data-action="select-approval" data-id="${item.draft_id}" role="button" tabindex="0">
            <input type="checkbox" data-action="toggle-approval-check" data-id="${item.draft_id}" ${checkedItem ? "checked" : ""} aria-label="Select ${esc(item.name)}" style="margin-top:3px;accent-color:var(--accent);flex:0 0 auto" />
            <div class="body">
              <div class="row1"><div class="name">${esc(item.name)}</div>${item.verification && item.verification !== "Unknown" ? `<span class="chip ${item.verification === "Deliverable" ? "green" : item.verification === "Undeliverable" ? "red" : "amber"}" style="height:18px;font-size:9px">${esc(item.verification)}</span>` : ""}</div>
              <div class="company">${esc(item.role || "Role not set")} · ${esc(item.company || "Company not set")}</div>
              <div class="email">${esc(item.email)}</div>
              <div class="meta"><span class="chip gray" style="height:18px;font-size:9.5px">${esc(item.industry || "Industry not set")}</span><span class="chip violet" style="height:18px;font-size:9.5px">${esc(item.campaign_name)}</span></div>
            </div>
          </div>
        `;
      }).join("") : emptyState(state.approvalQuery ? "No matches" : "Nothing waiting", state.approvalQuery ? `No pending draft matches "${state.approvalQuery}".` : "Every draft has been approved or denied for this view.", "approvals")}
    </div>
  `;
  const selectAll = $("#approval-select-all");
  if (selectAll) {
    selectAll.addEventListener("change", () => {
      if (selectAll.checked) state.approvalChecked = new Set(items.map((item) => item.draft_id));
      else state.approvalChecked = new Set();
      renderApprovalList();
    });
  }
}

function renderApprovalDetail() {
  const container = $("#approval-detail-card");
  if (!container) return;
  const item = (state.approvals.items || []).find((row) => Number(row.draft_id) === Number(state.selectedApproval));
  if (!item) {
    container.innerHTML = `<div style="min-height:540px;display:grid;place-items:center">${emptyState("Select an email", "Choose a person on the left to inspect the draft and decide.", "approvals")}</div>`;
    return;
  }
  const pool = state.approvals.pools?.[item.campaign_id] || { count: 0, suggested: null };
  container.innerHTML = `
    <div class="person-card">
      <div class="person-top">
        <div class="person-avatar">${esc(initials(item.name))}</div>
        <div style="min-width:0;flex:1">
          <div class="person-name">${esc(item.name)}</div>
          <div class="person-role">${esc(item.role || "Role not set")}</div>
          <div class="person-company">${icon("campaigns", 13)} ${esc(item.company || "Company not set")}</div>
        </div>
        <div class="row">${item.verification ? `<span class="chip ${item.verification === "Deliverable" ? "green" : item.verification === "Undeliverable" ? "red" : "amber"}">${esc(item.verification)}</span>` : ""}<span class="chip gray">${esc(item.email_grade || "Grade ?")}</span></div>
      </div>
      <div class="person-contact">
        <span>${icon("mail", 13)} ${esc(item.email)}</span>
        ${item.website ? `<span>${icon("globe", 13)} ${esc(item.website.replace(/^https?:\/\//, ""))}</span>` : ""}
        ${item.city ? `<span>${icon("target", 13)} ${esc(item.city)}</span>` : ""}
      </div>
      <div class="person-meta">
        <div><div class="meta-label">Campaign</div><div class="meta-value truncate">${esc(item.campaign_name)}</div></div>
        <div><div class="meta-label">Industry</div><div class="meta-value truncate">${esc(item.industry || "-")}</div></div>
        <div><div class="meta-label">Source</div><div class="meta-value truncate">${esc(item.source || "Local")}</div></div>
        <div><div class="meta-label">Draft age</div><div class="meta-value">${esc(fmtRelative(item.draft_created_at))}</div></div>
      </div>
    </div>

    <div class="email-shell">
      <div class="email-toolbar">
        <span class="label">Email preview</span>
        <div class="right"><button class="btn xs" data-action="edit-draft" data-id="${item.draft_id}">${icon("edit", 12)} Edit</button><button class="btn xs" data-action="regenerate-draft" data-id="${item.draft_id}">${icon("refresh", 12)} Re-render</button>${state.settings.agent_webhook ? `<button class="btn xs" data-action="agent-draft" data-id="${item.draft_id}">${icon("zap", 12)} Agent</button>` : ""}</div>
      </div>
      <div class="email-preview">
        <div class="email-head">
          <div class="email-subject">${esc(item.subject)}</div>
          <div class="email-meta"><span>To: ${esc(item.email)}</span><span>From: ${esc(pool.suggested || "rotation pool")}</span><span>${esc(item.campaign_name)}</span></div>
        </div>
        <div class="email-body">${esc(item.body)}</div>
      </div>
      <div class="assignment">${icon("inboxes", 14)} <span>Rotation pool: <strong>${fmtNumber(pool.count)} inboxes</strong> ready${pool.suggested ? ` · suggested <strong>${esc(pool.suggested)}</strong>` : ""}. A mailbox is reserved when you approve.</span></div>
    </div>

    <div class="action-bar">
      <div class="hint"><span class="kbd">j</span><span class="kbd">k</span> move <span class="kbd">a</span> approve <span class="kbd">d</span> deny <span class="kbd">e</span> edit</div>
      <button class="btn danger" data-action="deny" data-id="${item.draft_id}">${icon("x", 14)} Deny</button>
      <button class="btn" data-action="edit-draft" data-id="${item.draft_id}">${icon("edit", 14)} Edit</button>
      <button class="btn success" data-action="approve" data-id="${item.draft_id}">${icon("check", 14)} Approve & queue</button>
    </div>
  `;
}

function selectedApprovalItem() {
  return (state.approvals.items || []).find((row) => Number(row.draft_id) === Number(state.selectedApproval));
}

function moveApproval(delta) {
  const items = state.approvals.items || [];
  if (!items.length) return;
  const index = items.findIndex((item) => Number(item.draft_id) === Number(state.selectedApproval));
  const next = items[Math.max(0, Math.min(items.length - 1, index + delta))];
  if (!next) return;
  state.selectedApproval = next.draft_id;
  renderApprovalList();
  renderApprovalDetail();
}

function removeApprovalLocal(draftId) {
  const items = state.approvals.items || [];
  const index = items.findIndex((item) => Number(item.draft_id) === Number(draftId));
  if (index < 0) return;
  const wasSelected = Number(state.selectedApproval) === Number(draftId);
  state.approvals.items = items.filter((item) => Number(item.draft_id) !== Number(draftId));
  state.approvals.total = Math.max(0, Number(state.approvals.total || 0) - 1);
  if (wasSelected) {
    const next = state.approvals.items[Math.min(index, state.approvals.items.length - 1)];
    state.selectedApproval = next?.draft_id || null;
  }
  state.approvalChecked.delete(draftId);
  setApprovalBadge(state.approvals.total);
  renderApprovalList();
  renderApprovalDetail();
}

async function approveDraft(draftId) {
  if (state.approvalBusy) return;
  state.approvalBusy = true;
  try {
    const result = await api(`/approvals/${draftId}/approve`, { method: "POST", body: JSON.stringify({}) });
    toast(`Queued via ${result.mailbox.email} for ${fmtDate(result.queue.scheduled_at)}`);
    if (state.page === "approvals") {
      removeApprovalLocal(draftId);
      state.approvalBusy = false;
      setTimeout(() => {
        if (state.page === "approvals") loadApprovals().catch(() => {});
      }, 250);
    } else {
      await renderPage();
      await refreshApprovalBadge();
    }
  } catch (error) {
    toast(error.message, "error");
  } finally {
    state.approvalBusy = false;
  }
}

function draftItem(draftId) {
  return (
    (state.approvals.items || []).find((row) => Number(row.draft_id) === Number(draftId)) ||
    (Number(state.leadDraft?.draft_id) === Number(draftId) ? state.leadDraft : null)
  );
}

function openDenyModal(draftId) {
  const item = draftItem(draftId);
  openModal({
    title: "Deny this email",
    sub: item ? `${item.name}${item.company ? ` at ${item.company}` : ""}` : "The draft will not be sent.",
    narrow: true,
    body: `
      <form id="modal-form">
        <div class="field"><label for="deny-reason">Reason</label><textarea class="textarea" id="deny-reason" name="reason" placeholder="Why should this not go out?">Not a fit for this campaign</textarea></div>
        <label class="checkline mt-12"><input type="checkbox" name="suppress" /> Never contact this address again</label>
        <div class="hint mt-8">This also denies other pending drafts and cancels queued sends for the same address.</div>
      </form>
    `,
    footer: `<button class="btn" data-action="close-modal">Cancel</button><button class="btn danger" type="submit" form="modal-form">Deny email</button>`,
    onSubmit: async (formData) => {
      await api(`/approvals/${draftId}/deny`, {
        method: "POST",
        body: JSON.stringify({ reason: formData.get("reason") || "", suppress: formData.get("suppress") === "on" }),
      });
      toast("Draft denied. Nothing was sent.");
      if (state.page === "approvals") {
        removeApprovalLocal(draftId);
        setTimeout(() => {
          if (state.page === "approvals") loadApprovals().catch(() => {});
        }, 250);
      } else {
        await renderPage();
        await refreshApprovalBadge();
      }
    },
  });
}

function openEditDraftModal(draftId) {
  const item = draftItem(draftId) || selectedApprovalItem();
  if (!item) {
    toast("Select the draft again before editing it.", "error");
    return;
  }
  openModal({
    title: "Edit draft",
    sub: "Saving puts the draft back in the pending queue. You still have to approve it.",
    wide: true,
    body: `
      <form id="modal-form">
        <div class="field"><label for="draft-subject">Subject</label><input class="input" id="draft-subject" name="subject" value="${esc(item.subject)}" /></div>
        <div class="field mt-12"><label for="draft-body">Body</label><textarea class="textarea" id="draft-body" name="body" style="min-height:300px">${esc(item.body)}</textarea></div>
      </form>
    `,
    footer: `<button class="btn" data-action="close-modal">Cancel</button><button class="btn primary" type="submit" form="modal-form">Save draft</button>`,
    onSubmit: async (formData) => {
      await api(`/drafts/${draftId}`, {
        method: "PATCH",
        body: JSON.stringify({ subject: formData.get("subject"), body: formData.get("body") }),
      });
      toast("Draft updated. It is still waiting for approval.");
      if (state.page === "approvals") {
        await loadApprovals();
      } else if (state.page === "leads" && state.leadDraft?.lead_id) {
        await openLeadModal(state.leadDraft.lead_id);
      }
    },
  });
}

async function bulkApprovals(action) {
  const ids = [...state.approvalChecked];
  if (!ids.length) return;
  if (action === "approve") {
    openConfirm(`Approve ${ids.length} emails?`, "Each one will reserve a mailbox and join the send queue. Mock mode is safe.", async () => {
      const result = await api("/approvals/bulk", {
        method: "POST",
        body: JSON.stringify({ draft_ids: ids, action: "approve" }),
      });
      toast(`Queued ${result.approved.length} email(s).${result.errors.length ? ` ${result.errors.length} failed.` : ""}`);
      state.approvalChecked = new Set();
      await loadApprovals();
    });
  } else {
    openConfirm(`Deny ${ids.length} emails?`, "They will not be sent. No suppression is added unless you do it individually.", async () => {
      const result = await api("/approvals/bulk", {
        method: "POST",
        body: JSON.stringify({ draft_ids: ids, action: "deny", reason: "Bulk denied by operator" }),
      });
      toast(`Denied ${result.denied.length} email(s).`);
      state.approvalChecked = new Set();
      await loadApprovals();
    });
  }
}

/* ----------------------------- campaigns ----------------------------- */

async function renderCampaigns(token) {
  const data = await api("/campaigns");
  if (token !== state.renderToken) return;
  state.campaigns = data.items || [];
  renderCampaignOptions();
  const campaigns = data.items || [];
  $("#page").innerHTML = `
    <div class="page-head">
      <div><h1 class="page-title">Campaigns</h1><div class="page-sub">${esc(PAGES.campaigns.sub)}</div></div>
      <div class="page-actions"><button class="btn" data-action="refresh">${icon("refresh", 15)} Refresh</button><button class="btn primary" data-action="new-campaign">${icon("plus", 15)} New campaign</button></div>
    </div>
    ${campaigns.length ? `<div class="grid campaign-grid">${campaigns.map(campaignCard).join("")}</div>` : `<div class="card">${emptyState("No campaigns yet", "Create your first campaign, then import a lead pack or add leads manually.", "campaigns")}</div>`}
  `;
}

function campaignCard(campaign) {
  const active = campaign.status === "active";
  return `
    <div class="card card-body campaign-card">
      <div class="domain-top">
        <div class="domain-icon" style="background:var(--accent-soft);color:var(--accent)">${icon("campaigns", 16)}</div>
        <div style="min-width:0;flex:1"><div class="domain-name">${esc(campaign.name)}</div><div class="domain-provider">${active ? "Active" : campaign.status} · ${esc(campaign.approval_mode)} approval · ${fmtNumber(campaign.mailbox_count)} inboxes</div></div>
        ${active ? '<span class="chip green">Active</span>' : '<span class="chip gray">Paused</span>'}
      </div>
      <div class="numbers" style="display:flex;gap:17px;margin-top:16px">
        <div><div class="meta-label">Leads</div><div class="meta-value" style="font-size:17px">${fmtNumber(campaign.lead_count)}</div></div>
        <div><div class="meta-label">Pending</div><div class="meta-value" style="font-size:17px;color:var(--amber)">${fmtNumber(campaign.pending_count)}</div></div>
        <div><div class="meta-label">Sent</div><div class="meta-value" style="font-size:17px;color:var(--accent-2)">${fmtNumber(campaign.sent_count)}</div></div>
        <div><div class="meta-label">Queued</div><div class="meta-value" style="font-size:17px;color:var(--blue)">${fmtNumber(campaign.queued_count)}</div></div>
      </div>
      <div class="mt-16"><div class="row small muted" style="justify-content:space-between"><span>Daily volume</span><span>${fmtNumber(campaign.sent_today)} / ${fmtNumber(campaign.daily_limit)}</span></div><div class="mt-8">${progress(campaign.sent_today, campaign.daily_limit, "green")}</div></div>
      <div class="row mt-16 wrap" style="justify-content:space-between;gap:8px">
        <div class="row wrap" style="gap:6px"><span class="chip gray">${esc(campaign.rotation_strategy.replaceAll("_", " "))}</span><span class="chip gray">${esc(campaign.timezone)}</span></div>
        <div class="row" style="gap:6px"><button class="icon-btn bordered" data-action="campaign-settings" data-id="${campaign.id}" title="Campaign settings" aria-label="Campaign settings">${icon("settings", 14)}</button><button class="btn sm" data-action="toggle-campaign" data-id="${campaign.id}">${active ? "Pause" : "Activate"}</button><button class="btn sm primary" data-action="open-campaign" data-id="${campaign.id}">Open leads</button></div>
      </div>
    </div>
  `;
}

function openCampaignModal() {
  const timezone = state.settings.default_timezone || "Asia/Kolkata";
  openModal({
    title: "New campaign",
    sub: "A campaign owns a lead pool, a sequence and its own sending limits.",
    wide: true,
    body: `
      <form id="modal-form">
        <div class="form-section">
          <div class="form-section-title">Basics</div>
          <div class="form-grid">
            <div class="field full"><label for="camp-name">Campaign name</label><input class="input" id="camp-name" name="name" placeholder="NCR SME - November" required /></div>
            <div class="field"><label for="camp-status">Status</label><select class="select" id="camp-status" name="status"><option value="draft">Draft</option><option value="active" selected>Active</option><option value="paused">Paused</option></select></div>
            <div class="field"><label for="camp-approval">Approval mode</label><select class="select" id="camp-approval" name="approval_mode"><option value="manual" selected>Manual - you approve every email</option><option value="auto" disabled>Auto - not active yet</option></select></div>
          </div>
        </div>
        <div class="form-section">
          <div class="form-section-title">Volume and schedule</div>
          <div class="form-grid">
            <div class="field"><label for="camp-daily">Campaign daily limit</label><input class="input" id="camp-daily" name="daily_limit" type="number" min="1" value="250" /></div>
            <div class="field"><label for="camp-domain">Per-domain daily limit</label><input class="input" id="camp-domain" name="per_domain_limit" type="number" min="1" value="50" /></div>
            <div class="field"><label for="camp-start">Window start</label><input class="input" id="camp-start" name="window_start" type="time" value="09:30" /></div>
            <div class="field"><label for="camp-end">Window end</label><input class="input" id="camp-end" name="window_end" type="time" value="17:30" /></div>
            <div class="field"><label for="camp-rotation">Rotation</label><select class="select" id="camp-rotation" name="rotation_strategy"><option value="least_used" selected>Least used today</option><option value="round_robin">Round robin</option><option value="weighted">Weighted</option></select></div>
            <div class="field"><label for="camp-timezone">Timezone</label><input class="input" id="camp-timezone" name="timezone" value="${esc(timezone)}" /></div>
          </div>
          <div class="field mt-12"><label>Working days</label><div class="row wrap" style="gap:12px">${["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, index) => `<label class="checkline"><input type="checkbox" name="days" value="${index + 1}" ${index < 5 ? "checked" : ""}/> ${day}</label>`).join("")}</div></div>
        </div>
        <div class="form-section">
          <div class="form-section-title">Spacing</div>
          <div class="form-grid">
            <div class="field"><label for="camp-min">Minimum gap (seconds)</label><input class="input" id="camp-min" name="min_gap_seconds" type="number" value="90" /></div>
            <div class="field"><label for="camp-max">Maximum gap (seconds)</label><input class="input" id="camp-max" name="max_gap_seconds" type="number" value="360" /></div>
          </div>
          <div class="notice mt-12">Auto mode is not implemented. Every send waits for human approval, regardless of the transport.</div>
        </div>
      </form>
    `,
    footer: `<button class="btn" data-action="close-modal">Cancel</button><button class="btn primary" type="submit" form="modal-form">Create campaign</button>`,
    onSubmit: async (formData) => {
      const days = formData.getAll("days").map(Number);
      if (!days.length) throw new Error("Pick at least one working day.");
      const payload = {
        name: formData.get("name"),
        status: formData.get("status"),
        approval_mode: formData.get("approval_mode"),
        daily_limit: Number(formData.get("daily_limit")),
        per_domain_limit: Number(formData.get("per_domain_limit")),
        window_start: formData.get("window_start"),
        window_end: formData.get("window_end"),
        timezone: formData.get("timezone"),
        rotation_strategy: formData.get("rotation_strategy"),
        min_gap_seconds: Number(formData.get("min_gap_seconds")),
        max_gap_seconds: Number(formData.get("max_gap_seconds")),
        working_days: days,
      };
      await api("/campaigns", { method: "POST", body: JSON.stringify(payload) });
      await loadCampaigns();
      await refreshApprovalBadge();
      renderCampaignOptions();
      toast("Campaign created.");
      if (state.page === "campaigns") renderPage();
      else navigate("campaigns");
    },
  });
}

function openCampaignSettings(id) {
  const campaign = state.campaigns.find((item) => Number(item.id) === Number(id));
  if (!campaign) return;
  let days = [1, 2, 3, 4, 5];
  try {
    const parsed = JSON.parse(campaign.working_days || "[]");
    if (Array.isArray(parsed) && parsed.length) days = parsed.map(Number);
  } catch {
    days = [1, 2, 3, 4, 5];
  }
  openModal({
    title: "Campaign settings",
    sub: campaign.name,
    wide: true,
    body: `
      <form id="modal-form">
        <div class="form-grid">
          <div class="field full"><label for="cs-name">Name</label><input class="input" id="cs-name" name="name" value="${esc(campaign.name)}" required /></div>
          <div class="field"><label for="cs-status">Status</label><select class="select" id="cs-status" name="status">${["draft", "active", "paused", "archived"].map((value) => `<option value="${value}" ${campaign.status === value ? "selected" : ""}>${value}</option>`).join("")}</select></div>
          <div class="field"><label for="cs-approval">Approval mode</label><select class="select" id="cs-approval" name="approval_mode"><option value="manual" ${campaign.approval_mode === "manual" ? "selected" : ""}>Manual approval</option><option value="auto" disabled>Auto (not active yet)</option></select></div>
          <div class="field"><label for="cs-daily">Daily limit</label><input class="input" id="cs-daily" name="daily_limit" type="number" min="1" value="${esc(campaign.daily_limit)}" /></div>
          <div class="field"><label for="cs-domain">Per-domain limit</label><input class="input" id="cs-domain" name="per_domain_limit" type="number" min="1" value="${esc(campaign.per_domain_limit)}" /></div>
          <div class="field"><label for="cs-window-start">Window start</label><input class="input" id="cs-window-start" name="window_start" type="time" value="${esc(campaign.window_start)}" /></div>
          <div class="field"><label for="cs-window-end">Window end</label><input class="input" id="cs-window-end" name="window_end" type="time" value="${esc(campaign.window_end)}" /></div>
          <div class="field"><label for="cs-timezone">Timezone</label><input class="input" id="cs-timezone" name="timezone" value="${esc(campaign.timezone)}" /></div>
          <div class="field"><label for="cs-rotation">Rotation</label><select class="select" id="cs-rotation" name="rotation_strategy">${["least_used", "round_robin", "weighted"].map((value) => `<option value="${value}" ${campaign.rotation_strategy === value ? "selected" : ""}>${value.replaceAll("_", " ")}</option>`).join("")}</select></div>
          <div class="field"><label for="cs-gap-min">Minimum gap (seconds)</label><input class="input" id="cs-gap-min" name="min_gap_seconds" type="number" min="1" value="${esc(campaign.min_gap_seconds)}" /></div>
          <div class="field"><label for="cs-gap-max">Maximum gap (seconds)</label><input class="input" id="cs-gap-max" name="max_gap_seconds" type="number" min="1" value="${esc(campaign.max_gap_seconds)}" /></div>
        </div>
        <div class="field mt-12"><label>Working days</label><div class="row wrap" style="gap:12px">${["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, index) => `<label class="checkline"><input type="checkbox" name="days" value="${index + 1}" ${days.includes(index + 1) ? "checked" : ""}/> ${day}</label>`).join("")}</div></div>
        <div class="notice mt-12">Auto-send is not implemented. Every send still requires approval.</div>
      </form>
    `,
    footer: `<button class="btn" data-action="close-modal">Cancel</button><button class="btn primary" type="submit" form="modal-form">Save campaign</button>`,
    onSubmit: async (formData) => {
      const days = formData.getAll("days").map(Number);
      if (!days.length) throw new Error("Pick at least one working day.");
      await api(`/campaigns/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: formData.get("name"),
          status: formData.get("status"),
          approval_mode: "manual",
          daily_limit: Number(formData.get("daily_limit")),
          per_domain_limit: Number(formData.get("per_domain_limit")),
          window_start: formData.get("window_start"),
          window_end: formData.get("window_end"),
          timezone: formData.get("timezone"),
          rotation_strategy: formData.get("rotation_strategy"),
          min_gap_seconds: Number(formData.get("min_gap_seconds")),
          max_gap_seconds: Number(formData.get("max_gap_seconds")),
          working_days: days,
        }),
      });
      await loadCampaigns();
      toast("Campaign settings saved.");
      renderPage();
    },
  });
}

async function toggleCampaign(id) {
  const campaign = state.campaigns.find((item) => Number(item.id) === Number(id));
  if (!campaign) return;
  const next = campaign.status === "active" ? "paused" : "active";
  await api(`/campaigns/${id}`, { method: "PATCH", body: JSON.stringify({ status: next }) });
  toast(`Campaign ${next === "active" ? "activated" : "paused"}.`);
  await loadCampaigns();
  renderPage();
}

/* ----------------------------- leads ----------------------------- */

async function renderLeads(token) {
  const campaignFilter = state.campaignId || "";
  $("#page").innerHTML = `
    <div class="page-head">
      <div><h1 class="page-title">Leads</h1><div class="page-sub">${esc(PAGES.leads.sub)} ${state.campaignId ? `Viewing <strong>${esc(campaignName(state.campaignId))}</strong>. <a href="#" data-action="clear-campaign" style="text-decoration:underline">Show all campaigns</a>` : ""}</div></div>
      <div class="page-actions">
        <button class="btn" data-action="import-leads">${icon("upload", 15)} Import CSV</button>
        <a class="btn" href="/api/leads/export.csv?campaign_id=${encodeURIComponent(campaignFilter)}&status=${encodeURIComponent(state.leadFilters.status)}&q=${encodeURIComponent(state.leadFilters.q)}">${icon("download", 15)} Export</a>
      </div>
    </div>
    <div class="card">
      <div class="table-toolbar">
        <div class="search">${icon("search", 15)}<input id="lead-search" type="search" aria-label="Search leads" placeholder="Search name, email, company..." value="${esc(state.leadFilters.q)}" /></div>
        <select class="select" id="lead-status" style="width:160px;height:32px">${["", "pending_approval", "queued", "sent", "denied", "failed"].map((value) => `<option value="${value}" ${state.leadFilters.status === value ? "selected" : ""}>${value ? (STATUS[value]?.[0] || value) : "All statuses"}</option>`).join("")}</select>
        <span class="spacer"></span>
        <span class="muted small" id="lead-count">Loading...</span>
      </div>
      <div id="leads-table-shell"></div>
      <div id="leads-pagination"></div>
    </div>
  `;
  $("#lead-search").addEventListener(
    "input",
    debounce((event) => {
      state.leadFilters.q = event.target.value.trim();
      state.leadFilters.page = 1;
      loadLeads(token);
    }, 280),
  );
  $("#lead-status").addEventListener("change", (event) => {
    state.leadFilters.status = event.target.value;
    state.leadFilters.page = 1;
    loadLeads(token);
  });
  await loadLeads(token);
}

async function loadLeads(token = state.renderToken) {
  const shell = $("#leads-table-shell");
  if (!shell) return;
  const request = ++state.leadRequest;
  shell.innerHTML = `<div style="padding:18px"><div class="skeleton skel-line"></div><div class="skeleton skel-line"></div><div class="skeleton skel-line"></div></div>`;
  const query = new URLSearchParams({
    page: String(state.leadFilters.page),
    page_size: String(state.leadFilters.pageSize),
  });
  if (state.campaignId) query.set("campaign_id", state.campaignId);
  if (state.leadFilters.status) query.set("status", state.leadFilters.status);
  if (state.leadFilters.q) query.set("q", state.leadFilters.q);
  try {
    const data = await api(`/leads?${query.toString()}`);
    if (token !== state.renderToken || request !== state.leadRequest) return;
    state.leads = data;
    $("#lead-count").textContent = `${fmtNumber(data.total)} lead(s)`;
    $("#leads-table-shell").innerHTML = data.items.length ? `
      <div class="table-wrap">
        <table class="table leads-table">
          <thead><tr><th>Person</th><th>Email</th><th>Role</th><th>Industry</th><th>Campaign</th><th>Status</th></tr></thead>
          <tbody>${data.items.map((lead) => `
            <tr class="clickable" data-action="open-lead" data-id="${lead.id}" tabindex="0">
              <td><div class="cell-person"><div class="avatar sm ${avatarTone(lead.name)}">${esc(initials(lead.name))}</div><div><div class="name">${esc(lead.name)}</div><div class="sub">${esc(lead.company || "-")}</div></div></div></td>
              <td><span class="mono" style="font-size:11px">${esc(lead.email)}</span></td>
              <td class="cell-muted">${esc(lead.role || "-")}</td>
              <td class="cell-muted">${esc(lead.industry || "-")}</td>
              <td class="cell-muted truncate" style="max-width:170px" title="${esc(lead.campaign_name || "")}">${esc(lead.campaign_name || "-")}</td>
              <td>${statusChip(lead.status)}</td>
            </tr>
          `).join("")}</tbody>
        </table>
      </div>
    ` : emptyState("No leads match", "Try another status, campaign or search term. Import a CSV to add a new pool.", "leads");
    renderLeadPagination(data);
  } catch (error) {
    if (token !== state.renderToken || request !== state.leadRequest) return;
    shell.innerHTML = `<div class="card-body"><div class="notice red">${esc(error.message)}</div></div>`;
  }
}

function escapeMailbox(value) {
  return value ? `<span class="mono" style="font-size:10.5px">${esc(value)}</span>` : '<span class="muted small">-</span>';
}

function renderLeadPagination(data) {
  const container = $("#leads-pagination");
  if (!container) return;
  container.innerHTML = `
    <div class="pagination">
      <span>Page ${data.page} of ${data.pages} · ${fmtNumber(data.total)} total</span>
      <div class="right">
        <button class="btn sm" data-action="lead-page" data-page="${Math.max(1, data.page - 1)}" ${data.page <= 1 ? "disabled" : ""}>Previous</button>
        <button class="btn sm" data-action="lead-page" data-page="${Math.min(data.pages, data.page + 1)}" ${data.page >= data.pages ? "disabled" : ""}>Next</button>
      </div>
    </div>
  `;
}

async function openLeadModal(id) {
  try {
    const data = await api(`/leads/${id}`);
    const lead = data.lead;
    const draft = data.draft;
    const website = safeHref(lead.website);
    state.leadDraft = draft
      ? {
          draft_id: draft.id,
          lead_id: lead.id,
          name: lead.name,
          company: lead.company,
          email: lead.email,
          subject: draft.subject,
          body: draft.body,
        }
      : null;
    openModal({
      title: lead.name,
      sub: `${lead.role || "Role not set"} · ${lead.company || "Company not set"}`,
      wide: true,
      body: `
        <div class="person-meta" style="margin-top:0;border-top:0;padding-top:0">
          <div><div class="meta-label">Email</div><div class="meta-value mono" style="font-size:10.5px">${esc(lead.email)}</div></div>
          <div><div class="meta-label">Industry</div><div class="meta-value">${esc(lead.industry || "-")}</div></div>
          <div><div class="meta-label">City</div><div class="meta-value">${esc(lead.city || "-")}</div></div>
          <div><div class="meta-label">Verification</div><div class="meta-value">${esc(lead.verification || "-")}</div></div>
        </div>
        ${lead.notes ? `<div class="notice mt-12">${esc(lead.notes)}</div>` : ""}
        ${draft ? `
          <div class="mt-16"><div class="email-toolbar"><span class="label">Draft</span><div class="right">${statusChip(draft.status)}</div></div>
          <div class="email-preview"><div class="email-head"><div class="email-subject">${esc(draft.subject)}</div><div class="email-meta"><span>To: ${esc(lead.email)}</span><span>${esc(lead.company || "")}</span></div></div><div class="email-body" style="min-height:150px">${esc(draft.body)}</div></div></div>
        ` : `<div class="notice mt-16">No draft has been generated for this lead yet.</div>`}
        ${data.message ? `
          <div class="mt-16"><div class="email-toolbar"><span class="label">Sent message</span><div class="right">${statusChip("sent")}</div></div>
          <div class="notice green"><strong>${esc(fmtDate(data.message.sent_at))}</strong> from ${esc(data.message.from_email)} via ${esc(data.message.transport)}. Message ID <span class="mono" style="font-size:10.5px">${esc(data.message.message_id || "-")}</span></div></div>
        ` : data.queue ? `
          <div class="notice mt-16">${statusChip(data.queue.status)} Scheduled for <strong>${esc(fmtDate(data.queue.scheduled_at))}</strong> via ${esc(data.queue.mailbox_email || "a reserved mailbox")}.</div>
        ` : ""}
        ${website ? `<div class="mt-12 small muted">${icon("globe", 13)} <a href="${esc(website)}" target="_blank" rel="noreferrer">${esc(website)}</a></div>` : ""}
      `,
      footer: draft && draft.status === "pending"
        ? `<button class="btn" data-action="close-modal">Close</button><button class="btn danger" data-action="deny" data-id="${draft.id}">Deny</button><button class="btn" data-action="edit-draft" data-id="${draft.id}">${icon("edit", 14)} Edit</button><button class="btn success" data-action="approve" data-id="${draft.id}">Approve & queue</button>`
        : `<button class="btn" data-action="close-modal">Close</button>`,
    });
  } catch (error) {
    toast(error.message, "error");
  }
}

function openImportModal() {
  openModal({
    title: "Import leads",
    sub: "CSV or JSON. The file is read locally and stored in the gitignored SQLite database.",
    body: `
      <form id="modal-form">
        <div class="field"><label for="import-campaign">Campaign</label><select class="select" id="import-campaign" name="campaign_id">${state.campaigns.map((campaign) => `<option value="${campaign.id}" ${String(state.campaignId || "") === String(campaign.id) ? "selected" : ""}>${esc(campaign.name)}</option>`).join("")}</select></div>
        <div class="field mt-12"><label for="import-file">CSV or JSON file</label><input class="input" id="import-file" name="file" type="file" accept=".csv,.json" required style="padding-top:7px" /><div class="hint">Supported: Mailroom CSV, ICPExtractor leads.json, or the sheet-ready CSV format.</div></div>
        <div class="notice mt-12">Real lead data stays on this Mac. Never commit the database or the source CSV to the public repository.</div>
      </form>
    `,
    footer: `<button class="btn" data-action="close-modal">Cancel</button><button class="btn primary" type="submit" form="modal-form">Import</button>`,
    onSubmit: async (formData) => {
      const campaignId = formData.get("campaign_id");
      const file = formData.get("file");
      if (!file || !file.name) throw new Error("Choose a CSV or JSON file first");
      const body = new FormData();
      body.append("campaign_id", campaignId);
      body.append("file", file);
      const response = await fetch(`${API}/leads/import`, { method: "POST", body });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Import failed");
      toast(`Imported ${data.imported} lead(s) and generated ${data.drafts} draft(s).`);
      await loadCampaigns();
      await refreshApprovalBadge();
      renderCampaignOptions();
      if (state.page === "leads") renderPage();
      else navigate("leads");
    },
  });
}

/* ----------------------------- suppression ----------------------------- */

async function renderSuppression(token) {
  const data = await api("/suppression");
  if (token !== state.renderToken) return;
  const items = data.items || [];
  $("#page").innerHTML = `
    <div class="page-head">
      <div><h1 class="page-title">Suppression</h1><div class="page-sub">${esc(PAGES.suppression.sub)}</div></div>
      <div class="page-actions"><a class="btn" href="#/leads">${icon("leads", 14)} Back to leads</a></div>
    </div>
    <div class="grid dashboard-grid">
      <div class="card">
        <div class="card-head"><div><div class="card-title">Suppression list</div><div class="card-sub">${fmtNumber(items.length)} permanent stop address(es).</div></div></div>
        <div class="table-wrap"><table class="table suppression-table"><thead><tr><th>Email</th><th>Reason</th><th>Added</th><th></th></tr></thead><tbody>${items.map((item) => `<tr><td><span class="mono" style="font-size:11px">${esc(item.email)}</span></td><td class="cell-muted">${esc(item.reason || "-")}</td><td class="cell-muted cell-nowrap">${esc(fmtDate(item.created_at))}</td><td class="cell-actions"><button class="btn xs ghost" data-action="suppression-remove" data-email="${esc(item.email)}">Remove</button></td></tr>`).join("") || `<tr><td colspan="4">${emptyState("No suppressed addresses", "Denied contacts with Never contact ticked appear here. You can also add one manually.", "shield")}</td></tr>`}</tbody></table></div>
      </div>
      <div class="card">
        <div class="card-head"><div><div class="card-title">Add a stop address</div><div class="card-sub">This blocks campaign queueing and sending.</div></div></div>
        <form class="card-body" id="suppression-form">
          <div class="field"><label for="sup-email">Email</label><input class="input" id="sup-email" name="email" type="email" placeholder="person@example.com" required /></div>
          <div class="field mt-12"><label for="sup-reason">Reason</label><input class="input" id="sup-reason" name="reason" placeholder="Unsubscribed, competitor, do not contact..." /></div>
          <button class="btn primary mt-16" type="submit">${icon("plus", 14)} Add to suppression</button>
          <div class="notice mt-12">Adding an address here denies its pending drafts and cancels its queued sends immediately. A denied draft only suppresses the address when you tick the box in the deny dialog.</div>
        </form>
      </div>
    </div>
  `;
  $("#suppression-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      const result = await api("/suppression", {
        method: "POST",
        body: JSON.stringify({ email: form.email.value, reason: form.reason.value }),
      });
      toast(
        `Address suppressed. ${result.drafts_denied} draft(s) denied and ${result.queue_cancelled} queued send(s) cancelled.`,
      );
      renderPage();
    } catch (error) {
      toast(error.message, "error");
    }
  });
}

/* ----------------------------- inboxes ----------------------------- */

async function renderInboxes(token) {
  const [mailboxes, domains] = await Promise.all([api("/mailboxes"), api("/domains")]);
  if (token !== state.renderToken) return;
  state.inboxes = mailboxes.items || [];
  state.domains = domains.items || [];
  const totalCapacity = state.inboxes.reduce((sum, item) => sum + Number(item.daily_limit || 0), 0);
  const sentToday = state.inboxes.reduce((sum, item) => sum + Number(item.sent_today || 0), 0);
  const warmupToday = state.inboxes.reduce((sum, item) => sum + Number(item.warmup_sent_today || 0), 0);
  const realCount = state.inboxes.filter((item) => item.transport !== "mock").length;
  $("#page").innerHTML = `
    <div class="page-head">
      <div><h1 class="page-title">Inboxes & domains</h1><div class="page-sub">${esc(PAGES.inboxes.sub)}</div></div>
      <div class="page-actions"><button class="btn" data-action="new-domain">${icon("plus", 15)} Add domain</button><button class="btn primary" data-action="new-mailbox">${icon("plus", 15)} Add mailbox</button></div>
    </div>
    <div class="grid stat-grid">
      <div class="card stat-card"><div class="stat-label">Domains</div><div class="stat-value">${fmtNumber(state.domains.length)}</div><div class="stat-foot">${state.domains.filter((d) => d.status === "active").length} active</div></div>
      <div class="card stat-card"><div class="stat-label">Mailboxes</div><div class="stat-value">${fmtNumber(state.inboxes.length)}</div><div class="stat-foot">${realCount} real · ${state.inboxes.length - realCount} mock</div></div>
      <div class="card stat-card"><div class="stat-label">Campaign capacity</div><div class="stat-value">${fmtNumber(totalCapacity)}</div><div class="stat-foot">campaign sends across the pool</div></div>
      <div class="card stat-card"><div class="stat-label">Sending today</div><div class="stat-value">${fmtNumber(sentToday + warmupToday)}</div><div class="stat-foot">${fmtNumber(sentToday)} campaign · ${fmtNumber(warmupToday)} warmup</div></div>
    </div>
    <div class="domain-grid grid mt-16">
      ${state.domains.map((domain) => `
        <div class="card domain-card">
          <div class="domain-top"><div class="domain-icon">${icon("globe", 16)}</div><div style="min-width:0;flex:1"><div class="domain-name">${esc(domain.name)}</div><div class="domain-provider">${esc(domain.provider || "custom")} · ${fmtNumber(domain.mailbox_count)} inboxes</div></div>${domain.status === "active" ? '<span class="chip green">Active</span>' : '<span class="chip gray">Paused</span>'}</div>
          <div class="dns-pills">${dnsChip("MX", domain.mx_status)}${dnsChip("SPF", domain.spf_status)}${dnsChip("DKIM", domain.dkim_status)}${dnsChip("DMARC", domain.dmarc_status)}</div>
          <div class="domain-stats"><span><strong>${fmtNumber(domain.sent_today)}</strong> sent today</span><span><strong>${fmtNumber(domain.mailbox_count)}</strong> inboxes</span><span class="muted-2">${domain.last_check_at ? `checked ${esc(fmtRelative(domain.last_check_at))}` : "not checked"}</span></div>
          <div class="row mt-12"><button class="btn sm" data-action="check-domain" data-id="${domain.id}">${icon("refresh", 12)} Check DNS</button><button class="btn sm ghost" data-action="new-mailbox" data-domain="${domain.id}">${icon("plus", 12)} Add inbox</button><button class="icon-btn bordered" data-action="domain-settings" data-id="${domain.id}" title="Domain settings" aria-label="Domain settings">${icon("settings", 13)}</button></div>
        </div>
      `).join("") || `<div class="card">${emptyState("No domains yet", "Add a sending domain, then add mailboxes under it.", "globe")}</div>`}
    </div>
    <div class="card mt-16">
      <div class="card-head"><div><div class="card-title">Mailbox pool</div><div class="card-sub">Per-inbox caps and connection state.</div></div><div class="right"><button class="btn sm" data-action="new-mailbox">${icon("plus", 13)} Add mailbox</button></div></div>
      <div class="table-wrap">
        <table class="table mailbox-table">
          <thead><tr><th>Mailbox</th><th>Domain</th><th>Transport</th><th>Campaigns</th><th>Campaign / warmup</th><th>Hour</th><th>Status</th><th></th></tr></thead>
          <tbody>${state.inboxes.map((mailbox) => `
            <tr>
              <td><div class="cell-person"><div class="avatar sm ${avatarTone(mailbox.email)}">${esc(initials(mailbox.display_name || mailbox.email))}</div><div><div class="name">${esc(mailbox.display_name || mailbox.email.split("@")[0])}</div><div class="sub mono">${esc(mailbox.email)}</div></div></div></td>
              <td class="cell-muted">${esc(mailbox.domain_name)}</td>
              <td>${transportChip(mailbox.transport)}</td>
              <td class="cell-muted truncate" style="max-width:170px" title="${esc(mailbox.campaigns || "")}">${esc(mailbox.campaigns || "Unassigned")}</td>
              <td><div class="usage-inline">${progress(mailbox.sent_today, mailbox.daily_limit, "green")}<span>${fmtNumber(mailbox.sent_today)}/${fmtNumber(mailbox.daily_limit)}</span></div><div class="sub">${fmtNumber(mailbox.warmup_sent_today)} warmup · ${fmtNumber(mailbox.combined_sent_today)} total</div></td>
              <td class="cell-muted">${fmtNumber(mailbox.sent_hour)}/${fmtNumber(mailbox.hourly_limit)}</td>
              <td>${mailbox.status === "active" ? '<span class="chip green">Active</span>' : '<span class="chip amber">Paused</span>'}</td>
              <td class="cell-actions"><button class="btn xs" data-action="test-mailbox" data-id="${mailbox.id}">Test</button><button class="btn xs ghost" data-action="${mailbox.status === "active" ? "pause-mailbox" : "resume-mailbox"}" data-id="${mailbox.id}">${mailbox.status === "active" ? "Pause" : "Resume"}</button><button class="icon-btn bordered" data-action="edit-mailbox" data-id="${mailbox.id}" title="Edit mailbox" aria-label="Edit mailbox">${icon("settings", 13)}</button></td>
            </tr>
          `).join("")}</tbody>
        </table>
      </div>
    </div>
  `;
}

function openDomainModal() {
  openModal({
    title: "Add domain",
    sub: "Use a separate subdomain for outreach. DNS checks are read-only.",
    body: `
      <form id="modal-form">
        <div class="field"><label for="domain-name">Domain</label><input class="input" id="domain-name" name="name" placeholder="outreach.example.com" required /><div class="hint">No protocol, no path. SPF, DKIM and DMARC can be checked after saving.</div></div>
        <div class="form-grid mt-12">
          <div class="field"><label for="domain-provider">Provider</label><input class="input" id="domain-provider" name="provider" placeholder="Google Workspace, Zoho, other" /></div>
          <div class="field"><label for="domain-selector">DKIM selector</label><input class="input" id="domain-selector" name="dkim_selector" value="mail" /></div>
        </div>
      </form>
    `,
    footer: `<button class="btn" data-action="close-modal">Cancel</button><button class="btn primary" type="submit" form="modal-form">Add domain</button>`,
    onSubmit: async (formData) => {
      await api("/domains", {
        method: "POST",
        body: JSON.stringify({
          name: formData.get("name"),
          provider: formData.get("provider") || "other",
          dkim_selector: formData.get("dkim_selector") || "mail",
        }),
      });
      toast("Domain added. Run a DNS check next.");
      renderPage();
    },
  });
}

function openDomainSettings(id) {
  const domain = state.domains.find((item) => Number(item.id) === Number(id));
  if (!domain) return;
  openModal({
    title: "Domain settings",
    sub: domain.name,
    body: `
      <form id="modal-form">
        <div class="field"><label for="ds-provider">Provider label</label><input class="input" id="ds-provider" name="provider" value="${esc(domain.provider || "")}" placeholder="Google Workspace, Microsoft 365, custom..." /></div>
        <div class="field mt-12"><label for="ds-selector">DKIM selector</label><input class="input" id="ds-selector" name="dkim_selector" value="${esc(domain.dkim_selector || "mail")}" /><div class="hint">The selector used for <code>&lt;selector&gt;._domainkey.${esc(domain.name)}</code>. Change it, save, then run Check DNS.</div></div>
        <div class="field mt-12"><label for="ds-status">Status</label><select class="select" id="ds-status" name="status"><option value="active" ${domain.status === "active" ? "selected" : ""}>Active</option><option value="paused" ${domain.status === "paused" ? "selected" : ""}>Paused</option></select></div>
        <div class="notice mt-12">Pausing a domain stops campaign and warmup sends from every mailbox on it.</div>
      </form>
    `,
    footer: `<button class="btn" data-action="close-modal">Cancel</button><button class="btn primary" type="submit" form="modal-form">Save domain</button>`,
    onSubmit: async (formData) => {
      await api(`/domains/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          provider: formData.get("provider"),
          dkim_selector: formData.get("dkim_selector") || "mail",
          status: formData.get("status"),
        }),
      });
      toast("Domain settings saved. Run Check DNS if the selector changed.");
      renderPage();
    },
  });
}

function openMailboxModal(domainId = null, mailbox = null) {
  if (!state.domains.length) {
    toast("Add a domain first.", "error");
    return;
  }
  const editing = Boolean(mailbox);
  const selectedDomain = String(mailbox?.domain_id || domainId || state.domains[0].id);
  const transport = mailbox?.transport || "mock";
  const checkedCampaigns = new Set(
    (editing ? mailbox.campaign_ids || [] : state.campaigns.map((campaign) => campaign.id)).map(Number),
  );
  const timezone = mailbox?.timezone || state.settings.default_timezone || "Asia/Kolkata";
  openModal({
    title: editing ? "Edit mailbox" : "Add mailbox",
    sub: editing ? `${mailbox.email} · leave a password blank to keep the saved one` : "Mock is safe. SMTP and Apps Script are real transports.",
    wide: true,
    body: `
      <form id="modal-form">
        <div class="form-grid">
          <div class="field"><label for="mb-domain">Domain</label>${editing ? `<input class="input" id="mb-domain" value="${esc(mailbox.domain_name || "")}" disabled />` : `<select class="select" id="mb-domain" name="domain_id">${state.domains.map((domain) => `<option value="${domain.id}" ${selectedDomain === String(domain.id) ? "selected" : ""}>${esc(domain.name)}</option>`).join("")}</select>`}</div>
          <div class="field"><label for="mb-email">Mailbox email</label><input class="input" id="mb-email" name="email" type="email" value="${esc(mailbox?.email || "")}" ${editing ? "disabled" : ""} placeholder="alex@outreach.example.com" required /></div>
          <div class="field"><label for="mb-name">Display name</label><input class="input" id="mb-name" name="display_name" value="${esc(mailbox?.display_name || "")}" placeholder="Alex Morgan" /></div>
          <div class="field"><label for="mb-transport">Transport</label><select class="select" id="mb-transport" name="transport">${[["mock", "Mock - safe local outbox"], ["smtp", "SMTP - real mail"], ["gas", "Google Apps Script webhook"]].map(([value, label]) => `<option value="${value}" ${transport === value ? "selected" : ""}>${label}</option>`).join("")}</select></div>
        </div>
        <div class="form-section" data-for-transports="smtp">
          <div class="form-section-title">SMTP</div>
          <div class="form-grid">
            <div class="field"><label for="mb-host">Host</label><input class="input" id="mb-host" name="smtp_host" value="${esc(mailbox?.smtp_host || "")}" placeholder="smtp.example.com" /></div>
            <div class="field"><label for="mb-port">Port</label><input class="input" id="mb-port" name="smtp_port" type="number" value="${esc(mailbox?.smtp_port || 587)}" /></div>
            <div class="field"><label for="mb-user">Username</label><input class="input" id="mb-user" name="smtp_username" value="${esc(mailbox?.smtp_username || "")}" /></div>
            <div class="field"><label for="mb-pass">Password</label><input class="input" id="mb-pass" name="smtp_password" type="password" placeholder="${editing && mailbox.has_smtp_password ? "Saved. Leave blank to keep." : "Stored encrypted on this Mac"}" /></div>
          </div>
        </div>
        <div class="form-section" data-for-transports="gas">
          <div class="form-section-title">Google Apps Script</div>
          <div class="form-grid">
            <div class="field"><label for="mb-gas">Webhook URL</label><input class="input" id="mb-gas" name="gas_url" value="${esc(mailbox?.gas_url || "")}" placeholder="https://script.google.com/..." /></div>
            <div class="field"><label for="mb-secret">Shared secret</label><input class="input" id="mb-secret" name="gas_secret" type="password" placeholder="${editing && mailbox.has_gas_secret ? "Saved. Leave blank to keep." : ""}" /></div>
          </div>
        </div>
        <div class="form-section" data-for-transports="smtp,gas">
          <div class="form-section-title">IMAP (optional, for warmup read flags)</div>
          <div class="form-grid">
            <div class="field"><label for="mb-imap-host">Host</label><input class="input" id="mb-imap-host" name="imap_host" value="${esc(mailbox?.imap_host || "")}" placeholder="imap.example.com" /></div>
            <div class="field"><label for="mb-imap-port">Port</label><input class="input" id="mb-imap-port" name="imap_port" type="number" value="${esc(mailbox?.imap_port || 993)}" /></div>
            <div class="field"><label for="mb-imap-user">Username</label><input class="input" id="mb-imap-user" name="imap_username" value="${esc(mailbox?.imap_username || "")}" /></div>
            <div class="field"><label for="mb-imap-pass">Password</label><input class="input" id="mb-imap-pass" name="imap_password" type="password" placeholder="${editing && mailbox.has_imap_password ? "Saved. Leave blank to keep." : "Stored encrypted on this Mac"}" /></div>
          </div>
        </div>
        <div class="form-section">
          <div class="form-section-title">Caps and schedule</div>
          <div class="form-grid">
            <div class="field"><label for="mb-daily">Daily limit</label><input class="input" id="mb-daily" name="daily_limit" type="number" value="${esc(mailbox?.daily_limit || 25)}" /></div>
            <div class="field"><label for="mb-hourly">Hourly limit</label><input class="input" id="mb-hourly" name="hourly_limit" type="number" value="${esc(mailbox?.hourly_limit || 5)}" /></div>
            <div class="field"><label for="mb-min">Min gap (seconds)</label><input class="input" id="mb-min" name="min_gap_seconds" type="number" value="${esc(mailbox?.min_gap_seconds || 45)}" /></div>
            <div class="field"><label for="mb-max">Max gap (seconds)</label><input class="input" id="mb-max" name="max_gap_seconds" type="number" value="${esc(mailbox?.max_gap_seconds || 240)}" /></div>
            <div class="field full"><label for="mb-timezone">Timezone</label><input class="input" id="mb-timezone" name="timezone" value="${esc(timezone)}" /></div>
          </div>
        </div>
        <div class="field mt-12"><label>Assign to campaigns</label><div class="row wrap" style="gap:12px">${state.campaigns.map((campaign) => `<label class="checkline"><input type="checkbox" name="campaign_ids" value="${campaign.id}" ${checkedCampaigns.has(Number(campaign.id)) ? "checked" : ""} /> ${esc(campaign.name)}</label>`).join("")}</div></div>
      </form>
    `,
    footer: `<button class="btn" data-action="close-modal">Cancel</button><button class="btn primary" type="submit" form="modal-form">${editing ? "Save mailbox" : "Add mailbox"}</button>`,
    onReady: (root) => {
      const select = $("#mb-transport", root);
      const update = () => {
        $$("[data-for-transports]", root).forEach((section) => {
          const allowed = section.dataset.forTransports.split(",");
          section.classList.toggle("hidden", !allowed.includes(select.value));
        });
      };
      select.addEventListener("change", update);
      update();
    },
    onSubmit: async (formData) => {
      const selectedTransport = formData.get("transport");
      const payload = {
        display_name: formData.get("display_name") || "",
        transport: selectedTransport,
        smtp_host: selectedTransport === "smtp" ? formData.get("smtp_host") || null : null,
        smtp_port: selectedTransport === "smtp" && formData.get("smtp_port") ? Number(formData.get("smtp_port")) : null,
        smtp_username: selectedTransport === "smtp" ? formData.get("smtp_username") || null : null,
        smtp_password: selectedTransport === "smtp" ? formData.get("smtp_password") || null : null,
        imap_host: selectedTransport !== "mock" ? formData.get("imap_host") || null : null,
        imap_port: selectedTransport !== "mock" && formData.get("imap_port") ? Number(formData.get("imap_port")) : null,
        imap_username: selectedTransport !== "mock" ? formData.get("imap_username") || null : null,
        imap_password: selectedTransport !== "mock" ? formData.get("imap_password") || null : null,
        gas_url: selectedTransport === "gas" ? formData.get("gas_url") || null : null,
        gas_secret: selectedTransport === "gas" ? formData.get("gas_secret") || null : null,
        daily_limit: Number(formData.get("daily_limit")),
        hourly_limit: Number(formData.get("hourly_limit")),
        min_gap_seconds: Number(formData.get("min_gap_seconds")),
        max_gap_seconds: Number(formData.get("max_gap_seconds")),
        timezone: formData.get("timezone") || "Asia/Kolkata",
        campaign_ids: formData.getAll("campaign_ids").map(Number),
      };
      if (editing) {
        for (const key of ["smtp_password", "imap_password", "gas_secret"]) {
          if (!payload[key]) delete payload[key];
        }
        await api(`/mailboxes/${mailbox.id}`, { method: "PATCH", body: JSON.stringify(payload) });
        toast("Mailbox updated. Run Test if the connection changed.");
      } else {
        payload.domain_id = Number(formData.get("domain_id"));
        payload.email = formData.get("email");
        await api("/mailboxes", { method: "POST", body: JSON.stringify(payload) });
        toast("Mailbox added. Use Test to check the connection.");
      }
      renderPage();
    },
  });
}

async function testMailbox(id) {
  try {
    const result = await api(`/mailboxes/${id}/test`, { method: "POST" });
    toast(result.message || (result.ok ? "Connection OK" : "Connection failed"), result.ok ? "success" : "error");
  } catch (error) {
    toast(error.message, "error");
  }
}

async function toggleMailbox(id, action) {
  await api(`/mailboxes/${id}/${action}`, { method: "POST" });
  toast(action === "pause" ? "Mailbox paused." : "Mailbox resumed.");
  renderPage();
}

async function checkDomain(id) {
  try {
    const result = await api(`/domains/${id}/check`, { method: "POST" });
    toast(`DNS checked: MX ${result.mx}, SPF ${result.spf}, DKIM ${result.dkim}, DMARC ${result.dmarc}.`, result.spf === "pass" && result.dmarc === "pass" ? "success" : "error");
    renderPage();
  } catch (error) {
    toast(error.message, "error");
  }
}

/* ----------------------------- deliverability ----------------------------- */

async function renderDeliverability(token) {
  const data = await api("/deliverability");
  if (token !== state.renderToken) return;
  state.deliverability = data;
  const domains = data.domains || [];
  const mailboxes = data.mailboxes || [];
  const campaigns = data.campaigns || [];
  const daily = buildDailySeries(data.daily || []);
  const maxDaily = Math.max(1, ...daily.map((item) => item.sent));
  const sentToday = mailboxes.reduce((sum, item) => sum + Number(item.sent_today || 0), 0);
  const warmupToday = mailboxes.reduce((sum, item) => sum + Number(item.warmup_sent_today || 0), 0);
  const capacity = mailboxes.reduce((sum, item) => sum + Number(item.daily_limit || 0), 0);
  const bounceToday = mailboxes.reduce((sum, item) => sum + Number(item.bounces_today || 0), 0);

  $("#page").innerHTML = `
    <div class="page-head">
      <div><h1 class="page-title">Deliverability</h1><div class="page-sub">${esc(PAGES.deliverability.sub)}</div></div>
      <div class="page-actions"><button class="btn" data-action="refresh">${icon("refresh", 15)} Refresh</button></div>
    </div>
    <div class="grid stat-grid">
      <div class="card stat-card"><div class="stat-label">Sending today</div><div class="stat-value">${fmtNumber(sentToday + warmupToday)}</div><div class="stat-foot">${fmtNumber(sentToday)} campaign · ${fmtNumber(warmupToday)} warmup · ${fmtNumber(capacity)} campaign capacity</div></div>
      <div class="card stat-card"><div class="stat-label">Active domains</div><div class="stat-value">${fmtNumber(domains.filter((d) => d.status === "active").length)}</div><div class="stat-foot">${domains.length} configured</div></div>
      <div class="card stat-card"><div class="stat-label">Bounces today</div><div class="stat-value">${fmtNumber(bounceToday)}</div><div class="stat-foot">No reputation scoring yet</div></div>
      <div class="card stat-card"><div class="stat-label">DNS checks</div><div class="stat-value">${fmtNumber(domains.filter((d) => d.spf_status === "pass" && d.dmarc_status === "pass").length)}</div><div class="stat-foot">domains with SPF and DMARC pass</div></div>
    </div>

    <div class="grid deliverability-grid mt-16">
      <div class="grid" style="gap:14px">
        <div class="card">
          <div class="card-head"><div><div class="card-title">Last 7 days</div><div class="card-sub">Campaign sends from the local usage table. Warmup is counted separately.</div></div><div class="right"><div class="legend"><span><i></i> Sent</span></div></div></div>
          <div class="card-body">
            <div class="chart">${daily.map((item) => `<div class="chart-col"><div class="chart-bars"><div class="chart-bar" style="height:${Math.max(2, Math.round((item.sent / maxDaily) * 100))}%"></div></div><div class="chart-label">${esc(item.label)}</div></div>`).join("")}</div>
            <div class="row small muted mt-12"><span>Today: <strong>${fmtNumber(sentToday)}</strong></span><span>Capacity: ${fmtNumber(capacity)}</span><span>Campaign caps below</span></div>
          </div>
        </div>

        <div class="card">
          <div class="card-head"><div><div class="card-title">Domains</div><div class="card-sub">DNS state and volume by sending domain.</div></div></div>
          <div class="card-body" style="padding:6px 17px 10px">
            ${domains.map((domain) => `
              <div class="domain-row">
                <div class="main"><div class="name">${esc(domain.name)}</div><div class="dns-pills">${dnsChip("SPF", domain.spf_status)}${dnsChip("DKIM", domain.dkim_status)}${dnsChip("DMARC", domain.dmarc_status)}</div></div>
                <div class="domain-volume"><strong>${fmtNumber(domain.sent_today)}</strong> / ${fmtNumber(domain.daily_capacity)}<div>${fmtNumber(domain.mailbox_count)} inboxes · ${fmtNumber(domain.warmup_sent_today)} warmup</div></div>
                <button class="btn xs" data-action="check-domain" data-id="${domain.id}">Check</button>
              </div>
            `).join("")}
          </div>
        </div>
      </div>

      <div class="grid" style="gap:14px">
        <div class="card">
          <div class="card-head"><div><div class="card-title">Campaign caps</div><div class="card-sub">Volume against each campaign limit.</div></div></div>
          <div class="card-body">${campaigns.map((campaign) => `<div class="cap-row"><div class="main"><div class="name">${esc(campaign.name)}</div><div class="sub">${fmtNumber(campaign.total_sent)} of ${fmtNumber(campaign.total_leads)} leads sent</div></div><div style="width:110px">${progress(campaign.sent_today, campaign.daily_limit, "green")}</div><div class="value">${fmtNumber(campaign.sent_today)}/${fmtNumber(campaign.daily_limit)}</div></div>`).join("") || emptyState("No campaigns", "Create a campaign to see caps.", "campaigns")}</div>
        </div>
        <div class="card">
          <div class="card-head"><div><div class="card-title">Mailbox caps</div><div class="card-sub">The real limit is per inbox.</div></div></div>
          <div class="card-body">${mailboxes.slice(0, 8).map((mailbox) => `<div class="cap-row"><div class="main"><div class="name truncate">${esc(mailbox.email)}</div><div class="sub">${esc(mailbox.domain_name)} · ${esc(mailbox.transport)}</div></div><div style="width:90px">${progress(mailbox.sent_today, mailbox.daily_limit, "green")}</div><div class="value">${fmtNumber(mailbox.sent_today)}/${fmtNumber(mailbox.daily_limit)}</div></div>`).join("")}<a class="btn ghost sm mt-8" href="#/inboxes">View all ${fmtNumber(mailboxes.length)} inboxes ${icon("arrow", 12)}</a></div>
        </div>
        <div class="card card-body"><div class="notice">DNS checks are read-only. The demo domains use .test, so SPF, DKIM and DMARC will show missing until you replace them with real domains.</div></div>
      </div>
    </div>
  `;
}

function buildDailySeries(rows) {
  const map = new Map(rows.map((row) => [row.date, row]));
  const result = [];
  for (let offset = 6; offset >= 0; offset -= 1) {
    const date = new Date();
    date.setDate(date.getDate() - offset);
    const key = [
      date.getFullYear(),
      String(date.getMonth() + 1).padStart(2, "0"),
      String(date.getDate()).padStart(2, "0"),
    ].join("-");
    const row = map.get(key) || {};
    result.push({ date: key, sent: Number(row.sent || 0), label: new Intl.DateTimeFormat("en-US", { weekday: "short" }).format(date) });
  }
  return result;
}

/* ----------------------------- warmup ----------------------------- */

async function renderWarmup(token) {
  const data = await api("/warmup");
  if (token !== state.renderToken) return;
  state.warmup = data;
  const summary = data.summary || {};
  const settings = data.settings || {};
  const profiles = data.profiles || [];
  const active = profiles.filter((profile) => profile.enabled && ["ramping", "active"].includes(profile.status));
  const pairs = data.pair_preview || [];
  const recent = data.recent || [];
  const phases = [
    ["Days 1-3", settings.ramp?.[0] || 2],
    ["Days 4-7", settings.ramp?.[3] || 4],
    ["Days 8-14", settings.ramp?.[7] || 6],
    ["Days 15-21", settings.ramp?.[14] || 10],
    ["Days 22-30", settings.ramp?.[21] || 15],
    ["Day 31+", settings.ramp?.[29] || 20],
  ];
  $("#page").innerHTML = `
    <div class="page-head">
      <div><h1 class="page-title">Warmup</h1><div class="page-sub">${esc(PAGES.warmup.sub)}</div></div>
      <div class="page-actions">
        <span class="chip ${active.length ? "green" : "gray"}" title="Auto-refreshes every 6 seconds"><span class="dot"></span>${active.length ? "Live" : "Off"}</span>
        <button class="btn" data-action="refresh">${icon("refresh", 14)} Refresh</button>
        <button class="btn" data-action="warmup-settings">${icon("settings", 14)} Settings</button>
        <button class="btn" data-action="warmup-tick">${icon("play", 14)} Run tick</button>
        ${active.length ? `<button class="btn" data-action="warmup-pause-all">${icon("pause", 14)} Pause all</button>` : `<button class="btn primary" data-action="warmup-start-all">${icon("zap", 14)} Start all</button>`}
      </div>
    </div>

    <div class="notice ${active.length ? "violet" : "amber"}" style="margin-bottom:14px">
      <strong>${active.length ? "Closed-pool warmup is active." : "Warmup is currently off."}</strong>
      Your 10 domains and 25 mailboxes can warm each other, but this is a closed pool. Mailroom uses cross-domain pairs only, a ${fmtNumber(settings.pair_cooldown_days)}-day pair cooldown, ${fmtNumber(settings.daily_limit)} sends per mailbox per day and ${fmtNumber(settings.domain_daily_limit)} per domain per day. Add 2-4 external seed inboxes (Gmail or Outlook) later for a stronger reputation network.
    </div>

    <div class="grid stat-grid">
      <div class="card stat-card"><div class="stat-label">${icon("target", 14)} Active warmups</div><div class="stat-value">${fmtNumber(summary.active)}</div><div class="stat-foot">${fmtNumber(summary.total)} profiles configured</div><div class="stat-icon violet">${icon("target", 15)}</div></div>
      <div class="card stat-card"><div class="stat-label">${icon("send", 14)} Sent today</div><div class="stat-value">${fmtNumber(summary.sent_today)}</div><div class="stat-foot">${fmtNumber(summary.threads_today)} threads created</div><div class="stat-icon blue">${icon("send", 15)}</div></div>
      <div class="card stat-card"><div class="stat-label">${icon("mail", 14)} Replies today</div><div class="stat-value">${fmtNumber(summary.replies_today)}</div><div class="stat-foot">${fmtNumber(summary.opened_today)} opened</div><div class="stat-icon green">${icon("checkCircle", 15)}</div></div>
      <div class="card stat-card"><div class="stat-label">${icon("activity", 14)} Average health</div><div class="stat-value">${fmtNumber(summary.average_health)}<span style="font-size:14px;color:var(--muted-2)">/100</span></div><div class="stat-foot">${fmtNumber(summary.queued)} queued · ${fmtNumber(summary.failed)} failed</div><div class="stat-icon amber">${icon("activity", 15)}</div></div>
    </div>

    <div class="card mt-16">
      <div class="card-head"><div><div class="card-title">Mailbox warmup</div><div class="card-sub">Cross-domain only. Every profile has its own ramp and caps.</div></div><div class="right"><span class="chip ${active.length ? "violet" : "gray"}">${active.length ? "Running" : "Off"}</span></div></div>
        <div class="table-wrap" style="max-height:650px">
          <table class="table warmup-table">
            <thead><tr><th>Mailbox</th><th>Status</th><th>Day</th><th>Target</th><th>Sent</th><th>Replies</th><th>Health</th><th></th></tr></thead>
            <tbody>${profiles.map((profile) => `
              <tr>
                <td><div class="cell-person"><div class="avatar sm ${avatarTone(profile.email)}">${esc(initials(profile.display_name || profile.email))}</div><div><div class="name">${esc(profile.display_name || profile.email.split("@")[0])}</div><div class="sub mono">${esc(profile.email)}</div></div></div></td>
                <td>${statusChip(profile.status)}</td>
                <td class="cell-muted">${fmtNumber(profile.day)}</td>
                <td class="cell-muted">${fmtNumber(profile.daily_target)}/day</td>
                <td><div class="usage-inline">${progress(profile.sent_today, Math.max(1, profile.daily_target), "green")}<span>${fmtNumber(profile.sent_today)}</span></div></td>
                <td class="cell-muted">${fmtNumber(profile.replies_today)}</td>
                <td><div class="usage-inline">${progress(profile.health, 100, "green")}<span>${fmtNumber(profile.health)}</span></div></td>
                <td class="cell-actions">${profile.enabled && ["ramping", "active"].includes(profile.status) ? `<button class="btn xs ghost" data-action="warmup-pause-one" data-id="${profile.id}">Pause</button>` : `<button class="btn xs" data-action="warmup-start-one" data-id="${profile.id}">Start</button>`}</td>
              </tr>
            `).join("")}</tbody>
          </table>
        </div>
    </div>

    <div class="grid campaign-grid mt-16">
        <div class="card">
          <div class="card-head"><div><div class="card-title">Pairing preview</div><div class="card-sub">Next cross-domain interactions. No same-domain pairs.</div></div><div class="right"><span class="chip gray">${fmtNumber(pairs.length)} shown</span></div></div>
          <div class="card-body flush" style="padding:6px 17px 10px">
            ${pairs.length ? pairs.map((pair) => `<div class="queue-row"><div class="queue-main"><div class="name">${esc(pair.from)} <span style="color:var(--muted-2)">to</span> ${esc(pair.to || "no eligible target")}</div><div class="sub">${esc(pair.from_domain)} → ${esc(pair.to_domain || "waiting")}</div></div><span class="chip violet">Cross-domain</span></div>`).join("") : emptyState("No active pairs", "Start warmup to generate a cross-domain pairing plan.", "target")}
          </div>
        </div>

        <div class="card">
          <div class="card-head"><div><div class="card-title">Ramp and rules</div><div class="card-sub">Conservative by default. Raise caps only after DNS and placement are stable.</div></div></div>
          <div class="card-body">
            <div class="form-grid" style="gap:8px">
              ${phases.map(([label, value]) => `<div class="cap-row"><div class="main"><div class="name">${esc(label)}</div><div class="sub">warmup sends per mailbox</div></div><span class="chip gray">${fmtNumber(value)}/day</span></div>`).join("")}
            </div>
            <div class="divider"></div>
            <div class="cap-row"><div class="main"><div class="name">Reply rate</div><div class="sub">simulated and real replies</div></div><span class="chip green">${Math.round(Number(settings.reply_rate || 0) * 100)}%</span></div>
            <div class="cap-row"><div class="main"><div class="name">Open / read rate</div><div class="sub">best-effort IMAP read flag</div></div><span class="chip blue">${Math.round(Number(settings.open_rate || 0) * 100)}%</span></div>
            <div class="cap-row"><div class="main"><div class="name">Mark important</div><div class="sub">best-effort IMAP important flag</div></div><span class="chip amber">${Math.round(Number(settings.important_rate || 0) * 100)}%</span></div>
            <div class="cap-row"><div class="main"><div class="name">Pair cooldown</div><div class="sub">same two mailboxes cannot repeat</div></div><span class="chip gray">${fmtNumber(settings.pair_cooldown_days)} days</span></div>
            <div class="cap-row"><div class="main"><div class="name">Window</div><div class="sub">local mailbox timezone</div></div><span class="chip gray">${esc(settings.window_start)}-${esc(settings.window_end)}</span></div>
            <div class="notice mt-12">This is an activity score, not a provider reputation score. Add external seed inboxes and monitor real placement before relying on it.</div>
          </div>
        </div>

        <div class="card">
          <div class="card-head"><div><div class="card-title">Recent warmup activity</div><div class="card-sub">Opens and replies are recorded, not guessed.</div></div></div>
          <div class="card-body">${recent.length ? `<div class="timeline">${recent.slice(0, 7).map((message) => `<div class="timeline-item ${message.kind === "reply" ? "green" : "violet"}"><div class="timeline-title">${message.kind === "reply" ? "Reply sent" : "Warmup sent"} <span class="muted-2 small">${esc(message.from_email)} → ${esc(message.to_email)}</span></div><div class="timeline-sub">${message.read_at ? "read" : "not read"}${message.replied_at ? " · replied" : ""}</div><div class="timeline-time">${esc(fmtDate(message.sent_at))}</div></div>`).join("")}</div>` : emptyState("No warmup activity", "Start a batch and run a tick to see the interaction log.", "activity")}</div>
        </div>
    </div>
  `;
}

function openWarmupSettings() {
  const settings = state.warmup?.settings || {};
  openModal({
    title: "Warmup settings",
    sub: "Keep these conservative for new domains. The defaults are designed for a closed pool.",
    wide: true,
    body: `
      <form id="modal-form">
        <div class="form-grid">
          <div class="field"><label for="wu-daily">Daily limit per mailbox</label><input class="input" id="wu-daily" name="warmup_daily_limit" type="number" min="1" value="${esc(settings.daily_limit || 10)}" /></div>
          <div class="field"><label for="wu-domain">Daily limit per domain</label><input class="input" id="wu-domain" name="warmup_domain_daily_limit" type="number" min="1" value="${esc(settings.domain_daily_limit || 50)}" /></div>
          <div class="field"><label for="wu-cooldown">Pair cooldown (days)</label><input class="input" id="wu-cooldown" name="warmup_pair_cooldown_days" type="number" min="1" value="${esc(settings.pair_cooldown_days || 7)}" /></div>
          <div class="field"><label for="wu-reply">Reply rate (%)</label><input class="input" id="wu-reply" name="warmup_reply_rate" type="number" min="0" max="100" value="${Math.round(Number(settings.reply_rate || 0.3) * 100)}" /></div>
          <div class="field"><label for="wu-open">Open / read rate (%)</label><input class="input" id="wu-open" name="warmup_open_rate" type="number" min="0" max="100" value="${Math.round(Number(settings.open_rate || 0.8) * 100)}" /></div>
          <div class="field"><label for="wu-important">Mark important rate (%)</label><input class="input" id="wu-important" name="warmup_important_rate" type="number" min="0" max="100" value="${Math.round(Number(settings.important_rate || 0.3) * 100)}" /></div>
          <div class="field"><label for="wu-gap-min">Minimum gap (seconds)</label><input class="input" id="wu-gap-min" name="warmup_min_gap_seconds" type="number" min="1" value="${esc(settings.min_gap || 5)}" /></div>
          <div class="field"><label for="wu-gap-max">Maximum gap (seconds)</label><input class="input" id="wu-gap-max" name="warmup_max_gap_seconds" type="number" min="1" value="${esc(settings.max_gap || 30)}" /></div>
          <div class="field"><label for="wu-window-start">Window start</label><input class="input" id="wu-window-start" name="warmup_window_start" type="time" value="${esc(settings.window_start || "00:00")}" /></div>
          <div class="field"><label for="wu-window-end">Window end</label><input class="input" id="wu-window-end" name="warmup_window_end" type="time" value="${esc(settings.window_end || "23:59")}" /></div>
          <div class="field"><label for="wu-max-tick">Max sends per tick</label><input class="input" id="wu-max-tick" name="warmup_max_sends_per_tick" type="number" min="1" value="${esc(settings.max_per_tick || 10)}" /></div>
          <div class="field full"><label for="wu-ramp">Ramp (comma-separated sends per mailbox per day)</label><input class="input" id="wu-ramp" name="warmup_ramp" value="${esc((settings.ramp || []).join(","))}" /></div>
        </div>
        <label class="checkline mt-12"><input type="checkbox" name="warmup_weekdays_only" ${settings.weekdays_only ? "checked" : ""}/> Weekdays only</label>
        <div class="notice mt-12">For real domains, raise the gap to 5-15 minutes and keep 5-10 sends per mailbox per day. The demo uses short gaps so you can see activity immediately.</div>
      </form>
    `,
    footer: `<button class="btn" data-action="close-modal">Cancel</button><button class="btn primary" type="submit" form="modal-form">Save warmup settings</button>`,
    onSubmit: async (formData) => {
      const values = {
        warmup_daily_limit: formData.get("warmup_daily_limit"),
        warmup_domain_daily_limit: formData.get("warmup_domain_daily_limit"),
        warmup_pair_cooldown_days: formData.get("warmup_pair_cooldown_days"),
        warmup_reply_rate: String(Number(formData.get("warmup_reply_rate")) / 100),
        warmup_open_rate: String(Number(formData.get("warmup_open_rate")) / 100),
        warmup_important_rate: String(Number(formData.get("warmup_important_rate")) / 100),
        warmup_min_gap_seconds: formData.get("warmup_min_gap_seconds"),
        warmup_max_gap_seconds: formData.get("warmup_max_gap_seconds"),
        warmup_window_start: formData.get("warmup_window_start"),
        warmup_window_end: formData.get("warmup_window_end"),
        warmup_max_sends_per_tick: formData.get("warmup_max_sends_per_tick"),
        warmup_ramp: formData.get("warmup_ramp"),
        warmup_weekdays_only: formData.get("warmup_weekdays_only") === "on" ? "1" : "0",
      };
      await api("/warmup/settings", { method: "PATCH", body: JSON.stringify({ values }) });
      toast("Warmup settings saved.");
      renderPage();
    },
  });
}

async function warmupAction(action, id = null) {
  try {
    if (action === "start-all") {
      const profiles = state.warmup?.profiles || [];
      const real = profiles.filter((profile) => profile.transport && profile.transport !== "mock").length;
      const message = real
        ? `${real} mailbox(es) use a real transport. Warmup will send real email through them. Check DNS, caps and the gap settings first.`
        : "This starts the ramp for all eligible mailboxes. The demo pool uses the mock transport, so nothing leaves this Mac.";
      openConfirm("Start warmup?", message, async () => {
        const result = await api("/warmup/start", {
          method: "POST",
          body: JSON.stringify({ daily_limit: Number(state.warmup?.settings?.daily_limit || 10) }),
        });
        toast(`Warmup started for ${result.started} mailboxes. ${result.tick?.generated || 0} thread(s) generated.`);
        renderPage();
      });
      return;
    }
    if (action === "tick") {
      const result = await api("/warmup/tick", { method: "POST" });
      toast(`Warmup tick: ${result.generated || 0} generated, ${result.sent || 0} sent, ${result.replied || 0} replied.`);
      renderPage();
      return;
    }
    if (action === "pause-all") {
      await api("/warmup/pause", { method: "POST", body: JSON.stringify({}) });
      toast("Warmup paused for all mailboxes.");
      renderPage();
      return;
    }
    if (action === "start-one") {
      const result = await api("/warmup/start", {
        method: "POST",
        body: JSON.stringify({ mailbox_ids: [id], daily_limit: Number(state.warmup?.settings?.daily_limit || 10) }),
      });
      toast(`Warmup started for ${result.started} mailbox.`);
      renderPage();
      return;
    }
    if (action === "pause-one") {
      await api("/warmup/pause", { method: "POST", body: JSON.stringify({ mailbox_ids: [id] }) });
      toast("Warmup paused for this mailbox.");
      renderPage();
    }
  } catch (error) {
    toast(error.message, "error");
  }
}

/* ----------------------------- Google Sheets ----------------------------- */

async function renderSheets(token) {
  const data = await api("/sheets/status");
  if (token !== state.renderToken) return;
  state.sheets = data;
  const counts = data.local_counts || {};
  $("#page").innerHTML = `
    <div class="page-head">
      <div><h1 class="page-title">Google Sheets</h1><div class="page-sub">${esc(PAGES.sheets.sub)}</div></div>
      <div class="page-actions"><button class="btn" data-action="refresh">${icon("refresh", 14)} Refresh</button>${data.configured ? `<a class="btn" href="https://docs.google.com/spreadsheets/d/${encodeURIComponent(data.spreadsheet_id)}/edit" target="_blank" rel="noreferrer">${icon("globe", 14)} Open sheet</a>` : ""}<button class="btn" data-action="sheet-test" ${data.configured ? "" : 'disabled title="Save a connection first"'}>${icon("checkCircle", 14)} Test connection</button><button class="btn primary" data-action="sheet-sync" data-direction="both" ${data.configured ? "" : 'disabled title="Save a connection first"'}>${icon("refresh", 14)} Two-way sync</button></div>
    </div>
    ${data.configured ? `<div class="notice green" style="margin-bottom:14px">Connected${data.service_account_email ? ` as <strong>${esc(data.service_account_email)}</strong>` : ""}. Last sync: ${data.last_sync_at ? esc(fmtDate(data.last_sync_at)) : "never"}.</div>` : `<div class="notice amber" style="margin-bottom:14px">Not configured. Add a spreadsheet ID and service account JSON below, share the sheet with the service account email, then test.</div>`}
    <div class="grid dashboard-grid">
      <div class="card">
        <div class="card-head"><div><div class="card-title">Connection</div><div class="card-sub">Use a dedicated spreadsheet. The service account needs edit access.</div></div><div class="right"><span class="chip ${data.configured ? "green" : "gray"}">${data.configured ? "Configured" : "Not configured"}</span></div></div>
        <form class="card-body" id="sheets-form">
          <div class="field"><label for="sheet-id">Spreadsheet ID</label><input class="input" id="sheet-id" name="spreadsheet_id" value="${esc(data.spreadsheet_id || "")}" placeholder="1AbC... from the sheet URL" /></div>
          <div class="field mt-12"><label for="sheet-credentials">Service account JSON</label><textarea class="textarea" id="sheet-credentials" name="credentials_json" style="min-height:150px" placeholder="${data.credentials_present ? "Saved. Paste a new JSON to replace it." : "Paste the service account JSON here"}"></textarea><div class="hint">The JSON is encrypted at rest with the local Mailroom key. It is never returned by the API.</div></div>
          <div class="field mt-8"><label for="sheet-json-file">Or upload the JSON key file</label><input class="input" id="sheet-json-file" type="file" accept=".json,application/json" style="padding-top:7px" /></div>
          <div class="field mt-12"><label for="sheet-policy">Conflict policy</label><select class="select" id="sheet-policy" name="conflict_policy"><option value="merge" ${data.conflict_policy === "merge" ? "selected" : ""}>Merge: stop on conflicts and report them</option><option value="local" ${data.conflict_policy === "local" ? "selected" : ""}>Local wins</option><option value="remote" ${data.conflict_policy === "remote" ? "selected" : ""}>Sheet wins</option></select></div>
          <div class="row mt-16"><button class="btn primary" type="submit">${icon("check", 14)} Save connection</button><span class="muted small">The next step is Test connection.</span></div>
          ${data.service_account_email ? `<div class="notice violet mt-12">Share the sheet with <strong>${esc(data.service_account_email)}</strong> as an Editor. This is the service account, not your Google login.</div>` : ""}
        </form>
      </div>

      <div class="grid" style="gap:14px">
        <div class="card">
          <div class="card-head"><div><div class="card-title">Sync actions</div><div class="card-sub">Pull reads the sheet. Push writes the local database. Both applies non-conflicting remote changes, then writes.</div></div></div>
          <div class="card-body">
            <div class="row wrap"><button class="btn" data-action="sheet-sync" data-direction="pull" ${data.configured ? "" : "disabled"}>Pull from sheet</button><button class="btn" data-action="sheet-sync" data-direction="push" ${data.configured ? "" : "disabled"}>Push to sheet</button><button class="btn" data-action="sheet-sync" data-direction="both" data-dry="1" ${data.configured ? "" : "disabled"}>Dry run</button><button class="btn primary" data-action="sheet-sync" data-direction="both" ${data.configured ? "" : "disabled"}>Sync both ways</button></div>
            <div class="divider"></div>
            <div class="cap-row"><div class="main"><div class="name">Local records</div><div class="sub">leads · campaigns · suppression · warmup profiles</div></div><span class="chip gray">${fmtNumber(counts.leads)} · ${fmtNumber(counts.campaigns)} · ${fmtNumber(counts.suppression)} · ${fmtNumber(counts.warmup)}</span></div>
            <div class="cap-row"><div class="main"><div class="name">Tabs</div><div class="sub">created automatically on test</div></div><span class="chip gray">${Object.values(data.tabs || {}).length}</span></div>
            <div id="sheet-result" class="mt-12"></div>
          </div>
        </div>

        <div class="card card-body">
          <div class="card-title">What syncs</div>
          <div class="cap-row"><div class="main"><div class="name">Leads</div><div class="sub">name, email, role, company, industry, city, website, notes, offer, grade, verification</div></div><span class="chip green">Two-way</span></div>
          <div class="cap-row"><div class="main"><div class="name">Campaigns</div><div class="sub">name, status, limits, window, timezone, rotation</div></div><span class="chip green">Two-way</span></div>
          <div class="cap-row"><div class="main"><div class="name">Suppression</div><div class="sub">union of local and sheet emails</div></div><span class="chip blue">Union</span></div>
          <div class="cap-row"><div class="main"><div class="name">Warmup</div><div class="sub">read-only health and volume snapshot</div></div><span class="chip gray">Read-only</span></div>
          <div class="notice mt-12">Lead status is app-controlled. Use Approvals for approve/deny. This avoids a sheet edit bypassing the approval gate.</div>
        </div>

        <div class="card card-body">
          <div class="card-title">Setup</div>
          <div class="card-sub mt-8">1. Create a Google Cloud service account and enable the Sheets API. 2. Download the JSON key. 3. Share the spreadsheet with the service account email as Editor. 4. Paste the spreadsheet ID and JSON above. 5. Test connection, then pull.</div>
          <div class="small muted mt-12">Full guide: docs/GOOGLE_SHEETS.md</div>
        </div>
      </div>
    </div>
  `;
  $("#sheet-json-file").addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      $("#sheet-credentials").value = await file.text();
      toast("JSON key loaded. Click Save connection.");
    } catch (error) {
      toast(error.message, "error");
    }
  });
  $("#sheets-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await api("/sheets/configure", {
        method: "POST",
        body: JSON.stringify({
          spreadsheet_id: form.spreadsheet_id.value,
          credentials_json: form.credentials_json.value || null,
          conflict_policy: form.conflict_policy.value,
        }),
      });
      toast("Google Sheets connection saved. Run Test connection.");
      renderPage();
    } catch (error) {
      toast(error.message, "error");
    }
  });
}

async function sheetTest() {
  try {
    const result = await api("/sheets/test", { method: "POST" });
    toast(`Connected to ${result.spreadsheet}. ${Object.keys(result.tabs || {}).length} tabs ready.`);
    renderSheetResult({ ok: true, ...result });
  } catch (error) {
    toast(error.message, "error");
    renderSheetResult({ ok: false, error: error.message });
  }
}

async function sheetSync(direction, dryRun) {
  try {
    const result = await api("/sheets/sync", {
      method: "POST",
      body: JSON.stringify({ direction, dry_run: dryRun }),
    });
    const prefix = dryRun ? "Dry run" : "Sync";
    const failed = !result.ok || result.conflicts?.length || result.errors?.length;
    toast(`${prefix}: ${result.conflicts?.length || 0} conflict(s), ${result.errors?.length || 0} error(s).`, failed ? "error" : "success");
    renderSheetResult(result);
  } catch (error) {
    toast(error.message, "error");
    renderSheetResult({ ok: false, error: error.message });
  }
}

function renderSheetResult(result) {
  const box = $("#sheet-result");
  if (!box) return;
  const conflicts = result.conflicts || [];
  const errors = result.errors || [];
  const pulled = result.pulled || {};
  const pushed = result.pushed || {};
  const isTest = Boolean(result.spreadsheet && !result.pulled && !result.pushed);
  const tabs = result.tabs ? Object.values(result.tabs) : [];
  const failure = result.error || result.detail || "";
  const summary = isTest
    ? `Connected to ${esc(result.spreadsheet)}. ${tabs.length} tabs ready: ${tabs.map(esc).join(", ")}.`
    : `Pulled leads ${pulled.leads?.updated ?? 0}, created ${pulled.leads?.created ?? 0}; campaigns ${pulled.campaigns?.updated ?? 0}; suppression ${pulled.suppression?.inserted ?? 0}. Pushed leads ${pushed.leads ?? 0}, campaigns ${pushed.campaigns ?? 0}, warmup ${pushed.warmup ?? 0}.`;
  box.innerHTML = `
    <div class="notice ${result.ok && !conflicts.length && !errors.length ? "green" : "red"}">
      <strong>${isTest ? "Connection test" : result.ok === false ? "Needs attention" : "Sync result"}</strong>
      ${failure ? `<div class="mt-8">${esc(failure)}</div>` : ""}
      ${result.aborted_push ? `<div class="mt-8">${esc(result.aborted_push)}</div>` : ""}
      ${conflicts.length ? `<div class="mt-8">${conflicts.length} conflict(s) left untouched. Choose a policy or resolve the rows in the sheet.</div>` : ""}
      ${errors.length ? `<div class="mt-8">${errors.length} error(s).</div>` : ""}
      ${!failure && !conflicts.length && !errors.length ? `<div class="mt-8">${summary}</div>` : ""}
    </div>
    ${conflicts.length || errors.length ? `<div class="code-block mt-8">${esc(JSON.stringify({ conflicts, errors }, null, 2))}</div>` : ""}
  `;
}

/* ----------------------------- queue ----------------------------- */

async function renderQueue(token) {
  const base = state.campaignId ? `campaign_id=${encodeURIComponent(state.campaignId)}&` : "";
  const [data, sentData] = await Promise.all([
    api(`/queue?${base}`),
    api(`/queue?${base}status=sent&limit=12`),
  ]);
  if (token !== state.renderToken) return;
  state.queue = data;
  const items = data.items || [];
  const recent = sentData.items || [];
  const counts = data.counts || {};
  $("#page").innerHTML = `
    <div class="page-head">
      <div><h1 class="page-title">Send queue</h1><div class="page-sub">${esc(PAGES.queue.sub)} ${state.campaignId ? `Viewing <strong>${esc(campaignName(state.campaignId))}</strong>.` : ""}</div></div>
      <div class="page-actions"><span class="chip green" title="Auto-refreshes every 6 seconds"><span class="dot"></span>Live</span><button class="btn" data-action="queue-tick">${icon("play", 14)} Run worker</button><button class="btn" data-action="refresh">${icon("refresh", 15)} Refresh</button></div>
    </div>
    ${data.sending_paused ? `<div class="notice red" style="margin-bottom:14px"><strong>Sending is paused globally.</strong> The worker will hold these items until you resume in <a href="#/settings" style="text-decoration:underline">Settings</a>.</div>` : ""}
    <div class="grid stat-grid">
      <div class="card stat-card"><div class="stat-label">Queued</div><div class="stat-value">${fmtNumber(counts.queued)}</div><div class="stat-foot">waiting for their slot</div></div>
      <div class="card stat-card"><div class="stat-label">Sending</div><div class="stat-value">${fmtNumber(counts.leased)}</div><div class="stat-foot">leased by the worker</div></div>
      <div class="card stat-card"><div class="stat-label">Sent</div><div class="stat-value">${fmtNumber(counts.sent)}</div><div class="stat-foot">completed all time</div></div>
      <div class="card stat-card"><div class="stat-label">Failed</div><div class="stat-value">${fmtNumber(counts.failed)}</div><div class="stat-foot">needs an operator</div></div>
    </div>
    <div class="card mt-16">
      <div class="card-head"><div><div class="card-title">Upcoming sends</div><div class="card-sub">Each row has a mailbox reservation and a send time.</div></div><div class="right"><button class="btn sm" data-action="queue-tick">${icon("zap", 13)} Tick worker</button></div></div>
      ${items.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Scheduled</th><th>Person</th><th>Campaign</th><th>Mailbox</th><th>Status</th><th>Attempts</th><th></th></tr></thead><tbody>${items.map((item) => `
        <tr><td class="cell-nowrap">${esc(fmtDate(item.scheduled_at))}<div class="sub">${esc(fmtRelative(item.scheduled_at))}</div></td><td><div class="cell-person"><div class="avatar sm ${avatarTone(item.name)}">${esc(initials(item.name))}</div><div><div class="name">${esc(item.name)}</div><div class="sub">${esc(item.company)} · ${esc(item.email)}</div></div></div></td><td class="cell-muted">${esc(item.campaign_name)}</td><td class="cell-muted mono" style="font-size:10.5px">${esc(item.mailbox_email)}</td><td>${statusChip(item.status)}${item.last_error ? `<div class="sub" title="${esc(item.last_error)}">${esc(item.last_error.slice(0, 70))}${item.last_error.length > 70 ? "…" : ""}</div>` : ""}</td><td class="cell-muted">${fmtNumber(item.attempts)}</td><td class="cell-actions">${["queued", "failed"].includes(item.status) ? `<button class="btn xs" data-action="send-now" data-id="${item.id}">Send now</button><button class="btn xs ghost" data-action="cancel-queue" data-id="${item.id}">Cancel</button>` : ""}</td></tr>
      `).join("")}</tbody></table></div>` : emptyState("Queue is empty", "Approve a draft to reserve a mailbox and a send slot.", "queue")}
    </div>
    <div class="card mt-16">
      <div class="card-head"><div><div class="card-title">Recently sent</div><div class="card-sub">The last ${fmtNumber(recent.length)} accepted sends. Click a row to open the lead.</div></div><div class="right"><span class="chip green">${fmtNumber(counts.sent)} total</span></div></div>
      ${recent.length ? `<div class="table-wrap"><table class="table recent-table"><thead><tr><th>Sent</th><th>Person</th><th>Campaign</th><th>Mailbox</th><th>Subject</th><th>Status</th></tr></thead><tbody>${recent.map((item) => `
        <tr class="clickable" data-action="open-lead" data-id="${item.lead_id}" tabindex="0"><td class="cell-nowrap">${esc(fmtDate(item.updated_at))}<div class="sub">${esc(fmtRelative(item.updated_at))}</div></td><td><div class="cell-person"><div class="avatar sm ${avatarTone(item.name)}">${esc(initials(item.name))}</div><div><div class="name">${esc(item.name)}</div><div class="sub">${esc(item.company || "")} · ${esc(item.email)}</div></div></div></td><td class="cell-muted">${esc(item.campaign_name)}</td><td class="cell-muted mono" style="font-size:10.5px">${esc(item.mailbox_email)}</td><td class="cell-muted truncate" style="max-width:280px" title="${esc(item.subject)}">${esc(item.subject)}</td><td>${statusChip(item.status)}</td></tr>
      `).join("")}</tbody></table></div>` : emptyState("No sends yet", "Approved drafts appear here after the worker sends them.", "send")}
    </div>
  `;
}

async function queueTick() {
  try {
    const result = await api("/queue/tick", { method: "POST" });
    toast(`Worker processed ${result.processed || 0} item(s), sent ${result.sent || 0}.`);
    renderPage();
  } catch (error) {
    toast(error.message, "error");
  }
}

async function sendNow(id) {
  try {
    await api(`/queue/${id}/send-now`, { method: "POST" });
    toast("Send completed. Check the queue and activity log.");
    renderPage();
  } catch (error) {
    toast(error.message, "error");
  }
}

function cancelQueue(id) {
  openConfirm("Cancel this send?", "The draft will be denied and removed from the queue. It will not be sent.", async () => {
    await api(`/queue/${id}/cancel`, { method: "POST" });
    toast("Queue item cancelled.");
    renderPage();
  });
}

/* ----------------------------- activity ----------------------------- */

async function renderActivity(token) {
  const data = await api("/activity?limit=300");
  if (token !== state.renderToken) return;
  state.activity = data.items || [];
  $("#page").innerHTML = `
    <div class="page-head">
      <div><h1 class="page-title">Activity</h1><div class="page-sub">${esc(PAGES.activity.sub)}</div></div>
      <div class="page-actions"><button class="btn" data-action="refresh">${icon("refresh", 15)} Refresh</button></div>
    </div>
    <div class="card">
      <div class="table-toolbar"><select class="select" id="activity-kind" style="width:190px;height:32px"><option value="">All events</option>${[...new Set(state.activity.map((item) => item.kind))].sort().map((kind) => `<option value="${esc(kind)}">${esc(activityMeta(kind)[0])}</option>`).join("")}</select><span class="spacer"></span><span class="muted small">${fmtNumber(state.activity.length)} events</span></div>
      <div id="activity-list"></div>
    </div>
  `;
  renderActivityList();
  $("#activity-kind").addEventListener("change", renderActivityList);
}

function renderActivityList() {
  const kind = $("#activity-kind")?.value || "";
  const items = state.activity.filter((item) => !kind || item.kind === kind);
  const container = $("#activity-list");
  if (!container) return;
  container.innerHTML = items.length ? `<div class="card-body"><div class="timeline">${items.map((item) => {
    const meta = activityMeta(item.kind);
    return `<div class="timeline-item ${meta[1]}"><div class="timeline-title">${esc(meta[0])}${item.entity_type ? ` <span class="muted-2 small">· ${esc(item.entity_type)} ${esc(item.entity_id)}</span>` : ""}</div><div class="timeline-sub">${esc(activityDetail(item))}</div><div class="timeline-time">${esc(fmtDate(item.created_at))}</div></div>`;
  }).join("")}</div></div>` : emptyState("No events", "Try another filter.", "activity");
}

/* ----------------------------- settings ----------------------------- */

async function renderSettings(token) {
  const data = await api("/settings");
  if (token !== state.renderToken) return;
  state.settings = data.values || {};
  $("#page").innerHTML = `
    <div class="page-head"><div><h1 class="page-title">Settings</h1><div class="page-sub">${esc(PAGES.settings.sub)}</div></div></div>
    <div class="grid dashboard-grid">
      <div class="card">
        <div class="card-head"><div><div class="card-title">Sender identity</div><div class="card-sub">Used by the default template and the agent hook.</div></div></div>
        <form class="card-body" id="settings-form">
          <div class="form-grid">
            <div class="field"><label for="set-name">Sender name</label><input class="input" id="set-name" name="sender_name" value="${esc(state.settings.sender_name || "")}" /></div>
            <div class="field"><label for="set-title">Sender title</label><input class="input" id="set-title" name="sender_title" value="${esc(state.settings.sender_title || "")}" /></div>
            <div class="field"><label for="set-company">Company</label><input class="input" id="set-company" name="sender_company" value="${esc(state.settings.sender_company || "")}" /></div>
            <div class="field"><label for="set-timezone">Default timezone</label><input class="input" id="set-timezone" name="default_timezone" value="${esc(state.settings.default_timezone || "Asia/Kolkata")}" /></div>
            <div class="field full"><label for="set-offer">Default offer</label><input class="input" id="set-offer" name="default_offer" value="${esc(state.settings.default_offer || "")}" /><div class="hint">Used when a lead has no offer from the ICP pack.</div></div>
          </div>
          <div class="form-section">
            <div class="form-section-title">Safety and agent hook</div>
            <div class="toggle-row"><div><div class="toggle-label">Require DNS pass before real sending</div><div class="toggle-hint">Mock mode never blocks. This is a guard for SMTP or Apps Script.</div></div><label class="switch"><input type="checkbox" name="require_dns_pass" ${state.settings.require_dns_pass === "1" ? "checked" : ""}/><span></span></label></div>
            <div class="toggle-row"><div><div class="toggle-label">Pause all sending</div><div class="toggle-hint">Blocks new approvals and stops the campaign queue. Warmup keeps running on its own switch.</div></div><label class="switch"><input type="checkbox" name="sending_paused" ${state.settings.sending_paused === "1" ? "checked" : ""}/><span></span></label></div>
            <div class="field mt-12"><label for="set-webhook">Agent webhook</label><input class="input" id="set-webhook" name="agent_webhook" value="${esc(state.settings.agent_webhook || "")}" placeholder="https://your-agent.example/draft" /><div class="hint">Optional. Use the Agent button on an approval to POST one lead and receive JSON with subject and body. Leave empty to keep the local template.</div></div>
          </div>
          <div class="row mt-16"><button class="btn primary" type="submit">${icon("check", 14)} Save settings</button><span class="muted small">Stored in the local database.</span></div>
        </form>
      </div>
      <div class="grid" style="gap:14px">
        <div class="card card-body">
          <div class="card-title">Mock mode is the default</div>
          <div class="card-sub mt-8">Every mailbox created by the demo uses the mock transport. The worker writes .eml files to data/outbox/ and marks the message sent. No email leaves this Mac.</div>
          <div class="notice green mt-12">Safe for testing the approval flow with real-looking leads.</div>
        </div>
        <div class="card card-body">
          <div class="card-title">Going live</div>
          <div class="card-sub mt-8">1. Add a real domain. 2. Add an SMTP or Apps Script mailbox. 3. Run DNS checks. 4. Test the mailbox. 5. Raise caps gradually.</div>
          <div class="notice mt-12">Real sending requires a deliberate transport change per mailbox. The demo database and synthetic leads stay separate from your real ICP import.</div>
        </div>
        <div class="card card-body">
          <div class="card-title">Agent contract</div>
          <div class="card-sub mt-8">POST to your webhook with <code>{instruction, campaign, lead}</code>. Return <code>{subject, body}</code>. Click <strong>Agent</strong> on an approval to re-draft that lead. A failed call leaves the existing draft unchanged.</div>
          <div class="mono small muted mt-12" style="background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:10px;line-height:1.5">{"subject":"...","body":"..."}</div>
        </div>
      </div>
    </div>
  `;
  $("#settings-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const values = {
      sender_name: form.sender_name.value,
      sender_title: form.sender_title.value,
      sender_company: form.sender_company.value,
      default_timezone: form.default_timezone.value,
      default_offer: form.default_offer.value,
      agent_webhook: form.agent_webhook.value,
      require_dns_pass: form.require_dns_pass.checked ? "1" : "0",
      sending_paused: form.sending_paused.checked ? "1" : "0",
    };
    try {
      await api("/settings", { method: "PATCH", body: JSON.stringify({ values }) });
      toast("Settings saved.");
    } catch (error) {
      toast(error.message, "error");
    }
  });
}

/* ----------------------------- help and modal ----------------------------- */

function openHelpModal() {
  openModal({
    title: "How Mailroom works",
    sub: "A quick map of the approval, sending, warmup and sync layers.",
    wide: true,
    body: `
      <div class="grid" style="grid-template-columns:1fr 1fr;gap:12px">
        <div class="card card-body">
          <div class="card-title">1. Approve</div>
          <div class="card-sub mt-8">Open Approvals, choose a campaign in the left sidebar, and review one person at a time. Approve & queue reserves a mailbox and a send slot. Deny is terminal. Status is app-controlled, not editable from the sheet.</div>
          <a class="btn sm mt-12" href="#/approvals">Open approvals</a>
        </div>
        <div class="card card-body">
          <div class="card-title">2. Send</div>
          <div class="card-sub mt-8">The queue worker checks caps, domain limits, the send window and the mailbox. Mock mode writes .eml files under data/outbox. Real SMTP or Apps Script mailboxes send for real.</div>
          <a class="btn sm mt-12" href="#/queue">Open queue</a>
        </div>
        <div class="card card-body">
          <div class="card-title">3. Warm up</div>
          <div class="card-sub mt-8">Your 10 domains and 25 mailboxes can warm each other, but it is a closed pool. Warmup uses cross-domain pairs, a 7-day pair cooldown, a slow ramp and separate caps. Add 2-4 external seed inboxes later.</div>
          <a class="btn sm mt-12" href="#/warmup">Open warmup</a>
        </div>
        <div class="card card-body">
          <div class="card-title">4. Sync a sheet</div>
          <div class="card-sub mt-8">Leads and campaigns can go both ways. Suppression is a union. Warmup is read-only. Conflicts are reported instead of silently overwritten. Open the Google Sheets page for setup.</div>
          <a class="btn sm mt-12" href="#/sheets">Open sheets</a>
        </div>
      </div>
      <div class="notice green mt-12">Default = mock mode. No mail leaves this Mac until a real mailbox transport is configured. Real lead data stays in data/mailroom.db and is gitignored.</div>
      <div class="notice mt-12">The detailed guides are docs/OPERATIONS.md, docs/WARMUP.md and docs/GOOGLE_SHEETS.md in the repository.</div>
    `,
    footer: `<button class="btn primary" data-action="close-modal">Got it</button>`,
  });
}

function closeModal() {
  const root = $("#modal-root");
  if (root) root.innerHTML = "";
}

function openModal({ title, sub = "", body = "", footer = "", wide = false, narrow = false, onSubmit = null, onReady = null }) {
  closeModal();
  const root = $("#modal-root");
  root.innerHTML = `
    <div class="modal-backdrop" data-action="close-modal">
      <div class="modal ${wide ? "wide" : ""} ${narrow ? "narrow" : ""}" role="dialog" aria-modal="true">
        <div class="modal-head"><div><div class="modal-title">${esc(title)}</div>${sub ? `<div class="modal-sub">${esc(sub)}</div>` : ""}</div><button class="icon-btn" data-action="close-modal" aria-label="Close">${icon("x", 16)}</button></div>
        <div class="modal-body">${body}</div>
        ${footer ? `<div class="modal-foot">${footer}</div>` : ""}
      </div>
    </div>
  `;
  const modal = $(".modal", root);
  modal.addEventListener("click", (event) => event.stopPropagation());
  const form = $("#modal-form", root);
  if (form && onSubmit) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submit = $('button[type="submit"]', root);
      if (submit) submit.disabled = true;
      try {
        await onSubmit(new FormData(form), form);
        closeModal();
      } catch (error) {
        toast(error.message || "Could not save", "error");
        if (submit) submit.disabled = false;
      }
    });
  }
  if (onReady) onReady(root);
}

function openConfirm(title, message, onConfirm, confirmLabel = "Confirm", danger = false) {
  openModal({
    title,
    narrow: true,
    body: `<form id="modal-form"><div class="notice">${esc(message)}</div><input type="hidden" name="confirm" value="yes" /></form>`,
    footer: `<button class="btn" data-action="close-modal">Cancel</button><button class="btn ${danger ? "danger" : "primary"}" type="submit" form="modal-form">${esc(confirmLabel)}</button>`,
    onSubmit: async () => {
      await onConfirm();
    },
  });
}

function navigate(page) {
  if (location.hash === `#/${page}`) renderPage();
  else location.hash = `#/${page}`;
}

/* ----------------------------- events ----------------------------- */

document.addEventListener("click", async (event) => {
  const target = event.target.closest("[data-action]");
  if (!target) return;
  if (target.tagName === "A") event.preventDefault();
  const action = target.dataset.action;
  const id = target.dataset.id ? Number(target.dataset.id) : null;

  if (action === "close-modal") {
    closeModal();
    return;
  }
  if (action === "refresh") {
    renderPage();
    return;
  }
  if (action === "clear-campaign") {
    state.campaignId = null;
    localStorage.removeItem("mailroom.campaign");
    renderCampaignOptions();
    renderPage();
    return;
  }
  if (action === "help") {
    openHelpModal();
    return;
  }
  if (action === "new-campaign") {
    openCampaignModal();
    return;
  }
  if (action === "import-leads") {
    openImportModal();
    return;
  }
  if (action === "new-domain") {
    openDomainModal();
    return;
  }
  if (action === "new-mailbox") {
    openMailboxModal(target.dataset.domain ? Number(target.dataset.domain) : null);
    return;
  }
  if (action === "select-approval") {
    if (target.tagName === "INPUT") return;
    state.selectedApproval = id;
    renderApprovalList();
    renderApprovalDetail();
    return;
  }
  if (action === "toggle-approval-check") {
    event.stopPropagation();
    if (target.checked) state.approvalChecked.add(id);
    else state.approvalChecked.delete(id);
    renderApprovalList();
    return;
  }
  if (action === "approve") {
    closeModal();
    await approveDraft(id);
    return;
  }
  if (action === "deny") {
    closeModal();
    openDenyModal(id);
    return;
  }
  if (action === "edit-draft") {
    openEditDraftModal(id);
    return;
  }
  if (action === "regenerate-draft") {
    try {
      await api(`/drafts/${id}/regenerate`, { method: "POST" });
      toast("Draft re-rendered from the campaign template.");
      await loadApprovals();
    } catch (error) {
      toast(error.message, "error");
    }
    return;
  }
  if (action === "agent-draft") {
    if (target.dataset.busy) return;
    const original = target.innerHTML;
    target.dataset.busy = "1";
    target.disabled = true;
    target.innerHTML = `${icon("zap", 12)} Working...`;
    try {
      await api(`/drafts/${id}/agent`, { method: "POST" });
      toast("The agent returned a new draft. Review it before approving.");
      await loadApprovals();
    } catch (error) {
      toast(error.message, "error");
    } finally {
      delete target.dataset.busy;
      target.disabled = false;
      target.innerHTML = original;
    }
    return;
  }
  if (action === "bulk-approve") {
    await bulkApprovals("approve");
    return;
  }
  if (action === "bulk-deny") {
    await bulkApprovals("deny");
    return;
  }
  if (action === "open-campaign") {
    state.campaignId = id;
    localStorage.setItem("mailroom.campaign", String(id));
    renderCampaignOptions();
    navigate("leads");
    return;
  }
  if (action === "campaign-settings") {
    openCampaignSettings(id);
    return;
  }
  if (action === "toggle-campaign") {
    try {
      await toggleCampaign(id);
    } catch (error) {
      toast(error.message, "error");
    }
    return;
  }
  if (action === "lead-page") {
    state.leadFilters.page = Number(target.dataset.page || 1);
    await loadLeads();
    return;
  }
  if (action === "open-lead") {
    await openLeadModal(id);
    return;
  }
  if (action === "suppression-remove") {
    const email = target.dataset.email;
    openConfirm(
      "Remove from suppression?",
      `${email} will be eligible for new campaigns again. Existing denied drafts and cancelled sends stay that way.`,
      async () => {
        await api(`/suppression/${encodeURIComponent(email)}`, { method: "DELETE" });
        toast("Address removed from suppression.");
        renderPage();
      },
      "Remove",
      true,
    );
    return;
  }
  if (action === "edit-mailbox") {
    const mailbox = state.inboxes.find((item) => Number(item.id) === Number(id));
    if (mailbox) openMailboxModal(mailbox.domain_id, mailbox);
    return;
  }
  if (action === "test-mailbox") {
    await testMailbox(id);
    return;
  }
  if (action === "pause-mailbox" || action === "resume-mailbox") {
    await toggleMailbox(id, action === "pause-mailbox" ? "pause" : "resume");
    return;
  }
  if (action === "domain-settings") {
    openDomainSettings(id);
    return;
  }
  if (action === "check-domain") {
    await checkDomain(id);
    return;
  }
  if (action === "warmup-settings") {
    openWarmupSettings();
    return;
  }
  if (action === "warmup-tick") {
    await warmupAction("tick");
    return;
  }
  if (action === "warmup-start-all") {
    await warmupAction("start-all");
    return;
  }
  if (action === "warmup-pause-all") {
    await warmupAction("pause-all");
    return;
  }
  if (action === "warmup-start-one") {
    await warmupAction("start-one", id);
    return;
  }
  if (action === "warmup-pause-one") {
    await warmupAction("pause-one", id);
    return;
  }
  if (action === "sheet-test" || action === "sheet-sync") {
    if (target.dataset.busy) return;
    const original = target.innerHTML;
    target.dataset.busy = "1";
    target.disabled = true;
    target.innerHTML = `${icon("refresh", 14)} Working...`;
    try {
      if (action === "sheet-test") await sheetTest();
      else await sheetSync(target.dataset.direction || "both", target.dataset.dry === "1");
    } finally {
      delete target.dataset.busy;
      target.disabled = false;
      target.innerHTML = original;
    }
    return;
  }
  if (action === "queue-tick") {
    await queueTick();
    return;
  }
  if (action === "send-now") {
    await sendNow(id);
    return;
  }
  if (action === "cancel-queue") {
    cancelQueue(id);
    return;
  }
});

document.addEventListener("keydown", (event) => {
  const active = document.activeElement;
  if (
    (event.key === "Enter" || event.key === " ") &&
    active?.dataset?.action &&
    !["BUTTON", "A", "INPUT", "TEXTAREA", "SELECT"].includes(active.tagName)
  ) {
    event.preventDefault();
    active.click();
    return;
  }
  if (event.key === "Escape" && $("#modal-root")?.children.length) {
    closeModal();
    return;
  }
  if (event.key === "?" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) {
    event.preventDefault();
    openHelpModal();
    return;
  }
  if (state.page !== "approvals") return;
  if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) return;
  if (!selectedApprovalItem()) return;
  if (event.key === "j") {
    event.preventDefault();
    moveApproval(1);
  } else if (event.key === "k") {
    event.preventDefault();
    moveApproval(-1);
  } else if (event.key === "a") {
    event.preventDefault();
    approveDraft(state.selectedApproval);
  } else if (event.key === "d") {
    event.preventDefault();
    openDenyModal(state.selectedApproval);
  } else if (event.key === "e") {
    event.preventDefault();
    openEditDraftModal(state.selectedApproval);
  }
});

/* ----------------------------- boot ----------------------------- */

async function init() {
  try {
    await loadCampaigns();
  } catch (error) {
    $("#app").innerHTML = `<div class="boot">Could not load Mailroom: ${esc(error.message)}</div>`;
    return;
  }
  try {
    state.settings = (await api("/settings")).values || {};
  } catch {
    state.settings = {};
  }
  const saved = localStorage.getItem("mailroom.campaign");
  state.campaignId = saved ? Number(saved) : null;
  if (state.campaignId && !state.campaigns.some((item) => Number(item.id) === state.campaignId)) state.campaignId = null;
  renderShell();
  await refreshApprovalBadge();
  window.addEventListener("hashchange", route);
  await route();
  setInterval(() => {
    if (document.visibilityState !== "visible") return;
    if (!["queue", "warmup"].includes(state.page)) return;
    if ($("#modal-root")?.children.length) return;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) return;
    renderPage().catch(() => {});
  }, 6000);
  setInterval(() => {
    if (document.visibilityState === "visible") refreshApprovalBadge();
  }, 30000);
}

init();
