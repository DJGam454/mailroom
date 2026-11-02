# Architecture

## 1. System map

```text
Browser (zero-build SPA)
        |
        | JSON over localhost
        v
FastAPI (app/main.py)
   |        |         |
   |        |         +--> DNS checker (MX/SPF/DMARC/DKIM)
   |        +------------> Scheduler / rotation
   +---------------------> SQLite (WAL) under data/
                              |
                              +--> mock outbox (.eml)
                              +--> SMTP / IMAP per mailbox
                              +--> Google Apps Script webhook per mailbox
```

The background worker runs inside the FastAPI process. It leases due queue
items and sends them. The API and worker share SQLite with WAL enabled and use
short transactions.

## 2. Data model

Core tables:

| Table | Purpose |
| --- | --- |
| `domains` | sending domains and DNS check state |
| `mailboxes` | 25 inboxes, transport credentials, caps, cooldowns |
| `campaigns` | campaign status, approval mode, limits, window |
| `campaign_mailboxes` | which inboxes can send for a campaign |
| `leads` | one row per campaign lead |
| `campaign_steps` | sequence template; first step is used now |
| `drafts` | the exact subject and body awaiting approval |
| `send_queue` | reserved mailbox and scheduled send time |
| `messages` | sent message metadata and transport result |
| `mailbox_usage_daily` | daily counters for caps and analytics |
| `suppression` | permanent stop list |
| `activity` | append-only operator and worker audit |
| `settings` | app-level transport, warmup and Sheets settings |
| `warmup_profiles` | per-mailbox ramp, status, caps and engagement settings |
| `warmup_threads` | one closed-pool conversation and its selected pair |
| `warmup_messages` | initial and reply messages, read and reply timestamps |
| `warmup_queue` | scheduled send, open and reply tasks |
| `sheet_sync_state` | last local/remote timestamp per synced row |

Lead states:

```text
new -> drafted -> pending_approval -> approved -> queued -> sending -> sent
                         |               |
                         v               v
                      denied          failed
```

Stop states: `denied`, `sent`, `replied`, `bounced`, `suppressed`.

Draft states:

```text
pending -> approved -> queued -> sending -> sent
   |
   +-> denied
   +-> failed
```

## 3. Approval flow

1. Import leads into a campaign.
2. Render a draft from the campaign step template and the lead fields.
3. The Approvals page shows one person at a time:
   name, email, role, company, industry, source, verification, campaign,
   subject, body, assigned mailbox.
4. The operator can:
   - edit the draft,
   - approve and queue,
   - deny with a reason,
   - approve or deny several at once.
   Deny with **Never contact** calls the suppression service, which denies
   other pending drafts and cancels queued sends for the same address.
5. Approval calls the rotation service, which reserves a mailbox and a
   scheduled time.
6. The worker sends only due queue items whose campaign is active.
7. Every transition writes an activity row.

`approval_mode` is kept in the schema for a future automation phase, but the
API accepts only `manual` and the database normalizes any old value to
`manual`. Auto-send is deliberately not implemented: no sheet edit, campaign
setting or API call can bypass the human approval step.

## 4. Rotation and scheduling

Eligibility:

- `mailbox.status = active`
- `domain.status = active`
- `campaign_mailboxes.enabled = 1`
- `mailbox_usage_daily.sent < mailbox.daily_limit`
- sends in the last hour `< mailbox.hourly_limit`
- domain sends today `< campaign.per_domain_limit`
- campaign is active and inside its window
- global sending is not paused
- the recipient has no prior Mailroom send and no other queued send

Selection:

- `least_used`: `(sent_today, next_available_at, last_sent_at)`
- `round_robin`: `(last_sent_at nulls first, id)`
- `weighted`: random choice proportional to campaign membership weight

Reservation:

```text
scheduled_at = max(now, mailbox.next_available_at, next_window_start)
mailbox.next_available_at = scheduled_at + random(effective_min, effective_max)
```

The effective minimum is the higher of the campaign and mailbox minimums. The
effective maximum is the lower of their maximums, never below the effective
minimum.

