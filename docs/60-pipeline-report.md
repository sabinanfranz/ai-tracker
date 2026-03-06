# 프로덕트별 데이터 파이프라인 보고서

> 생성일: 2026-03-04
> 대상 테이블: `update_event`
> 대상 필드: `title`, `summary_ko`, `summary_en`, `evidence_excerpt`, `tags`, `severity`, `title_ko`

---

## 파이프라인 개요

```
backfill.py → collect.py(insert) → localize_data.py → generate_title_ko.py
```

| 단계 | 스크립트 | 역할 |
|------|---------|------|
| 1단계 | `scripts/backfill.py` | HTML/MD 파싱 → title, summary_ko, evidence_excerpt, tags 생성 |
| 2단계 | `scripts/collect.py` | id, detected_at, severity 계산 후 DB INSERT |
| 3단계 | `scripts/localize_data.py` | 영어 summary_ko → 한국어 변환 (chatgpt/codex/claude_code만) |
| 4단계 | `scripts/generate_title_ko.py` | summary_ko에서 title_ko 헤드라인 생성 (전체 프로덕트) |

---

## DB 스키마 (`apps/api/database.py`)

```sql
CREATE TABLE update_event (
    id              TEXT PRIMARY KEY,       -- UUID
    product         TEXT NOT NULL,
    component       TEXT NOT NULL DEFAULT 'default',
    event_date      TEXT NOT NULL,
    detected_at     TEXT NOT NULL,
    title           TEXT NOT NULL,
    title_ko        TEXT,                   -- nullable
    summary_ko      TEXT NOT NULL,
    summary_en      TEXT,                   -- nullable
    tags            TEXT NOT NULL DEFAULT '[]',   -- JSON array
    severity        INTEGER NOT NULL DEFAULT 1,
    source_url      TEXT NOT NULL,
    evidence_excerpt TEXT NOT NULL DEFAULT '[]',  -- JSON array
    raw_ref         TEXT NOT NULL DEFAULT '{}'
);

UNIQUE INDEX: (product, event_date, title)
```

---

## 프로덕트별 상세 파이프라인

### 1. ChatGPT (102건)

| 항목 | 내용 |
|------|------|
| **소스 파일** | `data/snapshots/chatgpt_latest.html` |
| **소스 URL** | `https://help.openai.com/en/articles/6825453-chatgpt-release-notes` |
| **원문 언어** | 영어 |

#### 필드별 처리

| 필드 | 백필 (1단계) | INSERT (2단계) | 한국어화 (3단계) | title_ko 생성 (4단계) |
|------|-------------|---------------|-----------------|---------------------|
| **title** | HTML heading 텍스트. 순수 날짜면 첫 번째 bullet[:100] 또는 `"ChatGPT update {date}"` | 그대로 저장 | - | - |
| **summary_ko** | 첫 3개 bullet `"; "` 로 연결 (각 150자, 총 500자 제한). **영어 텍스트** | 그대로 저장 | 동사 패턴 매칭 + 용어 치환으로 **한국어 변환** | - |
| **summary_en** | 미설정 (None) | None으로 저장 | 원본 영어 텍스트를 summary_en에 **백업 저장** | - |
| **evidence_excerpt** | 첫 5개 bullet (각 200자 제한), JSON 배열 | JSON 직렬화 후 저장 | - | - |
| **tags** | `classify_tags(title + summary_ko)` → 영어 키워드 매칭 | JSON 직렬화 후 저장 | - | - |
| **severity** | - | `calculate_severity(title, summary_ko)` 영어 키워드 스캔 | - | - |
| **title_ko** | 미설정 | None으로 저장 | - | summary_ko(한국어)에서 최적 문장 선택 → 어미 제거 → 55자 절삭 |

#### ChatGPT 특이사항
- 릴리즈 노트가 **산문 형태** (예: "We're rolling out...", "Users can now share...")로 되어 있어 localize_data의 동사 패턴("Added X", "Fixed X")에 잘 매칭되지 않음
- 매칭 실패 시 용어 치환만 적용됨 (예: "slash commands" → "슬래시 명령어")
- 많은 항목이 부분적으로만 한국어화되는 한계 존재

---

### 2. Codex (48건)

| 항목 | 내용 |
|------|------|
| **소스 파일** | `data/snapshots/codex_latest.html` |
| **소스 URL** | `https://developers.openai.com/codex/changelog/` |
| **원문 언어** | 영어 |

#### 필드별 처리

