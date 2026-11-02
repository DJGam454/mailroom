#!/usr/bin/env python3
"""Run Google Sheets sync from the command line.

Examples:
  python3 scripts/sync_sheets.py --sync
  python3 scripts/sync_sheets.py --pull --dry-run
  python3 scripts/sync_sheets.py --push
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import db  # noqa: E402
from app.services import sheets  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Mailroom Google Sheets sync")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pull", action="store_true", help="Pull changes from the sheet")
    group.add_argument("--push", action="store_true", help="Push local changes to the sheet")
    group.add_argument("--sync", action="store_true", help="Two-way sync")
    parser.add_argument("--dry-run", action="store_true", help="Compare without writing")
    args = parser.parse_args()
    direction = "pull" if args.pull else "push" if args.push else "both"
    db.init_db()
    with db.transaction() as conn:
        result = sheets.sync(conn, direction, args.dry_run)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
