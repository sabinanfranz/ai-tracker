"""Codex backfill strategy.

Schema: independent (id, event_date, title, entry_type, version, body, source_url)
Parser: parse_codex() -> list of dicts with 7 fields
Source: data/snapshots/codex_latest.html
"""

from __future__ import annotations

from scripts.backfill import SNAPSHOTS_DIR, _safe_print, clear_table
from scripts.collect import insert_events
from scripts.parsers.codex import parse_codex

SNAPSHOT_FILE = "codex_latest.html"


def backfill(*, reparse: bool = False) -> dict:
    """Run Codex backfill. If reparse=True, DELETE all rows first."""
    if reparse:
        deleted = clear_table("codex")
        _safe_print(f"  Deleted {deleted} Codex events")

    path = SNAPSHOTS_DIR / SNAPSHOT_FILE
    if not path.exists():
        _safe_print(f"  [WARN] {path} not found")
        return {"parsed": 0, "inserted": 0, "skipped": 0, "error": f"{path} not found"}

    html = path.read_text(encoding="utf-8")
    events = parse_codex(html)

    if not events:
        return {"parsed": 0, "inserted": 0, "skipped": 0}

    result = insert_events(events)
    return {"parsed": len(events), "inserted": result["inserted"], "skipped": result["skipped"]}
