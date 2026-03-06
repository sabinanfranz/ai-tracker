#!/usr/bin/env python3
"""Validate title_kor and content_kor style in tracker.db.

Checks that all claude_code_event card_yn=1 records follow the Korean
enrichment rules:
- title_kor is not null for card_yn=1
- title_kor is ~30 chars (10-40 range)
- content_kor has exactly 3 bullets (•)
- card_yn=0 records have no title_kor
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

    # card_yn=1 records (should have translations)
    card_rows = conn.execute(
        "SELECT id, title_kor, content_kor, change_type "
        "FROM claude_code_event WHERE card_yn = 1"
    ).fetchall()

    # card_yn=0 records (should NOT have translations)
    non_card_with_kor = conn.execute(
        "SELECT COUNT(*) FROM claude_code_event "
        "WHERE card_yn = 0 AND title_kor IS NOT NULL"
    ).fetchone()[0]

    conn.close()

    total = len(card_rows)
    errors: list[str] = []
    null_title = 0
    null_content = 0

    for rid, title_kor, content_kor, change_type in card_rows:
        short_id = rid[:8]

        # --- title_kor checks ---
        if title_kor is None:
            null_title += 1
            continue

        if len(title_kor) < 10:
            errors.append(f"  [{short_id}] title_kor too short ({len(title_kor)}ch): {title_kor}")
        if len(title_kor) > 40:
            errors.append(f"  [{short_id}] title_kor too long ({len(title_kor)}ch): {title_kor}")

        # --- content_kor checks ---
        if content_kor is None:
            null_content += 1
            continue

        bullet_count = content_kor.count("\u2022")  # •
        if bullet_count != 3:
            errors.append(
                f"  [{short_id}] content_kor has {bullet_count} bullets (expected 3)"
            )

    filled_title = total - null_title
    filled_content = total - null_content

    print(f"Total card_yn=1 records: {total}")
    print(f"title_kor filled: {filled_title}/{total}")
    print(f"content_kor filled: {filled_content}/{total}")

    if null_title > 0:
        print(f"\nMissing title_kor: {null_title} records")
    if null_content > 0:
        print(f"\nMissing content_kor: {null_content} records")
    if non_card_with_kor > 0:
        errors.append(f"  card_yn=0 records with title_kor: {non_card_with_kor} (should be 0)")

    if errors:
        print(f"\nStyle issues ({len(errors)}):")
        for e in errors:
            print(e)
        sys.exit(1)
    elif null_title == 0 and null_content == 0:
        print("\nAll card_yn=1 records pass style validation.")
    else:
        print("\nFilled records pass style validation (some records still missing).")


if __name__ == "__main__":
    main()
