# Email warmup

## Can 10 domains and 25 mailboxes warm each other?

Yes, mechanically. They can send plain-text conversations to each other, open
them, reply, and mark them read. The implementation in Mailroom does exactly
that.

But it is a **closed pool**. Every message stays inside domains you own, with
the same infrastructure and the same operator. That is weaker than a diverse
network of external mailboxes. The honest answer is:

- useful for testing mechanics and keeping low-level activity alive,
- not a substitute for real inbox placement testing,
- best supplemented with 2-4 external seed inboxes from Gmail, Outlook, or
  another provider,
- keep volume conservative and stagger new domains over 7-14 days.

The UI says this on the Warmup page. The code does not pretend a closed pool is
a full reputation network.

## What the engine does

- Pairs mailboxes only across different domains.
- Excludes the same pair for 7 days by default.
- Gives every mailbox its own slow ramp.
- Caps sends per mailbox and per domain.
- Uses a configurable send window and optional weekdays-only mode.
- Sends short, varied plain-text emails.
- Schedules opens and replies separately.
- Records opens and replies in the local database.
- Best-effort IMAP `\Seen` on open, plus `\Flagged` on the configured
  important-rate share.
- Keeps warmup traffic separate from campaign traffic and campaign caps.
- Moves a profile from `ramping` to `active` after the configured ramp ends.
- Exposes a health score based on activity and engagement, not provider
  reputation.

## Ramp

The default ramp is:

| Phase | Sends per mailbox per day |
| --- | --- |
| Days 1-3 | 2 |
| Days 4-7 | 4 |
| Days 8-14 | 6 |
| Days 15-21 | 10 |
| Days 22-30 | 15 |
| Day 31+ | 20 |

The per-mailbox daily limit and the per-domain daily limit can lower this.
Defaults are 10 per mailbox and 50 per domain. For a new domain, start lower
and raise only after DNS and placement are stable.

Instantly's warmup guidance uses a similar shape: start at 5-10 per inbox per
day, ramp toward 30 over roughly four weeks, reply rate around 30%, and keep
warmup running alongside campaigns. Warmbly and Bounceproof both recommend a
7-day or longer recent-partner gap. InboxAlly's 2026 analysis is a useful
warning about the limits of reciprocal pools.

## Algorithm

At each warmup tick:

1. Reclaim expired leases.
2. Process due send, open, and reply tasks.
3. Select active profiles that are inside their window.
4. Compute the day and ramp target.
5. Count sent volume and already-created threads for today.
6. Skip if the mailbox or domain cap is reached.
7. Choose a target:
   - different mailbox,
   - different domain,
   - active profile,
   - not paired in the cooldown window,
   - under its receive limit,
   - weighted toward pairs with fewer past interactions.
8. Create a thread and reserve a send slot with a random gap.
9. After a successful send, schedule an open and, probabilistically, a reply.
10. Record every event in `warmup_*` tables and the activity log.

The worker runs every 5 seconds by default. The first demo gaps are 5-30
seconds so you can see activity quickly. For real domains, raise the gap to
300-900 seconds.

## Using it

```text
Warmup -> Start all
```

or start one mailbox at a time.

Useful controls:

- **Settings**: daily limit, domain limit, reply %, open %, important %, ramp,
  pair cooldown, gap range, window, weekdays only, max sends per tick.
- **Run tick**: force a scheduling and processing pass.
- **Pause all / Pause**: stop new sends while keeping history.
- **Start**: resume the ramp.

The demo mailboxes are mock, so warmup writes `.eml` files to
`data/warmup_outbox/`. Nothing leaves the Mac.

## Real warmup checklist

- SPF, DKIM and DMARC pass on every domain.
- MX is live.
- A real SMTP/IMAP mailbox is connected and tested.
- Start one domain at a time, or stagger domains by 7-14 days.
- Start at 2-5 warmup sends per mailbox per day.
- Keep total mailbox volume under 30 per day including campaigns. The Inboxes
  page shows campaign and warmup sends together; the caps are separate counters
  but the provider quota is shared.
- Raise the gap to 5-15 minutes.
- Add external seed inboxes for diversity where possible.
- Keep warmup running after campaigns start.
- Monitor bounces, complaints and inbox placement separately. This phase does
  not implement provider placement tests or spam rescue.

## Research references

- Instantly warmup settings and product guide:
  <https://help.instantly.ai/en/articles/7988514-warmup-settings>
  and <https://instantly.ai/email-warmup>
- Warmbly warmup pools, recent-partner gap and pool quality:
  <https://docs.warmbly.com/learn/warmup-pools/>
- Bounceproof multi-domain parallel ramp guidance:
  <https://blog.bounceproof.co/advanced-email-warm-up-strategy/>
- InboxAlly peer-to-peer warmup risks:
  <https://www.inboxally.com/blog/peer-to-peer-email-warmup>
- Warmy warmup at scale and ramp examples:
  <https://www.warmy.io/blog/how-to-warmup-inboxes-at-scale/>

## Important limitation

The health score is an internal activity score. It is not Google Postmaster
reputation, Microsoft SNDS, or an inbox placement measurement. Add a real
placement test before trusting a domain with campaign volume.
