"""Synthetic demo data.

This file contains no real leads and no real credentials. The public repo uses
this data so anyone can run the app. Real ICP data is imported separately and
stored only in the gitignored local database.
"""

from __future__ import annotations

import argparse
import random
from datetime import timedelta
from email.utils import make_msgid

from app import db
from app.services import drafting, rotation

DOMAINS = [
    ("atlas-outreach.test", "mock"),
    ("beacon-outreach.test", "mock"),
    ("cobalt-outreach.test", "mock"),
    ("delta-outreach.test", "mock"),
    ("ember-outreach.test", "mock"),
    ("fable-outreach.test", "mock"),
    ("granite-outreach.test", "mock"),
    ("harbor-outreach.test", "mock"),
    ("indigo-outreach.test", "mock"),
    ("juniper-outreach.test", "mock"),
]

MAILBOXES = [
    ("alex@atlas-outreach.test", "Alex Morgan", "atlas-outreach.test"),
    ("maya@atlas-outreach.test", "Maya Chen", "atlas-outreach.test"),
    ("sam@atlas-outreach.test", "Sam Rivera", "atlas-outreach.test"),
    ("nina@beacon-outreach.test", "Nina Shah", "beacon-outreach.test"),
    ("omar@beacon-outreach.test", "Omar Khan", "beacon-outreach.test"),
    ("priya@beacon-outreach.test", "Priya Nair", "beacon-outreach.test"),
    ("leo@cobalt-outreach.test", "Leo Martins", "cobalt-outreach.test"),
    ("ava@cobalt-outreach.test", "Ava Brooks", "cobalt-outreach.test"),
    ("noah@delta-outreach.test", "Noah Kim", "delta-outreach.test"),
    ("mia@delta-outreach.test", "Mia Patel", "delta-outreach.test"),
    ("eli@ember-outreach.test", "Eli Turner", "ember-outreach.test"),
    ("zoe@ember-outreach.test", "Zoe Adams", "ember-outreach.test"),
    ("kai@fable-outreach.test", "Kai Wong", "fable-outreach.test"),
    ("ivy@fable-outreach.test", "Ivy Singh", "fable-outreach.test"),
    ("max@granite-outreach.test", "Max Weber", "granite-outreach.test"),
    ("luna@granite-outreach.test", "Luna Costa", "granite-outreach.test"),
    ("ben@harbor-outreach.test", "Ben Okafor", "harbor-outreach.test"),
    ("ada@harbor-outreach.test", "Ada Mensah", "harbor-outreach.test"),
    ("raj@indigo-outreach.test", "Raj Mehta", "indigo-outreach.test"),
    ("emma@indigo-outreach.test", "Emma Stone", "indigo-outreach.test"),
    ("dan@juniper-outreach.test", "Dan Whitfield", "juniper-outreach.test"),
    ("olivia@juniper-outreach.test", "Olivia Park", "juniper-outreach.test"),
    ("jon@atlas-outreach.test", "Jon Alvarez", "atlas-outreach.test"),
    ("sara@beacon-outreach.test", "Sara Ali", "beacon-outreach.test"),
    ("amir@cobalt-outreach.test", "Amir Hassan", "cobalt-outreach.test"),
]

