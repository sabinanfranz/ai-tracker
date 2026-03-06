"""Claude Code CHANGELOG.md parser — bullet-level events with npm date automation."""

from __future__ import annotations

import json
import logging
import re
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CACHE_FILE = PROJECT_ROOT / "data" / "cache" / "npm_versions.json"

# Cache TTL: 24 hours
_CACHE_TTL_SECONDS = 86_400

# ---------------------------------------------------------------------------
# 1. npm date fetching
# ---------------------------------------------------------------------------

def _fetch_npm_dates(force: bool = False) -> dict[str, str]:
    """Fetch version publish dates from npm registry, with 24h file cache.

    Returns dict mapping version string -> "YYYY-MM-DD".
    """
    # Check cache
    if not force and _CACHE_FILE.exists():
        age = time.time() - _CACHE_FILE.stat().st_mtime
        if age < _CACHE_TTL_SECONDS:
            try:
                data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data:
                    return data
            except (json.JSONDecodeError, OSError):
                pass

    # Fetch from npm registry
    try:
        result = subprocess.run(
            ["npm", "view", "@anthropic-ai/claude-code", "time", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=True,  # Windows: npm.cmd
        )
        if result.returncode != 0:
            logger.warning("npm view failed: %s", result.stderr[:200])
            return _load_cache_fallback()

        raw: dict = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning("npm date fetch failed: %s", e)
        return _load_cache_fallback()

    # Parse: {"0.2.0": "2025-03-05T...", "modified": "...", "created": "..."}
    date_map: dict[str, str] = {}
    for key, ts in raw.items():
        if key in ("modified", "created"):
            continue
        # ts is like "2025-03-05T12:34:56.789Z"
        if isinstance(ts, str) and len(ts) >= 10:
            date_map[key] = ts[:10]

    # Save cache
    if date_map:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(
            json.dumps(date_map, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return date_map


def _load_cache_fallback() -> dict[str, str]:
    """Load from cache file even if expired (better than nothing)."""
    if _CACHE_FILE.exists():
        try:
            data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {}


# ---------------------------------------------------------------------------
# 2. change_type extraction
# ---------------------------------------------------------------------------

_CHANGE_TYPE_MAP: dict[str, str] = {
    "added": "added",
    "add": "added",
    "new": "added",
    "fixed": "fixed",
    "fix": "fixed",
    "improved": "improved",
    "improve": "improved",
    "enhanced": "improved",
    "changed": "changed",
    "removed": "removed",
    "remove": "removed",
    "updated": "updated",
    "update": "updated",
    "deprecated": "deprecated",
}


def _extract_change_type(text: str) -> str:
    """Extract change type from the first word of a bullet."""
    words = text.split()
    if not words:
        return "other"
    first_word = words[0].lower().rstrip(":").rstrip(".")
    return _CHANGE_TYPE_MAP.get(first_word, "other")


# ---------------------------------------------------------------------------
# 3. subsystem extraction
# ---------------------------------------------------------------------------

_SUBSYSTEM_NORMALIZE: dict[str, str] = {
    "vscode": "vscode",
    "vs code": "vscode",
    "vscode extension": "vscode",
    "sdk": "sdk",
    "ide": "ide",
    "jetbrains": "jetbrains",
    "windows": "windows",
    "linux": "linux",
    "macos": "macos",
    "mac": "macos",
    "mcp": "mcp",
    "hooks": "hooks",
    "hook": "hooks",
    "bedrock": "bedrock",
    "vertex": "vertex",
    "agents": "agents",
    "agent": "agents",
    "settings": "settings",
    "memory": "memory",
    "terminal": "terminal",
    "git": "git",
    "oauth": "oauth",
    "permissions": "permissions",
    "api": "api",
    "max": "max",
}

# Known bracket prefixes like [VSCode], [SDK], [IDE]
_BRACKET_RE = re.compile(r"^\[([A-Za-z][A-Za-z0-9 ]*)\]\s*")
# Colon prefix like "Windows: ..."
_COLON_PREFIX_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 ]{1,20}):\s+")


def _extract_subsystem(text: str) -> str | None:
    """Extract subsystem from bracket prefix or colon prefix."""
    # [VSCode] Added something...
    m = _BRACKET_RE.match(text)
    if m:
        key = m.group(1).strip().lower()
        return _SUBSYSTEM_NORMALIZE.get(key, key)

    # Windows: Fixed something... (only match known subsystems)
    m = _COLON_PREFIX_RE.match(text)
    if m:
        key = m.group(1).strip().lower()
        if key in _SUBSYSTEM_NORMALIZE:
            return _SUBSYSTEM_NORMALIZE[key]

    return None


# ---------------------------------------------------------------------------
# 4. Markdown version parsing
# ---------------------------------------------------------------------------

def _parse_versions(md: str) -> list[tuple[str, list[str]]]:
    """Parse CHANGELOG.md into list of (version, [bullet_texts])."""
    version_pattern = re.compile(r"^## (\d+\.\d+\.\d+)\s*$", re.MULTILINE)
    matches = list(version_pattern.finditer(md))

    result: list[tuple[str, list[str]]] = []
    for i, match in enumerate(matches):
        version = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        content = md[start:end].strip()

        bullets: list[str] = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                bullet_text = line[2:].strip()
                if bullet_text:
                    bullets.append(bullet_text)

        if bullets:
            result.append((version, bullets))

    return result


# ---------------------------------------------------------------------------
# 5. Main parser
# ---------------------------------------------------------------------------

_SOURCE_URL = "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md"


def parse_claude_code(md: str) -> list[dict]:
    """Parse Claude Code CHANGELOG.md into bullet-level event dicts.

    Each bullet becomes one event with change_type and subsystem fields.
    Dates come from npm registry (cached).
    Only includes versions published on or after 2025-01-01.
    """
    date_map = _fetch_npm_dates()
    events: list[dict] = []

    for version, bullets in _parse_versions(md):
        date_str = date_map.get(version)
        if not date_str:
            continue
        if date_str < "2025-01-01":
            continue

        for bullet in bullets:
            events.append({
                "product": "claude_code",
                "event_date": date_str,
                "title": bullet,
                "version": version,
                "change_type": _extract_change_type(bullet),
                "subsystem": _extract_subsystem(bullet),
                "source_url": _SOURCE_URL,
            })

    return events
