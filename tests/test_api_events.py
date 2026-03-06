"""Tests for event and metadata API endpoints (US-001)."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from apps.api.database import PRODUCT_TABLES, get_connection, init_db
from apps.api.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _insert_event(
    *,
    product: str = "chatgpt",
    event_date: str = "2025-06-15",
    title: str = "Test event",
    summary_ko: str = "Test summary",
    tags: list[str] | None = None,
    severity: int = 2,
    source_url: str = "https://example.com",
    evidence_excerpt: list[str] | None = None,
    event_id: str | None = None,
) -> str:
    """Insert a test event and return its id."""
    table = PRODUCT_TABLES[product]
    eid = event_id or str(uuid.uuid4())
    conn = get_connection()
    try:
        if product == "chatgpt":
            conn.execute(
                """
                INSERT INTO chatgpt_event
                    (id, event_date, title, content, source_url,
                     tags, severity, evidence_excerpt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (eid, event_date, title, summary_ko, source_url,
                 json.dumps(tags or []), severity, json.dumps(evidence_excerpt or [])),
            )
        elif product == "codex":
            conn.execute(
                """
                INSERT INTO codex_event
                    (id, event_date, title, entry_type, body, source_url)
                VALUES (?, ?, ?, 'general', ?, ?)
                """,
                (eid, event_date, title, summary_ko, source_url),
            )
        elif product == "claude_code":
            conn.execute(
                """
                INSERT INTO claude_code_event
                    (id, event_date, title, version, change_type, source_url)
                VALUES (?, ?, ?, '0.0.0', 'other', ?)
                """,
                (eid, event_date, title, source_url),
            )
        elif product == "gemini":
            conn.execute(
                """
                INSERT INTO gemini_event
                    (id, event_date, title, content, source_url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (eid, event_date, title, summary_ko, source_url),
            )
        else:
            raise ValueError(f"Unknown product in test helper: {product}")
        conn.commit()
    finally:
        conn.close()
    return eid


@pytest.fixture(autouse=True)
def _clean_db():
    """Ensure a fresh database for every test."""
    init_db()
    conn = get_connection()
    try:
        for table in PRODUCT_TABLES.values():
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
    finally:
        conn.close()
    yield


# ---------------------------------------------------------------------------
# GET /api/events
# ---------------------------------------------------------------------------

class TestListEvents:
    def test_empty_response(self):
        res = client.get("/api/events")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_returns_inserted_events(self):
        _insert_event(title="Event A", event_date="2025-06-10")
        _insert_event(title="Event B", event_date="2025-06-11")

        res = client.get("/api/events")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        # Sorted by event_date DESC
        assert data["items"][0]["event_date"] == "2025-06-11"
        assert data["items"][1]["event_date"] == "2025-06-10"

    def test_filter_by_product(self):
        _insert_event(product="chatgpt", title="ChatGPT event")
        _insert_event(product="gemini", title="Gemini event")

        res = client.get("/api/events?product=chatgpt")
        data = res.json()
        assert data["total"] == 1
        assert data["items"][0]["product"] == "chatgpt"

    def test_filter_by_multiple_products(self):
        _insert_event(product="chatgpt")
        _insert_event(product="gemini")
        _insert_event(product="codex")

        res = client.get("/api/events?product=chatgpt,gemini")
        data = res.json()
        assert data["total"] == 2

    def test_filter_by_severity_min(self):
        _insert_event(product="chatgpt", severity=1, title="Low")
        _insert_event(product="chatgpt", severity=3, title="Medium")
        _insert_event(product="chatgpt", severity=5, title="High")

        res = client.get("/api/events?severity_min=3")
        data = res.json()
        assert data["total"] == 2
        severities = {item["severity"] for item in data["items"]}
        assert severities == {3, 5}

    def test_filter_by_year(self):
        _insert_event(event_date="2025-03-01", title="2025 event")
        _insert_event(event_date="2026-01-15", title="2026 event")

        res = client.get("/api/events?year=2025")
        data = res.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "2025 event"

    def test_filter_by_tag(self):
        _insert_event(product="chatgpt", tags=["new", "pricing"], title="New event")
        _insert_event(product="chatgpt", tags=["fix"], title="Fix event")
        _insert_event(product="chatgpt", tags=["change"], title="Change event")

        res = client.get("/api/events?tag=new")
        data = res.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "New event"

    def test_filter_by_multiple_tags(self):
        _insert_event(product="chatgpt", tags=["new"], title="New event")
        _insert_event(product="chatgpt", tags=["fix"], title="Fix event")
        _insert_event(product="chatgpt", tags=["change"], title="Change event")

        res = client.get("/api/events?tag=new,change")
        data = res.json()
        assert data["total"] == 2

    def test_pagination_offset_limit(self):
        for i in range(10):
            _insert_event(
                event_date=f"2025-06-{10 + i:02d}",
                title=f"Event {i}",
            )

        res = client.get("/api/events?offset=3&limit=2")
        data = res.json()
        assert data["total"] == 10
        assert data["offset"] == 3
        assert data["limit"] == 2
        assert len(data["items"]) == 2

    def test_limit_max_200(self):
        res = client.get("/api/events?limit=999")
        assert res.status_code == 422  # validation error

    def test_tags_are_parsed_as_list(self):
        _insert_event(product="chatgpt", tags=["new", "pricing"])

        res = client.get("/api/events")
        data = res.json()
        assert isinstance(data["items"][0]["tags"], list)
        assert "new" in data["items"][0]["tags"]


# ---------------------------------------------------------------------------
# GET /api/events/{event_id}
# ---------------------------------------------------------------------------

class TestGetEvent:
    def test_returns_event_detail(self):
        eid = _insert_event(title="Detail test", tags=["new"])

        res = client.get(f"/api/events/{eid}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == eid
        assert data["title"] == "Detail test"
        assert "detected_at" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "raw_ref" in data
        assert isinstance(data["tags"], list)

    def test_not_found(self):
        res = client.get("/api/events/nonexistent-id")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/products
# ---------------------------------------------------------------------------

class TestListProducts:
    def test_returns_all_products(self):
        res = client.get("/api/products")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 4
        ids = {p["id"] for p in data}
        assert ids == {"chatgpt", "gemini", "codex", "claude_code"}

    def test_event_counts(self):
        _insert_event(product="chatgpt", title="ChatGPT event 1")
        _insert_event(product="chatgpt", title="ChatGPT event 2")
        _insert_event(product="gemini", title="Gemini event 1")

        res = client.get("/api/products")
        data = res.json()
        counts = {p["id"]: p["event_count"] for p in data}
        assert counts["chatgpt"] == 2
        assert counts["gemini"] == 1
        assert counts["codex"] == 0
        assert counts["claude_code"] == 0

    def test_product_metadata(self):
        res = client.get("/api/products")
        data = res.json()
        chatgpt = next(p for p in data if p["id"] == "chatgpt")
        assert chatgpt["label"] == "ChatGPT"
        assert chatgpt["color"] == "#10A37F"


# ---------------------------------------------------------------------------
# GET /api/tags
# ---------------------------------------------------------------------------

class TestListTags:
    def test_returns_all_tag_labels(self):
        res = client.get("/api/tags")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 4
        ids = {t["id"] for t in data}
        assert ids == {"new", "change", "pricing", "fix"}

    def test_tag_counts(self):
        _insert_event(product="chatgpt", tags=["new", "pricing"], title="Event with pricing")
        _insert_event(product="chatgpt", tags=["new"], title="Event new only")
        _insert_event(product="chatgpt", tags=["fix"], title="Event fix only")

        res = client.get("/api/tags")
        data = res.json()
        counts = {t["id"]: t["count"] for t in data}
        assert counts["new"] == 2
        assert counts["pricing"] == 1
        assert counts["fix"] == 1
        assert counts["change"] == 0
