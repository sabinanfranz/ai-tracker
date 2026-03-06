"""Codex changelog HTML parser.

Parses each <li class="scroll-mt-28"> entry into a dict with:
  event_date, title, entry_type, version, body, source_url, product
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Version extraction patterns
# ---------------------------------------------------------------------------

_APP_VERSION_RE = re.compile(r"(\d+\.\d+)")        # e.g. "26.226"
_CLI_VERSION_RE = re.compile(r"(\d+\.\d+\.\d+)")   # e.g. "0.106.0"


def _extract_version(title: str, entry_type: str) -> str | None:
    """Extract version string from title based on entry_type."""
    if entry_type == "codex-cli":
        m = _CLI_VERSION_RE.search(title)
        return m.group(1) if m else None
    elif entry_type == "codex-app":
        m = _APP_VERSION_RE.search(title)
        return m.group(1) if m else None
    return None


def _build_body(article, entry_type: str) -> str:
    """Extract structured plain-text body from an <article> element.

    - codex-app: h3 sections + bullet lists directly in article
    - codex-cli: <details> inner prose-content div, h2 sections + bullets
    - general: prose paragraphs + optional bullet lists
    """
    from bs4 import Tag

    parts: list[str] = []

    if entry_type == "codex-cli":
        # CLI entries have content inside <details> > <div class="prose-content">
        details = article.find("details")
        if details:
            prose_div = details.find("div", class_="prose-content")
            if prose_div:
                _parse_sections(prose_div, parts, heading_tags=("h2", "h3"))
        # If no details found, fall through to direct article parsing
        if not parts:
            _parse_sections(article, parts, heading_tags=("h2", "h3"))

    elif entry_type == "codex-app":
        # App entries have h3 sections + ul directly in article
        _parse_sections(article, parts, heading_tags=("h3",))

    else:
        # General entries: prose paragraphs and optional lists
        _parse_sections(article, parts, heading_tags=("h2", "h3"))

    return "\n".join(parts).strip()


def _parse_sections(container, parts: list[str], heading_tags: tuple[str, ...]) -> None:
    """Walk direct children of container, building [Section] + bullet text.

    Stops if a [Changelog] section is encountered (CLI PR lists).
    """
    from bs4 import NavigableString, Tag

    current_section: str | None = None

    for child in container.children:
        if isinstance(child, NavigableString):
            text = child.strip()
            if text:
                parts.append(text)
            continue

        if not isinstance(child, Tag):
            continue

        # Skip <pre> tags (install commands)
        if child.name == "pre":
            continue

        # Skip <details> if we're not already inside one
        # (avoid double-processing)
        if child.name == "details":
            continue

        # Heading → new section
        if child.name in heading_tags:
            section_text = child.get_text(strip=True)
            # Stop at [Changelog] section
            if section_text.lower() == "changelog":
                break
            current_section = section_text
            parts.append(f"[{current_section}]")
            continue

        # Lists → bullet items
        if child.name in ("ul", "ol"):
            for li in child.find_all("li", recursive=False):
                li_text = li.get_text(separator=" ", strip=True)
                if li_text:
                    parts.append(f"- {li_text}")
            continue

        # Paragraphs → prose text
        if child.name == "p":
            p_text = child.get_text(separator=" ", strip=True)
            if p_text:
                parts.append(p_text)
            continue


def parse_codex(html: str) -> list[dict]:
    """Parse Codex changelog HTML and return a list of event dicts.

    Each dict has: product, event_date, title, entry_type, version, body, source_url
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []

    entries = soup.find_all("li", class_="scroll-mt-28")

    for entry in entries:
        # 1. Date from <time> tag
        time_tag = entry.find("time")
        if not time_tag:
            continue
        date_str = time_tag.get_text(strip=True)

        # 2. Entry type from data-codex-topics attribute
        entry_type = entry.get("data-codex-topics", "general")

        # 3. Title from <h3 class="group"> > <span>
        h3 = entry.find("h3")
        if not h3:
            continue
        # Get the first <span> child's text (contains the title)
        span = h3.find("span")
        if span:
            title_text = span.get_text(separator=" ", strip=True)
        else:
            title_text = h3.get_text(separator=" ", strip=True)
        # Remove "Copy link" button text artifacts
        title_text = re.sub(r"\s*Copy link.*$", "", title_text, flags=re.IGNORECASE).strip()

        if not title_text:
            continue

        # 4. Version extraction
        version = _extract_version(title_text, entry_type)

        # 5. Body from <article>
        article = entry.find("article")
        body = _build_body(article, entry_type) if article else ""

        events.append({
            "product": "codex",
            "event_date": date_str,
            "title": title_text,
            "entry_type": entry_type,
            "version": version,
            "body": body,
            "source_url": "https://developers.openai.com/codex/changelog/",
        })

    return events
