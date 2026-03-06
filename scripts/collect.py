"""Data collection toolkit for AI Update Tracker.

Provides helper functions for daily data collection:
  - Fetch source pages and save snapshots
  - Check for duplicate events
  - Insert new events into the database

Usage:
    python -m scripts.collect             # fetch all sources
    python -m scripts.collect --status    # show snapshot status only
"""

from __future__ import annotations

import difflib
import hashlib
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path so we can import apps.api
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.database import PRODUCT_TABLES, get_connection, init_db
from apps.api.services.scorer import calculate_severity
from scripts.parsers.chatgpt import parse_chatgpt
from scripts.parsers.codex import parse_codex
from scripts.parsers.gemini import parse_gemini
from scripts.parsers.claude_code import parse_claude_code

# ---------------------------------------------------------------------------
# Parser mapping (source_id → parser function)
# ---------------------------------------------------------------------------

PARSERS: dict[str, callable] = {
    "chatgpt": parse_chatgpt,
    "codex": parse_codex,
    "gemini": parse_gemini,
    "claude_code": parse_claude_code,
}

# ---------------------------------------------------------------------------
# Source configuration
# ---------------------------------------------------------------------------

SOURCES: dict[str, dict] = {
    "chatgpt": {
        "url": "https://help.openai.com/en/articles/6825453-chatgpt-release-notes",
        "format": "html",
        "filename": "chatgpt_latest.html",
    },
    "gemini": {
        "url": "https://gemini.google/release-notes/",
        "format": "html",
        "filename": "gemini_latest.html",
    },
    "codex": {
        "url": "https://developers.openai.com/codex/changelog/",
        "format": "html",
        "filename": "codex_latest.html",
    },
    "claude_code": {
        "url": "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md",
        "format": "markdown",
        "filename": "claude_code_latest.md",
    },
}

SNAPSHOTS_DIR = PROJECT_ROOT / "data" / "snapshots"

# 1 MB threshold for storing raw content in DB
_MAX_RAW_CONTENT_BYTES = 1_048_576


# ---------------------------------------------------------------------------
# 1a. Playwright-based fetcher (for Cloudflare-protected sites)
# ---------------------------------------------------------------------------

