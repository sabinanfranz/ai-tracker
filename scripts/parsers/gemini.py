"""Gemini release notes HTML parser.

Each ``<h3>`` feature title produces one event row.
Content (내용/이유 bullets) is preserved as markdown in the ``content`` field.
"""

from __future__ import annotations

import re


def _p_to_markdown(p_tag) -> str:
    """Convert a <p> tag to markdown, preserving <b> and <a> elements."""
    parts: list[str] = []
    for child in p_tag.children:
        if getattr(child, "name", None) == "b":
            parts.append(f"**{child.get_text()}**")
        elif getattr(child, "name", None) == "a":
            href = child.get("href", "")
            text = child.get_text()
            parts.append(f"[{text}]({href})" if href else text)
        else:
            parts.append(str(child.string or child))
    return "".join(parts).strip()


def _extract_feature_content(feature_div) -> str:
    """Extract markdown content from a feature's bullet list."""
    bullets_ul = feature_div.find("ul", class_=re.compile(r"_featureBullets_"))
    if not bullets_ul:
        # Fallback: collect all <p> tags directly
        paragraphs = feature_div.find_all("p")
        return "\n\n".join(_p_to_markdown(p) for p in paragraphs if p.get_text(strip=True))

    parts: list[str] = []
    for li in bullets_ul.find_all("li", recursive=False):
        body_div = li.find("div", class_=re.compile(r"_featureBulletBody_"))
        container = body_div if body_div else li
        for p in container.find_all("p"):
            md = _p_to_markdown(p)
            if md:
                parts.append(md)
    return "\n\n".join(parts)


def _extract_old_feature_content(content_div, h3_tag) -> str:
    """Extract content for an h3 in old-style (2024) card structure.

    Collects elements between this h3 and the next h3 sibling.
    """
    parts: list[str] = []
    sibling = h3_tag.find_next_sibling()
    while sibling:
        if sibling.name == "h3":
            break
        if sibling.name == "ul":
            for li in sibling.find_all("li", recursive=False):
                for p in li.find_all("p"):
                    md = _p_to_markdown(p)
                    if md:
                        parts.append(md)
        elif sibling.name == "p":
            md = _p_to_markdown(sibling)
            if md:
                parts.append(md)
        sibling = sibling.find_next_sibling()
    return "\n\n".join(parts)


def parse_gemini(html: str) -> list[dict]:
    """Parse Gemini release notes HTML and return a list of event dicts.

    Each ``<h3>`` feature title becomes one event with:
    - product, event_date, title, content, source_url

    Handles two HTML structures:
    - 2024 (old): content is directly inside ``_releaseNoteCardBody_`` div
    - 2025+ (new): ``_releaseNoteCardBody_`` is empty; actual content is in a
      sibling ``_features_`` div.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []

    all_divs = soup.find_all("div", class_=re.compile(r"_releaseNoteCard_"))
    cards: list = []
    for d in all_divs:
        class_str = " ".join(d.get("class", []))
        if "_releaseNoteCardTitle_" not in class_str and "_releaseNoteCardBody_" not in class_str:
            cards.append(d)

    for card in cards:
        h2 = card.find("h2", class_=re.compile(r"_releaseNoteCardTitle_"))
        if not h2:
            continue
        date_raw = h2.get_text(strip=True)
        date_match = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", date_raw)
        if not date_match:
            continue
        date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"

        body_div = card.find("div", class_=re.compile(r"_releaseNoteCardBody_"))
        features_div = card.find("div", class_=re.compile(r"_features_"))

        body_has_content = (
            body_div is not None
            and body_div.get_text(strip=True) != ""
        )

        if body_has_content:
            # ---- OLD structure (2024-style, content in body_div) ----
            content_div = body_div
            h3_tags = content_div.find_all("h3")

            if not h3_tags:
                # No h3 — create a single event from all content
                first_text = content_div.get_text(strip=True)[:200]
                title_text = first_text if first_text else f"Gemini update {date_str}"
                paragraphs = content_div.find_all("p")
                content = "\n\n".join(
                    _p_to_markdown(p) for p in paragraphs if p.get_text(strip=True)
                )
                events.append({
                    "product": "gemini",
                    "event_date": date_str,
                    "title": title_text[:200],
                    "content": content,
                    "source_url": "https://gemini.google/release-notes/",
                })
            else:
                for h3 in h3_tags:
                    title_text = h3.get_text(strip=True)
                    if not title_text:
                        continue
                    content = _extract_old_feature_content(content_div, h3)
                    events.append({
                        "product": "gemini",
                        "event_date": date_str,
                        "title": title_text[:200],
                        "content": content,
                        "source_url": "https://gemini.google/release-notes/",
                    })

        elif features_div is not None:
            # ---- NEW structure (2025+, content in _features_ div) ----
            # Each direct child div with an h3 is a feature
            feature_containers = []
            for child_div in features_div.find_all("div", recursive=False):
                h3 = child_div.find("h3")
                if h3:
                    feature_containers.append((h3, child_div))

            if not feature_containers:
                # Fallback: find any h3 tags
                h3_tags = features_div.find_all("h3")
                for h3 in h3_tags:
                    feature_containers.append((h3, h3.parent))

            for h3, container in feature_containers:
                title_text = h3.get_text(strip=True)
                if not title_text:
                    continue
                content = _extract_feature_content(container)
                events.append({
                    "product": "gemini",
                    "event_date": date_str,
                    "title": title_text[:200],
                    "content": content,
                    "source_url": "https://gemini.google/release-notes/",
                })

    return events
