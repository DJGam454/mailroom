# Operations runbook

## 1. Start the app

```sh
cd mailroom
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m app.seed          # synthetic demo only
uvicorn app.main:app --host 127.0.0.1 --port 4600 --reload
```

Open <http://127.0.0.1:4600>. The app binds to localhost only.

The first start without a database seeds synthetic demo data: 10 `.test`
domains, 25 mock inboxes, two campaigns and 34 leads. There are no real
addresses and no credentials in the repository.

After the first seed, set `MAILROOM_AUTO_SEED=0` in `.env` if you do not want
demo data recreated when the campaign table is empty.

## 2. Import your real ICP pack

The real pack lives outside this repository. The app stores it in
`data/mailroom.db`, which is gitignored.

Main A/B pool:

```sh
python3 scripts/import_icp.py \
  --json ~/ICPExtractor/output/leads.json \
  --campaign "NCR SME - Nov 2026" \
  --grades A,B
```

Main freemail pool:

```sh
python3 scripts/import_icp.py \
  --json ~/ICPExtractor/output/leads.json \
  --campaign "NCR Freemail - Nov 2026" \
  --grades C
```

Healthcare A/B and freemail:

```sh
python3 scripts/import_icp.py \
  --csv ~/ICPExtractor/output/healthcare_sheet_ready.csv \
  --campaign "NCR Healthcare - Nov 2026"

python3 scripts/import_icp.py \
  --csv ~/ICPExtractor/output/healthcare_sheet_ready_freemail.csv \
  --campaign "NCR Healthcare Freemail - Nov 2026"
```

The importer creates the campaign if it does not exist, assigns every mailbox,
renders the first draft for every new lead and is idempotent by email within a
campaign.

The default schedule is all day, every day, so the demo can be exercised
immediately. For a real campaign, create it with office hours and a weekday
schedule, or update it from the API. Real sending should use a conservative
window.

## 3. Approve and deny

Open **Approvals**. Each card shows:

- person or business name
- email address
- role or owner label
- company and industry
- campaign and verification grade
- the exact subject and body that will be sent

Actions:

- **Approve & queue** reserves the best eligible mailbox and a slot.
- **Deny** marks the draft and lead denied. Tick **Never contact this address**
  to add a permanent suppression.
- **Edit** changes the subject or body. The draft returns to pending and must be
  approved again.
- **Re-render** rebuilds the draft from the campaign template.
- Search by name, email, company or role with the field above the queue.
- Keyboard: `j` / `k` move, `a` approve, `d` deny, `e` edit.
- Bulk approve or deny with the checkboxes.

Approval is blocked when the recipient already received a Mailroom send in any
campaign, when the address is suppressed, or when **Pause all sending** is on.
The worker repeats the same checks before delivery.

The demo data has a few sent and queued examples. The real imported campaigns
start with every draft pending.

The **Suppression** page is the permanent stop list. Adding an address denies
its pending drafts, cancels its queued sends and marks its leads suppressed.
Removing the address lifts the block for new campaigns, but existing denied
drafts stay denied. A denied draft only suppresses an address when **Never
contact this address again** is ticked. Suppression blocks queueing and is
checked again at send time.

The gear button on a campaign card opens campaign settings for the name,
status, limits, window, timezone and rotation. Auto-send is not implemented;
every send still requires approval.

## 4. Rotation and caps

Every mailbox has:

- daily limit (default 25)
- hourly limit (default 5)
- minimum and maximum gap in seconds
- timezone
- status
- transport

Every campaign has:

- daily limit across the whole campaign
- per-domain daily limit
- rotation strategy: least used, round robin, weighted
- send window and working days
- gap range

The scheduler reserves a slot at approval time:

```text
scheduled_at = max(now, mailbox.next_available_at, next window start)
mailbox.next_available_at = scheduled_at + random gap
```

The effective gap uses the higher of the campaign and mailbox minimums and the
lower of their maximums. That lets a mailbox enforce a conservative floor even
when a campaign is configured more loosely.

At send time it re-checks campaign status, mailbox status, domain status,
suppression, repeat contact, the window, the campaign total for its local day,
mailbox daily and hourly limits and the per-domain limit. A paused mailbox or a
campaign that already hit its daily cap cannot send a stale approval.

**Inboxes & domains** shows campaign and warmup volume together, including
warmup replies. The campaign cap and the warmup cap are separate counters, but
both consume the provider's quota. Keep the combined number under the real
provider limit.

Daily counters use the Mac's local date. Keep the Mac timezone aligned with the
default timezone in Settings so the counter reset matches the campaign window.

**Settings -> Pause all sending** is the emergency stop. It blocks new
approvals and stops campaign sends. Warmup has its own pause controls.

## 5. Connect a real domain and inbox

1. Add the domain under **Inboxes & domains**.
2. Open the gear on the domain card and set the DKIM selector if it is not
   `mail`. The same panel pauses the domain and labels the provider.
3. Click **Check DNS**. SPF, DKIM, DMARC and MX are read-only checks.
4. Add a mailbox under that domain.
5. Choose the transport:
   - `mock` for a local `.eml` outbox,
   - `smtp` for host, port, username and password,
   - `gas` for a Google Apps Script webhook.
6. Click **Test** to verify the connection without sending a real email.
7. Assign the mailbox to the campaign and keep caps low.
8. Use the gear on a mailbox row to edit its caps, timezone, campaigns or
   SMTP/IMAP credentials later. Leave a password blank to keep the saved one.
   IMAP is optional and only used for best-effort warmup read flags.

Credentials are encrypted with Fernet. The key is created at
`data/secret.key` with mode 0600 on first use. Set `MAILROOM_SECRET_KEY` to use
a key from a password manager instead.

