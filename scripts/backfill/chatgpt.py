"""ChatGPT backfill strategy.

Schema: simple (id, event_date, title, content, source_url)
Parser: parse_chatgpt() -> list of dicts with 5 fields
Source: data/snapshots/chatgpt_latest.html
"""

from __future__ import annotations

from scripts.backfill import SNAPSHOTS_DIR, _safe_print, clear_table
from scripts.collect import insert_events
from scripts.parsers.chatgpt import parse_chatgpt

SNAPSHOT_FILE = "chatgpt_latest.html"


def backfill(*, reparse: bool = False) -> dict:
    """Run ChatGPT backfill. If reparse=True, DELETE all rows first."""
    if reparse:
        deleted = clear_table("chatgpt")
        _safe_print(f"  Deleted {deleted} ChatGPT events")

    path = SNAPSHOTS_DIR / SNAPSHOT_FILE
    if not path.exists():
        _safe_print(f"  [WARN] {path} not found (save manually from browser)")
        return {"parsed": 0, "inserted": 0, "skipped": 0, "error": f"{path} not found"}

    html = path.read_text(encoding="utf-8")
    events = parse_chatgpt(html)

    if not events:
        return {"parsed": 0, "inserted": 0, "skipped": 0}

    result = insert_events(events)
    return {"parsed": len(events), "inserted": result["inserted"], "skipped": result["skipped"]}
