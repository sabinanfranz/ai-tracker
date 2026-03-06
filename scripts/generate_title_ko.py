"""
Generate short Korean headlines (title_ko) from summary_ko.

Extracts the first sentence, strips formal endings, and caps length
to create a headline like "코드 간소화·일괄 처리 추가".

Usage:
    python -m scripts.generate_title_ko              # apply
    python -m scripts.generate_title_ko --dry-run    # preview
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.database import PRODUCT_TABLES, get_connection, init_db

# Max chars for the headline (55 = ~2 lines at 13px)
MAX_TITLE_LEN = 55

# Formal endings to strip (longest first to avoid partial matches)
_FORMAL_ENDINGS = [
    "이 추가되었습니다",
    "가 추가되었습니다",
    "를 지원합니다",
    "을 지원합니다",
    "가 지원됩니다",
    "이 지원됩니다",
    "가 적용됩니다",
    "이 적용됩니다",
    "가 포함됩니다",
    "이 포함됩니다",
    "되었습니다",
    "었습니다",
    "있습니다",
    "겠습니다",
    "습니다",
    "입니다",
    "됩니다",
    "합니다",
    "십시오",
    "니다",
    "세요",
]

# Parenthetical content to simplify
_PAREN_RE = re.compile(r"\([^)]{0,20}\)")


def _make_headline(summary_ko: str, title: str) -> str:
    """Create a short Korean headline from summary_ko.

    Improvements over simple first-sentence extraction:
    - Prefer sentences containing action keywords (추가/출시/변경/수정/지원 등)
    - Use semicolon-split first item when applicable
    - Natural-boundary truncation at 55 chars
    """
    if not summary_ko or not summary_ko.strip():
        return title or ""

    # Split into sentences
    sentences = re.split(r"[.。]\s*", summary_ko.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return title or ""

    # Prefer sentence with action keywords (indicates core change)
    _ACTION_KW = ["추가", "출시", "변경", "수정", "지원", "제공", "폐기", "개선", "통합", "확대", "인상", "감소"]
    best = sentences[0]
    for sent in sentences:
        if any(kw in sent for kw in _ACTION_KW):
            best = sent
            break

    # If semicolon-separated, take only the first item
    if ";" in best:
        best = best.split(";")[0].strip()

    # Strip formal endings
    for ending in _FORMAL_ENDINGS:
        if best.endswith(ending):
            best = best[: -len(ending)].rstrip()
            break

    # Remove parenthetical details to save space
    best = _PAREN_RE.sub("", best).strip()

    # Clean up leftover punctuation
    best = re.sub(r"\s+", " ", best).strip(" ,;.")

    # Truncate at natural boundary if too long
    if len(best) > MAX_TITLE_LEN:
        cut = best[:MAX_TITLE_LEN]
        # Find last natural break point
        last_break = max(
            cut.rfind(" "), cut.rfind(","), cut.rfind("와"),
            cut.rfind("과"), cut.rfind("·"), cut.rfind("—"),
        )
        if last_break > MAX_TITLE_LEN // 2:
            cut = cut[:last_break].rstrip(" ,;.")
        best = cut

    return best if best else (title or "")


def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    force = "--force" in args

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    init_db()
    conn = get_connection()

    try:
        rows = conn.execute(
            "SELECT id, 'gemini' AS product, title, "
            "COALESCE(content_ko, content, title) AS summary_ko, title_ko "
            "FROM gemini_event ORDER BY event_date DESC"
        ).fetchall()

        _safe_print("")
        mode_label = "(미리보기)" if dry_run else "(강제 덮어쓰기)" if force else ""
        _safe_print(f"title_ko 생성 {mode_label}")
        _safe_print(f"  대상: {len(rows)}개 이벤트")
        _safe_print("")

        updated = 0
        skipped = 0

        for row in rows:
            eid = row["id"]
            product = row["product"]
            title = row["title"]
            summary_ko = row["summary_ko"]
            existing = row["title_ko"]

            # Skip if already has title_ko (unless --force)
            if existing and existing.strip() and not force:
                skipped += 1
                continue

            headline = _make_headline(summary_ko, title)

            if dry_run:
                _safe_print(f"  {title}")
                _safe_print(f"    ko: {summary_ko[:60]}...")
                _safe_print(f"    -> {headline}")
                _safe_print("")
            else:
                table = PRODUCT_TABLES.get(product, "chatgpt_event")
                conn.execute(
                    f"UPDATE {table} SET title_ko = ? WHERE id = ?",
                    (headline, eid),
                )

            updated += 1

        if not dry_run:
            conn.commit()

        _safe_print(f"  결과: 생성 {updated}, 건너뜀 {skipped}")
        if dry_run:
            _safe_print("  (미리보기 — DB 변경 없음)")
        _safe_print("")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
