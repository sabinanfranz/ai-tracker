# 30 — Architecture

## 시스템 개요

```
┌──────────────────────────────────────────────────────────┐
│                      Browser (Client)                     │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  apps/web/  (바닐라 HTML/CSS/JS)                     │  │
│  │  - index.html (단일 페이지, 멀티레일 타임라인)       │  │
│  │  - css/style.css                                     │  │
│  │  - js/ (api, card, filters, timeline, app)           │  │
│  └───────────────────────┬─────────────────────────────┘  │
└──────────────────────────┼────────────────────────────────┘
                           │ HTTP (JSON)
┌──────────────────────────┼────────────────────────────────┐
│  FastAPI Server          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐  │
│  │  apps/api/                                           │  │
│  │  ├── main.py           (FastAPI app + CORS + static) │  │
│  │  ├── routers/                                        │  │
│  │  │   ├── events.py     (GET /api/events, /{id})      │  │
│  │  │   └── meta.py       (GET /api/products, /tags)    │  │
│  │  ├── database.py       (SQLite 연결 + 테이블 생성)   │  │
│  │  ├── schemas.py        (Pydantic response schemas)   │  │
│  │  └── services/                                       │  │
│  │      └── scorer.py    (규칙 기반 Severity 점수)      │  │
│  └─────────────────────────────────────────────────────┘  │
│                           │                                │
│  ┌────────────────────────▼────────────────────────────┐  │
│  │  data/tracker.db  (SQLite)                           │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│  데이터 수집 (Claude Code 기반 — 사용자가 직접 실행)       │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  scripts/collect.py                                  │  │
│  │  - fetch_source() / fetch_all_sources()             │  │
│  │  - get_existing_events() / check_duplicate()        │  │
│  │  - insert_event() / insert_events()                 │  │
│  │  - get_snapshot_status()                             │  │
│  └───────────────────────┬─────────────────────────────┘  │
│                           │                                │
│  data/snapshots/          │  (HTML/MD 스냅샷 파일 저장)    │
│  - chatgpt_latest.html   │                                │
│  - gemini_latest.html    │                                │
│  - codex_latest.html     │                                │
│  - claude_code_latest.md │                                │
└───────────────────────────────────────────────────────────┘
```

## 기술 스택

| 레이어 | 기술 | 비고 |
|--------|------|------|
| Frontend | HTML / CSS / JS (바닐라) | 프레임워크 없음, fetch API 사용 |
| Backend | FastAPI (Python 3.11+) | uvicorn, CORS middleware |
| Database | SQLite | 파일: `data/tracker.db` |
| HTTP Client | httpx (sync) | 소스 페이지 다운로드 |
| 파싱 | Claude Code (AI) | 소스 내용 이해 + 이벤트 추출 |
| LLM | 미사용 (MVP) | v1.1에서 LangGraph 도입 예정 |
| 배포 | Railway | SQLite 영속성: 볼륨 마운트 |

## DB 스키마

### update_event

```sql
CREATE TABLE update_event (
    id              TEXT PRIMARY KEY,           -- UUID v4
    product         TEXT NOT NULL,              -- chatgpt | gemini | codex | claude_code
    component       TEXT NOT NULL DEFAULT 'default',
    event_date      TEXT NOT NULL,              -- YYYY-MM-DD
    detected_at     TEXT NOT NULL,              -- ISO 8601
    title           TEXT NOT NULL,
    summary_ko      TEXT NOT NULL,
    summary_en      TEXT,
    tags            TEXT NOT NULL DEFAULT '[]', -- JSON array
    severity        INTEGER NOT NULL DEFAULT 1, -- 1~5
    source_url      TEXT NOT NULL,
    evidence_excerpt TEXT NOT NULL DEFAULT '[]',-- JSON array of strings
    raw_ref         TEXT NOT NULL DEFAULT '{}', -- JSON object
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_event_date ON update_event(event_date DESC);
CREATE INDEX idx_product ON update_event(product);
CREATE INDEX idx_severity ON update_event(severity);
CREATE INDEX idx_product_date ON update_event(product, event_date DESC);
```

### source_snapshot