If no mailbox is eligible, approval returns an error and the draft stays
pending. The operator can pause, add a mailbox or raise a cap, then approve
again.

Send-time checks repeat eligibility. If a mailbox was paused or a cap was hit
after approval, the item is retried and rescheduled. It is not reassigned to a
different mailbox automatically; cancel and re-approve to pick another one.
This prevents stale assignments from sending.

## 5. Worker

- Runs every 2 seconds by default and processes up to 20 due items per tick.
- Leases each due item with `BEGIN IMMEDIATE` before the network call.
- Leases for 120 seconds. A crashed worker leaves the item leased; the next
  cycle reclaims expired leases.
- On success: draft/lead/message/usage/activity updates in one transaction.
- `mailbox_usage_daily.date` is the campaign-local date. Dashboard counters
  evaluate timestamps against the Mac's local date, so keep the Mac timezone
  aligned with the default campaign timezone.
- On a temporary condition (window closed, cap reached, paused mailbox): keep
  the attempt count and reschedule after 300 seconds.
- On a send error: increment attempts, write the error, retry after 60 seconds,
  then mark failed after 3 attempts.
- A global thread lock prevents overlapping ticks in one process.

## 6. Transports

### mock

Writes a `.eml` file to `data/outbox/` and returns a synthetic message ID.
Used for the demo and tests. Nothing leaves the machine.

### smtp

Per-mailbox SMTP host, port, username and encrypted password. Port 465 uses
implicit TLS; other ports require STARTTLS for authenticated sending, so
credentials are never sent in plaintext. Optional IMAP fields drive the
best-effort warmup read/flag operations; reply ingestion is still deferred.
Test connection logs in without sending.

### gas

Per-mailbox Google Apps Script webhook URL and encrypted shared secret. The URL
must use HTTPS because the shared secret is sent in the body. The worker POSTs
a JSON body and expects `{ok: true, messageId: "..."}`. A sample Apps Script is
in `integrations/apps_script/Code.gs`. This is the bridge for the user's
existing Gmail/Apps Script workflow.

## 6.5 Warmup

Warmup is a separate queue and worker from campaign mail.

Pairing rules:

- source and target must be different mailboxes,
- they must be on different domains,
- both warmup profiles must be enabled and ramping or active,
- the pair cannot repeat within the cooldown window,
- the target must be under its receive cap,
- candidates with fewer past interactions are weighted higher.

The ramp is a list in settings. The default starts at 2 sends per mailbox per
day and rises to 20. Per-mailbox and per-domain caps can lower it. The window
and weekdays-only flag control timing.

Each thread creates:

1. a send task at a randomized slot,
2. after a successful send, an open task,
3. probabilistically, a reply task.

Open tasks update the local read timestamp and make a best-effort IMAP
`\Seen \Flagged` call when an IMAP profile exists. Reply tasks send a threaded
reply with `In-Reply-To` and `References`. Warmup mock mail goes to
`data/warmup_outbox/`, not the campaign outbox.

The health score is an internal activity score:

```text
20 + min(30, sent_7d * 1.5)
   + min(25, reply_rate * 25)
   + min(15, open_rate * 15)
   + min(10, received_7d * 0.5)
```

It is not provider reputation or inbox placement. The UI says so.

## 6.6 Google Sheets

The Sheets integration uses a Google service account and four tabs:

- `Mailroom Leads` (two-way)
- `Mailroom Campaigns` (two-way)
- `Mailroom Suppression` (union)
- `Mailroom Warmup` (read-only)

`sheet_sync_state` stores `local_updated_at`, `remote_updated_at`,
`last_synced_at` and a content hash per row. The hash catches sheet edits made
without changing the timestamp cell. On pull:

- remote-only change: apply,
- local-only change: leave for push,
- both changed: conflict,
- merge policy: report and abort push,
- local/remote policy: explicit resolution.

The service account JSON is encrypted with the same local Fernet key as
mailbox credentials. Sync is manual or CLI-driven in this phase. There is no
background webhook or Google push notification.

