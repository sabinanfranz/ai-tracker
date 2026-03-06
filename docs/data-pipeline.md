# 데이터 수집 파이프라인

> 4개 AI 제품(ChatGPT, Gemini, Codex, Claude Code)의 업데이트 이벤트를 수집·파싱·저장·서빙하는 파이프라인.

---

## 1. 파이프라인 개요

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Collect  │───▶│  Parse  │───▶│  Store  │───▶│  Serve  │
│          │    │         │    │         │    │         │
│ 소스 페이지 │    │ HTML/MD  │    │ SQLite  │    │ FastAPI │
│ fetch +   │    │ 파싱 →   │    │ DB 저장  │    │ REST    │
│ 스냅샷 저장 │    │ 이벤트 추출│    │         │    │ API     │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
 collect.py     backfill/      database.py    routers/
                parsers/       collect.py     events.py
                                              meta.py
```

**단계 요약:**

| 단계 | 스크립트 | 입력 | 출력 |
|------|---------|------|------|
| Collect | `scripts/collect.py` | 소스 URL | `data/snapshots/` 파일 + `source_snapshot` DB 레코드 |
| Parse | `scripts/backfill/` + `scripts/parsers/` | 스냅샷 파일 | 제품별 이벤트 테이블 DB 레코드 |
| Store | `apps/api/database.py` + `scripts/collect.py` | 이벤트 dict | SQLite `data/tracker.db` |
| Serve | `apps/api/routers/` | HTTP 요청 | JSON 응답 |

---

## 2. 소스 설정

4개 제품의 소스 정보는 `scripts/collect.py`의 `SOURCES` dict에 정의된다.

| 제품 | source_id | URL | 포맷 | 스냅샷 파일명 |
|------|-----------|-----|------|-------------|
| ChatGPT | `chatgpt` | `https://help.openai.com/en/articles/6825453-chatgpt-release-notes` | HTML | `chatgpt_latest.html` |
| Gemini | `gemini` | `https://gemini.google/release-notes/` | HTML | `gemini_latest.html` |
| Codex | `codex` | `https://developers.openai.com/codex/changelog/` | HTML | `codex_latest.html` |
| Claude Code | `claude_code` | `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md` | Markdown | `claude_code_latest.md` |

스냅샷 저장 경로: `data/snapshots/`

---

## 3. 수집 (`scripts/collect.py`)

### 3.1 fetch 전략: httpx → Playwright fallback

각 소스에 대해 2단계 fetch를 시도한다.

```
httpx.get() ──성공──▶ content_text 확보
    │
    ▼ (403 / 실패)
Playwright (headless Chromium) ──성공──▶ content_text 확보
    │
    ▼ (실패)
source_snapshot에 status='fail' 기록, 에러 반환
```

**httpx (1차 시도):**
- `timeout=30`, `follow_redirects=True`
- 브라우저 User-Agent 헤더 사용 (`Chrome/131.0.0.0`)

**Playwright fallback (2차 시도):**
- `_fetch_with_playwright()` 함수
- headless Chromium, `domcontentloaded` 이벤트 대기 + 3초 추가 대기
- Cloudflare 등 anti-bot 보호 우회 목적

### 3.2 스냅샷 저장

fetch 성공 시:

1. **파일 저장**: `data/snapshots/{filename}`에 원문 저장
2. **해시 계산**: SHA-256 해시로 콘텐츠 변경 여부 감지
3. **DB 기록**: `source_snapshot` 테이블에 기록
   - `raw_content`는 1MB 이하일 때만 DB에 저장
   - 이전 스냅샷 해시와 비교하여 `changed` 여부 판별

### 3.3 전체 수집 (`fetch_all_sources`)

- 4개 소스를 순차적으로 fetch
- 소스 간 1초 간격(politeness delay)
- 결과 요약: success/failed/changed/unchanged 카운트

---

## 4. 파싱 (`scripts/parsers/`)