```sql
CREATE TABLE source_snapshot (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       TEXT NOT NULL,              -- chatgpt | gemini | codex | claude_code
    fetched_at      TEXT NOT NULL,              -- ISO 8601
    content_hash    TEXT NOT NULL,              -- SHA-256
    raw_content     TEXT,                       -- 원본 HTML/Markdown
    status          TEXT NOT NULL DEFAULT 'success', -- success | fail
    error_message   TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_snapshot_source ON source_snapshot(source_id, fetched_at DESC);
```

## API 계약

### GET /api/events

이벤트 목록 조회 (타임라인 메인 데이터)

**Query Parameters:**

| Parameter | Type | Default | 설명 |
|-----------|------|---------|------|
| product | string | (all) | 쉼표 구분. 예: `chatgpt,gemini` |
| tag | string | (all) | 쉼표 구분. 예: `breaking,model` |
| severity_min | int | 1 | 최소 severity (1~5) |
| year | int | (all) | 연도 필터 |
| offset | int | 0 | 페이지네이션 offset |
| limit | int | 50 | 페이지네이션 limit (max 200) |

**Response 200:**

```json
{
  "total": 142,
  "offset": 0,
  "limit": 50,
  "items": [
    {
      "id": "uuid-string",
      "product": "chatgpt",
      "component": "default",
      "event_date": "2026-02-28",
      "title": "GPT-4.5 research preview available",
      "summary_ko": "GPT-4.5 연구 프리뷰가 Plus 이상 사용자에게 공개됨",
      "tags": ["model", "new_feature"],
      "severity": 4,
      "source_url": "https://help.openai.com/en/articles/...",
      "evidence_excerpt": ["GPT-4.5 is now available in research preview..."]
    }
  ]
}
```

### GET /api/events/{id}

이벤트 상세 (카드 펼치기용)

**Response 200:**

```json
{
  "id": "uuid-string",
  "product": "chatgpt",
  "component": "default",
  "event_date": "2026-02-28",
  "detected_at": "2026-02-28T10:00:00Z",
  "title": "GPT-4.5 research preview available",
  "summary_ko": "GPT-4.5 연구 프리뷰가 Plus 이상 사용자에게 공개됨",
  "summary_en": "GPT-4.5 research preview now available for Plus and above",
  "tags": ["model", "new_feature"],
  "severity": 4,
  "source_url": "https://help.openai.com/en/articles/...",
  "evidence_excerpt": [
    "GPT-4.5 is now available in research preview...",
    "Available for Plus, Pro, and Team users"
  ],
  "raw_ref": {
    "source_id": "chatgpt_release_notes",
    "section_key": "february-28-2026"
  },
  "created_at": "2026-02-28T10:30:00Z",
  "updated_at": "2026-02-28T10:30:00Z"
}
```

### GET /api/products

제품 메타 정보 (필터 UI용)

**Response 200:**

```json
{
  "products": [
    { "id": "chatgpt", "label": "ChatGPT", "color": "#10A37F", "event_count": 45 },
    { "id": "gemini", "label": "Gemini", "color": "#4285F4", "event_count": 38 },
    { "id": "codex", "label": "Codex", "color": "#A855F7", "event_count": 22 },
    { "id": "claude_code", "label": "Claude Code", "color": "#D97706", "event_count": 37 }
  ]
}
```

### GET /api/tags

태그 메타 정보 (필터 UI용)

**Response 200:**

```json
{
  "tags": [
    { "id": "new_feature", "label": "New Feature", "count": 52 },
    { "id": "model", "label": "Model", "count": 18 },
    { "id": "breaking", "label": "Breaking", "count": 7 },
    { "id": "deprecation", "label": "Deprecation", "count": 5 },
    { "id": "access", "label": "Pricing/Access", "count": 12 },
    { "id": "bugfix", "label": "Bugfix", "count": 48 }
  ]
}
```

## 데이터 수집 (Claude Code 기반)

### 설계 원칙

- **스케줄러 없음** — 사용자가 Claude Code를 실행하면 수집 시작
- **파서 클래스 없음** — Claude Code가 HTML/Markdown을 직접 읽고 이해하여 이벤트 추출
- **scripts/collect.py** — 네트워크(fetch)/DB(insert) 작업만 담당하는 유틸리티

### 소스 설정