def _fetch_with_playwright(url: str, timeout_ms: int = 60_000) -> str:
    """Fetch page content using a headless Chromium browser via Playwright.

    This bypasses Cloudflare and other anti-bot protections by running a
    real browser. Requires: pip install playwright && playwright install chromium
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = context.new_page()
        # Use 'domcontentloaded' — faster than 'networkidle' and sufficient
        # for server-rendered HTML content
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        # Extra wait for JS-rendered content to settle
        page.wait_for_timeout(3000)
        content = page.content()
        browser.close()
    return content


# ---------------------------------------------------------------------------
# 1. fetch_source
# ---------------------------------------------------------------------------

def fetch_source(source_id: str) -> dict:
    """Fetch a single source page, save snapshot, record in DB.

    Uses httpx first; on 403/Cloudflare block, falls back to Playwright
    (headless Chromium) automatically.

    Returns a dict with keys: source_id, success, fetched_at, content_hash,
    changed, prev_hash, cached_file, error, content_length.
    """
    if source_id not in SOURCES:
        raise ValueError(f"Unknown source_id: {source_id!r}. Valid: {list(SOURCES)}")

    import httpx

    src = SOURCES[source_id]
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Ensure snapshots directory exists
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    cached_file = str(SNAPSHOTS_DIR / src["filename"])

    # Use browser-like headers for sources that block simple User-Agents
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    content_text = None
    fetch_error = None

    # Attempt 1: httpx (fast, lightweight)
    try:
        resp = httpx.get(
            src["url"],
            timeout=30,
            headers=headers,
            follow_redirects=True,
        )
        resp.raise_for_status()
        content_text = resp.text
    except Exception as e:
        fetch_error = e

    # Attempt 2: Playwright fallback on 403 or other HTTP errors
    if content_text is None:
        try:
            print(f"  [INFO] httpx failed for {source_id} ({fetch_error}), trying Playwright...")
            content_text = _fetch_with_playwright(src["url"])
            fetch_error = None  # success via Playwright
        except Exception as pw_err:
            # Both methods failed — record the combined error
            combined_error = f"httpx: {fetch_error}; playwright: {pw_err}"
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO source_snapshot "
                    "(source_id, fetched_at, content_hash, raw_content, status, error_message) "
                    "VALUES (?, ?, ?, ?, 'fail', ?)",
                    (source_id, fetched_at, "", None, combined_error),
                )
                conn.commit()
            finally:
                conn.close()

            return {
                "source_id": source_id,
                "success": False,
                "fetched_at": fetched_at,
                "content_hash": None,
                "changed": None,
                "prev_hash": None,
                "cached_file": None,
                "error": combined_error,
                "content_length": 0,
            }

    # Success path — content_text is set by either httpx or Playwright
    content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
    content_length = len(content_text.encode("utf-8"))

    # Save to disk
    Path(cached_file).write_text(content_text, encoding="utf-8")

    # Determine raw_content for DB storage
    raw_content = content_text if content_length <= _MAX_RAW_CONTENT_BYTES else None
    error_message = None
    if content_length > _MAX_RAW_CONTENT_BYTES:
        error_message = f"Content too large ({content_length} bytes), raw_content not stored"

    # Check previous snapshot hash
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT content_hash FROM source_snapshot "
            "WHERE source_id=? ORDER BY fetched_at DESC LIMIT 1",
            (source_id,),
        ).fetchone()
        prev_hash = row["content_hash"] if row else None
        changed = (prev_hash != content_hash) if prev_hash else True

        conn.execute(
            "INSERT INTO source_snapshot "
            "(source_id, fetched_at, content_hash, raw_content, status, error_message) "
            "VALUES (?, ?, ?, ?, 'success', ?)",
            (source_id, fetched_at, content_hash, raw_content, error_message),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "source_id": source_id,
        "success": True,
        "fetched_at": fetched_at,
        "content_hash": content_hash,
        "changed": changed,
        "prev_hash": prev_hash,
        "cached_file": cached_file,
        "error": None,
        "content_length": content_length,
    }


# ---------------------------------------------------------------------------
# 2. fetch_all_sources
# ---------------------------------------------------------------------------

def fetch_all_sources() -> dict:
    """Fetch all configured sources with a 1-second delay between requests."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results: list[dict] = []
    source_ids = list(SOURCES.keys())

    for i, sid in enumerate(source_ids):
        result = fetch_source(sid)
        results.append(result)
        # Politeness delay between requests (not after the last one)
        if i < len(source_ids) - 1:
            time.sleep(1.0)

    success_count = sum(1 for r in results if r["success"])
    failed_count = sum(1 for r in results if not r["success"])
    changed_count = sum(1 for r in results if r["success"] and r["changed"])
    unchanged_count = sum(1 for r in results if r["success"] and not r["changed"])

    return {
        "timestamp": timestamp,
        "results": results,
        "summary": {
            "total": len(results),
            "success": success_count,
            "failed": failed_count,
            "changed": changed_count,
            "unchanged": unchanged_count,
        },
    }


# ---------------------------------------------------------------------------
# 3. get_snapshot_status
# ---------------------------------------------------------------------------

def get_snapshot_status() -> list[dict]:
    """Return the status of the most recent snapshot for each source."""
    conn = get_connection()
    statuses: list[dict] = []
    try:
        for source_id in SOURCES:
            row = conn.execute(
                "SELECT fetched_at, content_hash, status, error_message "
                "FROM source_snapshot WHERE source_id=? ORDER BY fetched_at DESC LIMIT 1",
                (source_id,),
            ).fetchone()

            if not row:
                statuses.append({
                    "source_id": source_id,
                    "last_fetched_at": None,
                    "status": "never",
                    "content_hash": None,
                    "error_message": None,
                    "age_hours": None,
                })
            else:
                fetched_dt = datetime.fromisoformat(
                    row["fetched_at"].replace("Z", "+00:00")
                )
                now_utc = datetime.now(timezone.utc)
                age_hours = (now_utc - fetched_dt).total_seconds() / 3600.0

                statuses.append({
                    "source_id": source_id,
                    "last_fetched_at": row["fetched_at"],
                    "status": row["status"],
                    "content_hash": row["content_hash"],
                    "error_message": row["error_message"],
                    "age_hours": age_hours,
                })
    finally:
        conn.close()

    return statuses


# ---------------------------------------------------------------------------
# 4. get_existing_events
# ---------------------------------------------------------------------------

