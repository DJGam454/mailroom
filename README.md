# Mailroom

A local-first approval and sending control room for cold email.

Mailroom is built for the gap between one Google Sheet and a real outbound
operation. It keeps one lead database, multiple campaigns, a shared inbox pool
and an explicit human approval step before anything is sent.

The demo ships with **10 domains and 25 inboxes**, a **mock transport**, and a
queue that rotates volume across the pool. No email leaves the machine until
you connect a real inbox and deliberately switch transports.

- Repository: <https://github.com/DJGam454/mailroom>
- Local app: <http://127.0.0.1:4600>
- License: MIT

## Why this exists

The existing 4400 and 4500 panels are useful operator consoles for one Apps
Script mailbox and one Google Sheet. This project is the next layer:

- one local database instead of one sheet per campaign,
- many campaigns with separate lead pools,
- 25 mailboxes across 10 domains,
- approval before send,
- mailbox rotation with daily and hourly caps,
- a coordinated queue instead of a burst,
- closed-pool warmup with cross-domain pairing and a slow ramp,
- two-way Google Sheets sync for leads and campaigns,
- mock, SMTP and Google Apps Script transports.

See [docs/RESEARCH.md](docs/RESEARCH.md) for the Instantly feature research and
the findings from the existing Apps Script projects. Warmup details are in
[docs/WARMUP.md](docs/WARMUP.md) and Sheets setup is in
[docs/GOOGLE_SHEETS.md](docs/GOOGLE_SHEETS.md).

## Quick start

```sh
git clone https://github.com/DJGam454/mailroom.git
cd mailroom
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m app.seed
uvicorn app.main:app --host 127.0.0.1 --port 4600 --reload
```

Open <http://127.0.0.1:4600>. Requires Python 3.12 or newer.

The seed creates synthetic data only:

- 10 `.test` domains
- 25 mock inboxes
- 2 demo campaigns
- 34 fictional leads
- 3 sent examples, 1 denied, 2 queued

There are no real addresses, credentials or private lead records in the public
repository.

## The approval flow

```text
lead -> draft -> pending approval -> approved -> queued -> sending -> sent
                         |
                         +-> denied
                         +-> failed
```

The Approvals page shows one card per email:

- person or business name
- email
- role or owner label
- company and industry
- campaign, source and verification grade
- exact subject and body
- the rotation pool that will assign a mailbox

You can approve and queue, deny, edit the copy, re-render from the template, or
bulk approve. Search the queue by name, email, company or role. Keyboard
shortcuts: `j` / `k` move, `a` approve, `d` deny, `e` edit.

Approval is server-side. A denied draft can never be picked up by the worker.
Every transition is written to the activity log.

## Mailbox rotation

Each approval reserves the best eligible mailbox and a send slot.

Filters:

- campaign is active and inside its window
- mailbox and domain are active
- mailbox is assigned to the campaign
- under the mailbox daily and hourly limit
- under the campaign per-domain limit
- recipient is not suppressed
- recipient has not already received a Mailroom send in any campaign
- global sending is not paused in Settings

Strategies:

- `least_used` (default): fewest sends today, then earliest next slot
- `round_robin`: least recently used
- `weighted`: weighted random choice

Slot reservation:

```text
scheduled_at = max(now, mailbox.next_available_at, next window start)
mailbox.next_available_at = scheduled_at + random gap
```

The worker re-checks every limit before sending, so a paused mailbox or a
campaign that was stopped cannot send a stale approval.

## Real ICP data

The public repo contains synthetic leads. Your real ICPExtractor pack is
imported into `data/mailroom.db`, which is gitignored.

Main A/B pool:

```sh
python3 scripts/import_icp.py \
  --json ~/ICPExtractor/output/leads.json \
  --campaign "NCR SME - Nov 2026" --grades A,B
```

Freemail pool:

```sh
python3 scripts/import_icp.py \
  --json ~/ICPExtractor/output/leads.json \
  --campaign "NCR Freemail - Nov 2026" --grades C
```