스냅샷 파일을 제품별 파서로 분석하여 이벤트 목록(`list[dict]`)을 추출한다. 모든 파서는 `2025-01-01` 이후 이벤트만 포함한다.

**제품별 스키마 유형:**

| 제품 | 스키마 유형 | 파서 출력 필드 |
|------|-----------|--------------|
| ChatGPT | 독립 (simple) | `product, event_date, title, content, source_url` |
| Codex | 독립 (independent) | `product, event_date, title, entry_type, version, body, source_url` |
| Gemini | 공통 (common) | `product, event_date, title, summary_ko, tags, severity, source_url, evidence_excerpt` |
| Claude Code | 독립 (bullet-level) | `product, event_date, title, version, change_type, subsystem, source_url` |

### 4.1 ChatGPT 파서 (`parse_chatgpt`)

**입력**: `chatgpt_latest.html`

**HTML 구조**: 영문 날짜 헤딩(`h1`) + h2/h3 기능 제목 + 불릿 리스트

**파싱 로직:**
1. 모든 `<h1>` 태그에서 영문 날짜 패턴 탐색
   - 정규식: `(January|February|...|Dec)\s+\d{1,2},?\s+\d{4}`
   - 예: `"January 15, 2026"` → `"2026-01-15"`
2. 날짜 h1 사이의 형제 요소를 h2/h3 기준으로 그룹 분할
   - h2 = 기능 제목 (새 이벤트 그룹 시작)
   - h3/h4 = 서브섹션 (Web / iOS / Android 등)
   - `<ul>/<ol>` 안의 `<li>`, 독립 `<p>` 태그 = 콘텐츠
3. 제목 결정: h2 텍스트, 없으면 h3 텍스트, 없으면 첫 번째 콘텐츠 라인[:100]
4. content: 그룹 내 모든 불릿/텍스트를 `\n`으로 연결
   - 서브섹션 항목은 `"{heading}: {item}"` 형태로 접두어 포함

**출력 dict:**
```python
{
    "product": "chatgpt",
    "event_date": "2026-02-25",
    "title": "Canvas improvements",
    "content": "Added new editing tools\niOS: Fixed rendering issue",
    "source_url": "https://help.openai.com/en/articles/6825453-chatgpt-release-notes",
}
```

### 4.2 Gemini 파서 (`parse_gemini`)

**입력**: `gemini_latest.html`

**이중 HTML 구조**: 2024(old) vs 2025+(new) 레이아웃이 혼재

```
[공통] _releaseNoteCard_ 컨테이너
  ├── <h2 class="_releaseNoteCardTitle_"> : 날짜 (YYYY.MM.DD 형식)
  │
  ├── [2024 old] _releaseNoteCardBody_ : 콘텐츠 직접 포함
  │     └── <h3> 제목들 + <p>/<li> 본문
  │
  └── [2025+ new] _features_ : 실제 콘텐츠
        ├── <h3 class="_featureTitle_"> : 기능 제목
        └── <div class="_featureBulletBody_"> : 상세 설명
              └── <p> 태그들 (볼드 접두어 "내용:", "이유:" 등 제거)
```

**파싱 로직:**
1. `_releaseNoteCard_` 클래스 div에서 외부 카드만 필터링
2. `<h2>` 날짜 추출: `YYYY.MM.DD` → `YYYY-MM-DD` 변환
3. 콘텐츠 소스 결정:
   - `_releaseNoteCardBody_`에 텍스트가 있으면 → **old 구조** (2024)
   - 비어있고 `_features_` div가 있으면 → **new 구조** (2025+)
4. 한국어 원문 그대로 `summary_ko`에 사용 (번역 불필요)
5. evidence: `_featureBulletBody_`의 `<p>` 태그에서 추출, 볼드 접두어 제거

### 4.3 Codex 파서 (`parse_codex`)

> 상세 파싱 전략: `docs/codex-parsing-strategy.md` 참조

**입력**: `codex_latest.html`

