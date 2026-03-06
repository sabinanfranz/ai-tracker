# CCOS MVP Template

토이 프로젝트를 빠르게 찍어내기 위한 Claude Code 템플릿 레포.

## 빠른 시작

### 1. 실행 (Windows PowerShell)

```powershell
# 방법 1: 스크립트 사용
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1

# 방법 2: 직접 실행
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

브라우저에서 **http://127.0.0.1:8000** 접속.

### 2. 테스트

```bash
python -m pytest tests/ -x -q
```

### 3. MVP 워크플로우 (Claude Code)

```
# 새 MVP 기획 (PLAN)
/mvp-new 반려동물 산책 일지를 기록하고 통계를 보여주는 웹앱

# 백로그 1개 구현 (APPLY)
/mvp-next

# 로컬 실행 & 스모크 테스트
/mvp-demo
```

또는 에이전트 모드로:
```
claude --agent mvp-coordinator
```

## 구조

```
ccos-mvp-template/
├── .claude/
│   ├── agents/       # 7개 서브에이전트 (coordinator, pm, ux, be, fe, llm, qa)
│   └── skills/       # 3개 스킬 (mvp-new, mvp-next, mvp-demo)
├── apps/
│   ├── api/          # FastAPI 백엔드 (main.py)
│   ├── web/          # HTML/CSS/JS 프론트엔드
│   └── llm/          # LangGraph 오케스트레이션 (mock 기본)
├── docs/             # 기획 · 설계 · 테스트 문서
├── tests/            # 테스트 코드
├── data/             # SQLite DB (gitignore 대상)
├── scripts/          # dev.ps1 실행 스크립트
├── requirements.txt  # Python 의존성
├── CLAUDE.md         # 프로젝트 규칙 · 워크플로우
└── README.md
```

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Frontend | HTML / CSS / JS (바닐라) |
| Backend | FastAPI (Python) |
| Database | SQLite |
| LLM | LangGraph (mock 기본, 키 설정 시 실제 호출) |

## 에이전트 & 스킬

### 에이전트 (`.claude/agents/`)

| 에이전트 | 역할 |
|----------|------|
| `mvp-coordinator` | 전체 흐름 오케스트레이션 (PLAN/APPLY) |
| `product-manager` | PRD + 백로그 작성 |
| `ux-designer` | UX 플로우 + ASCII 와이어프레임 |
| `backend-dev` | FastAPI + SQLite 구현 |
| `frontend-dev` | HTML/CSS/JS 구현 |
| `llm-engineer` | LangGraph 파이프라인 |
| `qa-tester` | 테스트 계획 + 체크리스트 |

### 스킬 (`.claude/skills/`)

| 스킬 | 용도 |
|------|------|
| `/mvp-new <아이디어>` | MVP 한 줄 → 기획 문서 일괄 생성 |
| `/mvp-next` | 백로그 최상단 1개 구현 |
| `/mvp-demo` | 로컬 실행 + 스모크 체크 |

## LLM 키 설정 (선택)

mock 모드가 기본입니다. 실제 LLM을 사용하려면:

```bash
# .env 파일에 추가
OPENAI_API_KEY=sk-...
# 또는
ANTHROPIC_API_KEY=sk-ant-...
```
