"""
Localize English summary_ko to Korean for ChatGPT, Codex and Claude Code events.

Gemini events are already in Korean (parsed from Korean pages).
ChatGPT, Codex and Claude Code events have English text in summary_ko that needs
to be converted to readable Korean for non-developer users.

Strategy: Translate action verbs (Added/Fixed/Improved) to Korean suffixes,
then do careful whole-word term replacement for common technical terms.

Usage:
    python -m scripts.localize_data              # apply translations
    python -m scripts.localize_data --dry-run    # preview without writing
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.database import PRODUCT_TABLES, get_connection, init_db


# ---------------------------------------------------------------------------
# Whole-word term replacement (uses word boundaries to avoid partial matches)
# ---------------------------------------------------------------------------

# Pairs of (english_term, korean_term)
# These are replaced as whole words only (via \b boundaries)
_TERM_PAIRS: list[tuple[str, str]] = [
    # UI / UX
    ("theme picker", "테마 선택기"),
    ("live preview", "실시간 미리보기"),
    ("progress bar", "진행 표시줄"),
    ("status bar", "상태 표시줄"),
    ("model selector", "모델 선택기"),
    ("context menu", "컨텍스트 메뉴"),
    # Dev concepts
    ("slash commands", "슬래시 명령어"),
    ("slash command", "슬래시 명령어"),
    ("install script", "설치 스크립트"),
    ("code blocks", "코드 블록"),
    ("code block", "코드 블록"),
    ("auto-memory", "자동 메모리"),
    ("inline edit", "인라인 편집"),
    ("tool calls", "도구 호출"),
    ("tool call", "도구 호출"),
    ("tool use", "도구 사용"),
    ("file system", "파일 시스템"),
    ("error handling", "오류 처리"),
    ("rate limit", "사용량 제한"),
    ("rate limits", "사용량 제한"),
    ("rate-limit", "사용량 제한"),
    ("commit message", "커밋 메시지"),
    ("pull request", "풀 리퀘스트"),
    ("git hooks", "Git 훅"),
    ("git hook", "Git 훅"),
    ("system prompt", "시스템 프롬프트"),
    ("custom instructions", "사용자 지시"),
    ("custom instruction", "사용자 지시"),
    ("background tasks", "백그라운드 작업"),
    ("background task", "백그라운드 작업"),
    # Product terms
    ("Codex CLI", "Codex CLI(명령줄 도구)"),
    ("Codex app", "Codex 앱"),
]

# Build compiled patterns (word-boundary aware)
_COMPILED_TERMS: list[tuple[re.Pattern, str]] = []
for _eng, _kor in _TERM_PAIRS:
    # Use word boundaries only around alphanumeric edges
    _left = r"\b" if _eng[0].isalnum() else ""
    _right = r"\b" if _eng[-1].isalnum() else ""
    _pat = re.compile(_left + re.escape(_eng) + _right, re.IGNORECASE)
    _COMPILED_TERMS.append((_pat, _kor))


def _apply_terms(text: str) -> str:
    """Replace known terms as whole words only."""
    result = text
    for pat, kor in _COMPILED_TERMS:
        result = pat.sub(kor, result)
    return result


# ---------------------------------------------------------------------------
# Action verb patterns → Korean sentence restructuring
# ---------------------------------------------------------------------------

_VERB_PATTERNS: list[tuple[re.Pattern, str]] = [
    # "Added support for X" → "X 지원 추가"
    (re.compile(r"^Added?\s+support\s+for\s+(.+)", re.I), "{0} 지원 추가"),
    # "Support for X" → "X 지원"
    (re.compile(r"^Support(?:s|ed)?\s+for\s+(.+)", re.I), "{0} 지원"),
    # "Added X" → "X 추가됨"
    (re.compile(r"^Added?\s+(?:a\s+|an\s+|the\s+)?(.+)", re.I), "{0} 추가됨"),
    # "New X" → "새 X"
    (re.compile(r"^New\s+(.+)", re.I), "새 {0}"),
    # "Fixed a bug where/in/for/that/when X" → "X 수정됨"
    (re.compile(r"^Fix(?:ed|es)?\s+(?:a\s+)?(?:bug\s+)?(?:where|in|for|that|when|with)?\s*(.+)", re.I), "{0} 수정됨"),
    # "Improved X" → "X 개선됨"
    (re.compile(r"^Improv(?:ed?|es|ing)\s+(.+)", re.I), "{0} 개선됨"),
    # "Updated X" → "X 업데이트됨"
    (re.compile(r"^Updated?\s+(.+)", re.I), "{0} 업데이트됨"),
    # "Removed X" → "X 제거됨"
    (re.compile(r"^Removed?\s+(.+)", re.I), "{0} 제거됨"),
    # "Enabled X" → "X 활성화됨"
    (re.compile(r"^Enabled?\s+(.+)", re.I), "{0} 활성화됨"),
    # "Deprecated X" → "X 지원 종료 예정"
    (re.compile(r"^Deprecat(?:ed|ing)\s+(.+)", re.I), "{0} 지원 종료 예정"),
    # "Introduced X" → "X 도입됨"
    (re.compile(r"^Introduc(?:ed|ing)\s+(.+)", re.I), "{0} 도입됨"),
    # "Resolved X" → "X 해결됨"
    (re.compile(r"^Resolved?\s+(.+)", re.I), "{0} 해결됨"),
    # "Launched X" → "X 출시됨"
    (re.compile(r"^Launched?\s+(.+)", re.I), "{0} 출시됨"),
    # "Released X" → "X 출시됨"
    (re.compile(r"^Released?\s+(.+)", re.I), "{0} 출시됨"),
    # "Renamed X" → "X 이름 변경됨"
    (re.compile(r"^Renamed?\s+(.+)", re.I), "{0} 이름 변경됨"),
    # "Optimized X" → "X 최적화됨"
    (re.compile(r"^Optimiz(?:ed|ing)\s+(.+)", re.I), "{0} 최적화됨"),
    # "Switched to X" → "X(으)로 전환됨"
    (re.compile(r"^Switch(?:ed)?\s+to\s+(.+)", re.I), "{0}(으)로 전환됨"),
    # "Rewrote X" → "X 재작성됨"
    (re.compile(r"^Re(?:wrote|written)\s+(.+)", re.I), "{0} 재작성됨"),
    # "Replaced X" → "X 대체됨"
    (re.compile(r"^Replaced?\s+(.+)", re.I), "{0} 대체됨"),
    # "Changed X" → "X 변경됨"
    (re.compile(r"^Changed?\s+(.+)", re.I), "{0} 변경됨"),
    # "Allowed X" → "X 허용됨"
    (re.compile(r"^Allow(?:ed|s)?\s+(.+)", re.I), "{0} 허용됨"),
    # "Prevented X" → "X 방지됨"
    (re.compile(r"^Prevent(?:ed|s)?\s+(.+)", re.I), "{0} 방지됨"),
    # "Claude automatically X" → "Claude가 자동으로 X"
    (re.compile(r"^Claude\s+automatically\s+(.+)", re.I), "Claude가 자동으로 {0}"),
    # "Claude now X" → "Claude가 이제 X"
    (re.compile(r"^Claude\s+(?:now|can\s+now)\s+(.+)", re.I), "Claude가 이제 {0}"),
    # "The X now Y" → "X: 이제 Y"
    (re.compile(r"^The\s+(.+?)\s+now\s+(.+)", re.I), "{0}: 이제 {1}"),
    # "X is now Y" → "X: 이제 Y"
    (re.compile(r"^(.{3,30}?)\s+is\s+now\s+(.+)", re.I), "{0}: 이제 {1}"),
]


def _translate_item(item: str) -> str:
    """Translate a single summary item to Korean.

    Strategy:
    1. Strip common prefixes (IDE:, Hooks:, etc.)
    2. Try to match an action verb pattern
    3. Apply term replacement to the captured group only
    4. If no pattern matches, apply term replacement to the whole item
    """
    item = item.strip()
    if not item:
        return ""

    # Remove markdown bold markers
    clean = re.sub(r"\*\*(.+?)\*\*", r"\1", item)

    # Strip category prefixes (IDE:, Hooks:, Output Styles:, etc.)
    prefix = ""
    prefix_match = re.match(r"^([A-Z][A-Za-z /]+):\s*(.+)", clean)
    if prefix_match:
        prefix = prefix_match.group(1).strip() + ": "
        clean = prefix_match.group(2).strip()

    # Try action verb patterns
    for pattern, template in _VERB_PATTERNS:
        m = pattern.match(clean)
        if m:
            groups = [_apply_terms(g.strip()) for g in m.groups()]
            try:
                return prefix + template.format(*groups)
            except (IndexError, KeyError):
                pass

    # No pattern matched → apply term replacement only
    return prefix + _apply_terms(clean)


def translate_summary(english_summary: str) -> str:
    """Convert English summary to Korean.

    Splits by "; " separator (from backfill.py format),
    translates each item, and joins with ". ".
    """
    if not english_summary or not english_summary.strip():
        return english_summary or ""

    items = english_summary.split("; ")
    translated: list[str] = []

    for item in items:
        t = _translate_item(item)
        if t:
            # Trim trailing period/comma
            t = t.rstrip(".,")
            translated.append(t)

    if not translated:
        return english_summary

    return ". ".join(translated) + "."


# ---------------------------------------------------------------------------
# Korean character detection
# ---------------------------------------------------------------------------

def _has_korean(text: str) -> bool:
    """Check if text contains Korean Hangul characters."""
    return bool(text) and any("\uac00" <= c <= "\ud7a3" for c in text)


# ---------------------------------------------------------------------------
# Safe print (Windows encoding)
# ---------------------------------------------------------------------------

def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    init_db()
    conn = get_connection()

    try:
        # Only gemini uses the common schema with summary_ko/summary_en
        # chatgpt, codex, claude_code use independent schemas
        events = conn.execute(
            """
            SELECT id, 'gemini' AS product, title,
                   COALESCE(content_ko, content, title) AS summary_ko,
                   NULL AS summary_en
            FROM gemini_event
            ORDER BY event_date
            """
        ).fetchall()

        _safe_print("")
        _safe_print(f"AI Update Tracker - 한국어 변환 {'(미리보기)' if dry_run else ''}")
        _safe_print(f"  대상: {len(events)}개 이벤트 (gemini)")
        _safe_print("")

        updated = 0
        skipped_korean = 0
        skipped_empty = 0

        for event in events:
            eid = event["id"]
            product = event["product"]
            title = event["title"]
            summary_ko = event["summary_ko"]
            summary_en = event["summary_en"]

            # Skip if already Korean
            if summary_ko and _has_korean(summary_ko):
                skipped_korean += 1
                continue

            # Skip if empty
            if not summary_ko or not summary_ko.strip():
                skipped_empty += 1
                continue

            english_text = summary_ko
            korean_text = translate_summary(english_text)

            if dry_run:
                _safe_print(f"  [{product}] {title}")
                _safe_print(f"    EN: {english_text[:120]}")
                _safe_print(f"    KO: {korean_text[:120]}")
                _safe_print("")
            else:
                new_summary_en = summary_en if summary_en else english_text
                table = PRODUCT_TABLES.get(product, "chatgpt_event")
                conn.execute(
                    f"""
                    UPDATE {table}
                    SET summary_ko = ?, summary_en = ?
                    WHERE id = ?
                    """,
                    (korean_text, new_summary_en, eid),
                )

            updated += 1

        if not dry_run:
            conn.commit()

        _safe_print(f"  결과:")
        _safe_print(f"    변환 완료:    {updated}")
        _safe_print(f"    이미 한국어:  {skipped_korean}")
        _safe_print(f"    빈 요약:     {skipped_empty}")
        _safe_print(f"    전체:        {len(events)}")

        if dry_run:
            _safe_print("")
            _safe_print("  (미리보기 모드 — DB에 변경 사항 없음)")

        _safe_print("")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