| 소스 | URL | 형식 | 스냅샷 파일 |
|------|-----|------|-------------|
| ChatGPT | help.openai.com/en/articles/6825453-chatgpt-release-notes | HTML | chatgpt_latest.html |
| Gemini | gemini.google/release-notes/ | HTML | gemini_latest.html |
| Codex | developers.openai.com/codex/changelog/ | HTML | codex_latest.html |
| Claude Code | raw.githubusercontent.com/.../CHANGELOG.md | Markdown | claude_code_latest.md |

### 수집 툴킷 (scripts/collect.py) — 7개 함수

| 함수 | 용도 |
|------|------|
| `fetch_source(source_id)` | 단일 소스 다운로드 + SHA-256 해시 + 스냅샷 DB 기록 |
| `fetch_all_sources()` | 4개 소스 순차 fetch (1초 간격) |
| `get_snapshot_status()` | 각 소스의 최근 스냅샷 상태 조회 |
| `get_existing_events(product, limit)` | 기존 이벤트 조회 (중복 비교용) |
| `check_duplicate(product, event_date, title)` | 제목 유사도 0.7 기준 중복 판정 |
| `insert_event(event_dict)` | 단일 이벤트 삽입 (severity 자동 계산) |
| `insert_events(events_list)` | 배치 삽입 (트랜잭션) |

### 일일 수집 워크플로우

```
Step 1: python -m scripts.collect          → 4개 소스 fetch, 스냅샷 저장
Step 2: 변경된 소스의 스냅샷 파일 읽기       → data/snapshots/*.html|md
Step 3: 기존 이벤트 조회                    → get_existing_events("chatgpt")
Step 4: 새 이벤트 식별 (Claude Code가 판단)  → 소스 내용 vs 기존 이벤트 비교
Step 5: 새 이벤트 삽입                      → insert_event({...}) or insert_events([...])
Step 6: 사용자에게 결과 보고
```

### CLI 사용법

```bash
# 4개 소스 전부 fetch + 스냅샷 저장
python -m scripts.collect

# 상태만 확인 (fetch 없음)
python -m scripts.collect --status
```

## Severity 점수 규칙

```python
SEVERITY_RULES = {
    5: ["breaking", "deprecation", "shutdown", "removed", "end of life"],
    4: ["new model", "major feature", "launch", "generally available", "ga"],
    3: ["pricing", "access", "plan", "tier", "quota", "rate limit"],
    2: ["feature", "improvement", "update", "enhancement", "support"],
    1: ["fix", "bug", "patch", "performance", "minor"],
}
```

title + summary 텍스트를 lowercase 변환 후 키워드 매칭 → 최고 점수 채택. 매칭 없으면 기본값 2.

## 디렉토리 구조

```
ai-tracker/
├── apps/
│   ├── api/                           # backend-dev 소유
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── database.py                # SQLite 연결 + 테이블 생성
│   │   ├── schemas.py                 # Pydantic response schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── events.py
│   │   │   └── meta.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── scorer.py              # 규칙 기반 Severity 점수
│   ├── web/                           # frontend-dev 소유
│   │   ├── index.html
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── app.js
│   │       ├── api.js
│   │       ├── timeline.js
│   │       ├── filters.js
│   │       └── card.js
│   └── llm/                           # MVP 미사용
│       └── __init__.py
├── data/
│   ├── tracker.db                     # SQLite (gitignore)
│   └── snapshots/                     # 소스 스냅샷 파일
├── docs/
├── scripts/
│   ├── seed.py                        # 시드 데이터
│   └── collect.py                     # 수집 툴킷 (Claude Code용)
├── tests/
│   ├── test_api_events.py
│   ├── test_collect.py
│   ├── test_health.py
│   └── test_scorer.py
├── requirements.txt
└── .env.example
```

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DATABASE_URL` | SQLite DB 경로 | `sqlite:///data/tracker.db` |
| `PORT` | 서버 포트 | `8000` |

> MVP에서는 LLM API 키 불필요. 시크릿은 `.env`에만 보관.

## CORS 설정

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # MVP: 전체 허용
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 정적 파일 서빙

FastAPI에서 `apps/web/`을 정적 파일로 마운트:

```python
# API 라우터를 먼저 등록한 후, 마지막에 static mount
app.mount("/", StaticFiles(directory="apps/web", html=True), name="static")
```

## 배포 (Railway)

- Procfile: `web: uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`
- SQLite: Railway 볼륨 `/data/` 마운트
- 환경변수: Railway 대시보드에서 설정
