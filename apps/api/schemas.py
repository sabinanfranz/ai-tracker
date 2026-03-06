"""Pydantic response schemas for the AI Update Tracker API."""

from __future__ import annotations

from pydantic import BaseModel


class EventListItem(BaseModel):
    """Lightweight event representation for list / timeline view."""
    id: str
    product: str
    component: str
    event_date: str
    title: str
    title_ko: str | None
    summary_ko: str
    tags: list[str]
    severity: int
    source_url: str
    evidence_excerpt: list[str]


class EventDetail(BaseModel):
    """Full event representation for detail / expanded card view."""
    id: str
    product: str
    component: str
    event_date: str
    detected_at: str
    title: str
    title_ko: str | None
    summary_ko: str
    summary_en: str | None
    tags: list[str]
    severity: int
    source_url: str
    evidence_excerpt: list[str]
    raw_ref: dict
    product_data: dict | None = None
    created_at: str
    updated_at: str


class EventListResponse(BaseModel):
    """Paginated list of events."""
    total: int
    offset: int
    limit: int
    items: list[EventListItem]


class ProductInfo(BaseModel):
    """Product metadata for filter UI."""
    id: str
    label: str
    color: str
    event_count: int


class TagInfo(BaseModel):
    """Tag metadata for filter UI."""
    id: str
    label: str
    count: int