| 필드 | 백필 (1단계) | INSERT (2단계) | 한국어화 (3단계) | title_ko 생성 (4단계) |
|------|-------------|---------------|-----------------|---------------------|
| **title** | `<h3>` 태그 텍스트 ("Copy link..." 접미사 제거) | 그대로 저장 | - | - |
| **summary_ko** | `<article>` 내 첫 3개 `<li>` `"; "`로 연결 (각 120자, 총 500자). **영어 텍스트** | 그대로 저장 | 동사 패턴 + 용어 치환으로 **한국어 변환** | - |
| **summary_en** | 미설정 (None) | None으로 저장 | 원본 영어 텍스트를 summary_en에 **백업 저장** | - |
| **evidence_excerpt** | `<article>` 내 첫 5개 `<li>` (각 200자), JSON 배열 | JSON 직렬화 후 저장 | - | - |
| **tags** | `classify_tags(title + summary_ko)` | JSON 직렬화 후 저장 | - | - |
| **severity** | - | `calculate_severity(title, summary_ko)` 영어 키워드 스캔 | - | - |
| **title_ko** | 미설정 | None으로 저장 | - | summary_ko(한국어)에서 헤드라인 생성 |

#### Codex 특이사항
- 체인지로그 형식으로 "Added X", "Fixed Y" 패턴이 잘 맞아 한국어화 품질이 높음
- bullet 항목 최대 길이가 120자로 chatgpt(150자)보다 짧음

---

### 3. Claude Code (54건)

| 항목 | 내용 |
|------|------|
| **소스 파일** | `data/snapshots/claude_code_latest.md` (마크다운) |
| **소스 URL** | `https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md` |
| **원문 언어** | 영어 |

#### 필드별 처리

| 필드 | 백필 (1단계) | INSERT (2단계) | 한국어화 (3단계) | title_ko 생성 (4단계) |
|------|-------------|---------------|-----------------|---------------------|
| **title** | 항상 `"Claude Code {version}"` (예: `"Claude Code 2.1.63"`) | 그대로 저장 | - | - |
| **summary_ko** | `[VSCode]`/`[SDK]`/`[IDE]` 제외 후 상위 3개 bullet `"; "`로 연결 (각 150자, 총 500자). **영어 텍스트** | 그대로 저장 | 동사 패턴 + 용어 치환으로 **한국어 변환** | - |
| **summary_en** | 미설정 (None) | None으로 저장 | 원본 영어 텍스트를 summary_en에 **백업 저장** | - |
| **evidence_excerpt** | 첫 5개 markdown bullet (각 200자), JSON 배열 | JSON 직렬화 후 저장 | - | - |
| **tags** | `classify_tags(title + summary_ko + 첫 10개 bullet)` ← **다른 제품보다 넓은 범위** | JSON 직렬화 후 저장 | - | - |
| **severity** | - | `calculate_severity(title, summary_ko)` 영어 키워드 스캔 | - | - |
| **title_ko** | 미설정 | None으로 저장 | - | summary_ko(한국어)에서 헤드라인 생성 |

#### Claude Code 특이사항
- 마크다운 체인지로그 형식 → "Added", "Fixed" 패턴 매칭률이 높음
- `[VSCode]`, `[SDK]`, `[IDE]` 접두사 bullet을 summary에서 **제외** (IDE 관련 변경은 주요 사용자 대상이 아니므로)
- tag 분류 시 title + summary_ko + **첫 10개 bullet 전체**를 스캔 → 다른 제품 대비 더 정확한 태그 매칭
- 버전 포함 여부는 `_CLAUDE_CODE_INCLUDE_VERSIONS` 집합과 `_CLAUDE_CODE_DATE_MAP` 딕셔너리에 **수동 등록** 필요

---

### 4. Gemini (30건)

| 항목 | 내용 |
|------|------|
| **소스 파일** | `data/snapshots/gemini_latest.html` |
| **소스 URL** | `https://gemini.google/release-notes/` |
| **원문 언어** | **한국어** (Korean 페이지) |

#### 필드별 처리

| 필드 | 백필 (1단계) | INSERT (2단계) | 한국어화 (3단계) | title_ko 생성 (4단계) |
|------|-------------|---------------|-----------------|---------------------|
| **title** | 첫 번째 `<h3>` 피처 타이틀 (200자 제한) | 그대로 저장 | - | - |
| **summary_ko** | `<h3>` 피처 타이틀 최대 5개 `"; "`로 연결 (500자). **이미 한국어** | 그대로 저장 | **건너뜀** (이미 한국어이므로 localize 대상 제외) | - |
| **summary_en** | 미설정 (None) | None으로 저장 | **설정 안 됨** (localize가 건너뛰므로 영어 원본 없음) | - |
| **evidence_excerpt** | `_featureBulletBody_` 내 `<p>` 텍스트. 한국어 볼드 접두사 (`내용:`, `이유:`, `무엇:`, `왜:`) 제거. 최대 5개, 각 200자 | JSON 직렬화 후 저장 | - | - |
| **tags** | `classify_tags(title + summary_ko)` ← **한국어 텍스트에 영어 키워드 매칭** | JSON 직렬화 후 저장 | - | - |
| **severity** | - | `calculate_severity(title, summary_ko)` ← **한국어 텍스트에 영어 키워드 매칭** | - | - |
| **title_ko** | 미설정 | None으로 저장 | - | summary_ko(한국어)에서 헤드라인 생성 |

