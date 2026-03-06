"""Seed script — insert ~30 realistic sample events into the database.

Usage:
    python -m scripts.seed
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

# Ensure project root is on sys.path so we can import apps.api
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.database import PRODUCT_TABLES, get_connection, init_db

# ---------------------------------------------------------------------------
# Seed data — realistic AI product updates from 2025-01 to 2026-03
# ---------------------------------------------------------------------------

SEED_EVENTS: list[dict] = [
    # ===== ChatGPT =====
    {
        "product": "chatgpt",
        "component": "model",
        "event_date": "2025-01-09",
        "title": "GPT-4o mini launched for free tier users",
        "title_ko": "GPT-4o mini, 무료 사용자도 이용 가능 — 기존 모델 대비 성능 대폭 향상",
        "summary_ko": "GPT-4o mini 모델이 무료 사용자에게도 제공되기 시작함. 기존 GPT-3.5 turbo 대비 성능이 크게 향상됨.",
        "summary_en": "GPT-4o mini model now available for free tier users, significantly outperforming GPT-3.5 turbo.",
        "tags": ["new", "pricing"],
        "severity": 4,
        "source_url": "https://help.openai.com/en/articles/chatgpt-release-notes",
        "evidence_excerpt": ["GPT-4o mini is now available to free users", "Replaces GPT-3.5 turbo as the default model"],
    },
    {
        "product": "chatgpt",
        "component": "feature",
        "event_date": "2025-02-14",
        "title": "Memory feature generally available",
        "title_ko": "ChatGPT 메모리 기능 정식 출시 — 대화 간 맥락을 자동으로 기억",
        "summary_ko": "ChatGPT 메모리 기능이 Plus 이상 사용자에게 정식 출시됨. 대화 간 컨텍스트를 자동으로 기억함.",
        "summary_en": "ChatGPT memory feature is now generally available for Plus and above. Automatically remembers context across conversations.",
        "tags": ["new"],
        "severity": 4,
        "source_url": "https://help.openai.com/en/articles/chatgpt-release-notes",
        "evidence_excerpt": ["Memory is now generally available", "ChatGPT will remember relevant details from your conversations"],
    },
    {
        "product": "chatgpt",
        "component": "feature",
        "event_date": "2025-04-10",
        "title": "Canvas editing mode launched",
        "title_ko": "ChatGPT Canvas 출시 — 긴 글·코드를 별도 창에서 바로 편집 가능",
        "summary_ko": "ChatGPT Canvas가 정식 출시됨. 긴 글이나 코드를 별도 편집 창에서 실시간으로 수정 가능.",
        "summary_en": "ChatGPT Canvas launched. Enables real-time editing of long text and code in a separate editing window.",
        "tags": ["new"],
        "severity": 3,
        "source_url": "https://help.openai.com/en/articles/chatgpt-release-notes",
        "evidence_excerpt": ["Canvas is now available for ChatGPT Plus, Team, and Enterprise users"],
    },
    {
        "product": "chatgpt",
        "component": "voice",
        "event_date": "2025-05-20",
        "title": "Advanced Voice Mode expanded to all Plus users",
        "title_ko": "고급 음성 모드, 모든 Plus 사용자로 확대 — 실시간 다국어 대화 지원",
        "summary_ko": "고급 음성 모드가 모든 Plus 사용자에게 확대 제공됨. 실시간 대화 및 다국어 지원 개선.",
        "summary_en": "Advanced Voice Mode expanded to all Plus users with improved real-time conversation and multilingual support.",
        "tags": ["new", "pricing"],
        "severity": 3,
        "source_url": "https://help.openai.com/en/articles/chatgpt-release-notes",
        "evidence_excerpt": ["Advanced Voice is now available to all ChatGPT Plus subscribers"],
    },
    {
        "product": "chatgpt",
        "component": "api",
        "event_date": "2025-07-15",
        "title": "GPT-4o Realtime API deprecated in favor of GPT-4o-audio",
        "title_ko": "GPT-4o Realtime API 폐기 예정 — 10월까지 새 오디오 API로 전환 필요",
        "summary_ko": "GPT-4o Realtime API가 폐기 예정됨. GPT-4o-audio API로 마이그레이션 필요. 2025년 10월까지 유예.",
        "summary_en": "GPT-4o Realtime API deprecated. Migration to GPT-4o-audio API required by October 2025.",
        "tags": ["change"],
        "severity": 5,
        "source_url": "https://help.openai.com/en/articles/chatgpt-release-notes",
        "evidence_excerpt": ["The Realtime API will be sunset on October 1, 2025", "Please migrate to the new audio API endpoints"],
    },
    {
        "product": "chatgpt",
        "component": "feature",
        "event_date": "2025-09-03",
        "title": "ChatGPT Projects feature launched",
        "title_ko": "ChatGPT Projects 출시 — 대화·파일·지침을 프로젝트별로 정리 가능",
        "summary_ko": "ChatGPT Projects 기능 출시. 관련 대화, 파일, 지침을 프로젝트별로 그룹화 가능.",
        "summary_en": "ChatGPT Projects feature launched. Group related conversations, files, and instructions by project.",
        "tags": ["new"],
        "severity": 3,
        "source_url": "https://help.openai.com/en/articles/chatgpt-release-notes",
        "evidence_excerpt": ["Organize your work with Projects", "Group conversations and files together"],
    },
    {
        "product": "chatgpt",
        "component": "model",
        "event_date": "2025-12-05",
        "title": "o1 reasoning model released to Pro users",
        "title_ko": "o1 추론 모델 출시 — 수학·코딩·과학 문제에서 GPT-4o 압도",
        "summary_ko": "o1 추론 모델이 Pro 사용자에게 출시됨. 복잡한 수학, 코딩, 과학 문제에서 GPT-4o 대비 성능 크게 향상.",
        "summary_en": "o1 reasoning model released to Pro users. Significant performance improvement over GPT-4o on complex math, coding, and science problems.",
        "tags": ["new"],
        "severity": 4,
        "source_url": "https://help.openai.com/en/articles/chatgpt-release-notes",
        "evidence_excerpt": ["o1 is now available in ChatGPT Pro", "Achieves expert-level performance on reasoning tasks"],
    },
    {
        "product": "chatgpt",
        "component": "model",
        "event_date": "2026-02-28",
        "title": "GPT-4.5 research preview available",
        "title_ko": "GPT-4.5 연구 프리뷰 공개 — 더 자연스러운 대화와 향상된 세계 지식",
        "summary_ko": "GPT-4.5 연구 프리뷰가 Plus 이상 사용자에게 공개됨. 더 자연스러운 대화와 향상된 세계 지식.",
        "summary_en": "GPT-4.5 research preview now available for Plus and above. More natural conversation and enhanced world knowledge.",
        "tags": ["new"],
        "severity": 4,
        "source_url": "https://help.openai.com/en/articles/chatgpt-release-notes",
        "evidence_excerpt": ["GPT-4.5 is now available in research preview", "Available for Plus, Pro, and Team users"],
    },
    # ===== Gemini =====
    {
        "product": "gemini",
        "component": "model",
        "event_date": "2025-01-21",
        "title": "Gemini 1.5 Pro with 2M token context window",
        "title_ko": "Gemini 1.5 Pro, 200만 토큰 컨텍스트 지원 — 역대 최대 입력 길이",
        "summary_ko": "Gemini 1.5 Pro가 200만 토큰 컨텍스트 윈도우를 지원하기 시작함. 역대 최대 컨텍스트 길이.",
        "summary_en": "Gemini 1.5 Pro now supports 2M token context window, the largest context length to date.",
        "tags": ["new"],
        "severity": 4,
        "source_url": "https://blog.google/technology/ai/gemini-updates/",
        "evidence_excerpt": ["Gemini 1.5 Pro now supports up to 2 million tokens", "The longest context window of any large language model"],
    },
    {
        "product": "gemini",
        "component": "feature",
        "event_date": "2025-03-18",
        "title": "Gems custom chatbot feature launched",
        "title_ko": "Gems 커스텀 챗봇 출시 — 목적에 맞는 나만의 Gemini 봇 생성 가능",
        "summary_ko": "Gems 커스텀 챗봇 기능 출시. 사용자가 특정 목적에 맞는 맞춤형 Gemini 봇을 생성 가능.",
        "summary_en": "Gems custom chatbot feature launched. Users can create purpose-built custom Gemini bots.",
        "tags": ["new"],
        "severity": 3,
        "source_url": "https://blog.google/technology/ai/gemini-updates/",
        "evidence_excerpt": ["Gems lets you create a custom version of Gemini", "Tailor Gemini for specific tasks"],
    },
    {
        "product": "gemini",
        "component": "feature",
        "event_date": "2025-06-02",
        "title": "Deep Research feature available to Advanced subscribers",
        "title_ko": "Gemini Deep Research 출시 — 복잡한 주제를 자동 조사해 보고서 생성",
        "summary_ko": "Deep Research 기능이 Advanced 구독자에게 제공됨. 복잡한 주제에 대해 자동으로 심층 조사 보고서 생성.",
        "summary_en": "Deep Research feature available to Advanced subscribers. Automatically generates in-depth research reports on complex topics.",
        "tags": ["new"],
        "severity": 3,
        "source_url": "https://blog.google/technology/ai/gemini-updates/",
        "evidence_excerpt": ["Deep Research can browse the web and compile comprehensive reports"],
    },
    {
        "product": "gemini",
        "component": "model",
        "event_date": "2025-08-12",
        "title": "Gemini 2.0 Flash generally available",
        "title_ko": "Gemini 2.0 Flash 정식 출시 — 이전 버전 대비 2배 빠르고 비용 절감",
        "summary_ko": "Gemini 2.0 Flash 모델이 정식 출시됨. 1.5 Flash 대비 속도 2배, 비용 절감.",
        "summary_en": "Gemini 2.0 Flash model generally available. 2x faster than 1.5 Flash with reduced costs.",
        "tags": ["new"],
        "severity": 4,
        "source_url": "https://blog.google/technology/ai/gemini-updates/",
        "evidence_excerpt": ["Gemini 2.0 Flash is now generally available", "2x faster inference at lower cost"],
    },
    {
        "product": "gemini",
        "component": "api",
        "event_date": "2025-10-30",
        "title": "Gemini API v1 deprecated, v2 migration required",
        "title_ko": "Gemini API v1 폐기 예정 — 2026년 3월까지 v2로 전환 필요",
        "summary_ko": "Gemini API v1이 폐기 예정. 2026년 3월까지 v2로 마이그레이션 필요. 엔드포인트 URL 변경.",
        "summary_en": "Gemini API v1 deprecated. Migration to v2 required by March 2026. Endpoint URL changes.",
        "tags": ["change"],
        "severity": 5,
        "source_url": "https://ai.google.dev/gemini-api/docs/changelog",
        "evidence_excerpt": ["API v1 endpoints will be removed on March 1, 2026", "Please update your integrations to use v2 endpoints"],
    },
    {
        "product": "gemini",
        "component": "feature",
        "event_date": "2026-01-15",
        "title": "Gemini in Google Workspace generally available",
        "title_ko": "Gemini, Google Workspace 전체 통합 — Gmail·Docs·Sheets에서 AI 지원",
        "summary_ko": "Gemini가 Google Workspace 전 제품에 통합됨. Gmail, Docs, Sheets에서 AI 어시스턴트 이용 가능.",
        "summary_en": "Gemini integrated across all Google Workspace products. AI assistant available in Gmail, Docs, Sheets.",
        "tags": ["new", "pricing"],
        "severity": 4,
        "source_url": "https://blog.google/technology/ai/gemini-updates/",
        "evidence_excerpt": ["Gemini is now integrated across Google Workspace", "Available to all Business and Enterprise plans"],
    },
    {
        "product": "gemini",
        "component": "model",
        "event_date": "2026-02-20",
        "title": "Gemini 2.0 Pro with improved coding and reasoning",
        "title_ko": "Gemini 2.0 Pro 출시 — 코딩 벤치마크·추론 성능 크게 향상",
        "summary_ko": "Gemini 2.0 Pro 출시. 코딩 벤치마크 및 추론 성능이 이전 버전 대비 크게 향상됨.",
        "summary_en": "Gemini 2.0 Pro released with significantly improved coding benchmarks and reasoning performance.",
        "tags": ["new"],
        "severity": 4,
        "source_url": "https://blog.google/technology/ai/gemini-updates/",
        "evidence_excerpt": ["Gemini 2.0 Pro achieves state-of-the-art performance on coding benchmarks"],
    },
    # ===== Codex (independent schema: entry_type, version, body) =====
    {
        "product": "codex",
        "event_date": "2025-02-26",
        "title": "Codex CLI 0.106.0",
        "entry_type": "codex-cli",
        "version": "0.106.0",
        "body": "[New Features]\n- Added multi-file editing support\n- Improved response latency for code completions\n[Bug Fixes]\n- Fixed syntax highlighting for Python files",
        "source_url": "https://developers.openai.com/codex/changelog/",
    },
    {
        "product": "codex",
        "event_date": "2025-05-10",
        "title": "Codex API rate limits updated for free tier",
        "entry_type": "general",
        "version": None,
        "body": "Codex API free tier rate limits updated. Requests per minute reduced from 60 to 20. Upgrade to a paid plan for higher limits.",
        "source_url": "https://developers.openai.com/codex/changelog/",
    },
    {
        "product": "codex",
        "event_date": "2025-07-22",
        "title": "Codex app 25.722",
        "entry_type": "codex-app",
        "version": "25.722",
        "body": "[New features]\n- Codex sandbox environment launched\n- Safely execute and test code in the cloud\n[Bug fixes]\n- Fixed rendering issues in code preview",
        "source_url": "https://developers.openai.com/codex/changelog/",
    },
    {
        "product": "codex",
        "event_date": "2025-10-15",
        "title": "Codex CLI 1.0.0",
        "entry_type": "codex-cli",
        "version": "1.0.0",
        "body": "[New Features]\n- Stable release with full feature set\n- Production-ready with improved reliability",
        "source_url": "https://developers.openai.com/codex/changelog/",
    },
    {
        "product": "codex",
        "event_date": "2026-01-08",
        "title": "Codex is now GA",
        "entry_type": "general",
        "version": None,
        "body": "Codex Tasks background execution feature added. Submit code tasks asynchronously and check results later.",
        "source_url": "https://developers.openai.com/codex/changelog/",
    },
    {
        "product": "codex",
        "event_date": "2026-02-05",
        "title": "Codex app 26.205",
        "entry_type": "codex-app",
        "version": "26.205",
        "body": "[Bug fixes]\n- Fixed token counting bug in streaming responses\n- Fixed inaccurate token counting in streaming mode",
        "source_url": "https://developers.openai.com/codex/changelog/",
    },
    # ===== Claude Code (independent schema: change_type, subsystem, version) =====
    {
        "product": "claude_code",
        "event_date": "2025-03-05",
        "title": "Added initial public release of Claude Code v0.2.0",
        "version": "0.2.0",
        "change_type": "added",
        "subsystem": None,
    },
    {
        "product": "claude_code",
        "event_date": "2025-05-19",
        "title": "Added multi-file context support for improved code generation",
        "version": "2.0.0",
        "change_type": "added",
        "subsystem": None,
    },
    {
        "product": "claude_code",
        "event_date": "2025-07-28",
        "title": "Added Git integration and PR review support",
        "version": "2.0.41",
        "change_type": "added",
        "subsystem": "git",
    },
    {
        "product": "claude_code",
        "event_date": "2025-09-19",
        "title": "Added Claude 3.5 Sonnet model support",
        "version": "2.0.69",
        "change_type": "added",
        "subsystem": None,
    },
    {
        "product": "claude_code",
        "event_date": "2025-11-10",
        "title": "Added MCP integration and IDE support in v1.0.0 stable release",
        "version": "2.1.15",
        "change_type": "added",
        "subsystem": "mcp",
    },
    {
        "product": "claude_code",
        "event_date": "2025-12-20",
        "title": "Fixed terminal rendering issues on Windows",
        "version": "2.1.34",
        "change_type": "fixed",
        "subsystem": "windows",
    },
    {
        "product": "claude_code",
        "event_date": "2026-01-22",
        "title": "Added agent mode for autonomous task execution",
        "version": "2.1.46",
        "change_type": "added",
        "subsystem": "agents",
    },
    {
        "product": "claude_code",
        "event_date": "2026-02-18",
        "title": "Updated Pro plan pricing from $20/month to $25/month",
        "version": "2.1.58",
        "change_type": "updated",
        "subsystem": None,
    },
]


def seed() -> None:
    """Insert seed events into the database."""
    init_db()
    conn = get_connection()

    inserted = 0
    try:
        for event in SEED_EVENTS:
            product = event["product"]
            table = PRODUCT_TABLES.get(product)
            if not table:
                print(f"  [WARN] Unknown product: {product}, skipping")
                continue

            event_id = str(uuid.uuid4())
            detected_at = f"{event['event_date']}T09:00:00Z"

            # ChatGPT uses simple schema
            if product == "chatgpt":
                conn.execute(
                    """
                    INSERT OR IGNORE INTO chatgpt_event
                        (id, event_date, title, content, source_url)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        event["event_date"],
                        event["title"],
                        event.get("summary_ko", ""),
                        event["source_url"],
                    ),
                )
                inserted += 1
                continue

            # Codex uses independent schema
            if product == "codex":
                conn.execute(
                    """
                    INSERT OR IGNORE INTO codex_event
                        (id, event_date, title, entry_type, version, body, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        event["event_date"],
                        event["title"],
                        event.get("entry_type", "general"),
                        event.get("version"),
                        event.get("body", ""),
                        event.get("source_url",
                                  "https://developers.openai.com/codex/changelog/"),
                    ),
                )
            elif product == "claude_code":
                # Claude Code uses independent schema
                conn.execute(
                    """
                    INSERT OR IGNORE INTO claude_code_event
                        (id, event_date, title, version, change_type, subsystem, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        event["event_date"],
                        event["title"],
                        event.get("version", ""),
                        event.get("change_type", "other"),
                        event.get("subsystem"),
                        event.get("source_url",
                                  "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md"),
                    ),
                )
            else:
                # Common schema products (gemini, etc.)
                conn.execute(
                    f"""
                    INSERT OR IGNORE INTO {table}
                        (id, component, event_date, detected_at, title,
                         title_ko, summary_ko, summary_en, tags, severity, source_url,
                         evidence_excerpt, raw_ref)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        event.get("component", "default"),
                        event["event_date"],
                        detected_at,
                        event["title"],
                        event.get("title_ko"),
                        event["summary_ko"],
                        event.get("summary_en"),
                        json.dumps(event["tags"]),
                        event["severity"],
                        event["source_url"],
                        json.dumps(event.get("evidence_excerpt", [])),
                        json.dumps({
                            "source_id": f"{product}_release_notes",
                            "section_key": event["event_date"],
                        }),
                    ),
                )
            inserted += 1

        conn.commit()
        print(f"Seed completed: {inserted} events inserted.")

        # Summary per product
        for pid, table in PRODUCT_TABLES.items():
            cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if cnt:
                print(f"  {pid}: {cnt} events")

    finally:
        conn.close()


if __name__ == "__main__":
    seed()