Healthcare:

```sh
python3 scripts/import_icp.py \
  --csv ~/ICPExtractor/output/healthcare_sheet_ready.csv \
  --campaign "NCR Healthcare - Nov 2026"

python3 scripts/import_icp.py \
  --csv ~/ICPExtractor/output/healthcare_sheet_ready_freemail.csv \
  --campaign "NCR Healthcare Freemail - Nov 2026"
```

The importer creates the campaign if needed, assigns every mailbox, renders a
first draft for each new lead and is idempotent by email within a campaign.

The default demo schedule is all day, every day. For a real campaign, use
office hours and a weekday schedule and keep volume low.

## Transports

### mock

The default. Writes a real `.eml` file to `data/outbox/` and marks the message
sent. Safe for testing the full approval and queue flow.

### smtp

Per-mailbox host, port, username and encrypted password. Port 465 uses
SMTP_SSL; other ports use STARTTLS when available. Profiles can be tested
without sending mail.

### gas

Per-mailbox Google Apps Script webhook. The sample bridge is in
[`integrations/apps_script`](integrations/apps_script/). Deploy one bridge per
Gmail mailbox and store its URL and shared secret in the mailbox settings.

## Domains and inboxes

The Inboxes page supports:

- adding domains
- adding mailboxes under a domain
- daily and hourly caps
- transport selection
- campaign assignment
- connection tests
- pause and resume
- MX, SPF, DKIM and DMARC checks
- volume against daily capacity

The demo has 25 mock inboxes. Replace them with real SMTP or Apps Script
mailboxes when the domains are ready.

## Deliverability checks

This phase reports volume, caps and DNS state. It does not score reputation.

- sent today per mailbox, domain and campaign
- remaining daily capacity
- hourly usage
- bounce counters
- DNS pass, missing or unknown for MX, SPF, DKIM and DMARC
- last seven days of sends

## Warmup

Warmup is a separate engine, not campaign mail.

- Cross-domain pairs only.
- 7-day pair cooldown.
- Slow ramp from 2 to 20 sends per mailbox per day.
- Per-mailbox and per-domain caps.
- Optional weekdays and send window.
- Plain-text conversations with opens and replies.
- Separate `data/warmup_outbox/` for mock mail.
- Best-effort IMAP read flags when an IMAP profile exists.

Your 10 domains and 25 mailboxes can warm each other, but that is a closed
pool. Add 2-4 external seed inboxes from Gmail or Outlook for a stronger
network. Full details: [docs/WARMUP.md](docs/WARMUP.md).

## Google Sheets two-way sync

Open **Google Sheets** to connect a service account.

Tabs:

- `Mailroom Leads` - two-way
- `Mailroom Campaigns` - two-way
- `Mailroom Suppression` - union
- `Mailroom Warmup` - read-only snapshot

Sync keeps per-row timestamps plus a content hash, so a normal sheet edit is
detected even when the timestamp cell is not updated. Conflicts are reported
instead of silently overwriting edits. Pull, push, two-way and dry run are available. Lead status is
app-controlled so a sheet edit cannot bypass approval.

Full details: [docs/GOOGLE_SHEETS.md](docs/GOOGLE_SHEETS.md).

## Operator pages

| Page | Purpose |
| --- | --- |
| Overview | approvals, queue, inbox health and recent activity |
| Approvals | person card, email preview, search, approve or deny |
| Campaigns | separate lead pools, limits and editable campaign settings |
| Leads | the single sheet: search, filter, import, export |
| Suppression | permanent stop addresses, add and remove |
| Inboxes & domains | connections, caps and DNS checks |
| Deliverability | volume and DNS state |
| Warmup | closed-pool ramp, pairs, health and engagement |
| Send queue | scheduled sends, recently sent, mailbox, retry state |
| Activity | append-only audit trail |
| Google Sheets | service account, tabs, pull/push/sync and conflicts |
| Settings | sender identity, safety switches, agent hook |

