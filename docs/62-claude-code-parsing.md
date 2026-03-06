# Claude Code 파싱 & 테이블 재설계

> `claude_code_event` 독립 스키마 도입과 bullet-level 파서 아키텍처에 대한 설명 문서.

---

## 1. 변경 동기

초기 구현에서는 모든 제품이 공통 스키마(`update_event`)를 공유했고, Claude Code는 **버전 단위** 이벤트를 수동 날짜 매핑으로 처리했다. 세 가지 문제가 드러나면서 독립 설계로 전환했다.

### 1.1 공통 스키마 → 독립 스키마

공통 스키마(`_COMMON_COLS`)는 15개 컬럼(component, severity, tags, summary_ko 등)을 포함한다. Claude Code CHANGELOG.md에는 심각도·태그·한국어 요약이 존재하지 않아 대부분의 컬럼이 기본값으로 채워졌다. 반면 변경 유형(`change_type`)과 서브시스템(`subsystem`) 같은 Claude Code 고유 정보를 저장할 컬럼이 없었다.

**결정**: Claude Code에 맞는 7컬럼 독립 스키마 도입.

### 1.2 버전 단위 → 불릿 단위

초기 파서는 `## 2.1.63` 헤더 하나를 이벤트 하나로 취급했다. 한 버전에 10개 이상의 변경사항이 포함될 수 있어 이벤트 단위가 너무 굵었다. 변경 유형별 필터링이나 서브시스템별 분석이 불가능했다.

**결정**: 불릿(`- `) 하나를 이벤트 하나로 분해. 동일 버전의 변경사항을 개별 추적 가능.

### 1.3 수동 날짜 매핑 → npm 자동 조회

초기 구현은 `_CLAUDE_CODE_DATE_MAP` dict에 버전→날짜를 하드코딩하고, `_CLAUDE_CODE_INCLUDE_VERSIONS` set으로 포함 버전을 수동 관리했다. 새 버전이 릴리즈될 때마다 코드를 수정해야 했다.

**결정**: npm 레지스트리(`@anthropic-ai/claude-code`)에서 publish 날짜를 자동 조회. 24시간 파일 캐시로 성능과 안정성 확보.

---

## 2. Before/After 비교표

| 항목 | Before (초기) | After (현재) |
|------|-------------|-------------|
| **DB 테이블** | `update_event` (공통 15컬럼) | `claude_code_event` (독립 7컬럼) |
| **이벤트 단위** | 버전 하나 = 이벤트 하나 | 불릿 하나 = 이벤트 하나 |
| **날짜 소스** | `_CLAUDE_CODE_DATE_MAP` (수동 dict) | npm registry 자동 조회 + 24h 캐시 |
| **포함 버전 관리** | `_CLAUDE_CODE_INCLUDE_VERSIONS` (수동 set) | `date_str >= "2025-01-01"` 자동 필터 |
| **파서 출력 필드** | `product, event_date, title, summary_ko, tags, severity, source_url` | `product, event_date, title, version, change_type, subsystem, source_url` |
| **변경 유형 분류** | 없음 | `change_type` 컬럼 (첫 단어 기반 자동 분류) |
| **서브시스템 추출** | 없음 | `subsystem` 컬럼 (bracket/colon 접두어 파싱) |
| **유지보수 부담** | 새 버전마다 dict/set 수동 갱신 | 코드 변경 불필요 |

---

## 3. 독립 테이블 스키마

정의 위치: `apps/api/database.py:115-129`

