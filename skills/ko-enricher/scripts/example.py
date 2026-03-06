#!/usr/bin/env python3
"""Validate title_updated_ko style in tracker.db.

Quick check that all title_updated_ko values follow the sentence-style rules:
- Not null
- No keyword-listing pattern (A, B 및 C)
- Ends with 해요/됐어요/있어요/나왔어요/시작돼요/봐요/받아요/돌려요
"""

import sqlite3
import re
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "tracker.db"

VALID_ENDINGS = re.compile(r"(해요|됐어요|있어요|나왔어요|시작돼요|봐요|받아요|돌려요|가능해요|줄었어요|해졌어요|표기돼요|처리돼요|가능해졌어요|친절해졌어요|스마트해졌어요)$")
KEYWORD_PATTERN = re.compile(r",\s*\S+\s+및\s+")


def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT id, title_updated_ko FROM codex_event WHERE title_updated_ko IS NOT NULL"
    ).fetchall()
    conn.close()

    errors = []
    for rid, title in rows:
        short_id = rid[:8]
        if KEYWORD_PATTERN.search(title):
            errors.append(f"  [{short_id}] keyword pattern: {title}")
        if not VALID_ENDINGS.search(title):
            errors.append(f"  [{short_id}] bad ending: {title}")
        if len(title) > 50:
            errors.append(f"  [{short_id}] too long ({len(title)}ch): {title}")

    null_count = sqlite3.connect(str(DB_PATH)).execute(
        "SELECT COUNT(*) FROM codex_event WHERE title_updated_ko IS NULL"
    ).fetchone()[0]

    print(f"Total records with title_updated_ko: {len(rows)}")
    print(f"Records missing title_updated_ko: {null_count}")

    if errors:
        print(f"\nStyle issues ({len(errors)}):")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print("All titles pass style validation.")


if __name__ == "__main__":
    main()
