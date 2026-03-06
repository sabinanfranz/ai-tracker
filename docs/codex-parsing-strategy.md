# Codex 파싱 전략 및 테이블 구조

## 1. 배경

Codex changelog(`https://developers.openai.com/codex/changelog/`)는 OpenAI Codex 제품의
앱 업데이트, CLI 릴리즈, 일반 발표를 한 페이지에 모아 보여주는 changelog이다.

기존 `codex_event` 테이블은 다른 제품(ChatGPT, Gemini)과 동일한 공통 14컬럼 스키마를 사용했으나,
Codex changelog의 실제 HTML 구조와 맞지 않아 독립 스키마로 재정의했다.

---

## 2. 소스 HTML 구조

소스 URL: `https://developers.openai.com/codex/changelog/`
스냅샷 파일: `data/snapshots/codex_latest.html`

### 엔트리 구조

```
<li class="scroll-mt-28" data-codex-topics="{entry_type}">
  <time>YYYY-MM-DD</time>
  <h3 class="group"><span>제목 <span class="text-tertiary">버전</span></span></h3>
  <article class="prose-content">
    <!-- 본문: h3/h2 섹션 + ul/ol 리스트 또는 prose 텍스트 -->
    <!-- codex-cli: <details> 안에 실제 내용 -->
  </article>
</li>
```

### 엔트리 유형별 특성 (총 48건)

| entry_type | 건수 | 제목 패턴 | 본문 특성 | body 평균/최대 |
|------------|------|----------|----------|--------------|
| `general` | 25 | "Introducing GPT-5.3-Codex", "Codex is now GA" | prose 텍스트 + 간혹 bullets | 727 / 1,528 chars |
| `codex-app` | 11 | "Codex app 26.226" | h3 섹션(New features/Bug fixes) + bullets | 288 / 673 chars |
| `codex-cli` | 12 | "Codex CLI 0.106.0" | `<details>` 안 h2 섹션 + bullets | 1,789 / 2,916 chars |

데이터 기간: 2025-05-19 ~ 2026-02-26

---

## 3. 테이블 스키마

### codex_event (독립 스키마)

```sql
CREATE TABLE IF NOT EXISTS codex_event (
    id              TEXT PRIMARY KEY,
    event_date      TEXT NOT NULL,          -- <time> 태그 값 (YYYY-MM-DD)
    title           TEXT NOT NULL,          -- 최상위 h3 > span 텍스트
    entry_type      TEXT NOT NULL,          -- 'general' | 'codex-app' | 'codex-cli'
    version         TEXT,                   -- app: "26.226", cli: "0.106.0", general: NULL
    body            TEXT NOT NULL DEFAULT '',-- 구조화된 플레인 텍스트
    source_url      TEXT NOT NULL DEFAULT 'https://developers.openai.com/codex/changelog/',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_codex_unique ON codex_event(event_date, title);
CREATE INDEX IF NOT EXISTS idx_codex_event_date ON codex_event(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_codex_entry_type ON codex_event(entry_type);
```

### 이전 스키마 대비 변경

- **제거**: `component`, `detected_at`, `title_ko`, `summary_ko`, `summary_en`, `tags`, `severity`, `evidence_excerpt`, `raw_ref`, `cli_version`
- **추가**: `entry_type`, `version`, `body`
- **유지**: `id`, `event_date`, `title`, `source_url`, `created_at`, `updated_at`

### all_events VIEW

codex_event는 독립 스키마이므로 `all_events` VIEW에서 제외됨.
4개 제품 모두 칼럼 재정의 완료 후 VIEW를 일괄 재설계할 예정.

---

## 4. 파서 구현 (`scripts/parsers/codex.py`)

### 4-1. 전체 흐름

```
HTML → BeautifulSoup
  → find_all("li", class_="scroll-mt-28")  # 각 changelog 엔트리
    → <time> 태그에서 날짜 추출
    → data-codex-topics 속성에서 entry_type 추출
    → <h3> > <span>에서 제목 추출 (Copy link 버튼 텍스트 제거)
    → 제목에서 regex로 version 추출
    → <article>에서 body 추출
  → event dict 리스트 반환
```

### 4-2. 날짜 추출

