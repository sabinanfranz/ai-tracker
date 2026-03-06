"""Tests for scripts/parsers/gemini.py -- parse_gemini() function.

Tests both the old (2024) HTML structure where content is inside
``_releaseNoteCardBody_`` and the new (2025+) structure where content
is in a sibling ``_features_`` div.

Each ``<h3>`` feature title now produces a separate event row with
``content`` preserving markdown labels (``**내용:**``, ``**이유:**``).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.parsers.gemini import parse_gemini


# ---------------------------------------------------------------------------
# HTML fixtures
# ---------------------------------------------------------------------------

# Old structure (2024): content inside _releaseNoteCardBody_
OLD_STRUCTURE_HTML = """
<html><body>
<div class="_releaseNoteCard_lm7ws_90">
  <h2 class="_releaseNoteCardTitle_lm7ws_104">2025.03.15</h2>
  <div class="_releaseNoteCardBody_lm7ws_108">
    <div>
      <h3>Gemini Advanced 모델 업데이트</h3>
      <ul>
        <li><p><b>무엇:</b> Gemini Advanced의 모델이 업데이트되었습니다.</p></li>
        <li><p><b>왜:</b> 더 나은 성능을 제공하기 위해서입니다.</p></li>
      </ul>
      <h3>새로운 기능 추가</h3>
      <ul>
        <li><p>파일 업로드 기능이 추가되었습니다.</p></li>
      </ul>
    </div>
  </div>
</div>
</body></html>
"""

# New structure (2025+): body is empty, content in _features_ div
NEW_STRUCTURE_HTML = """
<html><body>
<div class="_releaseNoteCard_lm7ws_90">
  <h2 class="_releaseNoteCardTitle_lm7ws_104">2026.02.19</h2>
  <div class="_releaseNoteCardBody_lm7ws_108"></div>
  <div class="_features_lm7ws_174">
    <div>
      <h3 class="_featureTitle_lm7ws_180">Gemini 3.1 Pro: 가장 복잡한 작업을 위한 모델</h3>
      <ul class="_featureBullets_lm7ws_140">
        <li><div class="_featureBulletBody_lm7ws_109">
          <p><b>내용:</b> Gemini 3.1 Pro가 출시되었습니다. 코딩, 수학 등에서 뛰어난 성능을 보입니다.</p>
          <p>추가 세부 사항이 여기에 있습니다.</p>
        </div></li>
        <li><div class="_featureBulletBody_lm7ws_109">
          <p><b>이유:</b> 사용자에게 더 강력한 AI 도구를 제공하기 위해서입니다.</p>
        </div></li>
      </ul>
    </div>
    <div>
      <h3 class="_featureTitle_lm7ws_180">이미지 생성 개선</h3>
      <ul class="_featureBullets_lm7ws_140">
        <li><div class="_featureBulletBody_lm7ws_109">
          <p><b>내용:</b> 이미지 생성 품질이 크게 향상되었습니다.</p>
        </div></li>
      </ul>
    </div>
  </div>
</div>
</body></html>
"""

# Mixed: one new card + one old card
MIXED_HTML = """
<html><body>
<div class="_releaseNoteCard_lm7ws_90">
  <h2 class="_releaseNoteCardTitle_lm7ws_104">2025.06.10</h2>
  <div class="_releaseNoteCardBody_lm7ws_108"></div>
  <div class="_features_lm7ws_174">
    <div>
      <h3 class="_featureTitle_lm7ws_180">Deep Research 기능 출시</h3>
      <ul class="_featureBullets_lm7ws_140">
        <li><div class="_featureBulletBody_lm7ws_109">
          <p><b>내용:</b> Deep Research는 복잡한 연구 질문에 대해 종합적인 보고서를 생성합니다.</p>
        </div></li>
      </ul>
    </div>
  </div>
</div>
<div class="_releaseNoteCard_lm7ws_90">
  <h2 class="_releaseNoteCardTitle_lm7ws_104">2025.01.20</h2>
  <div class="_releaseNoteCardBody_lm7ws_108">
    <div>
      <h3>Gemini Live 다국어 지원</h3>
      <ul>
        <li><p>Gemini Live가 한국어를 포함한 새로운 언어를 지원합니다.</p></li>
      </ul>
    </div>
  </div>
</div>
</body></html>
"""

# Card with neither body content nor features -- should be skipped
EMPTY_CARD_HTML = """
<html><body>
<div class="_releaseNoteCard_lm7ws_90">
  <h2 class="_releaseNoteCardTitle_lm7ws_104">2025.05.01</h2>
  <div class="_releaseNoteCardBody_lm7ws_108"></div>