**HTML 구조:**
```html
<li class="scroll-mt-28" data-codex-topics="{entry_type}">
  <time>2025-06-15</time>
  <h3 class="group"><span>Codex CLI 0.106.0 <span class="text-tertiary">버전</span></span></h3>
  <article class="prose-content">
    <!-- 본문: h3/h2 섹션 + ul/ol 리스트 또는 prose 텍스트 -->
    <!-- codex-cli: <details> 안에 실제 내용 -->
  </article>
</li>
```

**엔트리 유형 (총 48건):**

| entry_type | 건수 | 제목 패턴 | body 특성 |
|------------|------|----------|----------|
| `general` | 25 | "Introducing GPT-5.3-Codex" | prose 텍스트 + 간혹 bullets |
| `codex-app` | 11 | "Codex app 26.226" | h3 섹션(New features/Bug fixes) + bullets |
| `codex-cli` | 12 | "Codex CLI 0.106.0" | `<details>` 안 h2 섹션 + bullets |

**파싱 로직:**
1. `<li class="scroll-mt-28">` 엔트리 탐색
2. `<time>` 태그에서 날짜 추출 (이미 `YYYY-MM-DD` 형식)
3. `data-codex-topics` 속성에서 `entry_type` 추출 (미지정 시 `"general"`)
4. `<h3>` > `<span>` 제목 추출, "Copy link" 텍스트 잔여물 제거
5. 제목에서 regex로 `version` 추출:
   - `codex-cli`: `r"(\d+\.\d+\.\d+)"` → `"0.106.0"`
   - `codex-app`: `r"(\d+\.\d+)"` → `"26.226"`
   - `general`: `NULL`
6. `<article>`에서 구조화된 플레인 텍스트 `body` 추출:
   - `codex-app`: article 직속 h3 → `[섹션명]`, li → `- 텍스트`
   - `codex-cli`: `<details>` > `div.prose-content` h2 → `[섹션명]`, li → `- 텍스트`
   - `general`: article 직속 p → prose 텍스트, li → `- 텍스트`
7. `[Changelog]` 섹션 발견 시 이후 내용 제외, `<pre>` 태그 제외

**출력 dict:**
```python
{
    "product": "codex",
    "event_date": "2026-02-26",
    "title": "Codex CLI 0.106.0",
    "entry_type": "codex-cli",
    "version": "0.106.0",
    "body": "[New Features]\n- Added multi-file editing support\n[Bug Fixes]\n- Fixed crash on startup",
    "source_url": "https://developers.openai.com/codex/changelog/",
}
```

### 4.4 Claude Code 파서 (`parse_claude_code`)

**입력**: `claude_code_latest.md` (GitHub raw CHANGELOG.md)

**Markdown 구조:**
```markdown
## 2.1.63

- Added new multi-turn editing support
- [VSCode] Fixed sidebar rendering issue
- Improved performance for large files

## 2.1.62
...
```

**파싱 로직:**
1. `## X.Y.Z` 패턴 정규식으로 버전 헤더 분할
2. 각 버전 사이의 `- ` 불릿 파싱 → **불릿 하나 = 이벤트 하나** (bullet-level)
3. **버전→날짜 매핑**: npm 레지스트리에서 자동으로 publish 날짜를 가져옴
   - `npm view @anthropic-ai/claude-code time --json` 명령으로 전체 버전 날짜 조회
   - 24시간 파일 캐시 (`data/cache/npm_versions.json`) 사용
   - npm 실패 시 캐시 fallback
4. `change_type` 추출: 불릿 첫 단어에서 결정
   - `added/add/new` → `"added"`, `fixed/fix` → `"fixed"`, `improved/enhance` → `"improved"`
   - `changed` → `"changed"`, `removed` → `"removed"`, `updated` → `"updated"`
   - 매칭 없으면 `"other"`
5. `subsystem` 추출: 불릿 텍스트의 bracket/colon 접두어에서 결정
   - `[VSCode]` → `"vscode"`, `[SDK]` → `"sdk"`, `Windows:` → `"windows"` 등
   - 매칭 없으면 `NULL`