def get_existing_events(product: str, limit: int = 30) -> list[dict]:
    """Return recent events for a given product."""
    table = PRODUCT_TABLES.get(product)
    conn = get_connection()
    try:
        # ChatGPT has a simple schema
        if product == "chatgpt":
            rows = conn.execute(
                "SELECT id, event_date, title, source_url "
                "FROM chatgpt_event ORDER BY event_date DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "event_date": row["event_date"],
                    "title": row["title"],
                    "component": "default",
                    "tags": [],
                    "severity": 0,
                    "source_url": row["source_url"],
                }
                for row in rows
            ]

        # Codex has an independent schema
        if product == "codex":
            rows = conn.execute(
                "SELECT id, event_date, title, entry_type, version, source_url "
                "FROM codex_event ORDER BY event_date DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "event_date": row["event_date"],
                    "title": row["title"],
                    "component": row["entry_type"],
                    "tags": [],
                    "severity": 0,
                    "source_url": row["source_url"],
                }
                for row in rows
            ]

        # Gemini has an independent schema
        if product == "gemini":
            rows = conn.execute(
                "SELECT id, event_date, title, source_url "
                "FROM gemini_event ORDER BY event_date DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "event_date": row["event_date"],
                    "title": row["title"],
                    "component": "default",
                    "tags": [],
                    "severity": 0,
                    "source_url": row["source_url"],
                }
                for row in rows
            ]

        # Claude Code has an independent schema
        if product == "claude_code":
            rows = conn.execute(
                "SELECT id, event_date, title, change_type, version, source_url "
                "FROM claude_code_event ORDER BY event_date DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "event_date": row["event_date"],
                    "title": row["title"],
                    "component": row["change_type"],
                    "tags": [],
                    "severity": 0,
                    "source_url": row["source_url"],
                }
                for row in rows
            ]

        if not table:
            return []

        return []
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 5. check_duplicate
# ---------------------------------------------------------------------------