SME_LEADS = [
    ("Aarti Mehta", "Founder", "Loom & Line Design Studio", "Design studio", "Delhi", "aarti@loomline.test", "12-person branding studio with a strong portfolio and a slow site.", "Reels + social video"),
    ("Rohan Kapoor", "Marketing Head", "Northstar Interiors", "Interior design", "Gurugram", "rohan@northstarinteriors.test", "Premium interiors studio; site has no WhatsApp or booking path.", "Website + AI-search audit"),
    ("Neha Bansal", "Co-founder", "Paper Plane Films", "Video production", "Noida", "neha@paperplanefilms.test", "Small film studio with a strong showreel but no service pages.", "White-label video"),
    ("Vikram Rao", "Owner", "Rao Exports", "Exporter", "Moradabad", "vikram@raoexports.test", "Brassware exporter with 40 reviews and a desktop-only catalogue.", "Website + AI-search audit"),
    ("Simran Kaur", "Director", "Kaur & Co.", "D2C skincare", "Ludhiana", "simran@kaurco.test", "Shopify skincare brand with a strong Instagram and a thin product page.", "Reels + product content"),
    ("Arjun Sethi", "CEO", "Bluepeak SaaS", "B2B SaaS", "Bengaluru", "arjun@bluepeak.test", "B2B analytics product; hiring a platform team and publishing release notes.", "AI code review"),
    ("Meera Iyer", "Admissions Head", "Sunrise Preschool", "Education", "Dwarka", "meera@sunrisepreschool.test", "Preschool with 80 reviews and no virtual tour or booking form.", "Admissions reel + site refresh"),
    ("Kabir Malhotra", "Founder", "Studio K", "Architecture", "New Delhi", "kabir@studiok.test", "Architecture practice with an award-winning portfolio and a slow gallery.", "Website refresh"),
    ("Isha Verma", "Growth Lead", "The Daily Grind", "D2C coffee", "Mumbai", "isha@dailygrind.test", "D2C coffee brand with strong repeat demand and no subscription flow.", "Reels + product content"),
    ("Dev Patel", "Partner", "Pixelworks Agency", "Agency", "Ahmedabad", "dev@pixelworks.test", "12-person performance agency; white-label video capacity is the gap.", "White-label video"),
    ("Ananya Bose", "Founder", "Mint Studio", "Design studio", "Kolkata", "ananya@mintstudio.test", "Boutique design studio with a polished site and no case study pages.", "Reels + social video"),
    ("Harsh Vardhan", "Owner", "Vardhan Motors", "Auto parts", "Faridabad", "harsh@vardhanmotors.test", "Auto parts manufacturer with 90 reviews and no mobile catalogue.", "Website + AI-search audit"),
    ("Pooja Reddy", "Marketing Manager", "Craft & Clay", "Home decor", "Hyderabad", "pooja@craftandclay.test", "Home decor D2C brand with a strong catalogue and weak product photography.", "Reels + product content"),
    ("Aman Gupta", "Founder", "Signal Labs", "B2B SaaS", "Pune", "aman@signallabs.test", "Developer tooling startup with a self-serve trial and a small platform team.", "AI code review"),
    ("Ritika Sen", "Director", "Sen Hospitality", "Hospitality", "Goa", "ritika@senhospitality.test", "Boutique hotel group with a high-end site and no direct booking flow.", "Website + AI-search audit"),
    ("Nikhil Joshi", "Owner", "Joshi Textiles", "Textiles", "Surat", "nikhil@joshitextiles.test", "Textile exporter with a large catalogue and no English product copy.", "Website + AI-search audit"),
    ("Sneha Kulkarni", "Co-founder", "Bloom & Berry", "D2C wellness", "Pune", "sneha@bloomberry.test", "Wellness brand with a strong community and a slow checkout.", "Reels + product content"),
    ("Rahul Nair", "Head of Growth", "Finlite", "Fintech", "Bengaluru", "rahul@finlite.test", "Fintech app with a content-heavy site and a hiring platform team.", "AI code review"),
    ("Tara D'Souza", "Founder", "Tara Studio", "Photography", "Mumbai", "tara@tarastudio.test", "Photography studio with a large portfolio and no package pages.", "Reels + social video"),
    ("Yash Bhatia", "Owner", "Bhatia Packaging", "Packaging", "Noida", "yash@bhatiapackaging.test", "Packaging manufacturer with 25 reviews and a thin product catalogue.", "Website + AI-search audit"),
    ("Aditi Rao", "Marketing Head", "Nest Interiors", "Interior design", "Gurugram", "aditi@nestinteriors.test", "Interior design firm with premium projects and no lead magnet.", "Website refresh"),
    ("Karan Mehra", "Founder", "Orbit Media", "Agency", "Delhi", "karan@orbitmedia.test", "Content agency with a referral-heavy pipeline and no case studies.", "White-label video"),
    ("Sara Khan", "Founder", "Sara's Bakehouse", "D2C food", "Lucknow", "sara@sarasbakehouse.test", "Local bakery with a strong Instagram and no online ordering.", "Reels + product content"),
    ("Vivek Menon", "CTO", "StackWorks", "B2B SaaS", "Kochi", "vivek@stackworks.test", "Vertical SaaS team shipping weekly and hiring two senior engineers.", "AI code review"),
]

