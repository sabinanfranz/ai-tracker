"""Populate card_yn column for all claude_code_event rows."""

import sqlite3
import sys
from pathlib import Path

# Allow importing from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.classify_other import classify as classify_title

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tracker.db"

CARD_TYPES = {"added", "changed", "removed", "deprecated"}
SKIP_TYPES = {"fixed", "improved", "updated"}


def classify_event(change_type: str, title: str) -> int:
    """Return 1 (card) or 0 (skip) based on change_type and title."""
    if change_type in CARD_TYPES:
        return 1
    if change_type in SKIP_TYPES:
        return 0
    # other -> regex classify
    verdict, _ = classify_title(title)
    return 1 if verdict == "card" else 0


def main():
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT id, change_type, title FROM claude_code_event"
    ).fetchall()

    updates = []
    card_count = 0
    skip_count = 0

    for row_id, change_type, title in rows:
        card_yn = classify_event(change_type, title)
        updates.append((card_yn, row_id))
        if card_yn == 1:
            card_count += 1
        else:
            skip_count += 1

    conn.executemany(
        "UPDATE claude_code_event SET card_yn = ? WHERE id = ?",
        updates,
    )
    conn.commit()

    print(f"Updated {len(updates)} rows: card={card_count}, skip={skip_count}")

    # Verification
    result = conn.execute(
        "SELECT card_yn, COUNT(*) FROM claude_code_event GROUP BY card_yn"
    ).fetchall()
    print(f"\nVerification (card_yn, count): {result}")

    result2 = conn.execute(
        "SELECT change_type, card_yn, COUNT(*) "
        "FROM claude_code_event GROUP BY change_type, card_yn "
        "ORDER BY change_type"
    ).fetchall()
    print(f"\nBy change_type:")
    for ct, cy, cnt in result2:
        print(f"  {ct:12s} card_yn={cy} -> {cnt}")

    null_count = conn.execute(
        "SELECT COUNT(*) FROM claude_code_event WHERE card_yn IS NULL"
    ).fetchone()[0]
    print(f"\nNULL card_yn: {null_count}")

    conn.close()


if __name__ == "__main__":
    main()