def check_duplicate(product: str, event_date: str, title: str) -> dict:
    """Check if a similar event already exists for a given product and date.

    Uses SequenceMatcher with a threshold of 0.7 to detect duplicates.
    """
    table = PRODUCT_TABLES.get(product)
    if not table:
        return {"exists": False, "similar_event": None, "match_score": 0.0}
    conn = get_connection()
    try:
        rows = conn.execute(
            f"SELECT id, title FROM {table} "
            f"WHERE event_date=? LIMIT 10",
            (event_date,),
        ).fetchall()

        best_ratio = 0.0
        best_match = None

        for row in rows:
            ratio = difflib.SequenceMatcher(
                None, title.lower(), row["title"].lower()
            ).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = {"id": row["id"], "title": row["title"]}

        if best_ratio > 0.7 and best_match is not None:
            return {
                "exists": True,
                "similar_event": best_match,
                "match_score": round(best_ratio, 4),
            }

        return {
            "exists": False,
            "similar_event": None,
            "match_score": 0.0,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 6. insert_event
# ---------------------------------------------------------------------------

def _extra_cols_vals(product: str, event_dict: dict) -> tuple[str, str, list]:
    """Return (extra_col_names, extra_placeholders, extra_values) for product."""
    return "", "", []


def _insert_chatgpt_event(conn, event_dict: dict) -> dict:
    """Insert a single chatgpt event into chatgpt_event (simple schema)."""
    event_id = str(uuid.uuid4())

    try:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO chatgpt_event
                (id, event_date, title, content, source_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_dict["event_date"],
                event_dict["title"],
                event_dict.get("content", ""),
                event_dict.get("source_url",
                               "https://help.openai.com/en/articles/6825453-chatgpt-release-notes"),
            ),
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "event_id": event_id,
                "product": "chatgpt",
                "title": event_dict["title"],
                "error": "Duplicate key, insert ignored",
            }

        return {
            "success": True,
            "event_id": event_id,
            "product": "chatgpt",
            "event_date": event_dict["event_date"],
            "title": event_dict["title"],
            "severity": 0,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _insert_codex_event(conn, event_dict: dict) -> dict:
    """Insert a single codex event into codex_event (independent schema)."""
    event_id = str(uuid.uuid4())

    try:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO codex_event
                (id, event_date, title, entry_type, version, body, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_dict["event_date"],
                event_dict["title"],
                event_dict.get("entry_type", "general"),
                event_dict.get("version"),
                event_dict.get("body", ""),
                event_dict.get("source_url",
                               "https://developers.openai.com/codex/changelog/"),
            ),
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "event_id": event_id,
                "product": "codex",
                "title": event_dict["title"],
                "error": "Duplicate key, insert ignored",
            }

        return {
            "success": True,
            "event_id": event_id,
            "product": "codex",
            "event_date": event_dict["event_date"],
            "title": event_dict["title"],
            "severity": 0,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _insert_gemini_event(conn, event_dict: dict) -> dict:
    """Insert a single gemini event into gemini_event (independent schema)."""
    event_id = str(uuid.uuid4())

    try:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO gemini_event
                (id, event_date, title, content, source_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_dict["event_date"],
                event_dict["title"],
                event_dict.get("content", ""),
                event_dict.get("source_url",
                               "https://gemini.google/release-notes/"),
            ),
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "event_id": event_id,
                "product": "gemini",
                "title": event_dict["title"],
                "error": "Duplicate key, insert ignored",
            }

        return {
            "success": True,
            "event_id": event_id,
            "product": "gemini",
            "event_date": event_dict["event_date"],
            "title": event_dict["title"],
            "severity": 0,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _insert_claude_code_event(conn, event_dict: dict) -> dict:
    """Insert a single claude_code event into claude_code_event (independent schema)."""
    event_id = str(uuid.uuid4())

    try:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO claude_code_event
                (id, event_date, title, version, change_type, subsystem, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_dict["event_date"],
                event_dict["title"],
                event_dict.get("version", ""),
                event_dict.get("change_type", "other"),
                event_dict.get("subsystem"),
                event_dict.get("source_url",
                               "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md"),
            ),
        )

        if cursor.rowcount == 0:
            return {
                "success": False,
                "event_id": event_id,
                "product": "claude_code",
                "title": event_dict["title"],
                "error": "Duplicate key, insert ignored",
            }

        return {
            "success": True,
            "event_id": event_id,
            "product": "claude_code",
            "event_date": event_dict["event_date"],
            "title": event_dict["title"],
            "severity": 0,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def insert_event(event_dict: dict) -> dict:
    """Insert a single event into the database.

    For codex/claude_code: required fields are product, event_date, title.
    For others: required fields are product, event_date, title, summary_ko, source_url, tags.
    """
    product = event_dict.get("product")
    if not product:
        return {"success": False, "error": "Missing required field: product"}

    # ChatGPT uses a simple schema (id, event_date, title, content, source_url)
    if product == "chatgpt":
        for field in ["event_date", "title"]:
            if field not in event_dict:
                return {"success": False, "error": f"Missing required field: {field}"}
        conn = get_connection()
        try:
            result = _insert_chatgpt_event(conn, event_dict)
            conn.commit()
            return result
        finally:
            conn.close()

    # Codex uses an independent schema
    if product == "codex":
        for field in ["event_date", "title"]:
            if field not in event_dict:
                return {"success": False, "error": f"Missing required field: {field}"}
        conn = get_connection()
        try:
            result = _insert_codex_event(conn, event_dict)
            conn.commit()
            return result
        finally:
            conn.close()

    # Gemini uses an independent schema
    if product == "gemini":
        for field in ["event_date", "title"]:
            if field not in event_dict:
                return {"success": False, "error": f"Missing required field: {field}"}
        conn = get_connection()
        try:
            result = _insert_gemini_event(conn, event_dict)
            conn.commit()
            return result
        finally:
            conn.close()

    # Claude Code uses an independent schema
    if product == "claude_code":
        for field in ["event_date", "title"]:
            if field not in event_dict:
                return {"success": False, "error": f"Missing required field: {field}"}
        conn = get_connection()
        try:
            result = _insert_claude_code_event(conn, event_dict)
            conn.commit()
            return result
        finally:
            conn.close()

    required_fields = ["event_date", "title", "summary_ko", "source_url", "tags"]
    for field in required_fields:
        if field not in event_dict:
            return {"success": False, "error": f"Missing required field: {field}"}

    table = PRODUCT_TABLES.get(product)
    if not table:
        return {"success": False, "error": f"Unknown product: {product}"}

    event_id = str(uuid.uuid4())
    detected_at = datetime.now(timezone.utc).isoformat()
    severity = calculate_severity(event_dict["title"], event_dict["summary_ko"])
    component = event_dict.get("component", "default")

    tags_json = json.dumps(event_dict["tags"])
    evidence_json = json.dumps(event_dict.get("evidence_excerpt", []))
    raw_ref_json = json.dumps(event_dict.get("raw_ref", {}))

    extra_cols, extra_ph, extra_vals = _extra_cols_vals(product, event_dict)

    conn = get_connection()
    try:
        cursor = conn.execute(
            f"""
            INSERT OR IGNORE INTO {table}
                (id, component, event_date, detected_at, title,
                 summary_ko, summary_en, tags, severity, source_url,
                 evidence_excerpt, raw_ref{extra_cols})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?{extra_ph})
            """,
            (
                event_id,
                component,
                event_dict["event_date"],
                detected_at,
                event_dict["title"],
                event_dict["summary_ko"],
                event_dict.get("summary_en"),
                tags_json,
                severity,
                event_dict["source_url"],
                evidence_json,
                raw_ref_json,
                *extra_vals,
            ),
        )
        conn.commit()

        if cursor.rowcount == 0:
            return {
                "success": False,
                "event_id": event_id,
                "product": product,
                "event_date": event_dict["event_date"],
                "title": event_dict["title"],
                "severity": severity,
                "error": "Duplicate key, insert ignored",
            }

        return {
            "success": True,
            "event_id": event_id,
            "product": product,
            "event_date": event_dict["event_date"],
            "title": event_dict["title"],
            "severity": severity,
            "error": None,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 7. insert_events
# ---------------------------------------------------------------------------

def insert_events(events_list: list[dict]) -> dict:
    """Insert multiple events in a single transaction.

    Returns a summary with total, inserted, skipped, failed counts.
    """
    common_required = ["product", "event_date", "title", "summary_ko", "source_url", "tags"]
    codex_required = ["product", "event_date", "title"]
    results: list[dict] = []
    inserted = 0
    skipped = 0
    failed = 0

    conn = get_connection()
    try:
        for event_dict in events_list:
            product = event_dict.get("product")
            if not product:
                results.append({"success": False, "error": "Missing required field: product"})
                failed += 1
                continue

            # --- ChatGPT: simple schema ---
            if product == "chatgpt":
                chatgpt_required = ["product", "event_date", "title"]
                missing = [f for f in chatgpt_required if f not in event_dict]
                if missing:
                    results.append({"success": False, "error": f"Missing required field: {missing[0]}"})
                    failed += 1
                    continue

                result = _insert_chatgpt_event(conn, event_dict)
                if result.get("success"):
                    inserted += 1
                elif "Duplicate" in result.get("error", ""):
                    skipped += 1
                else:
                    failed += 1
                results.append(result)
                continue

            # --- Codex: independent schema ---
            if product == "codex":
                missing = [f for f in codex_required if f not in event_dict]
                if missing:
                    results.append({"success": False, "error": f"Missing required field: {missing[0]}"})
                    failed += 1
                    continue

                result = _insert_codex_event(conn, event_dict)
                if result.get("success"):
                    inserted += 1
                elif "Duplicate" in result.get("error", ""):
                    skipped += 1
                else:
                    failed += 1
                results.append(result)
                continue

            # --- Gemini: independent schema ---
            if product == "gemini":
                gemini_required = ["product", "event_date", "title"]
                missing = [f for f in gemini_required if f not in event_dict]
                if missing:
                    results.append({"success": False, "error": f"Missing required field: {missing[0]}"})
                    failed += 1
                    continue

                result = _insert_gemini_event(conn, event_dict)
                if result.get("success"):
                    inserted += 1
                elif "Duplicate" in result.get("error", ""):
                    skipped += 1
                else:
                    failed += 1
                results.append(result)
                continue

            # --- Claude Code: independent schema ---
            if product == "claude_code":
                cc_required = ["product", "event_date", "title"]
                missing = [f for f in cc_required if f not in event_dict]
                if missing:
                    results.append({"success": False, "error": f"Missing required field: {missing[0]}"})
                    failed += 1
                    continue

                result = _insert_claude_code_event(conn, event_dict)
                if result.get("success"):
                    inserted += 1
                elif "Duplicate" in result.get("error", ""):
                    skipped += 1
                else:
                    failed += 1
                results.append(result)
                continue

            # Unknown product
            results.append({"success": False, "error": f"Unknown product: {product}"})
            failed += 1

        conn.commit()
    finally:
        conn.close()

    return {
        "total": len(events_list),
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }


# ---------------------------------------------------------------------------
# 8. parse_and_insert_changed — auto-load after fetch
# ---------------------------------------------------------------------------

def parse_and_insert_changed(fetch_results: list[dict]) -> dict:
    """Parse snapshots for changed sources and insert new events.

    Only processes sources where changed=True (or all if force=True).
    Uses INSERT OR IGNORE so existing events are safely skipped.
    """
    summary: dict[str, dict] = {}

    for r in fetch_results:
        sid = r["source_id"]
        if not r.get("success") or not r.get("changed"):
            summary[sid] = {"status": "skipped", "reason": "unchanged or failed"}
            continue

        parser = PARSERS.get(sid)
        if not parser:
            summary[sid] = {"status": "skipped", "reason": "no parser"}
            continue

        cached_file = r.get("cached_file")
        if not cached_file or not Path(cached_file).exists():
            summary[sid] = {"status": "skipped", "reason": "snapshot file missing"}
            continue

        content = Path(cached_file).read_text(encoding="utf-8")
        events = parser(content)
        if not events:
            summary[sid] = {"status": "ok", "parsed": 0, "inserted": 0, "skipped": 0}
            continue

        # Add product field for insert_events
        for ev in events:
            if "product" not in ev:
                ev["product"] = sid

        result = insert_events(events)
        summary[sid] = {
            "status": "ok",
            "parsed": len(events),
            "inserted": result["inserted"],
            "skipped": result["skipped"],
        }

    return summary


def _build_all_changed_results() -> list[dict]:
    """Build fake fetch results for --parse-only (all existing snapshots)."""
    results = []
    for sid, src in SOURCES.items():
        cached = SNAPSHOTS_DIR / src["filename"]
        results.append({
            "source_id": sid,
            "success": cached.exists(),
            "changed": cached.exists(),
            "cached_file": str(cached) if cached.exists() else None,
        })
    return results


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _print_report(result: dict) -> None:
    """Print a human-readable collection report (ASCII-safe)."""
    print(f"\nAI Update Tracker - Collection Report")
    print(f"Time: {result['timestamp']}")
    print()
    for r in result["results"]:
        if not r["success"]:
            status_mark = "[FAIL]"
            detail = f"Error: {r['error']}"
        elif r["changed"]:
            status_mark = "[CHANGED]"
            prev_short = r["prev_hash"][:12] + "..." if r["prev_hash"] else "N/A"
            detail = f"Hash: {prev_short} -> {r['content_hash'][:12]}..."
        else:
            status_mark = "[unchanged]"
            detail = f"Hash: {r['content_hash'][:12]}..."

        print(f"  {status_mark:12} {r['source_id']:15} {detail}")

    s = result["summary"]
    print(
        f"\nSummary: {s['success']} fetched, {s['changed']} changed, "
        f"{s['unchanged']} unchanged, {s['failed']} failed"
    )


def _print_status(statuses: list[dict]) -> None:
    """Print snapshot status for each source (ASCII-safe)."""
    print("\nAI Update Tracker - Snapshot Status")
    print()
    for s in statuses:
        age = f"{s['age_hours']:.1f}h ago" if s.get("age_hours") is not None else "never"
        last = s.get("last_fetched_at", "N/A") or "N/A"
        print(f"  {s['source_id']:15} status={s['status']:8} last={last} ({age})")


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]

    init_db()

    if "--status" in args:
        status = get_snapshot_status()
        _print_status(status)
    elif "--parse-only" in args:
        # Parse existing snapshots without fetching
        fake_results = _build_all_changed_results()
        load_summary = parse_and_insert_changed(fake_results)
        print("\nAI Update Tracker - Parse-Only Results")
        for sid, info in load_summary.items():
            if info.get("status") == "skipped":
                print(f"  [skip] {sid:15} {info.get('reason', '')}")
            else:
                print(f"  [ok]   {sid:15} parsed={info['parsed']} inserted={info['inserted']} skipped={info['skipped']}")
    else:
        result = fetch_all_sources()
        _print_report(result)

        # Auto-parse and insert new events from changed sources
        load_summary = parse_and_insert_changed(result["results"])
        print("\nAuto-load results:")
        for sid, info in load_summary.items():
            if info.get("status") == "skipped":
                print(f"  [skip] {sid:15} {info.get('reason', '')}")
            else:
                print(f"  [ok]   {sid:15} parsed={info['parsed']} inserted={info['inserted']} skipped={info['skipped']}")


if __name__ == "__main__":
    main()