### 3.1 `claude_code_event` CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS claude_code_event (
    id            TEXT PRIMARY KEY,
    event_date    TEXT NOT NULL,
    title         TEXT NOT NULL,
    version       TEXT NOT NULL,
    change_type   TEXT NOT NULL,
    subsystem     TEXT,
    source_url    TEXT NOT NULL DEFAULT 'https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md',
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 3.2 컬럼 상세

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|-------|------|
| `id` | TEXT PK | NO | - | UUID v4 |
| `event_date` | TEXT | NO | - | npm publish 날짜 (`YYYY-MM-DD`) |
| `title` | TEXT | NO | - | 불릿 텍스트 (변경사항 1줄) |
| `version` | TEXT | NO | - | 릴리즈 버전 (`"2.1.63"`) |
| `change_type` | TEXT | NO | - | 변경 유형 (`added`, `fixed`, `improved`, `changed`, `removed`, `updated`, `deprecated`, `other`) |
| `subsystem` | TEXT | YES | `NULL` | 서브시스템 (`vscode`, `sdk`, `mcp` 등) |
| `source_url` | TEXT | NO | CHANGELOG.md URL | 원본 소스 URL |
| `created_at` | TEXT | NO | `datetime('now')` | 생성 시각 |
| `updated_at` | TEXT | NO | `datetime('now')` | 수정 시각 |

### 3.3 인덱스

| 인덱스 | 컬럼 | 용도 |
|--------|------|------|
| `idx_claude_code_unique` | `UNIQUE(event_date, title)` | 중복 방지 (`INSERT OR IGNORE`) |
| `idx_claude_code_event_date` | `event_date DESC` | 날짜순 조회 |
| `idx_claude_code_change_type` | `change_type` | 변경 유형별 필터 |
| `idx_claude_code_version` | `version` | 버전별 조회 |

### 3.4 마이그레이션

`init_db()` 실행 시, 기존 테이블에 `change_type` 컬럼이 없으면 구 스키마로 판단하여 자동 DROP + 재생성한다 (`database.py:194-205`).

```python
cols = {r[1] for r in conn.execute("PRAGMA table_info(claude_code_event)").fetchall()}
if cols and "change_type" not in cols:
    conn.execute("DROP TABLE IF EXISTS claude_code_event")
```

---

## 4. 파서 아키텍처

파서 위치: `scripts/parsers/claude_code.py`

### 4.1 npm 날짜 자동화

**함수**: `_fetch_npm_dates(force: bool = False) -> dict[str, str]`

```
npm view @anthropic-ai/claude-code time --json
  │
  ▼
{"0.2.0": "2025-03-05T12:34:56.789Z", "modified": "...", ...}
  │
  ▼
date_map: {"0.2.0": "2025-03-05", "0.2.1": "2025-03-12", ...}
  │
  ▼
data/cache/npm_versions.json 에 저장
```

| 항목 | 값 |
|------|-----|
| npm 패키지 | `@anthropic-ai/claude-code` |
| 명령어 | `npm view @anthropic-ai/claude-code time --json` |
| 캐시 파일 | `data/cache/npm_versions.json` |
| 캐시 TTL | 24시간 (`86_400`초) |
| Windows 호환 | `shell=True` (npm.cmd 실행) |
| 타임아웃 | 30초 |

**캐시 전략:**

1. 캐시 파일이 존재하고 24시간 이내 → 캐시 사용
2. npm 조회 성공 → 결과 저장 후 반환
3. npm 조회 실패 → `_load_cache_fallback()`: 만료된 캐시라도 읽어서 반환
4. 캐시도 없음 → 빈 dict 반환 (해당 버전의 이벤트는 건너뜀)

### 4.2 `change_type` 분류 매핑표

**함수**: `_extract_change_type(text: str) -> str`

불릿 텍스트의 **첫 단어**를 소문자로 변환한 뒤 `_CHANGE_TYPE_MAP`에서 조회한다. 콜론(`:`)과 마침표(`.`)는 제거한다. 매칭되지 않으면 `"other"`.

| 입력 키워드 | 매핑 결과 |
|------------|----------|
| `added`, `add`, `new` | `added` |
| `fixed`, `fix` | `fixed` |
| `improved`, `improve`, `enhanced` | `improved` |
| `changed` | `changed` |
| `removed`, `remove` | `removed` |
| `updated`, `update` | `updated` |
| `deprecated` | `deprecated` |
| *(기타)* | `other` |

**예시:**

