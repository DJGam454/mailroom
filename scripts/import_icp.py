#!/usr/bin/env python3
"""Import an ICPExtractor pack into the local Mailroom database.

Examples:
  python3 scripts/import_icp.py \
    --json ~/ICPExtractor/output/leads.json \
    --campaign "NCR SME - Nov 2026" --grades A,B

  python3 scripts/import_icp.py \
    --json ~/ICPExtractor/output/leads.json \
    --campaign "NCR Freemail - Nov 2026" --grades C

  python3 scripts/import_icp.py \
    --csv ~/ICPExtractor/output/healthcare_sheet_ready.csv \
    --campaign "NCR Healthcare - Nov 2026"

The source file and the resulting SQLite database are local. Neither belongs
in git.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402
from app.services import importer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Import an ICP pack into Mailroom")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--json", type=Path, help="Path to ICPExtractor leads.json")
    source.add_argument("--csv", type=Path, help="Path to a sheet-ready CSV")
    parser.add_argument("--campaign", required=True, help="Campaign name")
    parser.add_argument("--limit", type=int, default=None, help="Import at most N rows")
    parser.add_argument("--grades", default=None, help="JSON grades to import, for example A,B")
    parser.add_argument(
        "--office-hours",
        action="store_true",
        help="Use 09:30-17:30 weekdays instead of the all-day demo schedule",
    )
    args = parser.parse_args()

    path = args.json or args.csv
    if not path.exists():
        parser.error(f"File not found: {path}")

    grades = None
    if args.grades:
        grades = {grade.strip().upper() for grade in args.grades.split(",") if grade.strip()}

    db.init_db()
    with db.transaction() as conn:
        result = importer.import_file(
            conn,
            path,
            args.campaign,
            limit=args.limit,
            grades=grades,
            all_day=not args.office_hours,
        )
    print(
        json.dumps(
            {
                "ok": True,
                "campaign": result["campaign"]["name"],
                "campaign_id": result["campaign"]["id"],
                "imported": result["imported"],
                "skipped": result["skipped"],
                "drafts": result["drafts"],
                "source": str(path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