6. 제목: 불릿 텍스트 그대로 사용

**출력 dict:**
```python
{
    "product": "claude_code",
    "event_date": "2026-03-01",
    "title": "[VSCode] Fixed sidebar rendering issue",
    "version": "2.1.63",
    "change_type": "fixed",
    "subsystem": "vscode",
    "source_url": "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md",
}
```

---

## 5. 태그 분류 & 심각도 계산

> **적용 범위**: Gemini만 공통 스키마를 사용하므로 태그/심각도가 적용된다.
> ChatGPT, Codex, Claude Code는 독립 스키마로 이 로직을 사용하지 않는다.

### 5.1 태그 분류 (`classify_tags`)

`scripts/parsers/__init__.py`의 `classify_tags()` 함수. 제목+요약 텍스트에서 키워드 매칭으로 태그를 부여한다.

| 태그 | 매칭 키워드 |
|------|-----------|
| `change` | breaking, deprecated, removed, deprecation, shutdown, end of life |
| `new` | new feature, added, support for, new model, launch, model, opus, sonnet, gpt, gemini 2, gemini 1.5 |
| `fix` | fixed, bug, crash, regression, performance, improved, optimization, faster |
| `pricing` | pricing, plan, access, tier, quota |

- 텍스트를 소문자로 변환 후 각 카테고리의 키워드를 순차 검사
- 한 카테고리에서 키워드가 매칭되면 해당 태그 추가 후 다음 카테고리로 이동
- 아무 태그도 매칭되지 않으면 기본값 `["new"]` 부여
- 결과는 중복 제거 후 순서 유지

### 5.2 심각도 계산 (`calculate_severity`)

`apps/api/services/scorer.py`의 `calculate_severity()` 함수. 5단계 점수를 반환한다.

| 심각도 | 의미 | 매칭 키워드 |
|--------|------|-----------|
| 5 | Breaking/폐기 | breaking, deprecation, shutdown, removed, end of life |
| 4 | 주요 출시 | new model, major feature, launch, generally available, ga |
| 3 | 요금/접근 변경 | pricing, access, plan, tier, quota, rate limit |
| 2 | 기능 개선 | feature, improvement, update, enhancement, support |
| 1 | 버그 수정 | fix, bug, patch, performance, minor |

- `title + summary`를 합쳐 소문자로 변환
- 심각도 5 → 1 순서로 키워드 검사, 최초 매칭된 레벨 반환
- 매칭 없으면 기본값 `2`

---

## 6. DB 스키마

DB 파일: `data/tracker.db` (SQLite)

정의 위치: `apps/api/database.py`

4개 제품은 **제품별 독립 테이블**을 사용한다. Gemini만 공통 컬럼 정의(`_COMMON_COLS`)를 사용하고, ChatGPT·Codex·Claude Code는 각자 독립 스키마를 가진다.

### 6.1 `chatgpt_event` 테이블 (독립 — simple)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | TEXT PK | UUID v4 |
| `event_date` | TEXT NOT NULL | 이벤트 날짜 (`YYYY-MM-DD`) |
| `title` | TEXT NOT NULL | 기능 제목 (h2/h3 텍스트) |
| `content` | TEXT NOT NULL | 불릿/텍스트 원문 (`\n` 구분) |
| `source_url` | TEXT NOT NULL | 원본 소스 URL |
| `created_at` | TEXT NOT NULL | 생성 시각 |

**인덱스:**
- `UNIQUE(event_date, title)` — 중복 방지
- `idx_chatgpt_event_date`: `event_date DESC`

### 6.2 `codex_event` 테이블 (독립 — changelog entries)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | TEXT PK | UUID v4 |
| `event_date` | TEXT NOT NULL | `<time>` 태그 값 (`YYYY-MM-DD`) |
| `title` | TEXT NOT NULL | 최상위 h3 > span 텍스트 |
| `entry_type` | TEXT NOT NULL | `'general'` \| `'codex-app'` \| `'codex-cli'` |
| `version` | TEXT | app: `"26.226"`, cli: `"0.106.0"`, general: `NULL` |
| `body` | TEXT NOT NULL | 구조화된 플레인 텍스트 |
| `source_url` | TEXT NOT NULL | 원본 소스 URL |
| `created_at` | TEXT NOT NULL | 생성 시각 |
| `updated_at` | TEXT NOT NULL | 수정 시각 |