| 불릿 텍스트 | 첫 단어 | `change_type` |
|------------|---------|--------------|
| `"Added multi-turn editing support"` | `added` | `added` |
| `"Fix crash on Windows startup"` | `fix` | `fixed` |
| `"[VSCode] Improved sidebar performance"` | `[vscode]` | `other` (bracket이 첫 단어) |

> 주의: bracket 접두어(`[VSCode]`)가 첫 단어인 경우 `change_type`은 `"other"`가 된다. 이는 subsystem 추출과 별도로 동작하기 때문이다.

### 4.3 `subsystem` 추출 + 정규화표

**함수**: `_extract_subsystem(text: str) -> str | None`

두 가지 패턴을 순차 검사한다:

1. **Bracket 패턴**: `^\[([A-Za-z][A-Za-z0-9 ]*)\]\s*` — 예: `[VSCode] Added ...`
2. **Colon 패턴**: `^([A-Za-z][A-Za-z0-9 ]{1,20}):\s+` — 예: `Windows: Fixed ...`
   - Colon 패턴은 `_SUBSYSTEM_NORMALIZE` dict에 등록된 키워드만 매칭 (오탐 방지)

**`_SUBSYSTEM_NORMALIZE` 정규화표:**

| 입력 키 | 정규화 결과 |
|---------|-----------|
| `vscode`, `vs code`, `vscode extension` | `vscode` |
| `sdk` | `sdk` |
| `ide` | `ide` |
| `jetbrains` | `jetbrains` |
| `windows` | `windows` |
| `linux` | `linux` |
| `macos`, `mac` | `macos` |
| `mcp` | `mcp` |
| `hooks`, `hook` | `hooks` |
| `bedrock` | `bedrock` |
| `vertex` | `vertex` |
| `agents`, `agent` | `agents` |
| `settings` | `settings` |
| `memory` | `memory` |
| `terminal` | `terminal` |
| `git` | `git` |
| `oauth` | `oauth` |
| `permissions` | `permissions` |
| `api` | `api` |
| `max` | `max` |

- Bracket 패턴에 매칭되면 정규화표에서 조회. 등록되지 않은 키는 소문자 그대로 사용.
- Colon 패턴은 정규화표에 등록된 키워드만 매칭. 미등록 키는 `None` 반환.
- 두 패턴 모두 매칭 안 되면 `None`.

### 4.4 Markdown 버전 파싱

**함수**: `_parse_versions(md: str) -> list[tuple[str, list[str]]]`

```
CHANGELOG.md 전문
  │
  ▼
정규식: r"^## (\d+\.\d+\.\d+)\s*$"  (MULTILINE)
  │
  ▼
버전 헤더 위치 목록: [(match_0, "2.1.63"), (match_1, "2.1.62"), ...]
  │
  ▼
각 버전 영역에서 "- " 접두어 라인만 추출
  │
  ▼
[("2.1.63", ["Added ...", "[VSCode] Fixed ...", ...]),
 ("2.1.62", ["Improved ...", ...]),
 ...]
```

- `## X.Y.Z` 패턴만 인식 (3-part semver)
- 각 버전 헤더 사이의 텍스트에서 `- ` 시작 라인만 불릿으로 수집
- 불릿이 없는 버전은 건너뜀

---

## 5. 데이터 흐름

