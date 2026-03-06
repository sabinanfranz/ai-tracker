"""Classify 'other' change_type events into card-news vs skip."""

import sqlite3
import re
from collections import Counter
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tracker.db"

# === 판단 로직 v1 ===

# 카드뉴스 제외 (SKIP) 패턴 — 우선 적용
SKIP_PATTERNS = [
    # 1. IDE 버그픽스 (VSCode/JetBrains crash, fix)
    (r"(?:VS\s?Code|VSCode|JetBrains|IntelliJ).*(?:Fix|fix|crash|resolve|Improve|spinner|scroll|dimmed|Restore)", "ide_bugfix"),
    # 2. SDK 내부 변경 (개발자 전용)
    (r"^SDK:", "sdk_internal"),
    (r"\[SDK\]", "sdk_internal"),
    (r"SDK\s*(?:message|field|option|callback|tracking|cancel|support|entrypoint|consumer)", "sdk_internal"),
    (r"(?:emit messages from sub-tasks|parent_tool_use_id)", "sdk_internal"),
    # 3. Windows/Linux 플랫폼 버그픽스
    (r"(?:Windows|Linux).*(?:[Ff]ix|resolve|crash|cleanup|clean up|improve.*(?:permission|spawn|check))", "platform_bugfix"),
    # 4. 내부 도구 버그픽스
    (r"^(?:Bash|MCP|Hooks|OTEL|Settings|Agents|UI|Slash commands):.*(?:[Ff]ix|resolve|crash|[Ii]mprove|[Rr]educe|[Ss]plit|[Ee]xpose)", "tool_bugfix"),
    # 5. UI 미세 조정
    (r"(?:spinner|contrast|rendering|dimmed|visual hierarchy|animations|flickering|flicker|jitter|layout jitter)", "ui_micro"),
    # 6. 내부 성능 최적화
    (r"(?:Optimiz|optimiz|[Rr]educe.*(?:context|memory|prompt|token|clutter|flicker)|cache|cleanup|clean up|accumulate)", "perf_internal"),
    (r"(?:launch quicker|Reduced system prompt|Reduced unnecessary|[Ss]ilenced.*error|Reduced terminal)", "perf_internal"),
    # 7. 설정/경로 정리
    (r"(?:config backup|backup files|validation prevents|surfaced error|[Mm]oved.*(?:from|to).*(?:directory|root|~/))", "config_housekeeping"),
    (r"(?:[Mm]igrat(?:ed|ion).*(?:allowedTools|ignorePatterns|settings))", "config_housekeeping"),
    # 8. 검색/표시 미세 조정
    (r"(?:displayed in quotes|collapsed tool|Search patterns|Show condensed|condensed output)", "display_tweak"),
    # 9. Bedrock/Vertex 내부 (인증, 토큰, 프로필)
    (r"(?:Bedrock|Vertex).*(?:[Dd]isplay|[Ii]mprove|[Ee]fficiency|auth|token count|profile)", "cloud_provider_internal"),
    # 10. Hooks 내부 변경 (개발자 전용)
    (r"(?:Hooks?:.*(?:Split|Exposed|Reduced|modify))", "hooks_internal"),
    (r"(?:PreToolUse hooks can)", "hooks_internal"),
    # 11. 내부 리팩토링 / un-ship
    (r"(?:[Uu]nshipped|[Dd]eprecate.*config|Renamed /allowed)", "internal_refactor"),
    # 12. 문서/블로그 링크만 (공지가 아닌 참고용)
    (r"(?:Plugin documentation|Plugin announcement|Document --system)", "docs_only"),
    # 13. 내부 설정 조정 (임계값, 타임아웃, 인터벌)
    (r"(?:Increased.*(?:threshold|interval|otel)|Moved shell snapshots|Respect CLAUDE_CONFIG_DIR)", "config_tweak"),
    (r"(?:No longer inform Claude|Avoid mentioning hooks|Improvements to /help|Avoid flickering)", "minor_polish"),
    # 14. 3P 수동 업그레이드 안내 (내부)
    (r"3P.*(?:Bedrock|Vertex).*not automatically", "cloud_provider_internal"),
    # 15. Plugin 개발자 전용
    (r"(?:/plugin validate|Plugins can ship)", "plugin_dev"),
    # 16. Managed settings (관리자 전용)
    (r"(?:Managed settings|invalid managed settings)", "admin_only"),
    # 17. 내부 동작 조정 (유저 체감 없음)
    (r"(?:auto-compacting instant|Reduce unnecessary logins|Plugins UI polish|Switched.*/usage|Improvements to.*/help)", "minor_polish"),
    (r"(?:OAuth tokens now proactively|OAuth uses port)", "auth_internal"),
    (r"(?:MCP.*(?:UI improvement|authentication.*improvement|tool annotation|server list))", "mcp_internal"),
    # 18. CLI 플래그/환경변수 (파워유저/개발자 전용)
    (r"(?:CLAUDE_BASH_NO_LOGIN|--append-system-prompt|CLAUDE_CODE_SIMPLE)", "dev_flag"),
    # 19. 내부 리팩토링/리네이밍
    (r"(?:scopes have been renamed|Moved system.*status)", "internal_rename"),
    # 20. Plugin 팀 협업 (관리자)
    (r"(?:extraKnownMarketplaces|Repository-level plugin)", "plugin_admin"),
]