HEALTHCARE_LEADS = [
    ("Dr. Asha Rao", "Dentist", "Smile Studio Dental", "Dental clinic", "Delhi", "asha@smilestudio.test", "Dental clinic with 60 reviews and no online appointment flow.", "Website + local SEO"),
    ("Dr. Nikhil Shah", "Dermatologist", "Skin & Co.", "Dermatology clinic", "Mumbai", "nikhil@skinco.test", "Skin clinic with a strong before/after portfolio and a slow site.", "Reels + social video"),
    ("Dr. Priya Menon", "Pediatrician", "Little Steps Clinic", "Pediatric clinic", "Gurugram", "priya@littlesteps.test", "Pediatric clinic with high trust and no parent education content.", "Website + local SEO"),
    ("Dr. Arvind Kumar", "Orthopedist", "Kumar Ortho Care", "Orthopedic clinic", "Noida", "arvind@kumarortho.test", "Ortho clinic with 45 reviews and a dated website.", "Website refresh"),
    ("Dr. Fatima Sheikh", "Gynecologist", "Bloom Women's Health", "Women's health clinic", "Delhi", "fatima@bloomwomens.test", "Women's health clinic with a private practice and no booking form.", "Website + local SEO"),
    ("Dr. Sanjay Patel", "Dentist", "Bright Smile Dental", "Dental clinic", "Ahmedabad", "sanjay@brightsmile.test", "Multi-chair dental clinic with a Google listing and no service pages.", "Website + local SEO"),
    ("Dr. Ritu Agarwal", "Dermatologist", "Ritu Skin Clinic", "Dermatology clinic", "Jaipur", "ritu@ritusklinic.test", "Skin clinic with strong local demand and a thin website.", "Reels + social video"),
    ("Dr. Manish Verma", "ENT Specialist", "Verma ENT Centre", "ENT clinic", "Lucknow", "manish@vermaent.test", "ENT centre with 30 reviews and no online appointment path.", "Website + local SEO"),
    ("Dr. Kavita Nair", "Pediatrician", "Nair Child Care", "Pediatric clinic", "Kochi", "kavita@nairchildcare.test", "Pediatric practice with a loyal patient base and no content engine.", "Website + local SEO"),
    ("Dr. Imran Qureshi", "Orthopedist", "Qureshi Bone & Joint", "Orthopedic clinic", "Hyderabad", "imran@qureshibone.test", "Ortho clinic with a strong reputation and a desktop-only site.", "Website refresh"),
]


def _get_domain(conn, name: str) -> int:
    row = db.one(conn, "SELECT id FROM domains WHERE name = ?", (name,))
    if row:
        return int(row["id"])
    cursor = conn.execute(
        "INSERT INTO domains(name, provider, dkim_selector, status) VALUES (?, 'mock', 'mail', 'active')",
        (name,),
    )
    return int(cursor.lastrowid)


def _create_mailboxes(conn) -> None:
    for email, display_name, domain_name in MAILBOXES:
        domain_id = _get_domain(conn, domain_name)
        conn.execute(
            "INSERT OR IGNORE INTO mailboxes(domain_id, email, display_name, transport, daily_limit, hourly_limit, "
            "min_gap_seconds, max_gap_seconds, timezone, status) "
            "VALUES (?, ?, ?, 'mock', 25, 5, 45, 180, 'Asia/Kolkata', 'active')",
            (domain_id, email, display_name),
        )