**인덱스:**
- `UNIQUE(event_date, title)` — 중복 방지
- `idx_codex_event_date`: `event_date DESC`
- `idx_codex_entry_type`: `entry_type`

### 6.3 `gemini_event` 테이블 (공통 스키마)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | TEXT PK | UUID v4 |
| `component` | TEXT NOT NULL | 컴포넌트 (기본값: `'default'`) |
| `event_date` | TEXT NOT NULL | 이벤트 날짜 (`YYYY-MM-DD`) |
| `detected_at` | TEXT NOT NULL | 감지 시각 (ISO 8601) |
| `title` | TEXT NOT NULL | 영문 제목 |
| `title_ko` | TEXT | 한국어 헤드라인 (자동 생성) |
| `summary_ko` | TEXT NOT NULL | 한국어 요약 |
| `summary_en` | TEXT | 영문 요약 (선택) |
| `tags` | TEXT NOT NULL | JSON 배열 (기본값: `'[]'`) |
| `severity` | INTEGER NOT NULL | 심각도 1~5 (기본값: `1`) |
| `source_url` | TEXT NOT NULL | 원본 소스 URL |
| `evidence_excerpt` | TEXT NOT NULL | JSON 배열 — 근거 발췌 |
| `raw_ref` | TEXT NOT NULL | JSON 객체 — 원본 참조 정보 |
| `created_at` | TEXT NOT NULL | 생성 시각 |
| `updated_at` | TEXT NOT NULL | 수정 시각 |

**인덱스:**
- `UNIQUE(event_date, title)` — 중복 방지
- `idx_gemini_event_date`: `event_date DESC`
- `idx_gemini_severity`: `severity`

### 6.4 `claude_code_event` 테이블 (독립 — bullet-level)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | TEXT PK | UUID v4 |
| `event_date` | TEXT NOT NULL | npm publish 날짜 (`YYYY-MM-DD`) |
| `title` | TEXT NOT NULL | 불릿 텍스트 (변경사항 1줄) |
| `version` | TEXT NOT NULL | 릴리즈 버전 (`"2.1.63"`) |
| `change_type` | TEXT NOT NULL | 변경 유형 (`added`, `fixed`, `improved`, `changed`, `removed`, `updated`, `other`) |
| `subsystem` | TEXT | 서브시스템 (`vscode`, `sdk`, `mcp`, `hooks` 등, 없으면 `NULL`) |
| `source_url` | TEXT NOT NULL | CHANGELOG.md URL |
| `created_at` | TEXT NOT NULL | 생성 시각 |
| `updated_at` | TEXT NOT NULL | 수정 시각 |

**인덱스:**
- `UNIQUE(event_date, title)` — 중복 방지
- `idx_claude_code_event_date`: `event_date DESC`
- `idx_claude_code_change_type`: `change_type`
- `idx_claude_code_version`: `version`

### 6.5 `all_events` VIEW

4개 제품 중 3개(chatgpt, gemini, claude_code)를 공통 컬럼으로 매핑하는 UNION ALL VIEW.

- **codex 제외**: 독립 스키마의 `entry_type`/`body` 컬럼이 공통 스키마와 호환되지 않음
- chatgpt: `content` → `summary_ko`, `tags`/`severity` 기본값 매핑
- claude_code: `change_type` → `component`, `title` → `summary_ko` 매핑

