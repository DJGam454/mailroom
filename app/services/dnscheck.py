"""MX, SPF, DKIM and DMARC checks."""

from __future__ import annotations

import logging

from app import db

log = logging.getLogger("mailroom.dns")


def _resolve_txt(name: str) -> list[str]:
    try:
        import dns.resolver  # type: ignore

        answers = dns.resolver.resolve(name, "TXT", lifetime=6)
        return ["".join(part.decode("utf-8", "replace") for part in answer.strings) for answer in answers]
    except Exception:
        return []


def _status_for(records: list[str], prefix: str) -> str:
    if any(record.strip().lower().startswith(prefix.lower()) for record in records):
        return "pass"
    return "missing"


def check_domain(conn, domain_id: int) -> dict:
    domain = db.one(conn, "SELECT * FROM domains WHERE id = ?", (domain_id,))
    if not domain:
        return {"ok": False, "error": "Domain not found"}

    mx_status = "missing"
    try:
        import dns.resolver  # type: ignore

        answers = dns.resolver.resolve(domain["name"], "MX", lifetime=6)
        mx_status = "pass" if len(answers) > 0 else "missing"
    except Exception:
        mx_status = "missing"

    spf_status = _status_for(_resolve_txt(domain["name"]), "v=spf1")
    dmarc_status = _status_for(_resolve_txt(f"_dmarc.{domain['name']}"), "v=DMARC1")
    selector = (domain.get("dkim_selector") or "mail").strip()
    dkim_records = _resolve_txt(f"{selector}._domainkey.{domain['name']}")
    dkim_status = "pass" if any("p=" in record for record in dkim_records) else "missing"

    now = db.now_iso()
    conn.execute(
        "UPDATE domains SET mx_status = ?, spf_status = ?, dmarc_status = ?, dkim_status = ?, "
        "last_check_at = ? WHERE id = ?",
        (mx_status, spf_status, dmarc_status, dkim_status, now, domain_id),
    )
    db.audit(
        conn,
        "dns_checked",
        "domain",
        domain_id,
        {
            "domain": domain["name"],
            "mx": mx_status,
            "spf": spf_status,
            "dkim": dkim_status,
            "dmarc": dmarc_status,
        },
    )
    return {
        "ok": True,
        "domain": domain["name"],
        "mx": mx_status,
        "spf": spf_status,
        "dkim": dkim_status,
        "dmarc": dmarc_status,
        "checked_at": now,
    }