# 카드뉴스 포함 (INCLUDE) 패턴
INCLUDE_PATTERNS = [
    # A. 새 기능/명령어 출시
    (r"(?:Released|Introducing|Launch|new (?:command|feature|setting|mode))", "new_feature"),
    # B. 유저가 쓸 수 있는 새 기능
    (r"now (?:support|available|include|shared|skip|show|use|persist|update|disable)", "user_facing_change"),
    # C. 새 단축키/명령어
    (r"(?:Ctrl\+|ctrl\+|Shift\+|Press (?:Tab|Esc)|/\w+\s+(?:command|slash)|keyboard shortcut)", "keybinding"),
    # D. 모델 변경/업그레이드
    (r"(?:Upgraded?|Sonnet \d|Opus \d|Claude \d|model.*version|[Ff]ast mode|1M context)", "model_change"),
    # E. 중요 동작 변경
    (r"(?:Blocked|by default|default.*changed|no longer|instead of|Breaking change)", "behavior_change"),
    # F. 새 플랫폼 지원
    (r"(?:Added support for|Alpine|musl)", "platform_support"),
    # G. 유저 워크플로우 변경
    (r"(?:auto-?memory|Remote Control|worktree|background command|[Pp]lan [Mm]ode|[Ss]andbox)", "workflow"),
    # H. 구독/가격 변경
    (r"(?:Pro subscription|Max subscription|generally available)", "subscription"),
    # I. 유저 직접 사용 기능 (You can now, Claude can now)
    (r"(?:You can now|Claude can now|Claude now|you can now)", "direct_user_feature"),
    # J. 새 슬래시 명령어
    (r"(?:/rewind|/resume|/stats|/permissions|/agents|/config|/doctor|/model|/rename|/t |/add-dir)", "slash_command"),
    # K. 이미지/미디어 기능
    (r"(?:Copy\+paste images|paste.*images|Resizes images)", "media_feature"),
    # L. 대화/세션 기능
    (r"(?:--continue|--resume|Resume conversation|conversation compaction|infinite conversation)", "session_feature"),
    # M. MCP 유저 기능 (리소스, @-mention, 타임아웃 설정)
    (r"(?:MCP resources can|MCP.*@-mention|MCP_TIMEOUT|MCP.*OAuth.*port)", "mcp_user_feature"),
    # N. 사고 모드 (thinking)
    (r"(?:think|Think|thinking mode|ultrathink)", "thinking_feature"),
    # O. 커스텀 명령어/에이전트
    (r"(?:Custom slash command|custom subagent|\.claude/commands)", "custom_commands"),
    # P. 프로젝트 설정 공유
    (r"(?:Shared project|\.claude/settings\.json|permission rules)", "project_settings"),
    # Q. 비동기/백그라운드 기능
    (r"(?:asynchronously|background task|run.*background|send.*background)", "async_feature"),
    # R. 특정 주요 릴리스 기능
    (r"(?:Fresh coat of paint|Rewrote terminal renderer)", "major_release"),
    # S. 구독자 기능
    (r"(?:Skill character budget|linked to PR)", "power_user"),
    # T. UX 개선 (유저 체감)
    (r"(?:Redesigned.*tool|Merged slash commands|Un-deprecate)", "ux_change"),
    (r"(?:Pressing ESC|Press Shift|Press Ctrl|Ctrl-R|Ctrl-G)", "keybinding"),
    # U. 유저 편의 변경
    (r"(?:Usage limit notification|Switched /usage|Allow more safe git|Teleporting.*session)", "user_convenience"),
    (r"(?:Settings file changes take effect|Increased initial session count)", "user_convenience"),
    # V. Subagent 유저 기능
    (r"(?:Subagents:.*(?:resume|choose|model))", "subagent_feature"),
    # W. 웹 검색 개선
    (r"(?:Web search now takes|today.s date)", "search_improvement"),
    # X. MCP 설정 기능
    (r"(?:MCP SSE.*custom headers)", "mcp_user_feature"),
    # Y. Bash/도구 유저 편의
    (r"(?:Permit some uses|Task tool can now)", "tool_user_feature"),
    # Z. Keychain 보안
    (r"(?:API keys.*Keychain|stored in.*Keychain)", "security_feature"),
    # AA. auto-accept
    (r"(?:auto-accept|toggle auto-accept)", "keybinding"),
]


