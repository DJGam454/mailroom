# Research and design notes

Date: 2026-11-02

## 1. What Instantly does that matters here

Sources:

- <https://instantly.ai/outreach>
- <https://help.instantly.ai/en/articles/6222396-campaign-settings>
- <https://help.instantly.ai/en/articles/7046484-inbox-rotation-assign-sending-accounts-to-a-campaign>
- <https://help.instantly.ai/en/articles/6386134-how-to-create-campaigns-complete-setup-guide>
- <https://help.instantly.ai/en/articles/11991261-getting-started-with-the-email-accounts-dashboard>
- <https://help.instantly.ai/en/articles/5975329-how-warm-up-works-and-why-it-is-important>

The relevant product model:

1. **One workspace, many sending accounts.** Email accounts live in a global
   pool. A campaign selects the accounts it may use, and Instantly rotates
   sends across the selected accounts.
2. **Campaign-level and account-level limits.** Campaigns have a daily limit
   across all accounts. Accounts have a daily send limit. Instantly recommends
   roughly 30 campaign emails per account per day.
3. **Schedule and timezone.** Campaigns can send 24/7, during office hours, or
   in custom windows. The schedule has a timezone.
4. **Natural spacing.** There is a minimum gap and a random additional gap
   between emails. The documented default is 9 minutes plus a random 5 minutes.
5. **Sequence and variants.** A campaign has multiple steps and variants, with
   wait times between steps.
6. **Preview and launch as a deliberate step.** Before launch, the operator
   previews variables, sends tests, checks the deliverability score and then
   confirms publish. This is the closest analogue to our approval gate.
7. **Warmup and reputation.** Instantly warms inboxes, tracks health and
   placement. Warmup is explicitly out of scope for this phase, but the data
   model leaves room for a warmup state and health score.
8. **Unibox.** Every reply from every account lands in one inbox. This is a
   later phase for us.
9. **Lead Finder.** Instantly can source leads from an ICP. In this project the
   ICP extractor already produces the lead pack, so we import that instead of
   rebuilding a lead database.

The UI pattern worth copying is the shape, not the pixels: persistent left
navigation, campaign switcher, dense tables, account health cards, and a
review-before-send step.

## 2. Existing projects inspected

### 2.1 ICPExtractor

Location: `/Users/divyantiwari/ICPExtractor`

The output pack is high quality and already contains the fields an approval
screen needs:

- `business_name`
- `contact_name` and `contact_title`
- `email`, `email_grade`, `verification`
- `industry`, `segment`, `city`, `region`
- `website`, `phone`, `place_url`
- `observation`, `website_observation`, `business_strength`
- `recommended_offer`, `service_assigned`
- `icp_score`, `tier`, `fit`, `buy_signals`

The send-ready files are split by grade:

- `leads_sheet_ready.csv`: A/B grades, 217 rows.
- `leads_sheet_ready_freemail.csv`: C grade, 92 rows.
- `healthcare_sheet_ready.csv`: healthcare add-on.
- `leads.json`: 309 machine-readable records for the main pack.

The README explicitly warns that the existing 4400/4500 panels were built
around one Apps Script deployment and have an import bug that hardcodes
`Industry = Medical`. The new importer passes columns through instead of
hardcoding a vertical.

### 2.2 4400 and 4500 panels

Location: `/Users/divyantiwari/Desktop/EmailAutomation_Doctors/app` and the
India/Dubai copies.

Both are zero-dependency Node HTTP servers. They serve a static panel and proxy
JSON calls to an Apps Script web app with a shared secret in
`app/config.local.json`. Campaigns are a map, each with its own web-app URL,
secret and spreadsheet. This is a good low-dependency pattern, but it has three
limits for the new system:

- The sheet is the source of truth, so concurrent approval and sending are
  awkward.
- Every campaign is tied to one Apps Script deployment.
- There is no real queue or per-mailbox scheduler; Apps Script time triggers
  do the work.

### 2.3 Apps Script code

Locations:

