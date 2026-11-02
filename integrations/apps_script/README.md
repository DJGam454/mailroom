# Apps Script bridge

This is the optional bridge for keeping a Gmail mailbox. It is not required
when you use SMTP.

## Deploy one bridge per mailbox

1. Open <https://script.google.com> from the mailbox account.
2. Create a project and paste `Code.gs`.
3. Open **Project Settings -> Script Properties**.
4. Add `MAILROOM_SHARED_SECRET` with a long random value.
5. Deploy -> New deployment -> Web app.
6. Execute as **Me**, access **Anyone with the link**.
7. Copy the `/exec` URL.
8. In Mailroom, add the mailbox with transport `gas`, paste the URL and the
   shared secret.
9. Click **Test**.

The bridge answers a `ping` without sending. A `send` calls
`GmailApp.sendEmail` and returns a synthetic message ID.

## Why one per mailbox

Each deployment runs as the mailbox owner, so the mail comes from the correct
account. A single deployment cannot send as 25 different accounts.

## Quota

Gmail consumer and Workspace accounts have daily sending quotas. Keep the
Mailroom per-mailbox daily limit below the provider quota. SMTP is usually
easier to operate at 25 inboxes, but this bridge keeps the existing Apps Script
workflow available.
