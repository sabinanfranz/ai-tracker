#!/usr/bin/env python3
"""Validate title_ko and content_ko style in tracker.db for gemini_event.

Checks that all gemini_event records follow the Korean enrichment rules:
- title_ko IS NULL count
- title_ko length range (20-50 chars) violations
- content_ko line count (3 lines via \\n) violations
- Overall statistics
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "tracker.db"


def main() -> None:
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))

    rows = conn.execute(
        "SELECT id, title_ko, content_ko FROM gemini_event"
    ).fetchall()

    conn.close()

    total = len(rows)
    errors: list[str] = []
    null_title = 0
    null_content = 0

    for rid, title_ko, content_ko in rows:
        short_id = rid[:8]

        # --- title_ko checks ---
        if title_ko is None:
            null_title += 1
            continue

        if len(title_ko) < 20:
            errors.append(f"  [{short_id}] title_ko too short ({len(title_ko)}ch): {title_ko}")
        if len(title_ko) > 50:
            errors.append(f"  [{short_id}] title_ko too long ({len(title_ko)}ch): {title_ko}")

        # --- content_ko checks ---
        if content_ko is None:
            null_content += 1
            continue

        line_count = len(content_ko.split("\n"))
        if line_count < 3:
            errors.append(
                f"  [{short_id}] content_ko has {line_count} lines (expected 3)"
            )

    filled_title = total - null_title
    filled_content = total - null_content

    print(f"Total gemini_event records: {total}")
    print(f"title_ko filled: {filled_title}/{total}")
    print(f"content_ko filled: {filled_content}/{total}")

    if null_title > 0:
        print(f"\nMissing title_ko: {null_title} records")
    if null_content > 0:
        print(f"\nMissing content_ko: {null_content} records")

    if errors:
        print(f"\nStyle issues ({len(errors)}):")
        for e in errors:
            print(e)
        sys.exit(1)
    elif null_title == 0 and null_content == 0:
        print("\nAll gemini_event records pass style validation.")
    else:
        print("\nFilled records pass style validation (some records still missing).")


if __name__ == "__main__":
    main()