### 6.6 `source_snapshot` 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INTEGER PK | 자동 증가 |
| `source_id` | TEXT NOT NULL | 소스 ID (`chatgpt`, `gemini`, `codex`, `claude_code`) |
| `fetched_at` | TEXT NOT NULL | fetch 시각 (ISO 8601) |
| `content_hash` | TEXT NOT NULL | SHA-256 해시 |
| `raw_content` | TEXT | 원본 콘텐츠 (1MB 이하만 저장) |
| `status` | TEXT NOT NULL | `'success'` 또는 `'fail'` |
| `error_message` | TEXT | 에러 메시지 |
| `created_at` | TEXT NOT NULL | 생성 시각 |

**인덱스:**
- `idx_snapshot_source`: `(source_id, fetched_at DESC)`

### 6.7 DB 연결 설정

```python
conn = sqlite3.connect("data/tracker.db")
conn.row_factory = sqlite3.Row     # dict-like 접근
PRAGMA journal_mode = DELETE        # Windows 안정성
PRAGMA foreign_keys = ON
```

---

## 7. DB 삽입 (`scripts/collect.py`)

`insert_event()` / `insert_events()` 함수가 제품별로 분기하여 전용 INSERT 함수를 호출한다.

| 제품 | INSERT 함수 | 필수 필드 |
|------|------------|----------|
| ChatGPT | `_insert_chatgpt_event()` | `event_date`, `title` |
| Codex | `_insert_codex_event()` | `event_date`, `title` |
| Claude Code | `_insert_claude_code_event()` | `event_date`, `title` |
| Gemini | 공통 경로 | `event_date`, `title`, `summary_ko`, `source_url`, `tags` |

- 모든 삽입은 `INSERT OR IGNORE` — `UNIQUE(event_date, title)` 인덱스로 중복 방지
- Gemini만 `calculate_severity()` 호출하여 심각도 자동 계산

---

## 8. `title_ko` 생성 (`scripts/generate_title_ko.py`)

> **적용 범위**: `all_events` VIEW 기반이므로 Gemini에 주로 적용.

`summary_ko`에서 짧은 한국어 헤드라인을 자동 생성한다. 최대 55자.

### 알고리즘

```
summary_ko
  │
  ▼
1. 문장 분리 (마침표 기준)
  │
  ▼
2. 액션 키워드 포함 문장 우선 선택
   (추가, 출시, 변경, 수정, 지원, 제공, 폐기, 개선, 통합, 확대, 인상, 감소)
  │
  ▼
3. 세미콜론으로 구분된 경우 첫 번째 항목만 사용
  │
  ▼
4. 격식체 어미 제거
   ("되었습니다", "습니다", "합니다" 등 19개 패턴)
  │
  ▼
5. 괄호 내용 제거 (20자 이하 괄호)
  │
  ▼
6. 55자 초과 시 자연 경계에서 절단
   (공백, 쉼표, "와", "과", "·", "—" 위치)
  │
  ▼
title_ko (최대 55자)
```

**실행 옵션:**
- `--dry-run`: DB 변경 없이 미리보기
- `--force`: 이미 `title_ko`가 있는 이벤트도 덮어쓰기

---

## 9. API 서빙

FastAPI 기반 REST API. 라우터: `apps/api/routers/`

### 9.1 이벤트 API (`apps/api/routers/events.py`)

#### `GET /api/events`

이벤트 목록 조회 (페이지네이션, 필터링).

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| `product` | string | - | 쉼표 구분 제품 ID 필터 |
| `tag` | string | - | 쉼표 구분 태그 필터 (OR 조건) |
| `severity_min` | int (1~5) | 2 | 최소 심각도 |
| `year` | int | - | 연도 필터 |
| `offset` | int | 0 | 페이지네이션 오프셋 |
| `limit` | int (1~200) | 50 | 페이지네이션 크기 |

**응답**: `{ total, offset, limit, items: [...] }`

#### `GET /api/events/{event_id}`

단일 이벤트 상세 조회. 404 시 `HTTPException`.

### 9.2 메타 API (`apps/api/routers/meta.py`)

#### `GET /api/products`

제품 목록 + 이벤트 수.

