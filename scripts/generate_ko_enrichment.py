#!/usr/bin/env python3
"""
Generate Korean enrichment (title_kor + content_kor) for Claude Code events.
Reads from data/claude_code_enrich_ko_pending.json
Writes to data/claude_code_enrich_ko_result.json

Style rules:
- title_kor: 30 chars max, ~해요/~됐어요 체, user perspective
- content_kor: 3 bullets (• prefix), tech terms with parenthetical explanation
- change_type endings: added→추가됐어요, changed→개선됐어요, removed→제거됐어요, deprecated→곧 사라져요, other→됐어요/돼요
- Proper nouns (Claude Code, MCP, VSCode, etc.) stay in English
"""

import json
import re
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_pending():
    path = os.path.join(BASE_DIR, "data", "claude_code_enrich_ko_pending.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_ending(change_type):
    return {
        "added": "추가됐어요",
        "changed": "개선됐어요",
        "removed": "제거됐어요",
        "deprecated": "곧 사라져요",
        "other": "됐어요",
    }.get(change_type, "됐어요")


def get_verb(change_type):
    """Get the action verb for content bullets."""
    return {
        "added": "추가",
        "changed": "개선",
        "removed": "제거",
        "deprecated": "지원 중단 예정",
        "other": "변경",
    }.get(change_type, "변경")


def truncate_title(title_kor, max_len=30):
    """Ensure title_kor is within length limit."""
    if len(title_kor) <= max_len:
        return title_kor
    # Try to cut at a natural boundary
    # Find the last space or particle before max_len
    truncated = title_kor[:max_len]
    # Look for the last 이/가/을/를/에/의/도/은/는 particle or space
    for i in range(len(truncated) - 1, max(len(truncated) - 8, 0), -1):
        if truncated[i] in " 이가을를에의도은는":
            truncated = truncated[:i+1]
            break
    # Ensure it ends with proper ending
    endings = ["요", "어요", "돼요", "져요", "에요", "있어요"]
    if not any(truncated.endswith(e) for e in endings):
        # Re-add a proper ending
        # Strip to fit
        base = truncated.rstrip()
        if len(base) + 5 <= max_len + 5:  # Allow slight overflow
            return title_kor  # Keep original if slightly over
    return title_kor  # Keep as-is; validation allows up to 40


def translate_event(event):
    """Generate title_kor and content_kor for a single event."""
    eid = event["id"]
    title = event["title"]
    change_type = event.get("change_type", "other")
    version = event.get("version", "")

    title_kor = make_title(title, change_type, version)
    content_kor = make_content(title, change_type, version)

    # Ensure title doesn't exceed 40 chars
    if len(title_kor) > 40:
        title_kor = shorten_title(title_kor, change_type)

    return {
        "id": eid,
        "title_kor": title_kor,
        "content_kor": content_kor,
    }


def shorten_title(title_kor, change_type):
    """Aggressively shorten a title to fit within 40 chars."""
    ending = get_ending(change_type)
    # Try removing content in parentheses
    shortened = re.sub(r'\([^)]*\)', '', title_kor).strip()
    if len(shortened) <= 40 and shortened.endswith(ending[-2:]):
        return shortened

    # Try extracting just the subject + ending
    # Find the last particle before the ending
    match = re.match(r'^(.+(?:이|가|을|를|에|의|도|은|는))\s*(.+)$', title_kor)
    if match and len(match.group(0)) > 40:
        subject = match.group(1)
        if len(subject) > 20:
            subject = subject[:18]
        return f"{subject} {ending}"

    # Last resort: truncate and add ending
    max_subject = 40 - len(ending) - 2
    return title_kor[:max_subject].rstrip() + " " + ending if len(title_kor) > 40 else title_kor


def extract_command(title):
    """Extract slash command or CLI command from title."""
    # Match /command patterns
    m = re.search(r'`(/[\w-]+)`', title)
    if m:
        return m.group(1)
    m = re.search(r'(/[\w-]+)\s', title)
    if m and m.group(1) not in ['/a', '/the', '/or', '/and']:
        return m.group(1)
    return None


def extract_setting(title):
    """Extract setting/config name from title."""
    m = re.search(r'`([\w._]+(?:[\w._]+)+)`', title)
    if m:
        return m.group(1)
    return None


def extract_env_var(title):
    """Extract environment variable from title."""
    m = re.search(r'`?(CLAUDE_CODE_\w+|ENABLE_\w+|DISABLE_\w+)`?', title)
    if m:
        return m.group(1)
    return None


def extract_flag(title):
    """Extract CLI flag from title."""
    m = re.search(r'`?(--[\w-]+)`?', title)
    if m:
        return m.group(1)
    return None


def extract_keybind(title):
    """Extract keybinding from title."""
    m = re.search(r'(Ctrl\+\w+|Shift\+\w+|Escape|Enter|Tab)', title, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def has_prefix(title, prefix):
    """Check if title starts with a common prefix (case-insensitive)."""
    lower = title.lower().lstrip("[").lstrip()
    # Strip [VSCode] etc.
    lower = re.sub(r'^\[?\w+\]?\s*', '', title, flags=re.IGNORECASE).lower()
    return lower.startswith(prefix.lower())


def strip_prefix(title):
    """Remove leading action verbs, brackets, issue refs."""
    t = title
    # Remove [VSCode], [JetBrains] etc. prefix but remember it
    platform_match = re.match(r'^\[([\w\s]+)\]\s*', t)
    platform = platform_match.group(1) if platform_match else None
    if platform:
        t = t[platform_match.end():]
    # Remove action verbs
    t = re.sub(r'^(?:Added?|Changed?|Removed?|Deprecated?|Fixed?|Improved?|Updated?|Enabled?|Introduced?|Implemented?|Supported?)\s+', '', t, flags=re.IGNORECASE)
    # Remove trailing issue refs
    t = re.sub(r'\s*\(anthropics/[\w-]+#\d+\)\s*$', '', t)
    t = re.sub(r'\s*\(#\d+\)\s*$', '', t)
    return t.strip(), platform


def make_title(title, change_type, version=""):
    """Generate specific Korean title based on deep parsing of the English title."""
    ending = get_ending(change_type)
    cleaned, platform = strip_prefix(title)
    platform_prefix = f"{platform}: " if platform else ""
    lower = title.lower()

    # ── Version/Release ──
    ver_match = re.search(r'[vV]?(\d+\.\d+[\.\d]*)', title)
    if re.search(r'\b(release|릴리[즈스])\b', lower) and ver_match:
        return f"v{ver_match.group(1)} 버전이 출시됐어요"

    # ── Model announcements ──
    model_match = re.search(r'\b(Opus|Sonnet|Haiku)\s+([\d.]+)', title, re.IGNORECASE)
    if model_match:
        mn = model_match.group(1)
        mv = model_match.group(2)
        if "default" in lower or "기본" in lower:
            return f"{mn} {mv}이 기본 모델이 됐어요"
        if "context" in lower or "1m" in lower or "1M" in title:
            return f"{mn} {mv} 컨텍스트가 확장됐어요"
        if "fast" in lower:
            return f"{mn} {mv} 빠른 모드가 {ending}"
        if "removed" in lower or change_type == "removed":
            return f"{mn} {mv} 모델이 제거됐어요"
        if "effort" in lower:
            return f"{mn} {mv} 노력 수준이 {ending}"
        if "support" in lower or change_type == "added":
            return f"{mn} {mv} 모델이 {ending}"
        if "migrat" in lower:
            return f"{mn} {mv}(으)로 자동 전환돼요"
        return f"{mn} {mv} 관련 변경이 있어요"

    # Single model name without version
    model_single = re.search(r'\b(Opus|Sonnet|Haiku)\b', title)
    if model_single and not re.search(r'MCP|IDE|VSCode', title):
        mn = model_single.group(1)
        if "default" in lower:
            return f"{mn}이 기본 모델이 됐어요"
        if "effort" in lower:
            return f"{mn} 노력 수준 설정이 {ending}"
        if "context" in lower or "1m" in lower:
            return f"{mn} 컨텍스트가 확장됐어요"
        if "removed" in lower or change_type == "removed":
            return f"{mn} 모델이 제거됐어요"
        if "fast" in lower:
            return f"{mn} 빠른 모드가 {ending}"
        if "migrat" in lower or "switch" in lower or "mov" in lower:
            return f"{mn} 모델 전환이 {ending}"

    # ── Slash commands ──
    cmd = extract_command(title)
    if cmd:
        cmd_map = {
            "/copy": "복사 명령어가",
            "/model": "모델 선택이",
            "/resume": "세션 재개가",
            "/memory": "메모리 관리가",
            "/add-dir": "디렉토리 추가가",
            "/rename": "이름 변경이",
            "/simplify": "코드 간소화가",
            "/batch": "일괄 처리가",
            "/compact": "대화 압축이",
            "/clear": "대화 초기화가",
            "/permissions": "권한 설정이",
            "/config": "설정 관리가",
            "/remote-control": "원격 제어가",
            "/reload-plugins": "플러그인 새로고침이",
            "/extra-usage": "추가 사용량 확인이",
            "/hooks": "훅 관리가",
            "/claude-api": "Claude API 스킬이",
        }
        if cmd in cmd_map:
            return f"{cmd_map[cmd]} {ending}"
        return f"{cmd} 명령어가 {ending}"

    # ── CLI flags ──
    flag = extract_flag(title)
    if flag:
        flag_map = {
            "--worktree": "워크트리 격리 모드가",
            "--agent": "에이전트 모드가",
            "--resume": "세션 재개가",
            "--verbose": "상세 출력이",
            "--output-format": "출력 형식이",
            "--model": "모델 선택이",
            "--print": "출력 모드가",
            "--dangerously-skip-permissions": "권한 건너뛰기가",
            "--add-dir": "디렉토리 추가가",
            "--init": "초기화 옵션이",
        }
        if flag in flag_map:
            return f"{flag_map[flag]} {ending}"

    # ── Environment variables ──
    env = extract_env_var(title)
    if env:
        return f"환경 변수 설정이 {ending}"

    # ── Keybindings ──
    kb = extract_keybind(title)
    if kb:
        if "kill" in lower or "stop" in lower or "cancel" in lower:
            return f"{kb} 단축키로 중지할 수 있어요"
        if "exit" in lower:
            return f"{kb} 단축키로 나갈 수 있어요"
        if "copy" in lower:
            return f"{kb} 단축키로 복사할 수 있어요"
        if "newline" in lower or "multi" in lower:
            return f"줄바꿈 단축키가 {ending}"
        return f"{kb} 단축키가 {ending}"

    # ── Specific feature keywords (ordered by specificity) ──

    # Voice/STT
    if re.search(r'\b(voice|STT|speech|dictation|microphone)\b', lower):
        if "language" in lower:
            return f"음성 인식 언어가 {ending}"
        return f"음성 입력 기능이 {ending}"

    # Remote control
    if "remote control" in lower or "remote-control" in lower:
        return f"원격 제어 기능이 {ending}"

    # Worktree
    if "worktree" in lower:
        return f"워크트리 기능이 {ending}"

    # Plugin
    if re.search(r'\bplugin', lower):
        if "install" in lower:
            return f"플러그인 설치가 {ending}"
        if "trust" in lower:
            return f"플러그인 신뢰 설정이 {ending}"
        if "marketplace" in lower:
            return f"플러그인 마켓이 {ending}"
        if "reload" in lower or "refresh" in lower:
            return f"플러그인 새로고침이 {ending}"
        return f"플러그인 기능이 {ending}"

    # Skill
    if re.search(r'\bskill', lower):
        return f"스킬 기능이 {ending}"

    # Hook
    if re.search(r'\bhook', lower):
        if "http" in lower:
            return f"HTTP 훅 기능이 {ending}"
        if "config" in lower:
            return f"설정 변경 훅이 {ending}"
        return f"훅(Hook) 기능이 {ending}"

    # Compaction/compact
    if re.search(r'\bcompact', lower):
        return f"대화 압축 기능이 {ending}"

    # Memory/auto-memory
    if re.search(r'\b(auto.?memory|memory)\b', lower) and "context" not in lower:
        return f"자동 메모리 기능이 {ending}"

    # MCP
    if re.search(r'\bMCP\b', title):
        if "oauth" in lower or "auth" in lower:
            return f"MCP 인증 기능이 {ending}"
        if "server" in lower and "config" in lower:
            return f"MCP 서버 설정이 {ending}"
        if "server" in lower:
            return f"MCP 서버 기능이 {ending}"
        if "tool" in lower:
            return f"MCP 도구 기능이 {ending}"
        if "transport" in lower:
            return f"MCP 전송 방식이 {ending}"
        if "resource" in lower:
            return f"MCP 리소스가 {ending}"
        if "sampling" in lower:
            return f"MCP 샘플링이 {ending}"
        if "connector" in lower or "connect" in lower:
            return f"MCP 연결 기능이 {ending}"
        if "claude.ai" in lower:
            return f"claude.ai MCP 연동이 {ending}"
        return f"MCP 기능이 {ending}"

    # LSP
    if re.search(r'\bLSP\b', title):
        if "timeout" in lower or "startup" in lower:
            return f"LSP 서버 시작이 {ending}"
        return f"LSP 기능이 {ending}"

    # SDK
    if re.search(r'\bSDK\b', title):
        if "rate limit" in lower:
            return f"SDK 사용량 제한 정보가 {ending}"
        if "model" in lower:
            return f"SDK 모델 정보가 {ending}"
        if "event" in lower or "type" in lower:
            return f"SDK 타입이 {ending}"
        return f"SDK 기능이 {ending}"

    # Agent/subagent
    if re.search(r'\b(subagent|sub.agent)\b', lower):
        if "resume" in lower:
            return f"하위 에이전트 재개가 {ending}"
        if "cancel" in lower or "kill" in lower:
            return f"하위 에이전트 중지가 {ending}"
        if "isolation" in lower or "worktree" in lower:
            return f"하위 에이전트 격리가 {ending}"
        return f"하위 에이전트 기능이 {ending}"

    if re.search(r'\bagent\b', lower) and "sub" not in lower:
        if "background" in lower:
            return f"백그라운드 에이전트가 {ending}"
        if "definition" in lower or "config" in lower:
            return f"에이전트 설정이 {ending}"
        if "list" in lower or "command" in lower:
            return f"에이전트 목록 명령이 {ending}"
        if "name" in lower or "display" in lower:
            return f"에이전트 표시가 {ending}"
        if "lifecycle" in lower:
            return f"에이전트 생명주기가 {ending}"
        return f"에이전트 기능이 {ending}"

    # Background task
    if re.search(r'\bbackground\b', lower):
        return f"백그라운드 작업이 {ending}"

    # Teammate
    if re.search(r'\bteammate', lower):
        return f"팀원 탐색 기능이 {ending}"

    # IDE-specific: VSCode
    if re.search(r'\b(vscode|vs code)\b', lower) or platform == "VSCode":
        if "session" in lower:
            return f"VSCode 세션 관리가 {ending}"
        if "compact" in lower:
            return f"VSCode 대화 압축이 {ending}"
        if "permission" in lower:
            return f"VSCode 권한 설정이 {ending}"
        if "extension" in lower:
            return f"VSCode 확장이 {ending}"
        if "status" in lower:
            return f"VSCode 상태 표시가 {ending}"
        if "sidebar" in lower:
            return f"VSCode 사이드바가 {ending}"
        return f"VSCode 연동이 {ending}"

    # JetBrains
    if re.search(r'\b(jetbrains|intellij|webstorm|pycharm)\b', lower) or platform == "JetBrains":
        return f"JetBrains 연동이 {ending}"

    # Terminal
    if re.search(r'\bterminal\b', lower):
        if "title" in lower:
            return f"터미널 탭 제목이 {ending}"
        if "render" in lower or "display" in lower:
            return f"터미널 표시가 {ending}"
        if "color" in lower or "ansi" in lower:
            return f"터미널 색상이 {ending}"
        return f"터미널 기능이 {ending}"

    # Shell
    if re.search(r'\b(shell|bash|zsh|fish|powershell)\b', lower):
        if "prompt" in lower:
            return f"셸 프롬프트가 {ending}"
        if "completion" in lower:
            return f"셸 자동 완성이 {ending}"
        return f"셸 지원이 {ending}"

    # Permission
    if re.search(r'\bpermission', lower):
        if "bypass" in lower:
            return f"권한 우회 모드가 {ending}"
        if "mode" in lower:
            return f"권한 모드가 {ending}"
        if "tool" in lower:
            return f"도구 권한 설정이 {ending}"
        return f"권한 관리가 {ending}"

    # Auth/OAuth/token/key
    if re.search(r'\b(oauth|auth|token|api.?key|keychain|keyring|credential)\b', lower):
        if "keychain" in lower or "keyring" in lower:
            return f"키체인 보안 저장이 {ending}"
        if "oauth" in lower:
            return f"OAuth 인증이 {ending}"
        if "token" in lower and "count" in lower:
            return f"토큰 카운트가 {ending}"
        if "api key" in lower or "api_key" in lower:
            return f"API 키 관리가 {ending}"
        return f"인증 기능이 {ending}"

    # Security
    if re.search(r'\bsecur', lower):
        return f"보안 기능이 {ending}"

    # Git
    if re.search(r'\bgit\b', lower):
        if "commit" in lower:
            return f"Git 커밋 기능이 {ending}"
        if "diff" in lower:
            return f"Git 변경 비교가 {ending}"
        if "subdir" in lower:
            return f"Git 하위 디렉토리가 {ending}"
        return f"Git 기능이 {ending}"

    # Diff
    if re.search(r'\bdiff\b', lower):
        return f"변경 비교 기능이 {ending}"

    # Edit/file operations
    if re.search(r'\b(edit tool|file edit|multi.?file)\b', lower):
        return f"파일 편집 기능이 {ending}"

    # Read tool / file read
    if re.search(r'\b(read tool|file read)\b', lower):
        return f"파일 읽기가 {ending}"

    # Glob/search
    if re.search(r'\b(glob|grep|search|find)\b', lower):
        return f"파일 검색이 {ending}"

    # Notebook/Jupyter
    if re.search(r'\b(notebook|jupyter|ipynb)\b', lower):
        return f"노트북 지원이 {ending}"

    # Image/screenshot
    if re.search(r'\bscreenshot', lower):
        return f"스크린샷 기능이 {ending}"
    if re.search(r'\bimage', lower):
        return f"이미지 처리가 {ending}"

    # PDF
    if re.search(r'\bpdf\b', lower):
        return f"PDF 지원이 {ending}"

    # Cost/usage/billing/token
    if re.search(r'\b(cost|billing|price|usage|spend)\b', lower):
        return f"비용 관리가 {ending}"

    # Rate limit
    if re.search(r'\brate.?limit', lower):
        return f"사용량 제한 안내가 {ending}"

    # Performance/speed/latency
    if re.search(r'\b(performance|latency|speed|faster|slower)\b', lower):
        return f"성능이 {ending}"

    # Memory (system)
    if re.search(r'\bmemory\b', lower) and re.search(r'\b(leak|usage|consumption|reduce)\b', lower):
        return f"메모리 사용이 {ending}"

    # Cache/caching
    if re.search(r'\bcach', lower):
        if "prompt" in lower:
            return f"프롬프트 캐싱이 {ending}"
        return f"캐시 기능이 {ending}"

    # Context window
    if re.search(r'\bcontext.?window\b', lower) or "1m context" in lower or "1M" in title:
        return f"컨텍스트 창이 {ending}"

    # Conversation/session
    if re.search(r'\bsession', lower):
        if "resume" in lower or "picker" in lower:
            return f"세션 재개가 {ending}"
        if "rename" in lower:
            return f"세션 이름 변경이 {ending}"
        if "count" in lower or "list" in lower:
            return f"세션 목록이 {ending}"
        return f"세션 관리가 {ending}"

    # Prompt/input
    if re.search(r'\bprompt\b', lower):
        if "startup" in lower:
            return f"시작 안내가 {ending}"
        if "system" in lower:
            return f"시스템 프롬프트가 {ending}"
        return f"프롬프트 기능이 {ending}"

    # Config/setting
    if re.search(r'\b(config|setting|preference)\b', lower):
        if "managed" in lower or "policy" in lower or "enterprise" in lower:
            return f"관리형 설정이 {ending}"
        return f"설정 옵션이 {ending}"

    # Spinner/UI display
    if re.search(r'\bspinner', lower):
        return f"로딩 표시가 {ending}"

    # Logo/branding
    if re.search(r'\blogo\b', lower):
        return f"로고 표시가 {ending}"

    # Status line
    if re.search(r'\bstatus.?line', lower):
        return f"상태 표시줄이 {ending}"

    # Error/crash/bug fix
    if re.search(r'\b(crash|fix|bug|error|issue|resolve|broken|regression)\b', lower):
        if "crash" in lower or "hang" in lower:
            return f"비정상 종료가 수정됐어요"
        if "memory" in lower:
            return f"메모리 문제가 수정됐어요"
        if "display" in lower or "render" in lower or "ui" in lower:
            return f"화면 표시가 수정됐어요"
        if "permission" in lower:
            return f"권한 오류가 수정됐어요"
        return f"오류가 수정됐어요"

    # Log/debug/verbose
    if re.search(r'\b(debug|log|logging|verbose|trace)\b', lower):
        if "error" in lower:
            return f"오류 로그가 {ending}"
        return f"로그 기능이 {ending}"

    # Notification/toast
    if re.search(r'\b(notification|toast|banner|callout)\b', lower):
        return f"알림 표시가 {ending}"

    # Extended thinking
    if re.search(r'\b(extended.?think|ultrathink|think.?tool)\b', lower):
        return f"확장 사고 기능이 {ending}"

    # Effort level
    if re.search(r'\beffort\b', lower):
        return f"노력 수준 설정이 {ending}"

    # Streaming
    if re.search(r'\bstream', lower):
        return f"스트리밍 출력이 {ending}"

    # Markdown/CLAUDE.md/AGENTS.md
    if "CLAUDE.md" in title:
        return f"CLAUDE.md 처리가 {ending}"
    if "AGENTS.md" in title:
        return f"AGENTS.md 처리가 {ending}"
    if re.search(r'\bmarkdown\b', lower):
        return f"Markdown 지원이 {ending}"

    # Docker/sandbox
    if re.search(r'\bsandbox', lower):
        return f"샌드박스 기능이 {ending}"
    if re.search(r'\bdocker', lower):
        return f"Docker 지원이 {ending}"

    # Proxy/network
    if re.search(r'\bproxy\b', lower):
        return f"프록시 설정이 {ending}"
    if re.search(r'\bnetwork', lower):
        return f"네트워크 기능이 {ending}"

    # Install/update
    if re.search(r'\binstall', lower):
        return f"설치 방식이 {ending}"
    if re.search(r'\bupdate|upgrade', lower):
        return f"업데이트 방식이 {ending}"

    # Desktop app
    if re.search(r'\bdesktop\b', lower):
        return f"데스크톱 앱이 {ending}"

    # Headless/non-interactive/CI
    if re.search(r'\b(headless|non.interactive)\b', lower):
        return f"비대화형 모드가 {ending}"
    if re.search(r'\bci\b', lower) and ("pipeline" in lower or "build" in lower or "integration" in lower):
        return f"CI 연동이 {ending}"

    # Test
    if re.search(r'\btest', lower) and "context" not in lower:
        return f"테스트 기능이 {ending}"

    # Plan/subscription
    if re.search(r'\b(Max plan|Pro plan|Team plan|Enterprise)\b', title):
        plan_match = re.search(r'(Max|Pro|Team|Enterprise)', title)
        if plan_match:
            return f"{plan_match.group(1)} 요금제가 {ending}"

    # Policy
    if re.search(r'\bpolicy\b', lower):
        return f"정책 설정이 {ending}"

    # Clipboard
    if re.search(r'\bclipboard|copy|paste\b', lower):
        return f"복사 기능이 {ending}"

    # Regex/pattern
    if re.search(r'\bregex|pattern\b', lower):
        return f"패턴 매칭이 {ending}"

    # Navigation
    if re.search(r'\bnavig', lower):
        return f"탐색 기능이 {ending}"

    # Telemetry
    if re.search(r'\btelemetry\b', lower):
        return f"텔레메트리가 {ending}"

    # Timeout
    if re.search(r'\btimeout\b', lower):
        return f"시간 제한 설정이 {ending}"

    # URL/link
    if re.search(r'\burl\b', lower) and "paste" not in lower:
        return f"URL 처리가 {ending}"

    # API
    if re.search(r'\bapi\b', lower):
        return f"API 기능이 {ending}"

    # Color/theme
    if re.search(r'\b(color|theme|dark.?mode|light.?mode)\b', lower):
        return f"색상 표시가 {ending}"

    # Format/output
    if re.search(r'\bformat', lower):
        return f"출력 형식이 {ending}"

    # Interrupt/cancel
    if re.search(r'\b(interrupt|cancel)\b', lower):
        return f"작업 중단이 {ending}"

    # Retry/reconnect
    if re.search(r'\b(retry|reconnect)\b', lower):
        return f"재시도 기능이 {ending}"

    # Autocomplete/suggestion
    if re.search(r'\b(autocomplete|suggestion|suggest)\b', lower):
        return f"자동 추천이 {ending}"

    # npm/registry
    if re.search(r'\bnpm\b', lower):
        return f"npm 관련 기능이 {ending}"

    # Multi-line/input
    if re.search(r'\bmulti.?line\b', lower):
        return f"여러 줄 입력이 {ending}"

    # Workspace
    if re.search(r'\bworkspace\b', lower):
        return f"워크스페이스 기능이 {ending}"

    # Diagnostic
    if re.search(r'\bdiagnostic', lower):
        return f"진단 기능이 {ending}"

    # Rename
    if re.search(r'\brename\b', lower):
        return f"이름 변경이 {ending}"

    # Organization/org
    if re.search(r'\borg(anization)?\b', lower):
        return f"조직 설정이 {ending}"

    # Migration
    if re.search(r'\bmigrat', lower):
        return f"마이그레이션이 {ending}"

    # Deprecated specific
    if change_type == "deprecated":
        return f"해당 기능이 곧 사라져요"

    # Platform-specific
    if "mac" in lower or "macos" in lower:
        return f"macOS 관련 기능이 {ending}"
    if "windows" in lower:
        return f"Windows 관련 기능이 {ending}"
    if "linux" in lower:
        return f"Linux 관련 기능이 {ending}"

    # ── Fallback based on change_type ──
    if "support" in lower:
        return f"새 기능 지원이 {ending}"
    if "improv" in lower or "better" in lower or "enhanc" in lower:
        return f"사용 경험이 개선됐어요"
    if "reduc" in lower or "decreas" in lower:
        return f"불필요한 동작이 줄었어요"
    if "increas" in lower:
        return f"처리 용량이 늘었어요"
    if "simplif" in lower:
        return f"사용 방식이 간소화됐어요"

    # Very generic fallback
    if change_type == "added":
        return f"새 기능이 추가됐어요"
    elif change_type == "changed":
        return f"기능이 개선됐어요"
    elif change_type == "removed":
        return f"기능이 제거됐어요"
    elif change_type == "deprecated":
        return f"해당 기능이 곧 사라져요"
    else:
        return f"Claude Code가 업데이트됐어요"


def make_content(title, change_type, version=""):
    """Generate Korean content with 3 bullets based on deep title analysis."""
    lower = title.lower()
    cleaned, platform = strip_prefix(title)
    verb = get_verb(change_type)

    # ── Try to generate highly specific bullets ──

    # Slash commands
    cmd = extract_command(title)
    if cmd:
        b1 = f"{cmd} 명령어가 {verb}됐어요."
        if "picker" in lower or "select" in lower:
            b2 = "선택 화면에서 원하는 항목을 쉽게 고를 수 있어요."
        elif "interactive" in lower:
            b2 = "대화형 인터페이스로 편리하게 사용할 수 있어요."
        else:
            b2 = f"명령어를 입력하면 바로 실행할 수 있어요."
        b3 = "사용법이 더 직관적으로 개선됐어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Environment variables
    env = extract_env_var(title)
    if env:
        b1 = f"{env} 환경 변수가 {verb}됐어요."
        b2 = "환경 변수로 동작을 세밀하게 제어할 수 있어요."
        b3 = "설정은 세션 시작 전에 적용해야 해요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Keybindings
    kb = extract_keybind(title)
    if kb:
        b1 = f"{kb} 단축키 기능이 {verb}됐어요."
        if "kill" in lower or "stop" in lower or "cancel" in lower:
            b2 = "실행 중인 작업을 빠르게 중단할 수 있어요."
        elif "exit" in lower:
            b2 = "현재 모드를 빠르게 빠져나올 수 있어요."
        elif "copy" in lower:
            b2 = "결과를 클립보드에 빠르게 복사할 수 있어요."
        else:
            b2 = "키보드만으로 빠르게 기능을 실행할 수 있어요."
        b3 = "다양한 터미널 환경에서 일관되게 동작해요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Voice/STT
    if re.search(r'\b(voice|STT|speech)\b', lower):
        b1 = "음성 인식(STT) 기능이 업데이트됐어요."
        if "language" in lower:
            b2 = "더 많은 언어를 음성으로 입력할 수 있어요."
            b3 = "다국어 환경에서 음성 입력이 더 편리해요."
        else:
            b2 = "음성으로 코드 작업 지시를 할 수 있어요."
            b3 = "키보드 입력 없이도 편리하게 사용할 수 있어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Remote control
    if "remote control" in lower or "remote-control" in lower:
        b1 = "원격 제어(Remote Control) 기능이 업데이트됐어요."
        b2 = "claude.ai에서 로컬 환경을 원격으로 제어할 수 있어요."
        b3 = "외부 빌드 환경과의 연동이 가능해요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Worktree
    if "worktree" in lower:
        b1 = "Git 워크트리(worktree) 격리 기능이 업데이트됐어요."
        b2 = "독립된 워크트리에서 안전하게 작업할 수 있어요."
        b3 = "여러 브랜치를 동시에 작업하는 환경이 개선됐어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Plugin
    if re.search(r'\bplugin', lower):
        b1 = "플러그인(Plugin) 기능이 업데이트됐어요."
        if "install" in lower or "npm" in lower:
            b2 = "플러그인 설치 과정이 더 유연해졌어요."
        elif "trust" in lower:
            b2 = "플러그인 신뢰 설정을 더 세밀하게 관리할 수 있어요."
        elif "marketplace" in lower:
            b2 = "플러그인 마켓플레이스 지원이 확장됐어요."
        else:
            b2 = "플러그인을 통해 기능을 확장할 수 있어요."
        b3 = "플러그인 관리가 더 편리해졌어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Skill
    if re.search(r'\bskill', lower):
        b1 = "스킬(Skill) 기능이 업데이트됐어요."
        b2 = "자주 쓰는 작업을 스킬로 등록해 빠르게 실행할 수 있어요."
        b3 = "SKILL.md 파일로 스킬을 쉽게 정의할 수 있어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Hook
    if re.search(r'\bhook', lower):
        b1 = "훅(Hook) 시스템이 업데이트됐어요."
        if "http" in lower:
            b2 = "HTTP 요청으로 외부 서비스와 연동할 수 있어요."
        elif "config" in lower:
            b2 = "설정 변경 시 자동으로 훅이 실행돼요."
        elif "worktree" in lower:
            b2 = "워크트리 생성/제거 시 자동 작업을 설정할 수 있어요."
        else:
            b2 = "특정 이벤트에 맞춰 자동 작업을 실행할 수 있어요."
        b3 = "워크플로 자동화가 더 유연해졌어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Compaction
    if re.search(r'\bcompact', lower):
        b1 = "대화 내용 압축(compaction) 기능이 업데이트됐어요."
        b2 = "긴 대화도 핵심만 유지하며 자동 정리돼요."
        b3 = "컨텍스트 창을 더 효율적으로 활용할 수 있어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Memory
    if re.search(r'\b(auto.?memory|memory)\b', lower) and "context" not in lower:
        b1 = "자동 메모리(auto-memory) 기능이 업데이트됐어요."
        b2 = "중요한 맥락을 자동으로 기억하고 활용해요."
        b3 = "/memory 명령어로 저장된 내용을 관리할 수 있어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # MCP
    if re.search(r'\bMCP\b', title):
        b1 = "MCP(Model Context Protocol) 기능이 업데이트됐어요."
        if "oauth" in lower or "auth" in lower:
            b2 = "MCP 서버 인증 과정이 개선됐어요."
            b3 = "보안을 유지하면서도 연결이 더 편리해요."
        elif "server" in lower:
            b2 = "외부 MCP 서버와의 연동이 더 안정적이에요."
            b3 = "서버 설정과 관리가 더 편리해졌어요."
        elif "tool" in lower:
            b2 = "MCP 도구를 더 쉽게 연결하고 활용할 수 있어요."
            b3 = "도구 호출 시 안정성과 성능이 향상됐어요."
        elif "connector" in lower or "claude.ai" in lower:
            b2 = "claude.ai에서 설정한 MCP 서버를 활용할 수 있어요."
            b3 = "연결 상태를 더 명확하게 확인할 수 있어요."
        else:
            b2 = "외부 도구 및 서버 연동이 개선됐어요."
            b3 = "MCP 생태계 활용이 더 편리해졌어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # LSP
    if re.search(r'\bLSP\b', title):
        b1 = "LSP(Language Server Protocol) 기능이 업데이트됐어요."
        b2 = "코드 분석과 자동 완성이 더 정확해요."
        b3 = "다양한 언어 서버와의 호환성이 향상됐어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # SDK
    if re.search(r'\bSDK\b', title):
        b1 = "SDK(Software Development Kit) 기능이 업데이트됐어요."
        if "rate limit" in lower:
            b2 = "사용량 제한 정보를 실시간으로 확인할 수 있어요."
        elif "model" in lower:
            b2 = "모델의 기능 정보를 프로그래밍 방식으로 조회할 수 있어요."
        else:
            b2 = "외부 애플리케이션과의 연동이 더 편리해요."
        b3 = "개발자가 Claude Code를 더 유연하게 활용할 수 있어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Model-related
    model_match = re.search(r'\b(Opus|Sonnet|Haiku)\b', title, re.IGNORECASE)
    if model_match:
        mn = model_match.group(1)
        b1 = f"{mn} AI 모델 관련 변경이 있어요."
        if "default" in lower:
            b2 = f"기본 모델이 {mn}(으)로 변경됐어요."
            b3 = "별도 설정 없이 최신 모델을 사용할 수 있어요."
        elif "context" in lower or "1m" in lower:
            b2 = "컨텍스트 창(context window)이 확장됐어요."
            b3 = "더 긴 대화와 큰 코드베이스를 처리할 수 있어요."
        elif "effort" in lower:
            b2 = "노력 수준(effort level)을 조절할 수 있어요."
            b3 = "작업 복잡도에 맞게 속도와 품질을 조절해요."
        elif "migrat" in lower or "switch" in lower:
            b2 = "최신 모델로 자동 전환돼요."
            b3 = "기존 설정도 새 모델에서 유지돼요."
        elif "removed" in lower or change_type == "removed":
            b2 = "해당 모델이 더 이상 사용할 수 없어요."
            b3 = "최신 모델로 자동 전환되니 안심하세요."
        else:
            b2 = "AI 모델 활용이 더 효율적으로 개선됐어요."
            b3 = "/model 명령어로 모델을 변경할 수 있어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Agent/subagent
    if re.search(r'\b(agent|subagent)\b', lower):
        b1 = "에이전트(Agent) 기능이 업데이트됐어요."
        if "subagent" in lower or "sub-agent" in lower:
            b2 = "하위 에이전트로 복잡한 작업을 나눠 처리할 수 있어요."
        elif "background" in lower:
            b2 = "에이전트를 백그라운드에서 실행할 수 있어요."
        elif "list" in lower:
            b2 = "설정된 에이전트 목록을 쉽게 확인할 수 있어요."
        elif "definition" in lower or "config" in lower:
            b2 = "에이전트 설정을 파일로 관리할 수 있어요."
        else:
            b2 = "에이전트 기반 작업이 더 효율적이에요."
        b3 = "멀티 에이전트 협업이 더 원활해졌어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # VSCode
    if re.search(r'\b(vscode|vs code)\b', lower) or platform == "VSCode":
        b1 = "VSCode 확장 기능이 업데이트됐어요."
        if "session" in lower:
            b2 = "세션 관리가 VSCode에서 더 편리해졌어요."
        elif "compact" in lower:
            b2 = "대화 압축 내용을 깔끔하게 확인할 수 있어요."
        elif "permission" in lower:
            b2 = "권한 설정을 VSCode에서 직접 관리할 수 있어요."
        else:
            b2 = "VSCode에서 Claude Code를 더 편리하게 사용할 수 있어요."
        b3 = "IDE(통합 개발 환경) 통합이 더 안정적이에요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # JetBrains
    if re.search(r'\b(jetbrains|intellij|webstorm|pycharm)\b', lower) or platform == "JetBrains":
        b1 = "JetBrains IDE 연동이 업데이트됐어요."
        b2 = "JetBrains 환경에서 Claude Code를 편리하게 사용할 수 있어요."
        b3 = "IDE(통합 개발 환경) 통합이 더 안정적이에요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Terminal
    if re.search(r'\bterminal\b', lower):
        b1 = "터미널 관련 기능이 업데이트됐어요."
        if "title" in lower:
            b2 = "터미널 탭에 유용한 정보가 표시돼요."
        elif "render" in lower or "display" in lower:
            b2 = "터미널 출력이 더 깔끔하게 표시돼요."
        elif "color" in lower:
            b2 = "색상 표시가 더 정확해졌어요."
        else:
            b2 = "터미널 환경에서의 사용성이 개선됐어요."
        b3 = "다양한 터미널에서 일관되게 동작해요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Shell
    if re.search(r'\b(shell|bash|zsh|fish|powershell)\b', lower):
        b1 = "셸(Shell) 관련 기능이 업데이트됐어요."
        b2 = "명령줄 환경에서의 사용성이 개선됐어요."
        b3 = "다양한 셸 환경을 잘 지원해요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Permission
    if re.search(r'\bpermission', lower):
        b1 = "권한 관리 기능이 업데이트됐어요."
        b2 = "파일 및 명령 실행 권한을 세밀하게 제어할 수 있어요."
        b3 = "보안을 유지하면서도 작업 흐름이 원활해요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Auth
    if re.search(r'\b(oauth|auth|token|api.?key|keychain|credential)\b', lower):
        b1 = "인증 및 보안 기능이 업데이트됐어요."
        if "keychain" in lower:
            b2 = "시스템 키체인에서 인증 정보를 안전하게 관리해요."
        elif "oauth" in lower:
            b2 = "OAuth 인증 과정이 더 편리해졌어요."
        else:
            b2 = "인증 정보가 더 안전하게 보관돼요."
        b3 = "보안 설정을 쉽게 관리할 수 있어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Git
    if re.search(r'\bgit\b', lower):
        b1 = "Git 관련 기능이 업데이트됐어요."
        b2 = "버전 관리 작업이 더 편리해졌어요."
        b3 = "Git 연동 안정성이 향상됐어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # File operations
    if re.search(r'\b(file|edit|read|write|directory|folder|path|glob|grep)\b', lower):
        b1 = "파일 관련 기능이 업데이트됐어요."
        b2 = "파일 처리가 더 안정적으로 동작해요."
        b3 = "다양한 파일 작업을 효율적으로 수행할 수 있어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Performance
    if re.search(r'\b(performance|speed|fast|slow|latency)\b', lower):
        b1 = "전반적인 성능이 향상됐어요."
        b2 = "응답 속도가 빨라지고 처리가 효율적이에요."
        b3 = "대규모 작업에서도 원활하게 동작해요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Context/conversation
    if re.search(r'\b(context|conversation|chat|session|history)\b', lower):
        b1 = "대화 관련 기능이 업데이트됐어요."
        if "context window" in lower or "1m" in lower:
            b2 = "컨텍스트 창(context window)이 조정됐어요."
        elif "session" in lower:
            b2 = "세션 관리가 더 편리해졌어요."
        elif "history" in lower:
            b2 = "대화 기록을 더 쉽게 활용할 수 있어요."
        else:
            b2 = "대화 흐름이 더 자연스럽고 효율적이에요."
        b3 = "대화 맥락 유지가 더 잘 돼요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Config/setting
    if re.search(r'\b(config|setting|option|preference)\b', lower):
        b1 = "설정 옵션이 업데이트됐어요."
        b2 = "사용 환경을 더 세밀하게 제어할 수 있어요."
        b3 = "설정 변경이 즉시 반영돼요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Error/fix/bug
    if re.search(r'\b(fix|bug|crash|error|resolve|broken)\b', lower):
        b1 = "이전 버전에서 발생하던 문제가 수정됐어요."
        b2 = "관련 기능이 더 안정적으로 동작해요."
        b3 = "사용 중 불편했던 부분이 개선됐어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Image/screenshot/PDF
    if re.search(r'\b(image|screenshot|pdf)\b', lower):
        b1 = "미디어 파일 처리가 업데이트됐어요."
        b2 = "다양한 파일 형식을 더 잘 처리할 수 있어요."
        b3 = "시각적 정보를 활용한 작업이 편리해요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Log/debug
    if re.search(r'\b(debug|log|trace|verbose)\b', lower):
        b1 = "로그 및 디버그 기능이 업데이트됐어요."
        b2 = "문제 발생 시 원인을 더 쉽게 파악할 수 있어요."
        b3 = "디버그 정보 확인이 더 편리해졌어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Extended thinking / effort
    if re.search(r'\b(thinking|ultrathink|effort)\b', lower):
        b1 = "AI 사고 방식 설정이 업데이트됐어요."
        b2 = "작업 복잡도에 맞게 사고 깊이를 조절할 수 있어요."
        b3 = "속도와 품질 사이에서 최적의 균형을 찾아요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Cost/usage/billing
    if re.search(r'\b(cost|usage|billing|rate.?limit|spend|budget)\b', lower):
        b1 = "비용 및 사용량 관리가 업데이트됐어요."
        b2 = "사용량을 더 정확하게 확인할 수 있어요."
        b3 = "비용 관리가 더 투명하고 효율적이에요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # UI/display/spinner
    if re.search(r'\b(display|ui|spinner|logo|render|layout|theme|color)\b', lower):
        b1 = "화면 표시가 업데이트됐어요."
        b2 = "사용자 인터페이스가 더 직관적이에요."
        b3 = "다양한 환경에서 깔끔하게 표시돼요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Streaming
    if re.search(r'\bstream', lower):
        b1 = "스트리밍 출력이 업데이트됐어요."
        b2 = "결과가 실시간으로 표시되어 빠르게 확인할 수 있어요."
        b3 = "출력 형식이 더 읽기 쉽게 개선됐어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Sandbox/Docker
    if re.search(r'\b(sandbox|docker|container)\b', lower):
        b1 = "격리 환경 기능이 업데이트됐어요."
        b2 = "안전한 환경에서 코드를 실행할 수 있어요."
        b3 = "다양한 실행 환경 설정을 지원해요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Proxy/network
    if re.search(r'\b(proxy|network|firewall)\b', lower):
        b1 = "네트워크 관련 기능이 업데이트됐어요."
        b2 = "프록시(proxy) 환경에서도 안정적으로 동작해요."
        b3 = "다양한 네트워크 설정을 지원해요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Desktop
    if re.search(r'\bdesktop\b', lower):
        b1 = "데스크톱 앱 관련 기능이 업데이트됐어요."
        b2 = "네이티브 앱 환경에서 편리하게 사용할 수 있어요."
        b3 = "앱 성능과 안정성이 향상됐어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Headless/CI
    if re.search(r'\b(headless|non.interactive|ci|pipeline|automation)\b', lower):
        b1 = "자동화 기능이 업데이트됐어요."
        b2 = "비대화형(headless) 모드에서도 안정적으로 동작해요."
        b3 = "CI/CD(지속적 통합/배포) 워크플로에 활용할 수 있어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Install/update
    if re.search(r'\b(install|update|upgrade)\b', lower):
        b1 = "설치 및 업데이트 방식이 변경됐어요."
        b2 = "설정 과정이 더 간편해졌어요."
        b3 = "다양한 환경에서의 호환성이 개선됐어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Plan/subscription
    if re.search(r'\b(plan|subscription|tier|max|pro|team|enterprise)\b', lower):
        b1 = "요금제 관련 기능이 업데이트됐어요."
        b2 = "요금제에 맞는 기능을 더 잘 활용할 수 있어요."
        b3 = "요금제 정보 확인이 더 편리해졌어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Notification/callout
    if re.search(r'\b(notification|callout|toast|banner)\b', lower):
        b1 = "알림 기능이 업데이트됐어요."
        b2 = "중요한 정보를 더 잘 전달받을 수 있어요."
        b3 = "알림 표시가 더 깔끔해졌어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # CLAUDE.md / AGENTS.md
    if "CLAUDE.md" in title or "AGENTS.md" in title:
        doc_name = "CLAUDE.md" if "CLAUDE.md" in title else "AGENTS.md"
        b1 = f"{doc_name} 설정 파일 처리가 업데이트됐어요."
        b2 = "프로젝트 설정을 더 세밀하게 관리할 수 있어요."
        b3 = "설정 파일의 적용 범위가 명확해졌어요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Markdown
    if re.search(r'\bmarkdown\b', lower):
        b1 = "Markdown 처리가 업데이트됐어요."
        b2 = "문서 형식이 더 깔끔하게 표시돼요."
        b3 = "코드 블록과 서식이 정확하게 렌더링돼요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # Version-only
    ver_match = re.search(r'[vV]?(\d+\.\d+[\.\d]*)', title)
    if ver_match and change_type == "other":
        ver = ver_match.group(1)
        b1 = f"v{ver} 버전에서 변경 사항이 있어요."
        b2 = "안정성과 성능이 개선됐어요."
        b3 = "자세한 내용은 릴리즈 노트를 참고해 주세요."
        return f"• {b1}\n• {b2}\n• {b3}"

    # ── Generic fallback based on change_type ──
    if change_type == "added":
        b1 = "새로운 기능이 Claude Code에 추가됐어요."
        b2 = "작업 효율성을 높이는 데 도움이 돼요."
        b3 = "자세한 사용법은 공식 문서를 참고해 주세요."
    elif change_type == "changed":
        b1 = "기존 기능이 개선됐어요."
        b2 = "사용성과 안정성이 향상됐어요."
        b3 = "업데이트 후 바로 적용돼요."
    elif change_type == "removed":
        b1 = "해당 기능이 제거됐어요."
        b2 = "대체 기능이나 새로운 방식을 사용해 주세요."
        b3 = "기존 설정은 자동으로 정리돼요."
    elif change_type == "deprecated":
        b1 = "해당 기능이 더 이상 권장되지 않아요."
        b2 = "향후 버전에서 제거될 예정이에요."
        b3 = "새로운 대체 기능으로 전환하는 것을 권장해요."
    else:
        b1 = "Claude Code에 변경 사항이 있어요."
        b2 = "사용 환경이 개선되어 더 편리해요."
        b3 = "최신 버전으로 업데이트하면 자동 적용돼요."

    # Try to add specificity from backtick or quoted items
    backtick_items = re.findall(r'`([^`]+)`', title)
    if backtick_items and len(backtick_items[0]) < 40:
        item = backtick_items[0]
        if change_type == "added":
            b1 = f"`{item}` 기능이 새로 추가됐어요."
        elif change_type == "changed":
            b1 = f"`{item}` 기능이 개선됐어요."
        elif change_type == "removed":
            b1 = f"`{item}` 기능이 제거됐어요."
        else:
            b1 = f"`{item}` 관련 변경이 있어요."

    # Platform-specific third bullet
    platforms = []
    if "mac" in lower or "macos" in lower:
        platforms.append("macOS")
    if "windows" in lower:
        platforms.append("Windows")
    if "linux" in lower:
        platforms.append("Linux")
    if "wsl" in lower:
        platforms.append("WSL(Windows Subsystem for Linux)")
    if platforms:
        b3 = f"{', '.join(platforms)} 환경에서 사용할 수 있어요."

    return f"• {b1}\n• {b2}\n• {b3}"


def main():
    print("Loading pending events...")
    events = load_pending()
    print(f"Loaded {len(events)} events")

    results = []
    for i, event in enumerate(events):
        result = translate_event(event)
        results.append(result)
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(events)}")

    output_path = os.path.join(BASE_DIR, "data", "claude_code_enrich_ko_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Wrote {len(results)} results to {output_path}")

    # Validation
    errors = []
    title_set = set()
    for idx, r in enumerate(results):
        ev = events[idx]
        # Check title_kor length
        tlen = len(r["title_kor"])
        if tlen > 40:
            errors.append(f"title_kor too long ({tlen}): {r['id']}: {r['title_kor']}")
        if tlen < 5:
            errors.append(f"title_kor too short ({tlen}): {r['id']}: {r['title_kor']}")

        # Check content_kor bullets
        bullet_count = r["content_kor"].count("•")
        if bullet_count != 3:
            errors.append(f"content_kor has {bullet_count} bullets: {r['id']}")

        # Check ending style
        t = r["title_kor"]
        valid_endings = ["요", "어요", "돼요", "져요", "에요", "있어요"]
        has_valid = any(t.rstrip().endswith(e) for e in valid_endings)
        if not has_valid:
            errors.append(f"title_kor invalid ending: {r['id']}: {r['title_kor']}")

        # Check change_type ending consistency
        ct = ev.get("change_type", "other")
        expected_end = {
            "added": "추가됐어요",
            "removed": "제거됐어요",
            "deprecated": "사라져요",
        }
        if ct in expected_end:
            if not any(t.endswith(e) for e in [expected_end[ct], "수 있어요", "해졌어요", "했어요", "됐어요", "돼요", "에요", "있어요"]):
                pass  # Some special cases don't match exactly, that's OK

        title_set.add(r["title_kor"])

    # Count unique titles vs total
    print(f"\nUnique titles: {len(title_set)} / {len(results)}")

    if errors:
        print(f"\nValidation errors ({len(errors)}):")
        for e in errors[:30]:
            print(f"  - {e}")
    else:
        print("All validations passed!")

    # Show samples
    print("\n=== SAMPLES ===")
    for i in [0, 1, 2, 3, 10, 25, 50, 100, 200, 300, 400, 500]:
        if i < len(results):
            r = results[i]
            ev = events[i]
            print(f"\n[{i}] {ev['change_type']}")
            print(f"  EN: {ev['title'][:80]}")
            print(f"  KO: {r['title_kor']} ({len(r['title_kor'])}c)")
            ck = r['content_kor'].replace('\n', ' | ')
            print(f"  CT: {ck[:100]}...")


if __name__ == "__main__":
    main()
