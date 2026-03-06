"""Temporary analysis script for Codex HTML structure."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from bs4 import BeautifulSoup
import copy

html = open("data/snapshots/codex_latest.html", encoding="utf-8").read()
soup = BeautifulSoup(html, "html.parser")
entries = soup.find_all("li", class_="scroll-mt-28")

print("=== General entries ===")
for entry in entries:
    topic = entry.get("data-codex-topics", "?")
    if topic != "general":
        continue
    time_tag = entry.find("time")
    date = time_tag.get_text(strip=True) if time_tag else "?"
    top_h3 = entry.find("h3", class_="group")
    title = top_h3.find("span").get_text(separator=" ", strip=True) if top_h3 else "?"
    article = entry.find("article")
    if article:
        art_copy = copy.copy(article)
        for det in art_copy.find_all("details"):
            det.decompose()
        text = art_copy.get_text(separator=" ", strip=True)[:250]
    else:
        text = "(no article)"
    print(f"{date} | {title}")
    print(f"  {text}")
    print()

print("=== Codex app entry example ===")
for entry in entries:
    topic = entry.get("data-codex-topics", "?")
    if topic != "codex-app":
        continue
    article = entry.find("article")
    if not article:
        continue
    time_tag = entry.find("time")
    date = time_tag.get_text(strip=True)
    top_h3 = entry.find("h3", class_="group")
    title = top_h3.find("span").get_text(separator=" ", strip=True)
    print(f"Title: {title}")
    print(f"Date: {date}")
    current_section = None
    for child in article.children:
        if not hasattr(child, "name") or child.name is None:
            continue
        if child.name == "h3":
            current_section = child.get_text(strip=True)
        elif child.name == "ul" and current_section:
            lis = [li.get_text(strip=True) for li in child.find_all("li", recursive=False)]
            print(f"  [{current_section}]")
            for item in lis:
                print(f"    - {item[:120]}")
    print()
    break

print("=== Codex CLI entry example (with details) ===")
for entry in entries:
    topic = entry.get("data-codex-topics", "?")
    if topic != "codex-cli":
        continue
    details = entry.find("details")
    if not details:
        continue
    time_tag = entry.find("time")
    date = time_tag.get_text(strip=True)
    top_h3 = entry.find("h3", class_="group")
    title = top_h3.find("span").get_text(separator=" ", strip=True)
    print(f"Title: {title}")
    print(f"Date: {date}")
    detail_div = details.find("div", class_="prose-content")
    if detail_div:
        for child in detail_div.children:
            if not hasattr(child, "name") or child.name is None:
                continue
            if child.name in ("h2", "h3"):
                print(f"  [{child.get_text(strip=True)}]")
            elif child.name == "ul":
                lis = child.find_all("li", recursive=False)
                for li in lis[:3]:
                    print(f"    - {li.get_text(strip=True)[:120]}")
                if len(lis) > 3:
                    print(f"    ... ({len(lis)} total items)")
    print()
    break
