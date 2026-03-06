"""Metadata endpoints — products and tags for filter UI."""

from __future__ import annotations

import json

from fastapi import APIRouter

from apps.api.database import get_connection, PRODUCT_TABLES
from apps.api.schemas import ProductInfo, TagInfo

router = APIRouter(prefix="/api", tags=["meta"])

# ---------------------------------------------------------------------------
# Hardcoded product metadata
# ---------------------------------------------------------------------------

PRODUCT_META: dict[str, dict[str, str]] = {
    "chatgpt": {"label": "ChatGPT", "color": "#10A37F"},
    "gemini": {"label": "Gemini", "color": "#4285F4"},
    "codex": {"label": "Codex", "color": "#A855F7"},
    "claude_code": {"label": "Claude Code", "color": "#D97706"},
}

# ---------------------------------------------------------------------------
# Hardcoded tag labels
# ---------------------------------------------------------------------------

TAG_LABELS: dict[str, str] = {
    "new": "새 기능",
    "change": "주요 변경",
    "pricing": "요금/접근",
    "fix": "개선/수정",
}


@router.get("/products", response_model=list[ProductInfo])
def list_products() -> list[ProductInfo]:
    """Return product metadata with event counts from the database."""
    conn = get_connection()
    try:
        counts: dict[str, int] = {}
        for pid, table in PRODUCT_TABLES.items():
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            counts[pid] = count
    finally:
        conn.close()

    return [
        ProductInfo(
            id=pid,
            label=meta["label"],
            color=meta["color"],
            event_count=counts.get(pid, 0),
        )
        for pid, meta in PRODUCT_META.items()
    ]


@router.get("/tags", response_model=list[TagInfo])
def list_tags() -> list[TagInfo]:
    """Return tag metadata with counts from the database.

    Since tags are stored as JSON arrays, we use json_each to expand
    them and count occurrences.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT value as tag, COUNT(*) as cnt
            FROM chatgpt_event, json_each(chatgpt_event.tags)
            GROUP BY value
            """
        ).fetchall()
    finally:
        conn.close()

    counts: dict[str, int] = {row["tag"]: row["cnt"] for row in rows}

    return [
        TagInfo(
            id=tag_id,
            label=label,
            count=counts.get(tag_id, 0),
        )
        for tag_id, label in TAG_LABELS.items()
    ]
