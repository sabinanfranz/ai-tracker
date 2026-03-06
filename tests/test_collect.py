"""Tests for scripts/collect.py -- Collection toolkit.

These tests define the expected interface for the collection module that
fetches source pages, compares content hashes, detects duplicates, and
inserts parsed events into the database.

All network calls are mocked.  Each test uses an isolated temp SQLite DB.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure project root is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Source config expected by collect.py  (mirrors architecture docs)
# ---------------------------------------------------------------------------
KNOWN_SOURCES = {
    "chatgpt": "https://help.openai.com/en/articles/6825453-chatgpt-release-notes",
    "gemini": "https://gemini.google/release-notes/",
    "codex": "https://developers.openai.com/codex/changelog/",
    "claude_code": "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md",
}

SAMPLE_HTML = "<html><body><h2>March 2, 2026</h2><p>Something changed.</p></body></html>"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Create a temp SQLite database and patch all relevant paths.

    * Patches ``apps.api.database.DB_PATH`` and ``DB_DIR`` so that
      ``init_db()`` / ``get_connection()`` use the temp directory.
    * Patches ``SNAPSHOTS_DIR`` inside ``scripts.collect`` (if it exists)
      to use a temp subdirectory.
    * Calls ``init_db()`` to create the schema.
    * Yields the tmp_path for assertions that inspect the filesystem.
    * Cleanup is automatic (pytest removes tmp_path after the test).
    """
    db_file = tmp_path / "test_tracker.db"
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()

    # Patch database module-level variables BEFORE importing collect
    import apps.api.database as db_mod
    monkeypatch.setattr(db_mod, "DB_DIR", tmp_path)
    monkeypatch.setattr(db_mod, "DB_PATH", db_file)

    # Initialise schema in the temp DB
    db_mod.init_db()

    # Now import collect -- it may cache module-level values, so we also
    # patch after import.
    import scripts.collect as collect_mod

    if hasattr(collect_mod, "SNAPSHOTS_DIR"):
        monkeypatch.setattr(collect_mod, "SNAPSHOTS_DIR", snapshots_dir)

    yield tmp_path


def _get_conn(tmp_path: Path) -> sqlite3.Connection:
    """Return a raw connection to the temp DB for assertions."""
    from apps.api.database import get_connection
    return get_connection()


def _insert_raw_event(
    *,
    product: str = "chatgpt",
    event_date: str = "2026-02-28",
    title: str = "GPT-4.5 research preview available",
    summary_ko: str = "GPT-4.5 preview released",
    tags: list[str] | None = None,
    severity: int = 4,
    source_url: str = "https://help.openai.com/en/articles/chatgpt-release-notes",
    evidence_excerpt: list[str] | None = None,
) -> str:
    """Insert a test event directly into the DB, return its id."""
    from apps.api.database import PRODUCT_TABLES, get_connection
    table = PRODUCT_TABLES[product]
    eid = str(uuid.uuid4())
    conn = get_connection()
    try:
        if product == "chatgpt":
            conn.execute(
                """
                INSERT INTO chatgpt_event
                    (id, event_date, title, content, source_url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (eid, event_date, title, summary_ko, source_url),
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
            conn.execute(
                f"""
                INSERT INTO {table}
                    (id, component, event_date, detected_at, title,
                     summary_ko, tags, severity, source_url, evidence_excerpt)
                VALUES (?, 'default', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    eid,
                    event_date,
                    f"{event_date}T09:00:00Z",
                    title,
                    summary_ko,
                    json.dumps(tags or []),
                    severity,
                    source_url,
                    json.dumps(evidence_excerpt or []),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return eid


# ---------------------------------------------------------------------------
# Tests: fetch_source
# ---------------------------------------------------------------------------

class TestFetchSource:
    """Tests for ``fetch_source(source_id)``."""

    def test_fetch_source_success(self, tmp_path):
        """A successful HTTP fetch saves a snapshot and returns metadata."""
        import scripts.collect as collect_mod

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_response):
            result = collect_mod.fetch_source("chatgpt")

        # Basic result assertions
        assert result["success"] is True
        assert result["changed"] is True
        # content_hash should be a 64-char hex string (SHA-256)
        assert isinstance(result["content_hash"], str)
        assert len(result["content_hash"]) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", result["content_hash"])

        # The snapshot should be persisted in the DB
        conn = _get_conn(tmp_path)
        try:
            rows = conn.execute(
                "SELECT * FROM source_snapshot WHERE source_id = ?",
                ("chatgpt",),
            ).fetchall()
            assert len(rows) == 1
            assert rows[0]["status"] == "success"
        finally:
            conn.close()

    def test_fetch_source_invalid_id(self):
        """Passing an unknown source_id raises ValueError."""
        import scripts.collect as collect_mod

        with pytest.raises(ValueError):
            collect_mod.fetch_source("invalid_source")

    def test_fetch_source_network_error(self, tmp_path):
        """A network error returns success=False and logs the error."""
        import httpx
        import scripts.collect as collect_mod

        with patch("httpx.get", side_effect=httpx.ConnectError("Connection refused")):
            result = collect_mod.fetch_source("chatgpt")

        assert result["success"] is False
        assert "Connection refused" in result.get("error", "")

        # DB should still record the failed attempt
        conn = _get_conn(tmp_path)
        try:
            rows = conn.execute(
                "SELECT * FROM source_snapshot WHERE source_id = ?",
                ("chatgpt",),
            ).fetchall()
            assert len(rows) == 1
            assert rows[0]["status"] == "fail"
        finally:
            conn.close()

    def test_fetch_source_unchanged(self, tmp_path):
        """Fetching the same content twice marks the second call as unchanged."""
        import scripts.collect as collect_mod

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_response):
            first = collect_mod.fetch_source("chatgpt")
            second = collect_mod.fetch_source("chatgpt")

        assert first["changed"] is True
        assert second["changed"] is False


