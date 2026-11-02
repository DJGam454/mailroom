# Google Sheets two-way sync

Mailroom can keep a Google Sheet in sync with the local database. Leads and
campaigns are two-way. Suppression is a union. Warmup is a read-only snapshot.

## 1. Create a service account

1. Open <https://console.cloud.google.com/>.
2. Create or select a project.
3. Enable **Google Sheets API**.
4. Open **IAM & Admin -> Service Accounts**.
5. Create a service account.
6. Create a JSON key and download it.
7. Copy the `client_email` from the JSON. It looks like
   `mailroom@project.iam.gserviceaccount.com`.

## 2. Create and share the spreadsheet

1. Create a blank Google Sheet.
2. Copy the spreadsheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit`.
3. Share the sheet with the service account email as **Editor**.
4. Do not share it with a personal account instead of the service account.

## 3. Configure Mailroom

1. Open **Google Sheets** in Mailroom.
2. Paste the spreadsheet ID.
3. Paste the service account JSON.
4. Choose a conflict policy.
5. Click **Save connection**.
6. Click **Test connection**.

On test, Mailroom creates these tabs if they do not exist:

- `Mailroom Leads`
- `Mailroom Campaigns`
- `Mailroom Suppression`
- `Mailroom Warmup`

The service account JSON is encrypted at rest with the same local Fernet key as
mailbox credentials. The API never returns the JSON.

## 4. Sync semantics

### Pull

Reads the sheet and applies remote changes that do not conflict with local
changes.

### Push

Writes the current local rows to the sheet. This is the operation that creates
or refreshes the tabs.

Helper columns to the right of Mailroom's columns are preserved and matched by
the first column key (`ID`, `Email` or `Mailbox`). Do not insert a column
inside the Mailroom range: that shifts the schema. Add notes and helper columns
to the right of it.

### Two-way

Pull first. If there are conflicts and the policy is `merge`, the push is
aborted so the sheet is not overwritten. Resolve the conflicts and run again.

### Dry run

Reads and compares without writing local changes or updating the sheet.

## 5. Conflict model

`sheet_sync_state` stores the last local and remote timestamp, the last sync
time and a content hash for each row.

- Only remote changed after the last sync: apply the remote change.
- Only local changed: leave it for the push.
- Both changed and the timestamps or content differ: conflict.
- `merge`: report the conflict and stop the push.
- `local`: keep the local value.
- `remote`: replace the local value with the sheet value.

The content hash is important: a human often edits a cell without changing the
`Updated At` cell. The hash catches that edit on the next pull.

A first sync compares the two timestamps and reports a conflict when both sides
have different values. This is deliberate: it is better to ask than to lose an
edit.

## 6. What is editable

Leads:

- name
- email
- role
- company
- industry
- city
- website
- notes
- offer
- verification
- grade

Campaigns:

- name
- status
- daily limit
- per-domain limit
- timezone
- window start and end
- working days
- rotation strategy

Suppression:

- email and reason are unioned into the local suppression list.

Warmup:

- read-only snapshot. It is written by Mailroom and ignored on pull.

Lead status and campaign approval mode are intentionally app-controlled. This
prevents a sheet edit from bypassing the human approval gate. Use **Approvals**
for approve or deny.

## 7. Command line

```sh
python3 scripts/sync_sheets.py --sync
python3 scripts/sync_sheets.py --pull --dry-run
python3 scripts/sync_sheets.py --push
```

The CLI reads the same local configuration. Use it from cron or a terminal.

## 8. Limits

- One spreadsheet per Mailroom instance.
- The tabs are global, not one spreadsheet per campaign.
- Campaigns are separated by the Campaign column in the Leads tab.
- If the header row is changed, sync refuses to run until it is restored.
- Warmup is one row per mailbox, not a per-thread history.
- There is no background auto-sync in this phase. Run sync manually, from the
  UI, or from the CLI.

## 9. Troubleshooting

**The service account cannot open the sheet**

Share the sheet with the exact `client_email` from the JSON, not your own
Google account.

**403 API has not been used**

Enable the Google Sheets API in the same Google Cloud project.

**Header mismatch**

Restore the tab header row exactly as created by the Test button, or use a new
tab. This protects against writing into a sheet with a different layout.

**Conflicts keep coming back**

A conflict is expected when both the local row and the sheet row changed after
the last sync. Choose `local` or `remote` for a deliberate resolution, or edit
the sheet and run a pull.

**Credentials were replaced**

The JSON is encrypted with `data/secret.key`. If that key is lost or
`MAILROOM_SECRET_KEY` changes, re-save the JSON.
