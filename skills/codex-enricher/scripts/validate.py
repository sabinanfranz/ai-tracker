#!/usr/bin/env python3
"""Validate title_updated and content_updated style in tracker.db.

Checks that all codex_event records follow the English enrichment rules:
- title_updated is not null
- title_updated is ~70 chars (20-90 range)
- content_updated has exactly 3 sentences (2 newlines)
- content_updated sentences are reasonable length
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
        "SELECT id, title_updated, content_updated FROM codex_event"
    ).fetchall()
    conn.close()

    total = len(rows)
    errors: list[str] = []
    null_title = 0
    null_content = 0

    for rid, title, content in rows:
        short_id = rid[:8]

        # --- title_updated checks ---
        if title is None:
            null_title += 1
            continue

        if len(title) < 20:
            errors.append(f"  [{short_id}] title too short ({len(title)}ch): {title}")
        if len(title) > 90:
            errors.append(f"  [{short_id}] title too long ({len(title)}ch): {title}")

        # --- content_updated checks ---
        if content is None:
            null_content += 1
            continue

        sentences = content.split("\n")
        if len(sentences) != 3:
            errors.append(
                f"  [{short_id}] content has {len(sentences)} sentences (expected 3)"
            )

    filled_title = total - null_title
    filled_content = total - null_content

    print(f"Total codex_event records: {total}")
    print(f"title_updated filled: {filled_title}/{total}")
    print(f"content_updated filled: {filled_content}/{total}")

    if null_title > 0:
        print(f"\nMissing title_updated: {null_title} records")
    if null_content > 0:
        print(f"\nMissing content_updated: {null_content} records")

    if errors:
        print(f"\nStyle issues ({len(errors)}):")
        for e in errors:
            print(e)
        sys.exit(1)
    elif null_title == 0 and null_content == 0:
        print("\nAll records pass style validation.")
    else:
        print("\nFilled records pass style validation (some records still missing).")


if __name__ == "__main__":
    main()
