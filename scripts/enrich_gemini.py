"""Gemini event enrichment: generate/apply Korean title & summary.

Workflow (Claude Code session):
  1. python -m scripts.enrich_gemini --generate > data/gemini_enrich_pending.json
  2. Claude Code reads JSON, produces title_ko + content_ko for each row
  3. python -m scripts.enrich_gemini --apply data/gemini_enrich_result.json

Or use --interactive for stdin-based one-by-one enrichment.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tracker.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _pending_rows(conn: sqlite3.Connection, *, limit: int = 0, force: bool = False) -> list[dict]:
    """Return rows that need enrichment."""
    if force:
        where = "1=1"
    else:
        where = "title_ko IS NULL"
    sql = f"SELECT id, event_date, title, content FROM gemini_event WHERE {where} ORDER BY event_date DESC"
    if limit > 0:
        sql += f" LIMIT {limit}"
    rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


# ── generate ────────────────────────────────────────────────────────

def cmd_generate(args: argparse.Namespace) -> None:
    """Output pending rows as JSON for Claude Code to enrich."""
    conn = _connect()
    rows = _pending_rows(conn, limit=args.limit, force=args.force)
    conn.close()
    out = open(sys.stdout.fileno(), "w", encoding="utf-8", closefd=False)
    json.dump(rows, out, ensure_ascii=False, indent=2)
    out.flush()
    print(file=sys.stderr)
    print(f"[enrich_gemini] {len(rows)} row(s) pending", file=sys.stderr)


# ── apply ───────────────────────────────────────────────────────────

def cmd_apply(args: argparse.Namespace) -> None:
    """Read enrichment JSON and UPDATE the DB."""
    path = Path(args.file)
    if not path.exists():
        print(f"[error] file not found: {path}", file=sys.stderr)
        sys.exit(1)

    data: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    conn = _connect()
    updated = 0
    for item in data:
        rid = item.get("id")
        title_ko = item.get("title_ko")
        content_ko = item.get("content_ko")
        if not rid or not title_ko or not content_ko:
            print(f"[skip] incomplete: {rid}", file=sys.stderr)
            continue
        conn.execute(
            "UPDATE gemini_event SET title_ko = ?, content_ko = ?, updated_at = datetime('now') WHERE id = ?",
            (title_ko, content_ko, rid),
        )
        updated += 1
    conn.commit()
    conn.close()
    print(f"[enrich_gemini] applied {updated}/{len(data)} row(s)")


# ── interactive ─────────────────────────────────────────────────────

def cmd_interactive(args: argparse.Namespace) -> None:
    """One-by-one: print row, read JSON from stdin, update DB."""
    conn = _connect()
    rows = _pending_rows(conn, limit=args.limit, force=args.force)
    if not rows:
        print("[enrich_gemini] nothing to enrich")
        return

    updated = 0
    for row in rows:
        print(json.dumps(row, ensure_ascii=False, indent=2), flush=True)
        print("--- enter JSON {\"title_ko\": ..., \"content_ko\": ...} ---", file=sys.stderr)
        line = sys.stdin.readline().strip()
        if not line:
            print("[skip] empty input", file=sys.stderr)
            continue
        try:
            result = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"[skip] bad JSON: {e}", file=sys.stderr)
            continue
        title_ko = result.get("title_ko")
        content_ko = result.get("content_ko")
        if not title_ko or not content_ko:
            print("[skip] missing fields", file=sys.stderr)
            continue
        conn.execute(
            "UPDATE gemini_event SET title_ko = ?, content_ko = ?, updated_at = datetime('now') WHERE id = ?",
            (title_ko, content_ko, row["id"]),
        )
        conn.commit()
        updated += 1
        print(f"[ok] {row['id']}", file=sys.stderr)

    conn.close()
    print(f"[enrich_gemini] interactive: {updated}/{len(rows)} row(s) updated")


# ── status ──────────────────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> None:
    """Print enrichment progress."""
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM gemini_event").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM gemini_event WHERE title_ko IS NOT NULL").fetchone()[0]
    conn.close()
    pending = total - done
    print(f"[enrich_gemini] total={total}  done={done}  pending={pending}")


# ── CLI ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini event Korean enrichment")
    sub = parser.add_subparsers(dest="command")

    # generate
    p_gen = sub.add_parser("generate", aliases=["--generate"], help="Output pending rows as JSON")
    p_gen.add_argument("--limit", type=int, default=0, help="Max rows (0=all)")
    p_gen.add_argument("--force", action="store_true", help="Include already-enriched rows")

    # apply
    p_apply = sub.add_parser("apply", aliases=["--apply"], help="Apply enrichment JSON to DB")
    p_apply.add_argument("file", help="Path to enrichment JSON file")

    # interactive
    p_inter = sub.add_parser("interactive", aliases=["--interactive"], help="Interactive stdin enrichment")
    p_inter.add_argument("--limit", type=int, default=0, help="Max rows (0=all)")
    p_inter.add_argument("--force", action="store_true", help="Include already-enriched rows")

    # status
    sub.add_parser("status", aliases=["--status"], help="Show enrichment progress")

    args = parser.parse_args()

    # Support --flag style: map aliases
    cmd = args.command
    if cmd in ("generate", "--generate"):
        cmd_generate(args)
    elif cmd in ("apply", "--apply"):
        cmd_apply(args)
    elif cmd in ("interactive", "--interactive"):
        cmd_interactive(args)
    elif cmd in ("status", "--status"):
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
