"""SQLite database connection and table initialization.

Uses raw sqlite3 for MVP simplicity. DB path: data/tracker.db
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# DB path — relative to project root
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_DIR = PROJECT_ROOT / "data"
DB_PATH = DB_DIR / "tracker.db"

# ---------------------------------------------------------------------------
# Product table mapping
# ---------------------------------------------------------------------------

PRODUCT_TABLES = {
    "chatgpt": "chatgpt_event",
    "codex": "codex_event",
    "gemini": "gemini_event",
    "claude_code": "claude_code_event",
}


def _ensure_data_dir() -> None:
    """Create the data/ directory if it does not exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory.

    Uses DELETE journal mode (default) instead of WAL to avoid data loss
    when processes are force-killed on Windows.
    """
    _ensure_data_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ---------------------------------------------------------------------------
# Common column definitions (shared across all product tables)
# ---------------------------------------------------------------------------

_COMMON_COLS = """
    id              TEXT PRIMARY KEY,
    component       TEXT NOT NULL DEFAULT 'default',
    event_date      TEXT NOT NULL,
    detected_at     TEXT NOT NULL,
    title           TEXT NOT NULL,
    title_ko        TEXT,
    summary_ko      TEXT NOT NULL,
    summary_en      TEXT,
    tags            TEXT NOT NULL DEFAULT '[]',
    severity        INTEGER NOT NULL DEFAULT 1,
    source_url      TEXT NOT NULL,
    evidence_excerpt TEXT NOT NULL DEFAULT '[]',
    raw_ref         TEXT NOT NULL DEFAULT '{}',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
"""

# ---------------------------------------------------------------------------
# Schema DDL — per-product tables + UNION ALL view
# ---------------------------------------------------------------------------

_SCHEMA_SQL = f"""
-- ChatGPT events (enriched schema — raw h1/h2 data + metadata)
CREATE TABLE IF NOT EXISTS chatgpt_event (
    id              TEXT PRIMARY KEY,
    event_date      TEXT NOT NULL,
    title           TEXT NOT NULL,
    content         TEXT NOT NULL DEFAULT '',
    source_url      TEXT NOT NULL,
    summary_ko      TEXT,
    summary_en      TEXT,
    title_ko        TEXT,
    tags            TEXT NOT NULL DEFAULT '[]',
    severity        INTEGER NOT NULL DEFAULT 1,
    evidence_excerpt TEXT NOT NULL DEFAULT '[]',
    title_updated   TEXT,
    content_updated TEXT,
    title_updated_ko TEXT,
    content_updated_ko TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(event_date, title)
);
CREATE INDEX IF NOT EXISTS idx_chatgpt_event_date ON chatgpt_event(event_date DESC);