def _create_campaign(conn, name: str, daily_limit: int, per_domain_limit: int) -> int:
    now = db.now_iso()
    cursor = conn.execute(
        "INSERT INTO campaigns(name, status, approval_mode, daily_limit, per_domain_limit, timezone, "
        "window_start, window_end, working_days, rotation_strategy, min_gap_seconds, max_gap_seconds, "
        "created_at, updated_at) VALUES (?, 'active', 'manual', ?, ?, 'Asia/Kolkata', '00:00', '23:59', "
        "'[1,2,3,4,5,6,7]', 'least_used', 45, 240, ?, ?)",
        (name, daily_limit, per_domain_limit, now, now),
    )
    campaign_id = int(cursor.lastrowid)
    conn.execute(
        "INSERT OR IGNORE INTO campaign_mailboxes(campaign_id, mailbox_id) SELECT ?, id FROM mailboxes",
        (campaign_id,),
    )
    conn.execute(
        "INSERT INTO campaign_steps(campaign_id, step_no, delay_days, subject_template, body_template, enabled, created_at) "
        "VALUES (?, 1, 0, ?, ?, 1, ?)",
        (
            campaign_id,
            "Quick idea for {{company}}",
            "Hi {{first_name}},\n\n"
            "I came across {{company}} while looking at {{industry}} businesses in {{city}}.\n\n"
            "One thing that stood out: {{observation_line}}\n\n"
            "We help teams with {{offer}}.\n\n"
            "Would a 15-minute call be useful?\n\n"
            "{{sender_name}}\n{{sender_title}}, {{sender_company}}\n\n"
            'If this is not relevant, reply "no" and I will not follow up.',
            now,
        ),
    )
    return campaign_id


def _insert_leads(conn, campaign_id: int, rows: list[tuple]) -> list[int]:
    now = db.now_iso()
    lead_ids = []
    for row in rows:
        (name, role, company, industry, city, email, notes, offer) = row
        domain = email.split("@", 1)[1] if "@" in email else ""
        cursor = conn.execute(
            "INSERT INTO leads(campaign_id, external_id, name, email, role, company, industry, company_domain, "
            "website, city, notes, offer, email_grade, verification, source, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?, ?, 'B', 'Unknown', 'demo', 'new', ?, ?)",
            (campaign_id, email, name, email, role, company, industry, domain, city, notes, offer, now, now),
        )
        lead_ids.append(int(cursor.lastrowid))
    return lead_ids


