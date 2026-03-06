"""Claude Code backfill strategy.

Schema: independent (id, event_date, title, version, change_type, subsystem, source_url)
Parser: parse_claude_code() -> list of dicts with 7 fields (npm dates, bullet-level)
Source: data/snapshots/claude_code_latest.md
Note: Markdown format (other products use HTML)
"""

from __future__ import annotations

from scripts.backfill import SNAPSHOTS_DIR, _safe_print, clear_table
from scripts.collect import insert_events
from scripts.parsers.claude_code import parse_claude_code

SNAPSHOT_FILE = "claude_code_latest.md"


def backfill(*, reparse: bool = False) -> dict:
    """Run Claude Code backfill. If reparse=True, DELETE all rows first."""
    if reparse:
        deleted = clear_table("claude_code")
        _safe_print(f"  Deleted {deleted} Claude Code events")

    path = SNAPSHOTS_DIR / SNAPSHOT_FILE
    if not path.exists():
        _safe_print(f"  [WARN] {path} not found")
        return {"parsed": 0, "inserted": 0, "skipped": 0, "error": f"{path} not found"}

    md = path.read_text(encoding="utf-8")
    events = parse_claude_code(md)

    if not events:
        return {"parsed": 0, "inserted": 0, "skipped": 0}

    result = insert_events(events)
    return {"parsed": len(events), "inserted": result["inserted"], "skipped": result["skipped"]}