def classify(title: str) -> tuple[str, str]:
    """Return (verdict, reason). verdict = 'card' or 'skip'."""
    # SKIP 먼저
    for pat, reason in SKIP_PATTERNS:
        if re.search(pat, title):
            return ("skip", reason)

    # INCLUDE
    for pat, reason in INCLUDE_PATTERNS:
        if re.search(pat, title):
            return ("card", reason)

    # 2차: 신호어 기반
    if re.search(r"(?:Add|add|Enable|enable|Support|support|Introduce)", title):
        return ("card", "feature_signal")
    if re.search(r"(?:[Ff]ix|[Rr]esolve|[Pp]atch|[Cc]rash|[Bb]ug|[Ll]eak)", title):
        return ("skip", "fix_signal")

    # 미분류
    return ("card", "UNCERTAIN")


def main():
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT rowid, title, version, event_date "
        "FROM claude_code_event WHERE change_type = 'other' "
        "ORDER BY event_date DESC"
    ).fetchall()

    card, skip = [], []
    for rowid, title, ver, date in rows:
        verdict, reason = classify(title)
        entry = (rowid, ver, date, title[:130], reason)
        if verdict == "card":
            card.append(entry)
        else:
            skip.append(entry)

    print(f"=== 판단 결과 ===")
    print(f"카드뉴스 포함: {len(card)}건")
    print(f"카드뉴스 제외: {len(skip)}건")
    print(f"합계: {len(card)+len(skip)}건 / 전체 {len(rows)}건")

    card_reasons = Counter(r[4] for r in card)
    print(f"\n--- 카드뉴스 포함 (reason별) ---")
    for reason, cnt in card_reasons.most_common():
        print(f"  {reason:25s} {cnt}")

    skip_reasons = Counter(r[4] for r in skip)
    print(f"\n--- 카드뉴스 제외 (reason별) ---")
    for reason, cnt in skip_reasons.most_common():
        print(f"  {reason:25s} {cnt}")

    print(f"\n--- UNCERTAIN 항목 ---")
    for r in card:
        if r[4] == "UNCERTAIN":
            print(f"  [{r[1]}] {r[3]}")

    print(f"\n--- 카드뉴스 포함 샘플 (최근 15건) ---")
    for r in card[:15]:
        print(f"  [{r[1]}] ({r[4]}) {r[3]}")

    print(f"\n--- 카드뉴스 제외 샘플 (최근 15건) ---")
    for r in skip[:15]:
        print(f"  [{r[1]}] ({r[4]}) {r[3]}")

    conn.close()


if __name__ == "__main__":
    main()