def _seed_history(conn, campaign_id: int, lead_ids: list[int]) -> None:
    campaign = db.one(conn, "SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    mailboxes = db.rows(conn, "SELECT * FROM mailboxes ORDER BY id LIMIT 6")
    if not campaign or len(mailboxes) < 6:
        return
    now = db.now_iso()
    # Three sent examples.
    for index in range(3):
        lead = db.one(conn, "SELECT * FROM leads WHERE id = ?", (lead_ids[index],))
        draft = db.one(conn, "SELECT * FROM drafts WHERE lead_id = ?", (lead_ids[index],))
        mailbox = mailboxes[index]
        message_id = make_msgid(domain="mailroom.local")
        conn.execute(
            "UPDATE drafts SET status = 'sent', approved_at = ?, updated_at = ? WHERE id = ?",
            (now, now, draft["id"]),
        )
        conn.execute(
            "UPDATE leads SET status = 'sent', updated_at = ? WHERE id = ?",
            (now, lead["id"]),
        )
        conn.execute(
            "INSERT INTO send_queue(draft_id, lead_id, campaign_id, mailbox_id, scheduled_at, status, attempts, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'sent', 1, ?, ?)",
            (draft["id"], lead["id"], campaign_id, mailbox["id"], now, now, now),
        )
        conn.execute(
            "INSERT INTO messages(draft_id, lead_id, campaign_id, mailbox_id, direction, from_email, to_email, subject, body, "
            "message_id, transport, status, sent_at, created_at) VALUES (?, ?, ?, ?, 'outbound', ?, ?, ?, ?, ?, 'mock', 'sent', ?, ?)",
            (
                draft["id"],
                lead["id"],
                campaign_id,
                mailbox["id"],
                mailbox["email"],
                lead["email"],
                draft["subject"],
                draft["body"],
                message_id,
                now,
                now,
            ),
        )
        conn.execute(
            "INSERT INTO mailbox_usage_daily(mailbox_id, date, sent) VALUES (?, ?, 1) "
            "ON CONFLICT(mailbox_id, date) DO UPDATE SET sent = sent + 1",
            (mailbox["id"], rotation.local_date(campaign)),
        )
        db.audit(conn, "message_sent", "draft", draft["id"], {"seed": True, "mailbox": mailbox["email"]})

    # One denied example.
    denied_lead = db.one(conn, "SELECT * FROM leads WHERE id = ?", (lead_ids[3],))
    denied_draft = db.one(conn, "SELECT * FROM drafts WHERE lead_id = ?", (lead_ids[3],))
    conn.execute(
        "UPDATE drafts SET status = 'denied', denied_at = ?, deny_reason = ?, updated_at = ? WHERE id = ?",
        (now, "Not a fit for this campaign", now, denied_draft["id"]),
    )
    conn.execute(
        "UPDATE leads SET status = 'denied', updated_at = ? WHERE id = ?",
        (now, denied_lead["id"]),
    )
    db.audit(conn, "draft_denied", "draft", denied_draft["id"], {"seed": True, "reason": "Not a fit"})

    # Two queued examples, scheduled soon.
    for index in (4, 5):
        lead = db.one(conn, "SELECT * FROM leads WHERE id = ?", (lead_ids[index],))
        draft = db.one(conn, "SELECT * FROM drafts WHERE lead_id = ?", (lead_ids[index],))
        mailbox = mailboxes[index]
        scheduled = rotation.iso(rotation.now_utc() + timedelta(minutes=6 + index))
        conn.execute(
            "UPDATE drafts SET status = 'queued', approved_at = ?, updated_at = ? WHERE id = ?",
            (now, now, draft["id"]),
        )
        conn.execute(
            "UPDATE leads SET status = 'queued', updated_at = ? WHERE id = ?",
            (now, lead["id"]),
        )
        conn.execute(
            "INSERT INTO send_queue(draft_id, lead_id, campaign_id, mailbox_id, scheduled_at, status, attempts, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'queued', 0, ?, ?)",
            (draft["id"], lead["id"], campaign_id, mailbox["id"], scheduled, now, now),
        )
        db.audit(conn, "draft_queued", "draft", draft["id"], {"seed": True, "mailbox": mailbox["email"]})


def seed_demo(reset: bool = False) -> dict:
    db.init_db()
    with db.transaction() as conn:
        existing = db.one(conn, "SELECT COUNT(*) AS count FROM campaigns")
        if existing and int(existing["count"]) > 0 and not reset:
            return {"ok": True, "seeded": False, "reason": "campaigns already exist"}
        if reset:
            for table in (
                "messages",
                "send_queue",
                "drafts",
                "leads",
                "campaign_steps",
                "campaign_mailboxes",
                "campaigns",
                "mailbox_usage_daily",
                "mailboxes",
                "domains",
                "suppression",
                "sheet_sync_state",
                "activity",
            ):
                conn.execute(f"DELETE FROM {table}")

        _create_mailboxes(conn)
        conn.execute(
            "INSERT OR IGNORE INTO warmup_profiles(mailbox_id, enabled, status, daily_limit) "
            "SELECT id, 0, 'off', 10 FROM mailboxes"
        )
        sme_id = _create_campaign(conn, "Demo - NCR SME - Design & Video", 250, 50)
        healthcare_id = _create_campaign(conn, "Demo - NCR Healthcare - Doctors", 100, 25)
        sme_ids = _insert_leads(conn, sme_id, SME_LEADS)
        healthcare_ids = _insert_leads(conn, healthcare_id, HEALTHCARE_LEADS)
        drafting.generate_drafts(conn, sme_id)
        drafting.generate_drafts(conn, healthcare_id)
        _seed_history(conn, sme_id, sme_ids)
        db.audit(conn, "demo_seeded", "app", "", {"campaigns": 2, "leads": len(SME_LEADS) + len(HEALTHCARE_LEADS)})
        return {
            "ok": True,
            "seeded": True,
            "domains": len(DOMAINS),
            "mailboxes": len(MAILBOXES),
            "campaigns": 2,
            "leads": len(SME_LEADS) + len(HEALTHCARE_LEADS),
            "sme_leads": len(SME_LEADS),
            "healthcare_leads": len(HEALTHCARE_LEADS),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Mailroom with synthetic demo data")
    parser.add_argument("--reset", action="store_true", help="Delete existing local data before seeding")
    args = parser.parse_args()
    random.seed(7)
    print(seed_demo(reset=args.reset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
