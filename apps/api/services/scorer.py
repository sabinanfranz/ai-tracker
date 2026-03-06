"""Rule-based severity calculator for update events.

Scans title + summary text (lowercased) for keyword matches and returns the
highest matching severity level (1-5).  Falls back to 2 if no rule matches.
"""

from __future__ import annotations

SEVERITY_RULES: dict[int, list[str]] = {
    5: ["breaking", "deprecation", "shutdown", "removed", "end of life"],
    4: ["new model", "major feature", "launch", "generally available", "ga"],
    3: ["pricing", "access", "plan", "tier", "quota", "rate limit"],
    2: ["feature", "improvement", "update", "enhancement", "support"],
    1: ["fix", "bug", "patch", "performance", "minor"],
}


def calculate_severity(title: str, summary: str) -> int:
    """Return severity 1-5 based on keyword matching in title + summary.

    Combines *title* and *summary*, converts to lowercase, then checks
    keywords from highest severity to lowest.  Returns the first (highest)
    match found.  If nothing matches, returns the default value of 2.
    """
    text = f"{title} {summary}".lower()

    for severity in sorted(SEVERITY_RULES.keys(), reverse=True):
        for keyword in SEVERITY_RULES[severity]:
            if keyword in text:
                return severity

    # Default when no keyword matched
    return 2
