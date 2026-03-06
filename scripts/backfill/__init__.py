"""Product-specific backfill orchestrator.

Usage:
    python -m scripts.backfill                # 전체 backfill (INSERT OR IGNORE)
    python -m scripts.backfill --chatgpt      # ChatGPT만 재backfill (DELETE + reparse)
    python -m scripts.backfill --codex        # Codex만
    python -m scripts.backfill --gemini       # Gemini만
    python -m scripts.backfill --claude-code  # Claude Code만
    python -m scripts.backfill --all          # 전체 재backfill
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.database import PRODUCT_TABLES, get_connection, init_db

SNAPSHOTS_DIR = PROJECT_ROOT / "data" / "snapshots"


# ---------------------------------------------------------------------------
# Common utilities
# ---------------------------------------------------------------------------

def _safe_print(text: str) -> None:
    """Print text safely on Windows (cp949/utf-8 terminals)."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def clear_table(product: str) -> int:
    """Delete all rows from a product table. Returns deleted row count."""
    table = PRODUCT_TABLES[product]
    conn = get_connection()
    try:
        cursor = conn.execute(f"DELETE FROM {table}")
        deleted = cursor.rowcount
        conn.commit()
        return deleted
    finally:
        conn.close()


def run_backfill(product: str, *, reparse: bool = False) -> dict:
    """Run backfill for a single product.

    Args:
        product: One of 'chatgpt', 'codex', 'gemini', 'claude_code'.
        reparse: If True, DELETE all existing rows before re-inserting.

    Returns:
        dict with keys: parsed, inserted, skipped, and optionally error.
    """
    from scripts.backfill import chatgpt, codex, gemini, claude_code

    modules = {
        "chatgpt": chatgpt,
        "codex": codex,
        "gemini": gemini,
        "claude_code": claude_code,
    }
    mod = modules[product]
    return mod.backfill(reparse=reparse)


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------

def _print_single_report(product: str, result: dict) -> None:
    """Print a report for a single product rebackfill."""
    _safe_print("")
    _safe_print(f"AI Update Tracker - {product} Re-backfill")
    _safe_print(
        f"  {product:15}: {result['parsed']:3} events parsed, "
        f"{result['inserted']:3} inserted, {result['skipped']:3} skipped"
    )
    if result.get("error"):
        _safe_print(f"  [WARN] {result['error']}")
    _safe_print("")


def _print_full_report(results: dict[str, dict]) -> None:
    """Print a full backfill report for all products."""
    total_inserted = sum(r["inserted"] for r in results.values())
    total_skipped = sum(r["skipped"] for r in results.values())

    _safe_print("")
    _safe_print("AI Update Tracker - Backfill Report")
    for source, r in results.items():
        _safe_print(
            f"  {source:15}: {r['parsed']:3} events parsed, "
            f"{r['inserted']:3} inserted, {r['skipped']:3} skipped"
        )
        if r.get("error"):
            _safe_print(f"    [WARN] {r['error']}")
    _safe_print(f"  Total: {total_inserted} inserted, {total_skipped} skipped")
    _safe_print("")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

PRODUCT_FLAGS = {
    "--chatgpt": "chatgpt",
    "--codex": "codex",
    "--gemini": "gemini",
    "--claude-code": "claude_code",
}


def main() -> None:
    """CLI entry point for backfill."""
    init_db()
    args = sys.argv[1:]

    # Specific product flag → reparse that product only
    for flag, product in PRODUCT_FLAGS.items():
        if flag in args:
            result = run_backfill(product, reparse=True)
            _print_single_report(product, result)
            return

    # --all → reparse all products
    if "--all" in args:
        for product in PRODUCT_TABLES:
            result = run_backfill(product, reparse=True)
            _print_single_report(product, result)
        return

    # No flags → INSERT OR IGNORE for all products (preserve existing data)
    results = {}
    for product in PRODUCT_TABLES:
        results[product] = run_backfill(product, reparse=False)
    _print_full_report(results)
