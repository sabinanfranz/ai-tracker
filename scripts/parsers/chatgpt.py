"""ChatGPT release notes HTML parser — h1/h2 semantic parsing.

Structure of https://help.openai.com/en/articles/6825453-chatgpt-release-notes:
  - Page title h1: "ChatGPT — Release Notes" (no date → skip)
  - Date h1: "February 25, 2026" etc.
  - Within each date section (h1 → next h1):
    - h2 = feature title  → each h2 starts a new event group
    - h3 = sub-section (Web / iOS / Android) under an h2
    - p / ul / ol = content belonging to the current group

Edge cases:
  - h1 → h3 direct (no h2): treat h3 as feature title (new group)
  - h1 → p direct (no h2/h3): merge all p/ul into one event
  - h3 sub-sections (Web/iOS): prefix bullets with platform name
"""

from __future__ import annotations

from scripts.parsers import parse_en_date


def parse_chatgpt(html: str) -> list[dict]:
    """Parse ChatGPT release notes HTML and return a list of event dicts."""
    from bs4 import BeautifulSoup, Tag

    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []

    # 1. Collect all h1 tags with dates
    all_h1s = soup.find_all("h1")
    date_h1s: list[tuple[Tag, str]] = []
    for h1 in all_h1s:
        text = h1.get_text(strip=True)
        date_str = parse_en_date(text)
        if date_str:
            date_h1s.append((h1, date_str))

    # 2. For each date h1, collect siblings until next h1
    for idx, (h1, date_str) in enumerate(date_h1s):
        if date_str < "2025-01-01":
            continue

        # Collect all siblings between this h1 and the next h1
        siblings: list[Tag] = []
        sib = h1.find_next_sibling()
        while sib:
            if isinstance(sib, Tag) and sib.name == "h1":
                break
            if isinstance(sib, Tag):
                siblings.append(sib)
            sib = sib.find_next_sibling()

        # 3. Group siblings by h2/h3 headings
        groups = _group_siblings(siblings)

        if not groups:
            continue

        # 4. Convert each group into an event dict
        for group in groups:
            event = _group_to_event(group, date_str)
            if event:
                events.append(event)

    return events


def _group_siblings(siblings: list) -> list[dict]:
    """Split siblings into groups based on h2/h3 headings.

    Returns a list of group dicts:
        {"title": str | None, "content": list[str], "sub_sections": list[dict]}

    Each sub_section: {"heading": str, "items": list[str]}
    """
    groups: list[dict] = []
    current_group: dict | None = None
    current_sub: dict | None = None

    for sib in siblings:
        tag_name = sib.name

        if tag_name == "h2":
            # Flush previous group
            if current_group is not None:
                if current_sub:
                    current_group["sub_sections"].append(current_sub)
                    current_sub = None
                groups.append(current_group)

            h2_text = sib.get_text(strip=True)
            current_group = {
                "title": h2_text,
                "content": [],
                "sub_sections": [],
            }
            current_sub = None

        elif tag_name in ("h3", "h4"):
            heading_text = sib.get_text(strip=True)

            if current_group is None:
                # h1 → h3 direct: treat h3 as a new group title
                current_group = {
                    "title": heading_text,
                    "content": [],
                    "sub_sections": [],
                }
                current_sub = None
            else:
                # h3 under an existing h2: start a sub-section
                if current_sub:
                    current_group["sub_sections"].append(current_sub)
                current_sub = {"heading": heading_text, "items": []}

        elif tag_name in ("ul", "ol"):
            items = _extract_list_items(sib)
            if current_sub is not None:
                current_sub["items"].extend(items)
            elif current_group is not None:
                current_group["content"].extend(items)
            else:
                # No heading yet — start an implicit group
                current_group = {
                    "title": None,
                    "content": items,
                    "sub_sections": [],
                }

        elif tag_name == "p":
            p_text = sib.get_text(strip=True)
            if not p_text:
                continue
            if current_sub is not None:
                current_sub["items"].append(p_text)
            elif current_group is not None:
                current_group["content"].append(p_text)
            else:
                current_group = {
                    "title": None,
                    "content": [p_text],
                    "sub_sections": [],
                }

    # Flush last group
    if current_group is not None:
        if current_sub:
            current_group["sub_sections"].append(current_sub)
        groups.append(current_group)

    return groups


def _extract_list_items(ul_or_ol) -> list[str]:
    """Extract text from direct <li> children of a <ul>/<ol>."""
    items: list[str] = []
    for li in ul_or_ol.find_all("li", recursive=False):
        text = li.get_text(strip=True)
        if text:
            items.append(text)
    return items


def _group_to_event(group: dict, date_str: str) -> dict | None:
    """Convert a single group dict into an event dict."""
    # Build content: group content lines + sub-section items with prefix
    lines: list[str] = list(group["content"])
    for sub in group["sub_sections"]:
        prefix = sub["heading"]
        for item in sub["items"]:
            lines.append(f"{prefix}: {item}")

    if not lines and not group["title"]:
        return None

    # Title: h2 text, or h3 text, or first content[:100], or fallback
    title = group["title"]
    if not title:
        if lines:
            title = lines[0][:100]
        else:
            title = f"ChatGPT update {date_str}"
    title = title[:200]

    content = "\n".join(lines)

    return {
        "product": "chatgpt",
        "event_date": date_str,
        "title": title,
        "content": content,
        "source_url": "https://help.openai.com/en/articles/6825453-chatgpt-release-notes",
    }