# ---------------------------------------------------------------------------
# Tests: get_existing_events
# ---------------------------------------------------------------------------

class TestGetExistingEvents:
    """Tests for ``get_existing_events(source_id, limit)``."""

    def test_returns_events(self, tmp_path):
        """Inserted events are returned with expected fields."""
        _insert_raw_event(product="gemini", title="Event A")
        _insert_raw_event(product="gemini", title="Event B")
        _insert_raw_event(product="gemini", title="Event C")

        import scripts.collect as collect_mod
        events = collect_mod.get_existing_events("gemini", limit=10)

        assert len(events) == 3
        # Gemini uses independent schema — tags are always empty list
        for ev in events:
            assert isinstance(ev["tags"], list)
            assert ev["tags"] == []
            assert ev["component"] == "default"


# ---------------------------------------------------------------------------
# Tests: check_duplicate
# ---------------------------------------------------------------------------

class TestCheckDuplicate:
    """Tests for ``check_duplicate(source_id, event_date, title)``."""

    def test_duplicate_found(self, tmp_path):
        """A closely-matching title should be flagged as a duplicate."""
        _insert_raw_event(
            product="chatgpt",
            event_date="2026-02-28",
            title="GPT-4.5 research preview available",
        )
        import scripts.collect as collect_mod

        result = collect_mod.check_duplicate(
            "chatgpt", "2026-02-28", "GPT-4.5 research preview"
        )
        assert result["exists"] is True
        assert result["match_score"] > 0.7

    def test_duplicate_not_found(self, tmp_path):
        """A completely different title should not be considered a duplicate."""
        import scripts.collect as collect_mod

        result = collect_mod.check_duplicate(
            "chatgpt", "2026-03-15", "Completely new feature"
        )
        assert result["exists"] is False
        assert result["match_score"] < 0.7


# ---------------------------------------------------------------------------
# Tests: insert_event
# ---------------------------------------------------------------------------