- `/Users/divyantiwari/Desktop/Email_Automation_Sudipti`
- `/Users/divyantiwari/Desktop/EmailAutomation_Doctors`
- `/Users/divyantiwari/Desktop/India-Outreach-ai`
- `/Users/divyantiwari/Desktop/Dubai-Outreach-ai`

Reusable ideas:

- `Config.js` separates sender identity and limits from campaign copy.
- `Scheduling.js` gates sends by working day, window and timezone.
- `EmailEngine.js` processes follow-ups before first emails and enforces a run
  budget.
- `Validation.js` has a quota breaker and per-domain limits.
- `Bounces.js` and `Replies.js` maintain suppression and stop statuses.
- `SuppressionReconcile.js` keeps a permanent stop list.
- `Leads.js` has a clear status model and retry counts.
- `Personalizer.gs` uses verified website facts and falls back to generic copy
  when evidence is weak.

Things not to carry forward:

- One global Gmail account or one sheet per campaign.
- Time-trigger-only orchestration.
- Hardcoded industry on import.
- Approval represented only by a `TEST_MODE` flag.

## 3. Decisions for Mailroom

### 3.1 Database instead of a single sheet

SQLite in WAL mode is the local source of truth. It gives us:

- atomic state transitions for approval and queueing,
- indexes for a responsive lead table,
- a durable audit trail,
- no network latency,
- one file to back up.

A Google Sheet can be a mirror later. The operator-facing "sheet" is the Leads
page and CSV export, not the storage engine.

### 3.2 Local-first web app

FastAPI serves JSON and static files. The UI is plain HTML, CSS and JavaScript.
There is no build step, no CDN and no frontend dependency. This keeps startup
fast and removes a class of deployment problems.

### 3.3 Human approval is a state, not a flag

A draft moves through `pending -> approved -> queued -> sending -> sent`. Only
an explicit `approve` action creates a queue item. A denied draft can never be
picked up by the worker. Every action writes an activity row.

### 3.4 Rotate at queue time, re-check at send time

At approval time we pick the best eligible mailbox and reserve a slot. At send
time we re-check caps, status and the send window. This avoids a stale
assignment sending after a mailbox is paused or a cap is reached.

### 3.5 Mock first

The demo has 10 domains and 25 inboxes with `transport = mock`. The worker
writes `.eml` files under `data/outbox` and marks them sent. Real sending
requires per-mailbox SMTP/IMAP credentials or a Google Apps Script webhook, and
a deliberate campaign switch. This prevents an accidental real send while the
operator is learning the UI.

### 3.6 DNS checks, not reputation scoring

For this phase:

- MX check.
- SPF TXT check.
- DMARC TXT check.
- DKIM TXT check with a configurable selector.
- Sent-today and hourly counters per mailbox and domain.
- Bounce counters from send results.

Warmup, inbox placement and reputation are later.

## 4. Rotation model

Eligibility filters:

- mailbox and domain are active,
- mailbox is assigned to the campaign,
- mailbox is under its daily and hourly caps,
- domain is under the campaign's per-domain cap,
- campaign is active and inside its send window,
- recipient is not suppressed,
- draft is approved and not already sent.

Ordering strategies:

- `least_used` (default): fewest sends today, then earliest next available
  slot, then least recently used.
- `round_robin`: oldest `last_sent_at` first.
- `weighted`: weighted random choice among eligible mailboxes.

Slot reservation:

```text
scheduled_at = max(now, mailbox.next_available_at, next_window_start)
mailbox.next_available_at = scheduled_at + random(min_gap, max_gap)
```

This gives a coordinated stream instead of a burst. The worker sends only due
items and re-checks everything before opening a connection.

## 5. What is deliberately not built yet

- Google Sheet two-way sync.
- Mailbox warmup and inbox placement.
- Reply ingestion and Unibox.
- Open tracking, link tracking, A/B optimization.
- Bounce parsing from IMAP DSNs.
- Billing, teams, multi-tenant accounts.
- Lead Finder / enrichment.

These are kept as extension points in the schema and API.