## Safety

- The app binds to `127.0.0.1` only.
- Mock mode is the default.
- Real sending requires a deliberate transport change per mailbox.
- SMTP and Apps Script credentials are encrypted with Fernet.
- The key is created at `data/secret.key` with mode 0600.
- `data/`, `.env` and real lead exports are gitignored.
- Suppression is checked at approval and again at send. Adding an address
  denies its pending drafts and cancels its queued sends immediately.
- A repeat send to the same address is blocked across campaigns, at approval and
  again at send time.
- A denied draft is terminal.
- A stale approval cannot send after a mailbox is paused or a cap is reached.
- **Pause all sending** in Settings blocks new approvals and stops the campaign
  queue without touching warmup history.

Read [docs/OPERATIONS.md](docs/OPERATIONS.md) before connecting a real inbox.

## Project structure

```text
app/
  main.py              FastAPI entrypoint and worker lifecycle
  db.py                SQLite helpers
  schema.sql           tables and indexes
  seed.py              synthetic demo data
  crypto.py            local credential encryption
  routes/              JSON API
  services/            drafting, rotation, sender, worker, warmup, sheets, suppression, DNS, importer
  static/              zero-build operator UI
scripts/
  import_icp.py        import a real ICPExtractor pack locally
  sync_sheets.py       command-line Sheets sync
tests/                 45 backend tests
integrations/
  apps_script/         optional Gmail bridge
docs/
  RESEARCH.md          Instantly and existing-project research
  ARCHITECTURE.md      data model, rotation, queue, transports
  WARMUP.md            closed-pool algorithm and research
  GOOGLE_SHEETS.md     service account and conflict model
  OPERATIONS.md        runbook
  OVERNIGHT_REPORT.md  morning summary
```

## Tests and checks

```sh
make check
```

This compiles the Python, checks the JavaScript syntax and runs the 45-test
pytest suite. GitHub Actions runs the same checks on every push and pull
request.

## API

The UI uses a small JSON API:

```text
GET  /api/overview
GET  /api/campaigns
GET  /api/leads
GET  /api/approvals
POST /api/approvals/{draft_id}/approve
POST /api/approvals/{draft_id}/deny
POST /api/approvals/bulk
GET  /api/mailboxes
GET  /api/domains
GET  /api/deliverability
GET  /api/queue
POST /api/queue/tick
POST /api/queue/{queue_id}/send-now
POST /api/queue/{queue_id}/cancel
GET  /api/warmup
POST /api/warmup/start
POST /api/warmup/pause
POST /api/warmup/resume
POST /api/warmup/tick
PATCH /api/warmup/settings
GET  /api/sheets/status
POST /api/sheets/configure
POST /api/sheets/test
POST /api/sheets/sync
GET  /api/activity
GET  /api/suppression
POST /api/suppression
DELETE /api/suppression/{email}
GET  /api/settings
PATCH /api/settings
```

The live OpenAPI explorer is at <http://127.0.0.1:4600/docs>. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full surface and rules.

## Scope

Built in this phase:

- approval queue and audit log
- campaigns and lead worksheets
- 25-mailbox rotation and caps
- coordinated send queue and worker
- mock, SMTP and Apps Script transports
- DNS checks and volume reporting
- closed-pool warmup with a cross-domain algorithm
- Google Sheets two-way sync with conflict detection
- ICPExtractor import
- tests and CI

Deferred:

- inbox placement testing and provider-level spam rescue
- reply ingestion and Unibox
- automatic background Sheets sync
- open and link tracking
- follow-up sequence editor UI
- teams, billing and multi-user auth

## Agent hook

Settings includes an optional agent webhook. Mailroom can POST a lead and
campaign to an external agent and expects:

```json
{"subject": "...", "body": "..."}
```

If the agent fails, Mailroom falls back to the local template. This is the
connection point for the OpenCode or OpenBot agent team.

## License

MIT. See `LICENSE`.
