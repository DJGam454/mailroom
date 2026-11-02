# Mailroom

A local-first outbound control room for approval-first cold email.

Mailroom gives one operator a single place to see every lead, approve or deny
each email, and send through a rotating pool of mailboxes across multiple
domains. It is inspired by Instantly's campaign and inbox-rotation model, but
it is built for a small local operation and an explicit human approval gate.

> **Default is mock mode.** No email leaves this Mac until you configure a real
> transport and switch a campaign to live. The demo ships with 10 domains and
> 25 inboxes so rotation, caps and the approval flow can be tested end to end.

## What is in this repository

- FastAPI + SQLite backend.
- Zero-build HTML/CSS/JS operator UI.
- Approval queue with a person card and one-click approve or deny.
- Campaign workspace with multiple lead pools.
- 25-mailbox rotation across 10 domains.
- Per-mailbox, per-domain and per-campaign daily and hourly caps.
- Coordinated send queue with gaps and send windows.
- Domain checks for MX, SPF, DKIM and DMARC.
- Mock, SMTP/IMAP, and Google Apps Script webhook transports.
- CSV/JSON importer for the ICP extractor output.
- Tests and CI.

## Quick start

```sh
cd /Users/divyantiwari/github/DJGam454/mailroom
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m app.seed
uvicorn app.main:app --host 127.0.0.1 --port 4600 --reload
```

Open <http://127.0.0.1:4600>.

Import your real ICP pack locally (never committed):

```sh
python3 scripts/import_icp.py \
  --json /Users/divyantiwari/ICPExtractor/output/leads.json \
  --campaign "NCR SME - Nov 2026" \
  --limit 217
```

The importer writes only to the local SQLite database under `data/`, which is
gitignored.

## Why this exists

The existing 4400 and 4500 panels are useful operator consoles for one Apps
Script mailbox and one Google Sheet. This project is the next layer: one
database, many campaigns, many mailboxes, explicit approval, and a scheduler
that coordinates volume instead of sending everything at once.

See:

- [docs/RESEARCH.md](docs/RESEARCH.md) - what Instantly does and what we learned
  from the existing Apps Script projects.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - data model, rotation, queue,
  transports and failure handling.
- [docs/OPERATIONS.md](docs/OPERATIONS.md) - runbook.
- [docs/OVERNIGHT_REPORT.md](docs/OVERNIGHT_REPORT.md) - concise morning report.

## Status

This is the approval and sending foundation. Lead sourcing, warmup, reply inbox,
and analytics can be layered on later. The schema and API are designed for
that.

## License

MIT.
