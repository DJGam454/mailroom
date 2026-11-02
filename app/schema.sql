PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL DEFAULT 'other',
    dkim_selector TEXT NOT NULL DEFAULT 'mail',
    spf_status TEXT NOT NULL DEFAULT 'unknown',
    dkim_status TEXT NOT NULL DEFAULT 'unknown',
    dmarc_status TEXT NOT NULL DEFAULT 'unknown',
    mx_status TEXT NOT NULL DEFAULT 'unknown',
    last_check_at TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS mailboxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL DEFAULT '',
    transport TEXT NOT NULL DEFAULT 'mock',
    smtp_host TEXT,
    smtp_port INTEGER,
    smtp_username TEXT,
    smtp_password_enc TEXT,
    imap_host TEXT,
    imap_port INTEGER,
    imap_username TEXT,
    imap_password_enc TEXT,
    gas_url TEXT,
    gas_secret_enc TEXT,
    daily_limit INTEGER NOT NULL DEFAULT 25,
    hourly_limit INTEGER NOT NULL DEFAULT 5,
    min_gap_seconds INTEGER NOT NULL DEFAULT 45,
    max_gap_seconds INTEGER NOT NULL DEFAULT 240,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    status TEXT NOT NULL DEFAULT 'active',
    last_sent_at TEXT,
    next_available_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'draft',
    approval_mode TEXT NOT NULL DEFAULT 'manual',
    daily_limit INTEGER NOT NULL DEFAULT 250,
    per_domain_limit INTEGER NOT NULL DEFAULT 50,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    window_start TEXT NOT NULL DEFAULT '09:30',
    window_end TEXT NOT NULL DEFAULT '17:30',
    working_days TEXT NOT NULL DEFAULT '[1,2,3,4,5]',
    rotation_strategy TEXT NOT NULL DEFAULT 'least_used',
    min_gap_seconds INTEGER NOT NULL DEFAULT 90,
    max_gap_seconds INTEGER NOT NULL DEFAULT 360,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS campaign_mailboxes (
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    mailbox_id INTEGER NOT NULL REFERENCES mailboxes(id) ON DELETE CASCADE,
    weight INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (campaign_id, mailbox_id)
);

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    external_id TEXT,
    name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    industry TEXT NOT NULL DEFAULT '',
    company_domain TEXT NOT NULL DEFAULT '',
    website TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    offer TEXT NOT NULL DEFAULT '',
    email_grade TEXT NOT NULL DEFAULT '',
    verification TEXT NOT NULL DEFAULT 'Unknown',
    source TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE (campaign_id, email)
);

CREATE TABLE IF NOT EXISTS campaign_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    step_no INTEGER NOT NULL DEFAULT 1,
    delay_days INTEGER NOT NULL DEFAULT 0,
    subject_template TEXT NOT NULL,
    body_template TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE (campaign_id, step_no)
);

CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL UNIQUE REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    step_no INTEGER NOT NULL DEFAULT 1,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    approved_at TEXT,
    denied_at TEXT,
    deny_reason TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS send_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER NOT NULL UNIQUE REFERENCES drafts(id) ON DELETE CASCADE,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    mailbox_id INTEGER NOT NULL REFERENCES mailboxes(id),
    scheduled_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    attempts INTEGER NOT NULL DEFAULT 0,
    lease_until TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER NOT NULL REFERENCES drafts(id) ON DELETE CASCADE,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    mailbox_id INTEGER NOT NULL REFERENCES mailboxes(id),
    direction TEXT NOT NULL DEFAULT 'outbound',
    from_email TEXT NOT NULL,
    to_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    message_id TEXT,
    transport TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'sent',
    sent_at TEXT,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS mailbox_usage_daily (
    mailbox_id INTEGER NOT NULL REFERENCES mailboxes(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    sent INTEGER NOT NULL DEFAULT 0,
    failed INTEGER NOT NULL DEFAULT 0,
    bounces INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (mailbox_id, date)
);

CREATE TABLE IF NOT EXISTS suppression (
    email TEXT PRIMARY KEY,
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    entity_type TEXT NOT NULL DEFAULT '',
    entity_id TEXT NOT NULL DEFAULT '',
    detail TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_leads_campaign_status ON leads(campaign_id, status);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_email_lower ON leads(lower(email));
CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);
CREATE INDEX IF NOT EXISTS idx_drafts_campaign ON drafts(campaign_id);
CREATE INDEX IF NOT EXISTS idx_queue_due ON send_queue(status, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_queue_campaign ON send_queue(campaign_id);
CREATE INDEX IF NOT EXISTS idx_messages_lead ON messages(lead_id);
CREATE INDEX IF NOT EXISTS idx_messages_to_email ON messages(lower(to_email));
CREATE INDEX IF NOT EXISTS idx_messages_mailbox ON messages(mailbox_id, sent_at);
CREATE INDEX IF NOT EXISTS idx_usage_date ON mailbox_usage_daily(date);
CREATE INDEX IF NOT EXISTS idx_activity_created ON activity(created_at DESC);

CREATE TABLE IF NOT EXISTS warmup_profiles (
    mailbox_id INTEGER PRIMARY KEY REFERENCES mailboxes(id) ON DELETE CASCADE,
    enabled INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'off',
    started_at TEXT,
    daily_limit INTEGER NOT NULL DEFAULT 10,
    reply_rate REAL NOT NULL DEFAULT 0.30,
    open_rate REAL NOT NULL DEFAULT 0.80,
    important_rate REAL NOT NULL DEFAULT 0.30,
    last_run_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS warmup_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_mailbox_id INTEGER NOT NULL REFERENCES mailboxes(id) ON DELETE CASCADE,
    target_mailbox_id INTEGER NOT NULL REFERENCES mailboxes(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    last_activity_at TEXT
);

CREATE TABLE IF NOT EXISTS warmup_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL REFERENCES warmup_threads(id) ON DELETE CASCADE,
    mailbox_id INTEGER NOT NULL REFERENCES mailboxes(id) ON DELETE CASCADE,
    kind TEXT NOT NULL DEFAULT 'initial',
    direction TEXT NOT NULL DEFAULT 'outbound',
    from_email TEXT NOT NULL,
    to_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    message_id TEXT,
    status TEXT NOT NULL DEFAULT 'sent',
    sent_at TEXT,
    read_at TEXT,
    replied_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS warmup_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL REFERENCES warmup_threads(id) ON DELETE CASCADE,
    mailbox_id INTEGER NOT NULL REFERENCES mailboxes(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    attempts INTEGER NOT NULL DEFAULT 0,
    lease_until TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_warmup_profiles_status ON warmup_profiles(status);
CREATE INDEX IF NOT EXISTS idx_warmup_threads_source ON warmup_threads(source_mailbox_id, created_at);
CREATE INDEX IF NOT EXISTS idx_warmup_threads_target ON warmup_threads(target_mailbox_id, created_at);
CREATE INDEX IF NOT EXISTS idx_warmup_messages_mailbox ON warmup_messages(mailbox_id, sent_at);
CREATE INDEX IF NOT EXISTS idx_warmup_messages_to ON warmup_messages(to_email, sent_at);
CREATE INDEX IF NOT EXISTS idx_warmup_messages_thread ON warmup_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_warmup_queue_due ON warmup_queue(status, scheduled_at);

CREATE TABLE IF NOT EXISTS sheet_sync_state (
    sheet_name TEXT NOT NULL,
    entity_key TEXT NOT NULL,
    local_updated_at TEXT,
    remote_updated_at TEXT,
    last_synced_at TEXT,
    content_hash TEXT,
    PRIMARY KEY (sheet_name, entity_key)
);
