# Overnight build report

Date: 2026-11-02

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
- Activity log and CSV/JSON import.
- 13 passing tests and a GitHub Actions workflow.

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

## How to use it in the morning

```sh
cd /Users/divyantiwari/github/DJGam454/mailroom
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 4600 --reload
```

Then open <http://127.0.0.1:4600>.

Start on **Approvals**. Filter to `NCR SME - Nov 2026` to see the main campaign.
Approve a few, deny one, then open **Send queue** and watch the mock sends.

## Important safety state

- The app is in **mock mode**. No email leaves the Mac.
- The 10 domains and 25 inboxes are synthetic.
- `data/outbox/` contains the captured `.eml` messages.
- Real SMTP requires adding a real domain and mailbox and testing it.
- Warmup, replies and Google Sheet sync are intentionally deferred.

## Best next steps

1. Review the approval card and copy with a small batch of real leads.
2. Refine the template or connect the optional agent webhook.
3. Buy the 10 domains and 25 inboxes.
4. Set SPF, DKIM and DMARC and verify them in the Deliverability page.
5. Connect one real SMTP inbox and send a single test to yourself.
6. Raise caps gradually only after the first batch is read.
7. Add reply ingestion and a Unibox in phase two.