-- Codex events (independent schema — changelog entries)
CREATE TABLE IF NOT EXISTS codex_event (
    id              TEXT PRIMARY KEY,
    event_date      TEXT NOT NULL,
    title           TEXT NOT NULL,
    entry_type      TEXT NOT NULL,
    version         TEXT,
    body            TEXT NOT NULL DEFAULT '',
    title_updated   TEXT,
    content_updated TEXT,
    title_updated_ko   TEXT,
    content_updated_ko TEXT,
    source_url      TEXT NOT NULL DEFAULT 'https://developers.openai.com/codex/changelog/',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_codex_unique ON codex_event(event_date, title);
CREATE INDEX IF NOT EXISTS idx_codex_event_date ON codex_event(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_codex_entry_type ON codex_event(entry_type);

-- Gemini events (independent schema — per-feature entries)
CREATE TABLE IF NOT EXISTS gemini_event (
    id            TEXT PRIMARY KEY,
    event_date    TEXT NOT NULL,
    title         TEXT NOT NULL,
    content       TEXT NOT NULL DEFAULT '',
    title_ko      TEXT,
    content_ko    TEXT,
    source_url    TEXT NOT NULL DEFAULT 'https://gemini.google/release-notes/',
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(event_date, title)
);
CREATE INDEX IF NOT EXISTS idx_gemini_event_date ON gemini_event(event_date DESC);

-- Claude Code events (independent schema — bullet-level changelog entries)
CREATE TABLE IF NOT EXISTS claude_code_event (
    id            TEXT PRIMARY KEY,
    event_date    TEXT NOT NULL,
    title         TEXT NOT NULL,
    version       TEXT NOT NULL,
    change_type   TEXT NOT NULL,
    subsystem     TEXT,
    card_yn       INTEGER NOT NULL DEFAULT 0,
    title_kor     TEXT,
    content_kor   TEXT,
    source_url    TEXT NOT NULL DEFAULT 'https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md',
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_claude_code_unique ON claude_code_event(event_date, title);
CREATE INDEX IF NOT EXISTS idx_claude_code_event_date ON claude_code_event(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_claude_code_change_type ON claude_code_event(change_type);
CREATE INDEX IF NOT EXISTS idx_claude_code_version ON claude_code_event(version);

-- source_snapshot (unchanged)
CREATE TABLE IF NOT EXISTS source_snapshot (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       TEXT NOT NULL,
    fetched_at      TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    raw_content     TEXT,
    status          TEXT NOT NULL DEFAULT 'success',
    error_message   TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_snapshot_source ON source_snapshot(source_id, fetched_at DESC);
"""


def init_db() -> None:
    """Create tables and indexes if they do not exist."""
    conn = get_connection()
    try:
        # Migrate chatgpt_event: drop old common-schema table if it
        # has the platform column (old schema).
        try:
            cols = {
                r[1]
                for r in conn.execute(
                    "PRAGMA table_info(chatgpt_event)"
                ).fetchall()
            }
            if cols and "content" not in cols:
                conn.execute("DROP TABLE IF EXISTS chatgpt_event")
                conn.commit()
        except Exception:
            pass

        # Migrate chatgpt_event: add enrichment columns if missing
        try:
            cols = {
                r[1]
                for r in conn.execute(
                    "PRAGMA table_info(chatgpt_event)"
                ).fetchall()
            }
            if cols and "tags" not in cols:
                for col_sql in [
                    "ALTER TABLE chatgpt_event ADD COLUMN summary_ko TEXT",
                    "ALTER TABLE chatgpt_event ADD COLUMN summary_en TEXT",
                    "ALTER TABLE chatgpt_event ADD COLUMN title_ko TEXT",
                    "ALTER TABLE chatgpt_event ADD COLUMN tags TEXT NOT NULL DEFAULT '[]'",
                    "ALTER TABLE chatgpt_event ADD COLUMN severity INTEGER NOT NULL DEFAULT 1",
                    "ALTER TABLE chatgpt_event ADD COLUMN evidence_excerpt TEXT NOT NULL DEFAULT '[]'",
                    "ALTER TABLE chatgpt_event ADD COLUMN updated_at TEXT NOT NULL DEFAULT (datetime('now'))",
                ]:
                    try:
                        conn.execute(col_sql)
                    except Exception:
                        pass  # column already exists
                conn.commit()
        except Exception:
            pass

        # Migrate chatgpt_event: add updated_at if missing (may have been
        # skipped when tags already existed before this column was added)
        try:
            cols = {
                r[1]
                for r in conn.execute(
                    "PRAGMA table_info(chatgpt_event)"
                ).fetchall()
            }
            if cols and "updated_at" not in cols:
                try:
                    # SQLite ALTER TABLE ADD COLUMN cannot use expression
                    # defaults like (datetime('now')), so add as nullable.
                    # The VIEW uses COALESCE(updated_at, created_at).
                    conn.execute(
                        "ALTER TABLE chatgpt_event ADD COLUMN updated_at TEXT"
                    )
                except Exception:
                    pass
                conn.commit()
        except Exception:
            pass

        # Migrate chatgpt_event: add title_updated/content_updated if missing
        try:
            cols = {
                r[1]
                for r in conn.execute(
                    "PRAGMA table_info(chatgpt_event)"
                ).fetchall()
            }
            if cols and "title_updated" not in cols:
                for col_sql in [
                    "ALTER TABLE chatgpt_event ADD COLUMN title_updated TEXT",
                    "ALTER TABLE chatgpt_event ADD COLUMN content_updated TEXT",
                ]:
                    try:
                        conn.execute(col_sql)
                    except Exception:
                        pass
                conn.commit()
        except Exception:
            pass

        # Migrate chatgpt_event: add title_updated_ko/content_updated_ko if missing
        try:
            cols = {
                r[1]
                for r in conn.execute(
                    "PRAGMA table_info(chatgpt_event)"
                ).fetchall()
            }
            if cols and "title_updated_ko" not in cols:
                for col_sql in [
                    "ALTER TABLE chatgpt_event ADD COLUMN title_updated_ko TEXT",
                    "ALTER TABLE chatgpt_event ADD COLUMN content_updated_ko TEXT",
                ]:
                    try:
                        conn.execute(col_sql)
                    except Exception:
                        pass
                conn.commit()
        except Exception:
            pass

        # Migrate gemini_event: drop old common-schema table if it
        # lacks the content column (independent schema requires it).
        try:
            cols = {
                r[1]
                for r in conn.execute(
                    "PRAGMA table_info(gemini_event)"
                ).fetchall()
            }
            if cols and "content" not in cols:
                conn.execute("DROP TABLE IF EXISTS gemini_event")
                conn.commit()
        except Exception:
            pass

        # Migrate gemini_event: add title_ko/content_ko columns if missing
        try:
            cols = {
                r[1]
                for r in conn.execute(
                    "PRAGMA table_info(gemini_event)"
                ).fetchall()
            }
            if cols and "title_ko" not in cols:
                for col_sql in [
                    "ALTER TABLE gemini_event ADD COLUMN title_ko TEXT",
                    "ALTER TABLE gemini_event ADD COLUMN content_ko TEXT",
                ]:
                    try:
                        conn.execute(col_sql)
                    except Exception:
                        pass
                conn.commit()
        except Exception:
            pass

        # Migrate claude_code_event: drop old common-schema table if it
        # lacks the change_type column (independent schema requires it).
        try:
            cols = {
                r[1]
                for r in conn.execute(
                    "PRAGMA table_info(claude_code_event)"
                ).fetchall()
            }
            if cols and "change_type" not in cols:
                conn.execute("DROP TABLE IF EXISTS claude_code_event")
                conn.commit()
        except Exception:
            pass

        # Migrate claude_code_event: add title_kor/content_kor if missing
        try:
            cols = {
                r[1]
                for r in conn.execute(
                    "PRAGMA table_info(claude_code_event)"
                ).fetchall()
            }
            for col, sql in [
                ("title_kor", "ALTER TABLE claude_code_event ADD COLUMN title_kor TEXT"),
                ("content_kor", "ALTER TABLE claude_code_event ADD COLUMN content_kor TEXT"),
            ]:
                if cols and col not in cols:
                    try:
                        conn.execute(sql)
                    except Exception:
                        pass
            conn.commit()
        except Exception:
            pass

        conn.executescript(_SCHEMA_SQL)

        # Clean up legacy objects (already migrated to per-product tables)
        conn.execute("DROP VIEW IF EXISTS all_events")
        conn.execute("DROP TABLE IF EXISTS update_event")
        conn.execute("DROP TABLE IF EXISTS update_event_backup")
        conn.commit()
    finally:
        conn.close()