`<time>` 태그의 텍스트를 그대로 사용. 이미 `YYYY-MM-DD` 포맷.

### 4-3. entry_type 추출

`<li>` 태그의 `data-codex-topics` 속성값. 미지정 시 `"general"` 기본값.

### 4-4. version 추출

제목 텍스트에서 regex로 추출:

| entry_type | 패턴 | 예시 |
|---|---|---|
| `codex-cli` | `r"(\d+\.\d+\.\d+)"` | "Codex CLI 0.106.0" → `"0.106.0"` |
| `codex-app` | `r"(\d+\.\d+)"` | "Codex app 26.226" → `"26.226"` |
| `general` | 추출 안 함 | `NULL` |

### 4-5. body 추출 로직

구조화된 플레인 텍스트로 변환. 섹션 헤더는 `[섹션명]`, 항목은 `- ` 접두사.

**entry_type별 파싱 전략:**

| entry_type | 파싱 대상 | 전략 |
|---|---|---|
| `codex-app` | `<article>` 직속 h3 + ul | h3 → `[섹션명]`, li → `- 텍스트` |
| `codex-cli` | `<details>` > `<div class="prose-content">` | h2 → `[섹션명]`, li → `- 텍스트` |
| `general` | `<article>` 직속 p + ul | p → prose 텍스트, li → `- 텍스트` |

**공통 규칙:**
- `<pre>` 태그 (install 명령어) 제외
- `<details>` 이중 파싱 방지
- `[Changelog]` 섹션 발견 시 이후 내용 제외 (CLI PR 목록 — 너무 세부적)

**body 예시:**

codex-app:
```
[New features]
- Added new MCP shortcuts in the composer, including install keyword suggestions...
- Added support for @mentions and skill mentions in inline review comments.
[Performance improvements and bug fixes]
- Improved rendering of MCP tool calls and Mermaid diagram error handling.
```

codex-cli:
```
[New Features]
- Added a direct install script for macOS and Linux...
- Expanded the app-server v2 thread API with experimental endpoints...
[Bug Fixes]
- Improved realtime websocket reliability by retrying timeout-related failures...
```

general:
```
Today, we're releasing a research preview of GPT-5.3-Codex-Spark,
a smaller version of GPT-5.3-Codex and our first model designed for real-time coding.
```

---

## 5. 데이터 흐름

### 수집 (collect.py)

```
fetch_source("codex")
  → HTTP GET / Playwright 폴백
  → data/snapshots/codex_latest.html 저장
  → source_snapshot 테이블에 기록
```

### 파싱 + 삽입

```
parse_codex(html)  → list[dict]
insert_events(events)
  → product == "codex" 분기
  → _insert_codex_event(conn, event_dict)
     → INSERT OR IGNORE INTO codex_event (id, event_date, title, entry_type, version, body, source_url)
```

- 중복 방지: `UNIQUE(event_date, title)` 인덱스로 INSERT OR IGNORE
- 공통 INSERT 경로와 분리: codex는 `_insert_codex_event()` 전용 함수 사용

### Backfill

```bash
python -m scripts.backfill --codex
# DELETE 기존 → parse_codex → insert_events
```

---

## 6. 수정된 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `apps/api/database.py` | codex_event DDL 독립화, all_events VIEW에서 codex 제외 |
| `scripts/parsers/codex.py` | 전면 재작성 — entry_type/version/body 추출 |
| `scripts/collect.py` | `_insert_codex_event()` 추가, insert_event/insert_events codex 분기 |
| `scripts/seed.py` | codex 시드 데이터 새 스키마 적용 |
| `scripts/migrate_to_per_product.py` | codex 마이그레이션 브랜치 수정 |
| `tests/test_collect.py` | codex 테스트 및 `_insert_raw_event` 헬퍼 수정 |

---

## 7. 향후 과제

- [ ] `track_tag` 컬럼 추가 — body 내용 기반 태깅 (new/fix/change/pricing)
- [ ] 한국어 요약 생성 — body → summary_ko (LLM 또는 규칙 기반)
- [ ] codex 전용 API 엔드포인트 — all_events VIEW 없이 직접 조회
- [ ] all_events VIEW 재설계 — 4개 제품 모두 독립 스키마 완료 후 일괄 처리