## 7. Credentials

- Passwords and webhook secrets are encrypted with Fernet.
- Key file: `data/secret.key`, generated with mode 0600 on first run.
- Override with `MAILROOM_SECRET_KEY` if needed.
- The repo and the public demo database never contain credentials.

## 8. DNS checks

`app/services/dnscheck.py` uses `dnspython` when installed.

- MX: any MX record.
- SPF: TXT starting with `v=spf1`.
- DMARC: `_dmarc.<domain>` TXT starting with `v=DMARC1`.
- DKIM: `<selector>._domainkey.<domain>` TXT containing `p=`.

Results are stored on the domain row with a timestamp. The UI shows pass,
missing, unknown or error. Real sending can require a DNS pass via a setting;
mock mode never blocks on DNS.

## 9. API surface

```text
GET    /api/health
GET    /api/overview
GET    /api/campaigns
POST   /api/campaigns
PATCH  /api/campaigns/{id}

GET    /api/leads
GET    /api/leads/{id}
GET    /api/leads/export.csv
POST   /api/leads/import
POST   /api/drafts/{id}/regenerate

GET    /api/approvals
POST   /api/approvals/{draft_id}/approve
POST   /api/approvals/{draft_id}/deny
POST   /api/approvals/bulk
POST   /api/drafts/{id}/agent
PATCH  /api/drafts/{id}

GET    /api/mailboxes
POST   /api/mailboxes
PATCH  /api/mailboxes/{id}
POST   /api/mailboxes/{id}/test
POST   /api/mailboxes/{id}/pause
POST   /api/mailboxes/{id}/resume

GET    /api/domains
POST   /api/domains
PATCH  /api/domains/{id}
POST   /api/domains/{id}/check

GET    /api/deliverability
GET    /api/queue
POST   /api/queue/{id}/send-now
POST   /api/queue/{id}/cancel
POST   /api/queue/tick

GET    /api/warmup
POST   /api/warmup/start
POST   /api/warmup/pause
POST   /api/warmup/resume
POST   /api/warmup/stop
POST   /api/warmup/tick
PATCH  /api/warmup/settings

GET    /api/sheets/status
POST   /api/sheets/configure
POST   /api/sheets/test
POST   /api/sheets/sync

GET    /api/activity
GET    /api/suppression
POST   /api/suppression
DELETE /api/suppression/{email}
GET    /api/settings
PATCH  /api/settings
```

## 10. Latency choices

- SQLite WAL and indexes on every filter used by the UI.
- Server-side pagination for leads.
- The approval list uses one join; pool suggestions are resolved once per
  campaign, not once per row.
- Each page renders from one or two parallel fetches and caches the campaign
  list.
- No frontend framework, no bundler, no external fonts.
- The worker sends in its own thread, so the API stays responsive.

## 11. Security boundaries

- Bind to `127.0.0.1` by default.
- No secrets in git. `data/` is ignored.
- Approval is server-side; a UI-only flag is not trusted.
- Deny is terminal for the draft.
- Suppression is checked before queueing and again before sending. Adding a
  suppression also denies pending drafts and cancels queued sends.
- Repeat sends to the same address are blocked at approval and at send time.
- A global pause blocks approval and sending.
- Real transport requires a deliberate campaign status and mailbox transport;
  the demo defaults to mock.
- Authenticated SMTP requires implicit TLS or STARTTLS. Apps Script requires
  HTTPS. Message headers are stripped of CR/LF.
- Mailbox and sheet credentials are encrypted at rest. The API filters
  encrypted settings from responses.

## 12. Extension points

- `agent_webhook` setting: POST a lead to an agent and receive subject/body.
- `campaign_steps` for follow-ups.
- `messages.direction` for reply ingestion.
- `warmup_profiles` for external seed weighting and provider health.
- `mailbox_usage_daily` for campaign and warmup analytics.
- `domains` for per-domain reputation.
- Google Sheets background scheduling via cron or a queue worker.
