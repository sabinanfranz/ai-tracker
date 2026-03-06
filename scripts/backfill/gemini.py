"""Gemini backfill strategy.

Schema: independent (id, event_date, title, content, source_url, created_at, updated_at)
Parser: parse_gemini() -> list of dicts with 5 fields (product, event_date, title, content, source_url)
Each <h3> feature title produces one event row.
Source: data/snapshots/gemini_latest.html
"""

from __future__ import annotations

from scripts.backfill import SNAPSHOTS_DIR, _safe_print, clear_table
from scripts.collect import insert_events
from scripts.parsers.gemini import parse_gemini

SNAPSHOT_FILE = "gemini_latest.html"


def backfill(*, reparse: bool = False) -> dict:
    """Run Gemini backfill. If reparse=True, DELETE all rows first."""
    if reparse:
        deleted = clear_table("gemini")
        _safe_print(f"  Deleted {deleted} Gemini events")

    path = SNAPSHOTS_DIR / SNAPSHOT_FILE
    if not path.exists():
        _safe_print(f"  [WARN] {path} not found")
        return {"parsed": 0, "inserted": 0, "skipped": 0, "error": f"{path} not found"}

    html = path.read_text(encoding="utf-8")
    events = parse_gemini(html)

    if not events:
        return {"parsed": 0, "inserted": 0, "skipped": 0}

    result = insert_events(events)
    return {"parsed": len(events), "inserted": result["inserted"], "skipped": result["skipped"]}