```json
[
  { "id": "chatgpt",     "label": "ChatGPT",     "color": "#10A37F", "event_count": 8 },
  { "id": "gemini",      "label": "Gemini",      "color": "#4285F4", "event_count": 6 },
  { "id": "codex",       "label": "Codex",       "color": "#A855F7", "event_count": 5 },
  { "id": "claude_code", "label": "Claude Code", "color": "#D97706", "event_count": 7 }
]
```

#### `GET /api/tags`

태그 목록 + 사용 횟수. `json_each()`로 JSON 배열 내 태그를 집계한다.

```json
[
  { "id": "new",     "label": "새 기능",    "count": 20 },
  { "id": "change",  "label": "주요 변경",  "count": 3  },
  { "id": "pricing", "label": "요금/접근",  "count": 5  },
  { "id": "fix",     "label": "개선/수정",  "count": 4  }
]
```

---

## 10. 실행 가이드

### 수집 (소스 페이지 fetch)

```bash
# 모든 소스 fetch + 스냅샷 저장
python -m scripts.collect

# 스냅샷 상태만 확인
python -m scripts.collect --status
```

### 백필 (스냅샷 → 이벤트 파싱 + DB 저장)

```bash
# 전체 제품 백필 (INSERT OR IGNORE — 기존 보존)
python -m scripts.backfill

# 특정 제품만 재파싱 (기존 이벤트 삭제 후 재삽입)
python -m scripts.backfill --gemini
python -m scripts.backfill --codex
python -m scripts.backfill --chatgpt
python -m scripts.backfill --claude-code

# 전체 제품 재파싱
python -m scripts.backfill --all
```

### title_ko 생성

```bash
# 미리보기 (DB 변경 없음)
python -m scripts.generate_title_ko --dry-run

# 적용 (title_ko 없는 이벤트만)
python -m scripts.generate_title_ko

# 전체 덮어쓰기
python -m scripts.generate_title_ko --force
```

### 시드 데이터 (개발용)

```bash
# 약 30개 샘플 이벤트 삽입
python -m scripts.seed
```

### 일반적인 운영 흐름

```
1. python -m scripts.collect          # 소스 페이지 fetch
2. python -m scripts.backfill         # 스냅샷 파싱 → DB 저장
3. python -m scripts.generate_title_ko # 한국어 헤드라인 생성
4. uvicorn apps.api.main:app          # API 서버 시작
```

---

## 참조 파일 목록

| 파일 | 역할 |
|------|------|
| `scripts/collect.py` | 소스 페이지 fetch + 스냅샷 저장 + 이벤트 INSERT |
| `scripts/backfill/` | 스냅샷 → 파서 호출 → DB 삽입 오케스트레이션 (패키지) |
| `scripts/parsers/chatgpt.py` | ChatGPT HTML 파서 (h1/h2 → content) |
| `scripts/parsers/codex.py` | Codex HTML 파서 (entry_type/version/body) |
| `scripts/parsers/gemini.py` | Gemini HTML 파서 (이중 레이아웃) |
| `scripts/parsers/claude_code.py` | Claude Code MD 파서 (bullet-level + npm 날짜) |
| `scripts/parsers/__init__.py` | 공통 유틸 (`parse_en_date`, `classify_tags`) |
| `scripts/seed.py` | 개발용 시드 데이터 (~30개 샘플 이벤트) |
| `scripts/generate_title_ko.py` | summary_ko → 한국어 헤드라인 자동 생성 |
| `apps/api/database.py` | DB 스키마 정의 + 커넥션 관리 |
| `apps/api/services/scorer.py` | 키워드 기반 심각도 점수 계산 (1~5) |
| `apps/api/routers/events.py` | 이벤트 목록/상세 API |
| `apps/api/routers/meta.py` | 제품/태그 메타데이터 API |

---

## 참조 문서

| 문서 | 내용 |
|------|------|
| `docs/codex-parsing-strategy.md` | Codex 파싱 전략 및 테이블 구조 상세 |
| `docs/61-backfill-refactoring.md` | backfill.py → backfill/ 패키지 리팩터링 설명 |
