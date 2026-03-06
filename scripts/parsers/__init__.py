"""Shared utilities for product-specific parsers.

Each parser module (chatgpt, codex, gemini, claude_code) imports common
helpers from here.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Tag classification keywords
# ---------------------------------------------------------------------------

_TAG_RULES: list[tuple[list[str], str]] = [
    (["breaking", "deprecated", "removed", "deprecation", "shutdown", "end of life"], "change"),
    (["new feature", "added", "support for", "new model", "launch",
      "model", "opus", "sonnet", "gpt", "gemini 2", "gemini 1.5"], "new"),
    (["fixed", "bug", "crash", "regression",
      "performance", "improved", "optimization", "faster"], "fix"),
    (["pricing", "plan", "access", "tier", "quota"], "pricing"),
]


def classify_tags(text: str) -> list[str]:
    """Return a list of tags based on keyword matching in text."""
    text_lower = text.lower()
    tags: list[str] = []
    for keywords, tag in _TAG_RULES:
        for kw in keywords:
            if kw in text_lower:
                tags.append(tag)
                break
    if not tags:
        tags = ["new"]
    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


# ---------------------------------------------------------------------------
# English date parsing (used by ChatGPT and Claude Code parsers)
# ---------------------------------------------------------------------------

_MONTH_MAP: dict[str, str] = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "jun": "06", "jul": "07", "aug": "08", "sep": "09",
    "oct": "10", "nov": "11", "dec": "12",
}

_EN_DATE_RE = re.compile(
    r"(january|february|march|april|may|june|july|august|september|october|november|december"
    r"|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)"
    r"\s+(\d{1,2}),?\s+(\d{4})",
    re.IGNORECASE,
)


def parse_en_date(text: str) -> str | None:
    """Extract an English date string and return YYYY-MM-DD or None."""
    m = _EN_DATE_RE.search(text)
    if not m:
        return None
    month = _MONTH_MAP.get(m.group(1).lower())
    if not month:
        return None
    day = m.group(2).zfill(2)
    year = m.group(3)
    return f"{year}-{month}-{day}"