#### Gemini 특이사항
- 유일하게 **한국어 소스**에서 파싱 → localize_data 완전히 건너뜀
- `summary_en`이 **영구적으로 NULL** (영어 원본 자체가 없음)
- tags/severity 계산이 **영어 키워드 기반**인데 텍스트는 한국어 → 정확도 저하
  - "model", "Gemini 2" 같은 영어 차용어는 매칭 가능
  - "fix", "launch", "breaking" 등 순수 영어 키워드는 매칭 불가
- HTML 구조가 **2가지** (OLD: `_releaseNoteCardBody_` / NEW: `_features_`)로 분기 처리

---

## 횡단 비교: 한국어화 처리 방식

```
┌────────────┬──────────────────┬──────────────────┬──────────────────┐
│            │ summary_ko 원본  │ localize_data    │ summary_en       │
├────────────┼──────────────────┼──────────────────┼──────────────────┤
│ ChatGPT    │ 영어 (산문체)    │ 패턴+용어 치환   │ 원본 영어 백업   │
│ Codex      │ 영어 (체인지로그)│ 패턴+용어 치환   │ 원본 영어 백업   │
│ Claude Code│ 영어 (체인지로그)│ 패턴+용어 치환   │ 원본 영어 백업   │
│ Gemini     │ 한국어 (네이티브)│ 건너뜀           │ NULL (영원히)    │
└────────────┴──────────────────┴──────────────────┴──────────────────┘
```

---

## 한국어화 세부 로직 (`localize_data.py`)

### 동사 패턴 매칭 (23개)

| 영어 패턴 | 한국어 변환 | 예시 |
|-----------|------------|------|
| `Added support for X` | `X 지원 추가` | "Added support for MCP" → "MCP 지원 추가" |
| `Added X` | `X 추가됨` | "Added theme picker" → "테마 선택기 추가됨" |
| `New X` | `새 X` | "New progress bar" → "새 진행 표시줄" |
| `Fixed [bug] [where/in] X` | `X 수정됨` | "Fixed a bug in auth" → "auth 수정됨" |
| `Improved X` | `X 개선됨` | "Improved error handling" → "오류 처리 개선됨" |
| `Updated X` | `X 업데이트됨` | |
| `Removed X` | `X 제거됨` | |
| `Enabled X` | `X 활성화됨` | |
| `Deprecated X` | `X 지원 종료 예정` | |
| `Introduced X` | `X 도입됨` | |
| `Launched/Released X` | `X 출시됨` | |
| `Renamed X` | `X 이름 변경됨` | |
| `Optimized X` | `X 최적화됨` | |
| `Switched to X` | `X(으)로 전환됨` | |
| `Claude now X` | `Claude가 이제 X` | |
| ... 외 8개 패턴 | | |

### 용어 치환 (35쌍)

| 영어 | 한국어 |
|------|--------|
| slash commands | 슬래시 명령어 |
| code blocks | 코드 블록 |
| auto-memory | 자동 메모리 |
| tool calls | 도구 호출 |
| error handling | 오류 처리 |
| rate limit | 사용량 제한 |
| system prompt | 시스템 프롬프트 |
| background tasks | 백그라운드 작업 |
| ... 외 27쌍 | |

---

## title_ko 생성 로직 (`generate_title_ko.py`)

```
1. summary_ko를 "." 또는 "。"로 문장 분할
2. 액션 키워드 포함 문장 우선 선택 (추가/출시/변경/수정/지원/제공/폐기/개선/통합/확대/인상/감소)
3. 없으면 첫 번째 문장 사용
4. ";" 포함 시 첫 번째 항목만 취함
5. 한국어 어미 제거 (습니다/입니다/됩니다 등 16종)
6. 괄호 내용 제거 (20자 이하)
7. 55자 초과 시 자연 경계(공백/쉼표/와/과/·/—)에서 절삭
8. 빈 결과면 영어 title 폴백
```

---

## 알려진 문제점

| # | 문제 | 영향 |
|---|------|------|
| 1 | ChatGPT 산문체 → 패턴 매칭률 낮음 | chatgpt summary_ko 다수가 영어+일부 용어만 한국어 |
| 2 | Gemini severity/tags 정확도 | 한국어 텍스트에 영어 키워드 매칭 → 일부 태그/중요도 누락 |
| 3 | Gemini summary_en = NULL | 프론트엔드에서 영어 전환 시 Gemini만 표시할 내용 없음 |
| 4 | test_api_events가 운영 DB 사용 | pytest 실행 시 `init_db()` + `DELETE` → 운영 데이터 삭제됨 |
| 5 | Claude Code 버전 수동 등록 | 신규 버전은 `_CLAUDE_CODE_INCLUDE_VERSIONS` + `_CLAUDE_CODE_DATE_MAP` 모두 수동 추가 필요 |