```
GitHub raw CHANGELOG.md
  │
  │  fetch_source("claude_code") — httpx 또는 Playwright
  ▼
data/snapshots/claude_code_latest.md
  │
  │  parse_claude_code(md)
  ├──────────────────────────────────────────┐
  │                                          │
  │  _fetch_npm_dates()                      │  _parse_versions(md)
  │  ┌──────────────────┐                    │  ┌──────────────────┐
  │  │ npm registry 조회  │                    │  │ ## X.Y.Z 파싱     │
  │  │ → 24h 캐시 확인    │                    │  │ → 불릿 추출        │
  │  │ → fallback       │                    │  │                  │
  │  └──────┬───────────┘                    │  └──────┬───────────┘
  │         │                                │         │
  │         ▼                                │         ▼
  │  date_map: {version: date}               │  [(version, [bullets])]
  │         │                                │         │
  └─────────┼────────────────────────────────┘         │
            │                                          │
            ▼                                          │
    버전별 날짜 매핑 + 2025-01-01 이후 필터              │
            │                                          │
            ▼                                          │
    각 불릿에 대해:                                      │
      - _extract_change_type(bullet) → change_type      │
      - _extract_subsystem(bullet) → subsystem          │
            │                                          │
            ▼                                          │
    list[dict] — 이벤트 목록                             │
            │
            │  insert_events() / _insert_claude_code_event()
            ▼
    data/tracker.db :: claude_code_event 테이블
```

**날짜 필터**: `date_str < "2025-01-01"` 인 버전은 건너뛴다. npm에 날짜가 없는 버전도 건너뛴다.

**파서 출력 dict:**

```python
{
    "product": "claude_code",
    "event_date": "2026-03-01",         # npm publish date
    "title": "[VSCode] Fixed sidebar",  # bullet text
    "version": "2.1.63",               # from ## header
    "change_type": "fixed",            # from _extract_change_type()
    "subsystem": "vscode",             # from _extract_subsystem()
    "source_url": "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md",
}
```

---

## 6. `all_events` VIEW 매핑

정의 위치: `apps/api/database.py:145-170`

`claude_code_event` → 공통 VIEW 컬럼 projection:

| VIEW 컬럼 | 소스 | 설명 |
|-----------|------|------|
| `id` | `id` | 그대로 |
| `component` | `change_type` | 변경 유형을 component로 매핑 |
| `event_date` | `event_date` | 그대로 |
| `detected_at` | `created_at` | created_at으로 대체 |
| `title` | `title` | 그대로 |
| `title_ko` | `NULL` | 불릿 텍스트에 한국어 제목 없음 |
| `summary_ko` | `title` | title을 summary_ko로 재사용 |
| `summary_en` | `NULL` | 별도 영문 요약 없음 |
| `tags` | `'[]'` | 고정값 (태그 미사용) |
| `severity` | `1` | 고정값 (심각도 미사용) |
| `source_url` | `source_url` | 그대로 |
| `evidence_excerpt` | `'[]'` | 고정값 |
| `raw_ref` | `'{}'` | 고정값 |
| `created_at` | `created_at` | 그대로 |
| `updated_at` | `updated_at` | 그대로 |
| `product` | `'claude_code'` | 고정 리터럴 |

> Claude Code는 독립 스키마이므로 `tags`, `severity`, `evidence_excerpt`, `raw_ref` 등 공통 필드는 기본값으로 채워진다. VIEW를 통한 조회 시에만 이 매핑이 적용되며, 제품별 직접 조회(`GET /api/events?product=claude_code`)는 `claude_code_event` 테이블을 직접 쿼리한다.

---

## 7. 관련 파일 목록

| 파일 | 역할 |
|------|------|
| `scripts/parsers/claude_code.py` | Claude Code MD 파서 (bullet-level + npm 날짜 + change_type/subsystem) |
| `apps/api/database.py` | `claude_code_event` CREATE TABLE + 인덱스 + `all_events` VIEW 정의 |
| `scripts/collect.py` | `_insert_claude_code_event()` — DB INSERT 함수 |
| `scripts/backfill/claude_code.py` | Claude Code backfill 전략 (스냅샷 → 파서 → DB) |
| `data/cache/npm_versions.json` | npm publish 날짜 캐시 (24h TTL) |
| `data/snapshots/claude_code_latest.md` | CHANGELOG.md 스냅샷 파일 |

---

## 참조 문서

| 문서 | 내용 |
|------|------|
| `docs/data-pipeline.md` | 전체 데이터 파이프라인 (4개 제품 통합) |
| `docs/61-backfill-refactoring.md` | backfill 패키지 분리 리팩터링 |