class TestInsertEvent:
    """Tests for ``insert_event(event_dict)``."""

    def test_insert_event_success(self, tmp_path):
        """A valid event dict is inserted and returns a UUID-formatted id."""
        import scripts.collect as collect_mod

        event_data = {
            "product": "chatgpt",
            "event_date": "2026-03-01",
            "title": "New ChatGPT feature X",
            "content": "ChatGPT feature X description",
            "source_url": "https://help.openai.com/en/articles/chatgpt-release-notes",
        }

        result = collect_mod.insert_event(event_data)
        assert result["success"] is True
        # event_id should be a valid UUID
        parsed_uuid = uuid.UUID(result["event_id"])
        assert str(parsed_uuid) == result["event_id"]

        # Verify the event is in the DB
        conn = _get_conn(tmp_path)
        try:
            row = conn.execute(
                "SELECT * FROM chatgpt_event WHERE id = ?",
                (result["event_id"],),
            ).fetchone()
            assert row is not None
            assert row["title"] == "New ChatGPT feature X"
        finally:
            conn.close()

    def test_insert_event_missing_fields(self):
        """Missing required fields cause a failure result (not an exception)."""
        import scripts.collect as collect_mod

        # chatgpt requires event_date and title
        result = collect_mod.insert_event({"product": "chatgpt"})
        assert result["success"] is False
        assert "error" in result

    def test_insert_gemini_event(self, tmp_path):
        """Gemini events use the independent schema (id, event_date, title, content, source_url)."""
        import scripts.collect as collect_mod

        result = collect_mod.insert_event({
            "product": "gemini",
            "event_date": "2026-03-01",
            "title": "Gemini 3.0 출시",
            "content": "**내용:** Gemini 3.0이 출시되었습니다.",
            "source_url": "https://gemini.google/release-notes/",
        })
        assert result["success"] is True

        conn = _get_conn(tmp_path)
        try:
            row = conn.execute(
                "SELECT title, content FROM gemini_event WHERE id = ?",
                (result["event_id"],),
            ).fetchone()
            assert row["title"] == "Gemini 3.0 출시"
            assert "**내용:**" in row["content"]
        finally:
            conn.close()

    def test_insert_codex_event(self, tmp_path):
        """Codex events use the independent schema (entry_type, version, body)."""
        import scripts.collect as collect_mod

        result = collect_mod.insert_event({
            "product": "codex",
            "event_date": "2026-03-01",
            "title": "Codex CLI 0.107.0",
            "entry_type": "codex-cli",
            "version": "0.107.0",
            "body": "[New Features]\n- Added multi-file editing",
            "source_url": "https://developers.openai.com/codex/changelog/",
        })
        assert result["success"] is True

        conn = _get_conn(tmp_path)
        try:
            row = conn.execute(
                "SELECT entry_type, version, body FROM codex_event WHERE id = ?",
                (result["event_id"],),
            ).fetchone()
            assert row["entry_type"] == "codex-cli"
            assert row["version"] == "0.107.0"
            assert "[New Features]" in row["body"]
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Tests: insert_events (batch)
# ---------------------------------------------------------------------------

class TestInsertEventsBatch:
    """Tests for ``insert_events(event_list)``."""

    def test_insert_events_batch(self, tmp_path):
        """Batch insertion of multiple events returns correct counts."""
        import scripts.collect as collect_mod

        events = [
            {
                "product": "chatgpt",
                "event_date": "2026-03-01",
                "title": f"Event {i}",
                "content": f"Content {i}",
                "source_url": "https://example.com",
            }
            for i in range(3)
        ]

        result = collect_mod.insert_events(events)
        assert result["total"] == 3
        assert result["inserted"] == 3
        assert result["skipped"] == 0

        # Verify all 3 are in the DB
        conn = _get_conn(tmp_path)
        try:
            count = conn.execute(
                "SELECT COUNT(*) as cnt FROM chatgpt_event"
            ).fetchone()["cnt"]
            assert count == 3
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Tests: get_snapshot_status
# ---------------------------------------------------------------------------

class TestGetSnapshotStatus:
    """Tests for ``get_snapshot_status()``."""

    def test_empty_db(self, tmp_path):
        """With no snapshots, every source should report status='never'."""
        import scripts.collect as collect_mod

        statuses = collect_mod.get_snapshot_status()
        assert len(statuses) == 4  # chatgpt, gemini, codex, claude_code
        for entry in statuses:
            assert entry["status"] == "never"

    def test_after_fetch(self, tmp_path):
        """After a successful fetch, the source status should be 'success'."""
        import scripts.collect as collect_mod

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_response):
            collect_mod.fetch_source("chatgpt")

        statuses = collect_mod.get_snapshot_status()
        chatgpt_status = [s for s in statuses if s["source_id"] == "chatgpt"]
        assert len(chatgpt_status) == 1
        assert chatgpt_status[0]["status"] == "success"
        assert chatgpt_status[0]["age_hours"] >= 0
