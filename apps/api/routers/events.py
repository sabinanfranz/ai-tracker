"""Event endpoints — list and detail views for the timeline."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from apps.api.database import get_connection, PRODUCT_TABLES
from apps.api.schemas import EventDetail, EventListItem, EventListResponse

# ---------------------------------------------------------------------------
# Inline UNION ALL subquery (replaces the dropped all_events view)
# ---------------------------------------------------------------------------

_UNION_SQL = """
SELECT id, 'default' AS component, event_date,
       created_at AS detected_at,
       COALESCE(title_updated, title) AS title,
       COALESCE(title_updated_ko, title_ko) AS title_ko,
       COALESCE(summary_ko, content) AS summary_ko, summary_en,
       tags, severity, source_url,
       evidence_excerpt, '{}' AS raw_ref,
       title_updated, COALESCE(content_updated, content) AS content_updated,
       title_updated_ko, content_updated_ko,
       created_at, COALESCE(updated_at, created_at) AS updated_at,
       'chatgpt' AS product
FROM chatgpt_event
UNION ALL
SELECT id, 'default' AS component, event_date,
       created_at AS detected_at, title, title_ko,
       COALESCE(content_ko, content, title) AS summary_ko, NULL AS summary_en,
       '[]' AS tags, 1 AS severity, source_url,
       '[]' AS evidence_excerpt, '{}' AS raw_ref,
       NULL AS title_updated, NULL AS content_updated,
       NULL AS title_updated_ko, NULL AS content_updated_ko,
       created_at, COALESCE(updated_at, created_at) AS updated_at,
       'gemini' AS product
FROM gemini_event
UNION ALL
SELECT id, entry_type AS component, event_date,
       created_at AS detected_at,
       COALESCE(title_updated, title) AS title,
       COALESCE(title_updated_ko, title) AS title_ko,
       COALESCE(content_updated_ko, content_updated, body, title) AS summary_ko, NULL AS summary_en,
       '[]' AS tags, 1 AS severity, source_url,
       '[]' AS evidence_excerpt, '{}' AS raw_ref,
       title_updated, content_updated,
       title_updated_ko, content_updated_ko,
       created_at, COALESCE(updated_at, created_at) AS updated_at,
       'codex' AS product
FROM codex_event
UNION ALL
SELECT id, change_type AS component, event_date,
       created_at AS detected_at, title, title_kor AS title_ko,
       COALESCE(title_kor, title) AS summary_ko, NULL AS summary_en,
       '[]' AS tags, 1 AS severity, source_url,
       '[]' AS evidence_excerpt, '{}' AS raw_ref,
       NULL AS title_updated, NULL AS content_updated,
       NULL AS title_updated_ko, NULL AS content_updated_ko,
       created_at, updated_at,
       'claude_code' AS product