## 6. Google Apps Script bridge

`integrations/apps_script/Code.gs` is a sample webhook for one Gmail mailbox.
Deploy one per mailbox if you want to keep using Apps Script.

Deployment:

1. Create an Apps Script project from the mailbox account.
2. Add `Code.gs`.
3. Add a Script Property `MAILROOM_SHARED_SECRET` with a long random value.
4. Deploy as a web app, execute as the mailbox owner, access to anyone with the
   link.
5. In Mailroom, add the mailbox with transport `gas`, the deployment URL and
   the same secret.
6. Click **Test**. The script answers a `ping` without sending mail.

The script checks the shared secret, sends via `GmailApp.sendEmail`, and returns
`{ok: true, messageId}`. Gmail quota still applies per account.

## 7. Going live checklist

- Use separate outreach subdomains, not the primary company domain.
- SPF, DKIM and DMARC pass on every domain.
- At least one real inbox is connected and tested.
- The mailbox's daily limit is conservative (for example 20 to 30).
- The campaign window is in the correct timezone and working days.
- The campaign has an approve-first workflow.
- Send a test to yourself and inspect the rendered message.
- Approve exactly one lead and watch the queue and activity log.
- Check the `.eml` file in `data/outbox/` if using mock.
- Only then raise limits.

## 8. Backup and reset

Back up the database:

```sh
cp data/mailroom.db data/mailroom-backup-$(date +%Y%m%d).db
```

Reset the synthetic demo (destructive to local leads and messages):

```sh
python3 -m app.seed --reset
```

Do not commit `data/`, `.env`, or any real lead export.

## 9. Troubleshooting

**Port already in use**

```sh
lsof -iTCP:4600 -sTCP:LISTEN
```

Change `MAILROOM_PORT` or stop the old process.

**No eligible mailbox**

Check the campaign status, mailbox status, send window, daily limits,
per-domain limit and whether the mailbox is assigned to the campaign.

**Worker does not send**

The queue item may be scheduled in the future or the campaign may be paused.
Open **Send queue** and click **Tick worker** or **Send now**. Look at the
activity log for `send_retry` or `send_failed`.

**SMTP login fails**

Test the mailbox from the inbox page. For Gmail, use an App Password, not the
normal account password. Port 465 uses implicit SSL. Other ports use STARTTLS.
If the server does not support STARTTLS, Mailroom refuses to send the username
and password over plaintext.

**Apps Script returns an HTML sign-in page**

The deployment is not public or the account is not authorized. Use a web app
deployment with access to anyone, or use SMTP instead. The Apps Script URL
must use HTTPS; Mailroom refuses to send the shared secret over plain HTTP. The
existing 4400/4500 panels had the same failure mode.

**A test domain shows DNS missing**

`.test` domains have no real DNS. That is expected. Use a real domain for DNS
checks.

## 10. Warmup

Open **Warmup**.

This is a closed pool: the same 10 domains and 25 mailboxes exchange mail. It
is useful for testing and low-level activity, but a diverse external warmup
network is stronger. Add 2-4 Gmail or Outlook seed inboxes when possible.

The engine:

- only pairs across domains,
- avoids the same pair for 7 days,
- ramps 2, 4, 6, 10, 15, 20 per mailbox per day across the phases,
- the default per-mailbox cap of 10 trims the later ramp until you raise it,
- caps at 10 per mailbox and 50 per domain by default,
- sends short plain-text messages,
- records opens and replies,
- writes mock mail to `data/warmup_outbox/`.

Click **Start all** to start the demo. Click **Run tick** to force a scheduling
and processing pass. **Pause all** stops new sends and keeps history.

For real domains:

1. Verify SPF, DKIM, DMARC and MX.
2. Use SMTP/IMAP or the Apps Script bridge.
3. Raise the gap to 5-15 minutes.
4. Start at 2-5 sends per mailbox per day.
5. Stagger domains by 7-14 days.
6. Keep total volume per mailbox under 30 per day.
7. Keep warmup running after campaigns start.

The health number is an activity score, not provider reputation. See
[WARMUP.md](WARMUP.md).

## 11. Google Sheets

Open **Google Sheets**.

1. Create a Google Cloud service account.
2. Enable the Google Sheets API.
3. Download the JSON key.
4. Create a sheet and share it with the service account email as Editor.
5. Paste the spreadsheet ID and JSON into Mailroom.
6. Save, Test, and Pull.

Tabs:

- `Mailroom Leads` - two-way
- `Mailroom Campaigns` - two-way
- `Mailroom Suppression` - union
- `Mailroom Warmup` - read-only

Conflict policy:

- `merge`: report conflicts and stop the push.
- `local`: local values win.
- `remote`: sheet values win.

Use **Dry run** before a large push. The service account JSON is encrypted and
never returned by the API. See [GOOGLE_SHEETS.md](GOOGLE_SHEETS.md).

## 12. Scope of this phase

Built:

- approval queue
- campaign and lead management
- 25-mailbox rotation
- mock, SMTP and GAS transports
- queue worker with retries
- closed-pool warmup with cross-domain pairing and ramp
- Google Sheets two-way sync with conflicts
- suppression, repeat-send blocking and a global pause switch
- editable domains and mailboxes, including IMAP for warmup flags
- manual agent re-draft through a configurable webhook
- DNS checks and combined campaign plus warmup volume
- activity log
- CSV/JSON import and export round-trip
- tests and CI

Not built yet:

- provider-level inbox placement and spam rescue
- reply ingestion and Unibox
- automatic background Sheets sync
- open and link tracking
- multi-step follow-ups UI
- billing and multi-user accounts
