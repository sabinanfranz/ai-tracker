"""Railway startup script — backfill DB from snapshots + apply enrichments.

Run before uvicorn to ensure the database is populated on every deploy.
Usage: python -m scripts.startup
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.database import get_connection, init_db


def backfill_from_snapshots() -> None:
    """Parse snapshot files and insert events (INSERT OR IGNORE)."""
    from scripts.backfill import run_backfill
    from apps.api.database import PRODUCT_TABLES

    for product in PRODUCT_TABLES:
        try:
            result = run_backfill(product, reparse=False)
            print(f"  {product:15}: parsed={result['parsed']} inserted={result['inserted']} skipped={result['skipped']}")
        except Exception as e:
            print(f"  {product:15}: ERROR - {e}")


def apply_enrichments() -> None:
    """Apply enrichment JSON results to the database."""
    data_dir = PROJECT_ROOT / "data"

    # ChatGPT enrichments (EN)
    _apply_chatgpt_en(data_dir / "chatgpt_enrich_en_result.json")
    # ChatGPT enrichments (KO)
    _apply_chatgpt_ko(data_dir / "chatgpt_enrich_ko_result.json")
    # Codex enrichments (EN)
    _apply_codex_en(data_dir / "codex_enrich_en_result.json")
    # Codex enrichments (KO)
    _apply_codex_ko(data_dir / "codex_enrich_ko_result.json")
    # Gemini enrichments (KO)
    _apply_gemini_ko(data_dir / "gemini_enrich_ko_result.json")
    # Claude Code enrichments (KO)
    _apply_claude_code_ko(data_dir / "claude_code_enrich_ko_result.json")


def _load_json(path: Path) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  [WARN] Failed to load {path.name}: {e}")
        return []


def _apply_chatgpt_en(path: Path) -> None:
    items = _load_json(path)
    if not items:
        return
    conn = get_connection()
    updated = 0
    try:
        for item in items:
            eid = item.get("id")
            if not eid:
                continue
            title_updated = item.get("title_updated")
            content_updated = item.get("content_updated")
            summary_en = item.get("summary_en")
            tags = item.get("tags")
            severity = item.get("severity")
            evidence = item.get("evidence_excerpt")

            sets = []
            vals = []
            if title_updated:
                sets.append("title_updated = ?")
                vals.append(title_updated)
            if content_updated:
                sets.append("content_updated = ?")
                vals.append(content_updated)
            if summary_en:
                sets.append("summary_en = ?")
                vals.append(summary_en)
            if tags is not None:
                sets.append("tags = ?")
                vals.append(json.dumps(tags) if isinstance(tags, list) else str(tags))
            if severity is not None:
                sets.append("severity = ?")
                vals.append(severity)
            if evidence is not None:
                sets.append("evidence_excerpt = ?")
                vals.append(json.dumps(evidence) if isinstance(evidence, list) else str(evidence))

            if not sets:
                continue

            vals.append(eid)
            cursor = conn.execute(
                f"UPDATE chatgpt_event SET {', '.join(sets)} WHERE id = ?",
                vals,
            )
            updated += cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    print(f"  chatgpt_en     : {len(items)} items, {updated} rows updated")


def _apply_chatgpt_ko(path: Path) -> None:
    items = _load_json(path)
    if not items:
        return
    conn = get_connection()
    updated = 0
    try:
        for item in items:
            eid = item.get("id")
            if not eid:
                continue
            title_ko = item.get("title_updated_ko") or item.get("title_ko")
            content_ko = item.get("content_updated_ko") or item.get("content_ko")
            summary_ko = item.get("summary_ko")

            sets = []
            vals = []
            if title_ko:
                sets.append("title_updated_ko = ?")
                vals.append(title_ko)
            if content_ko:
                sets.append("content_updated_ko = ?")
                vals.append(content_ko)
            if summary_ko:
                sets.append("summary_ko = ?")
                vals.append(summary_ko)
            if item.get("title_ko"):
                sets.append("title_ko = ?")
                vals.append(item["title_ko"])

            if not sets:
                continue

            vals.append(eid)
            cursor = conn.execute(
                f"UPDATE chatgpt_event SET {', '.join(sets)} WHERE id = ?",
                vals,
            )
            updated += cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    print(f"  chatgpt_ko     : {len(items)} items, {updated} rows updated")


def _apply_codex_en(path: Path) -> None:
    items = _load_json(path)
    if not items:
        return
    conn = get_connection()
    updated = 0
    try:
        for item in items:
            eid = item.get("id")
            if not eid:
                continue
            title_updated = item.get("title_updated")
            content_updated = item.get("content_updated")

            sets = []
            vals = []
            if title_updated:
                sets.append("title_updated = ?")
                vals.append(title_updated)
            if content_updated:
                sets.append("content_updated = ?")
                vals.append(content_updated)

            if not sets:
                continue

            vals.append(eid)
            cursor = conn.execute(
                f"UPDATE codex_event SET {', '.join(sets)} WHERE id = ?",
                vals,
            )
            updated += cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    print(f"  codex_en       : {len(items)} items, {updated} rows updated")


def _apply_codex_ko(path: Path) -> None:
    items = _load_json(path)
    if not items:
        return
    conn = get_connection()
    updated = 0
    try:
        for item in items:
            eid = item.get("id")
            if not eid:
                continue
            title_ko = item.get("title_updated_ko")
            content_ko = item.get("content_updated_ko")

            sets = []
            vals = []
            if title_ko:
                sets.append("title_updated_ko = ?")
                vals.append(title_ko)
            if content_ko:
                sets.append("content_updated_ko = ?")
                vals.append(content_ko)

            if not sets:
                continue

            vals.append(eid)
            cursor = conn.execute(
                f"UPDATE codex_event SET {', '.join(sets)} WHERE id = ?",
                vals,
            )
            updated += cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    print(f"  codex_ko       : {len(items)} items, {updated} rows updated")


def _apply_gemini_ko(path: Path) -> None:
    items = _load_json(path)
    if not items:
        return
    conn = get_connection()
    updated = 0
    try:
        for item in items:
            eid = item.get("id")
            if not eid:
                continue
            title_ko = item.get("title_ko")
            content_ko = item.get("content_ko")

            sets = []
            vals = []
            if title_ko:
                sets.append("title_ko = ?")
                vals.append(title_ko)
            if content_ko:
                sets.append("content_ko = ?")
                vals.append(content_ko)

            if not sets:
                continue

            vals.append(eid)
            cursor = conn.execute(
                f"UPDATE gemini_event SET {', '.join(sets)} WHERE id = ?",
                vals,
            )
            updated += cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    print(f"  gemini_ko      : {len(items)} items, {updated} rows updated")


def _apply_claude_code_ko(path: Path) -> None:
    items = _load_json(path)
    if not items:
        return
    conn = get_connection()
    updated = 0
    try:
        for item in items:
            eid = item.get("id")
            if not eid:
                continue
            title_kor = item.get("title_kor")
            content_kor = item.get("content_kor")
            card_yn = item.get("card_yn")

            sets = []
            vals = []
            if title_kor:
                sets.append("title_kor = ?")
                vals.append(title_kor)
            if content_kor:
                sets.append("content_kor = ?")
                vals.append(content_kor)
            if card_yn is not None:
                sets.append("card_yn = ?")
                vals.append(int(card_yn))

            if not sets:
                continue

            vals.append(eid)
            cursor = conn.execute(
                f"UPDATE claude_code_event SET {', '.join(sets)} WHERE id = ?",
                vals,
            )
            updated += cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    print(f"  claude_code_ko : {len(items)} items, {updated} rows updated")


def main() -> None:
    print("=== Railway Startup: Initializing database ===")
    init_db()

    print("\n--- Backfill from snapshots ---")
    backfill_from_snapshots()

    print("\n--- Apply enrichments ---")
    apply_enrichments()

    print("\n=== Startup complete ===")


if __name__ == "__main__":
    main()