FROM claude_code_event
WHERE card_yn = 1
"""

# Fields unique to each product table (not in the common UNION schema)
PRODUCT_UNIQUE_FIELDS = {
    "chatgpt": ["title", "content", "title_updated", "content_updated", "title_updated_ko", "content_updated_ko"],
    "codex": ["title", "entry_type", "version", "body", "title_updated", "content_updated", "title_updated_ko", "content_updated_ko"],
    "gemini": ["title", "content", "content_ko"],
    "claude_code": ["version", "change_type", "subsystem", "card_yn", "title_kor", "content_kor"],
}

router = APIRouter(prefix="/api/events", tags=["events"])


def _row_to_list_item(row: dict) -> EventListItem:
    """Convert a sqlite3.Row (dict-like) to an EventListItem."""
    return EventListItem(
        id=row["id"],
        product=row["product"],
        component=row["component"],
        event_date=row["event_date"],
        title=row["title"],
        title_ko=row["title_ko"],
        summary_ko=row["summary_ko"],
        tags=json.loads(row["tags"]),
        severity=row["severity"],
        source_url=row["source_url"],
        evidence_excerpt=json.loads(row["evidence_excerpt"]),
    )


def _row_to_detail(row: dict) -> EventDetail:
    """Convert a sqlite3.Row (dict-like) to an EventDetail."""
    return EventDetail(
        id=row["id"],
        product=row["product"],
        component=row["component"],
        event_date=row["event_date"],
        detected_at=row["detected_at"],
        title=row["title"],
        title_ko=row["title_ko"],
        summary_ko=row["summary_ko"],
        summary_en=row["summary_en"],
        tags=json.loads(row["tags"]),
        severity=row["severity"],
        source_url=row["source_url"],
        evidence_excerpt=json.loads(row["evidence_excerpt"]),
        raw_ref=json.loads(row["raw_ref"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("", response_model=EventListResponse)
def list_events(
    product: Optional[str] = Query(None, description="Comma-separated product IDs"),
    tag: Optional[str] = Query(None, description="Comma-separated tag IDs"),
    severity_min: int = Query(1, ge=1, le=5, description="Minimum severity"),
    year: Optional[int] = Query(None, description="Filter by year"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
) -> EventListResponse:
    """Return a paginated list of events sorted by event_date DESC."""
    conditions: list[str] = []
    params: list = []

    # -- severity filter (always applied) --
    conditions.append("severity >= ?")
    params.append(severity_min)

    # -- product filter --
    if product:
        products = [p.strip() for p in product.split(",") if p.strip()]
        if products:
            placeholders = ",".join("?" for _ in products)
            conditions.append(f"product IN ({placeholders})")
            params.extend(products)

    # -- year filter --
    if year:
        conditions.append("event_date LIKE ?")
        params.append(f"{year}-%")

    # -- tag filter (use LIKE for each tag, any-match) --
    if tag:
        tags = [t.strip() for t in tag.split(",") if t.strip()]
        if tags:
            tag_conditions = []
            for t in tags:
                # Match tag inside JSON array, e.g. tags column contains '"new_feature"'
                tag_conditions.append("tags LIKE ?")
                params.append(f'%"{t}"%')
            conditions.append(f"({' OR '.join(tag_conditions)})")

    where = " AND ".join(conditions) if conditions else "1=1"

    conn = get_connection()
    try:
        # Count total matching rows
        count_sql = f"SELECT COUNT(*) FROM ({_UNION_SQL}) AS ae WHERE {where}"
        total = conn.execute(count_sql, params).fetchone()[0]

        # Fetch page
        data_sql = (
            f"SELECT * FROM ({_UNION_SQL}) AS ae WHERE {where} "
            f"ORDER BY event_date DESC, created_at DESC "
            f"LIMIT ? OFFSET ?"
        )
        rows = conn.execute(data_sql, params + [limit, offset]).fetchall()
    finally:
        conn.close()

    items = [_row_to_list_item(row) for row in rows]
    return EventListResponse(total=total, offset=offset, limit=limit, items=items)


@router.get("/{event_id}", response_model=EventDetail)
def get_event(event_id: str) -> EventDetail:
    """Return full detail for a single event, including product-specific fields."""
    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT * FROM ({_UNION_SQL}) AS ae WHERE id = ?", (event_id,)
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Event not found")

        detail = _row_to_detail(row)

        # Fetch product-specific fields from the original table
        product = row["product"]
        table = PRODUCT_TABLES.get(product)
        unique_fields = PRODUCT_UNIQUE_FIELDS.get(product)
        if table and unique_fields:
            product_row = conn.execute(
                f"SELECT * FROM {table} WHERE id = ?", (event_id,)
            ).fetchone()
            if product_row:
                product_data = {}
                for field in unique_fields:
                    try:
                        val = product_row[field]
                        if val is not None:
                            product_data[field] = val
                    except (IndexError, KeyError):
                        pass
                if product_data:
                    detail.product_data = product_data

        return detail
    finally:
        conn.close()