</div>
</body></html>
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParseGeminiOldStructure:
    """Tests for old (2024-style) HTML where content is in body_div."""

    def test_parses_old_structure_per_h3(self):
        """Each h3 in old structure becomes a separate event."""
        events = parse_gemini(OLD_STRUCTURE_HTML)
        assert len(events) == 2

        titles = [ev["title"] for ev in events]
        assert "Gemini Advanced 모델 업데이트" in titles
        assert "새로운 기능 추가" in titles

    def test_old_structure_fields(self):
        events = parse_gemini(OLD_STRUCTURE_HTML)
        ev = events[0]
        assert ev["product"] == "gemini"
        assert ev["event_date"] == "2025-03-15"
        assert ev["source_url"] == "https://gemini.google/release-notes/"
        assert "content" in ev

    def test_old_structure_content_has_markdown(self):
        events = parse_gemini(OLD_STRUCTURE_HTML)
        advanced_ev = [e for e in events if "Advanced" in e["title"]][0]
        # Bold labels should be preserved as markdown
        assert "**무엇:**" in advanced_ev["content"] or "**왜:**" in advanced_ev["content"]


class TestParseGeminiNewStructure:
    """Tests for new (2025+) HTML where content is in _features_ div."""

    def test_parses_new_structure_per_h3(self):
        """Each h3 feature title becomes a separate event."""
        events = parse_gemini(NEW_STRUCTURE_HTML)
        assert len(events) == 2

        titles = [ev["title"] for ev in events]
        assert any("Gemini 3.1 Pro" in t for t in titles)
        assert any("이미지 생성 개선" in t for t in titles)

    def test_new_structure_content_preserves_markdown_labels(self):
        events = parse_gemini(NEW_STRUCTURE_HTML)
        pro_ev = [e for e in events if "Gemini 3.1 Pro" in e["title"]][0]
        # **내용:** and **이유:** should be preserved in content
        assert "**내용:**" in pro_ev["content"]
        assert "**이유:**" in pro_ev["content"]

    def test_new_structure_content_is_korean(self):
        events = parse_gemini(NEW_STRUCTURE_HTML)
        ev = events[0]
        has_korean = any("\uac00" <= ch <= "\ud7a3" for ch in ev["content"])
        assert has_korean, "content should contain Korean text"

    def test_new_structure_image_event_separate(self):
        events = parse_gemini(NEW_STRUCTURE_HTML)
        img_ev = [e for e in events if "이미지 생성" in e["title"]][0]
        assert "**내용:**" in img_ev["content"]


class TestParseGeminiMixed:
    """Tests for HTML with both old and new card structures."""

    def test_parses_both_structures(self):
        events = parse_gemini(MIXED_HTML)
        assert len(events) == 2

        dates = {ev["event_date"] for ev in events}
        assert "2025-06-10" in dates  # new structure
        assert "2025-01-20" in dates  # old structure

    def test_new_card_has_features_content(self):
        events = parse_gemini(MIXED_HTML)
        new_ev = [e for e in events if e["event_date"] == "2025-06-10"][0]
        assert "Deep Research" in new_ev["title"]
        assert "**내용:**" in new_ev["content"]

    def test_old_card_has_body_content(self):
        events = parse_gemini(MIXED_HTML)
        old_ev = [e for e in events if e["event_date"] == "2025-01-20"][0]
        assert "Gemini Live" in old_ev["title"]


class TestParseGeminiEdgeCases:
    """Edge cases for parse_gemini()."""

    def test_empty_card_skipped(self):
        """Cards with neither body content nor features div are skipped."""
        events = parse_gemini(EMPTY_CARD_HTML)
        assert len(events) == 0

    def test_empty_html(self):
        """Empty HTML produces no events."""
        events = parse_gemini("")
        assert len(events) == 0

    def test_all_events_have_required_fields(self):
        """Every event dict has all required fields."""
        required = {"product", "event_date", "title", "content", "source_url"}
        for html in [OLD_STRUCTURE_HTML, NEW_STRUCTURE_HTML, MIXED_HTML]:
            events = parse_gemini(html)
            for ev in events:
                missing = required - set(ev.keys())
                assert not missing, f"Missing fields: {missing}"

    def test_no_tags_or_evidence_fields(self):
        """New schema events should NOT have tags or evidence_excerpt."""
        events = parse_gemini(NEW_STRUCTURE_HTML)
        for ev in events:
            assert "tags" not in ev
            assert "evidence_excerpt" not in ev
            assert "summary_ko" not in ev
