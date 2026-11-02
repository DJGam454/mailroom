# Overnight build report

Date: 2026-11-03

## What is ready

A working local-first approval and sending control room at:

```text
http://127.0.0.1:4600
```

Repository:

```text
https://github.com/DJGam454/mailroom
```

The app has:

- A dashboard with approvals, queue and inbox health.
- An approval queue with a person card and one-click approve or deny.
- Six campaigns: four real NCR campaigns imported locally, plus two synthetic
  demo campaigns.
- 444 leads in the local database, including 410 real ICPExtractor leads.
- 25 mock inboxes across 10 `.test` domains.
- Mailbox rotation with daily, hourly and per-domain caps.
- A send queue with scheduled slots and a background worker.
- Mock, SMTP and Google Apps Script transports.
- MX, SPF, DKIM and DMARC checks.
- Closed-pool warmup: cross-domain pairing, 7-day cooldown, slow ramp, opens,
  replies and separate caps.
- Google Sheets two-way sync for leads and campaigns, suppression union and a
  read-only warmup tab, with timestamp and content-hash conflict detection.
- Suppression management page and editable campaign settings.
- Editable domains and mailboxes, including IMAP credentials for warmup flags.
- Approval search, recently sent table and edit-from-lead.
- Manual Agent re-draft button for a configured webhook.
- Global pause switch, repeat-send protection across campaigns, and no auto
  approval path.
- Combined campaign plus warmup volume on the inbox and deliverability pages.
- Daily counters reset on the operator's local date; 00:00-23:59 is a true
  all-day window.
- Activity log and CSV/JSON import.
- 59 passing tests and a GitHub Actions workflow.

Real lead data is stored only in `data/mailroom.db`, which is gitignored. The
public repo contains synthetic demo leads only.

## Verified end to end

1. Imported 217 SME A/B leads.
2. Imported 92 freemail leads.
3. Imported 28 healthcare A/B leads.
4. Imported 73 healthcare freemail leads.
5. Approved a real lead.
6. Rotation selected `leo@cobalt-outreach.test`.
7. The worker wrote a mock `.eml` to `data/outbox/`.
8. The lead and draft moved to `sent`.
9. Started a closed-pool warmup cycle on the 25 mock inboxes: cross-domain
   threads were generated, mock sends were written to `data/warmup_outbox/`,
   and open/reply tasks processed.
10. Unit-tested Sheets row building, timestamp parsing, conflict handling,
    suppression union and fake-tab round trips.
11. Confirmed the global pause blocks approval and the worker, and confirmed a
    duplicate address is blocked at approval and at send time.
12. Ran a 25-mailbox warmup simulation: 50 cross-domain threads, 50 opens, 50
    replies, 100 mock files, no same-domain pairs and no failed tasks.
13. Verified the 23:59 all-day boundary and local-date counters with a fresh
    approval, mock send and queue read after local midnight.

## How to use it in the morning

```sh
cd mailroom
source .venv/bin/activate
python scripts/serve.py
```

Then open <http://127.0.0.1:4600>.

Start on **Approvals**. Filter to `NCR SME - Nov 2026` to see the main campaign.
Approve a few, deny one, then open **Send queue** and watch the mock sends.

Then open **Warmup** and press **Start all**. The demo uses short gaps so you
can see threads, opens and replies within a minute. Press **Pause all** when
you are done.

Then open **Google Sheets** if you want to connect a real sheet. Setup details
are in `docs/GOOGLE_SHEETS.md`.

## Important safety state

- The app is in **mock mode**. No email leaves the Mac.
- The 10 domains and 25 inboxes are synthetic.
- `data/outbox/` contains campaign mock messages.
- `data/warmup_outbox/` contains warmup mock messages.
- Real SMTP requires adding a real domain and mailbox and testing it.
- Warmup is off by default. It is safe to start on the mock pool.
- **Settings -> Pause all sending** is the emergency stop for campaigns.
- Adding a suppression denies pending drafts and cancels queued sends.
- A repeat send to the same address is blocked across campaigns.
- Auto approval is not implemented and cannot be enabled from the UI or API.
- Google Sheets has no live credentials yet; the code and tests are ready.
- Reply ingestion and the Unibox are still deferred.

## Best next steps

1. Review the approval card and copy with a small batch of real leads.
2. Refine the template or connect the optional agent webhook.
3. Buy the 10 domains and 25 inboxes.
4. Set SPF, DKIM and DMARC and verify them in the Deliverability page.
5. Connect one real SMTP inbox and send a single test to yourself.
6. Raise caps gradually only after the first batch is read.
7. Start warmup on one domain at a time when the real inboxes arrive.
8. Connect the Google Sheet with a service account and run a dry-run pull.
9. Add reply ingestion and a Unibox in phase two.
