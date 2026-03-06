# 31 — ChatGPT 파싱 전략 & 테이블 구조

## 1. HTML 원본 구조

ChatGPT Release Notes 페이지(`help.openai.com/en/articles/6825453-chatgpt-release-notes`)의 HTML은 시맨틱 헤딩 계층으로 구성된다.

```
ChatGPT Release Notes page
├── h1: "ChatGPT — Release Notes"        ← 스킵
├── h1: "February 25, 2026"              ← 날짜 마커
│   ├── h2: "Feature Title 1"            ← 이벤트 제목
│   │   ├── h3: "Web"                    ← 플랫폼 서브섹션
│   │   │   └── ul/ol: bullet points
│   │   ├── h3: "iOS"
│   │   │   └── ul/ol: bullet points
│   │   └── h3: "Android"
│   │       └── ul/ol: bullet points
│   ├── h2: "Feature Title 2"
│   │   └── p/ul/ol: 본문
│   └── ...
├── h1: "January 20, 2026"              ← 다음 날짜
│   └── ...
└── ...
```

### 패턴 변형

| 패턴 | 설명 | 처리 방식 |
|------|------|-----------|
| h1 → h2 → h3 → ul | 표준 구조 | h2=제목, h3=플랫폼 접두사 |
| h1 → h3 → ul (h2 없음) | h3이 직접 등장 | h3을 이벤트 제목으로 승격 |
| h1 → p/ul (h2/h3 없음) | 헤딩 없는 본문 | 모든 p/ul을 하나의 이벤트로 병합 |

---

## 2. 파싱 전략

**파서 위치:** `scripts/parsers/chatgpt.py`

### 핵심 함수

| 함수 | 역할 |
|------|------|
| `parse_chatgpt(html)` | 진입점. h1 기준 날짜 추출 → 2025-01-01 이후만 필터 → 형제 노드 그루핑 |
| `_group_siblings(siblings)` | h2/h3 기준으로 콘텐츠 그룹 생성 |
| `_extract_list_items(ul_or_ol)` | `<li>` 직계 자식만 추출 (재귀 없음) |
| `_group_to_event(group, date_str)` | 그룹 → 이벤트 dict 변환 |

### 파싱 흐름

```
HTML 입력
  ↓
1. BeautifulSoup 파싱
  ↓
2. 모든 h1 태그 수집
  ↓
3. h1 텍스트 → parse_en_date() → YYYY-MM-DD
   (날짜 파싱 실패 시 스킵, "Release Notes" 제목 스킵)
  ↓
4. 날짜 >= "2025-01-01" 필터링
  ↓
5. 연속 h1 사이의 형제 노드 수집
  ↓
6. _group_siblings() → 콘텐츠 그룹 리스트
  ↓
7. 각 그룹 → _group_to_event() → 이벤트 dict
  ↓
출력: list[dict]
```

### 그룹 구조

`_group_siblings()`가 반환하는 그룹:

```python
{
    "title": str | None,       # h2 텍스트 (없으면 h3 텍스트)
    "content": [str],          # p/ul 텍스트
    "sub_sections": [          # h3 플랫폼별 섹션
        {
            "heading": str,    # "Web", "iOS", "Android"
            "items": [str]     # bullet point 텍스트
        }
    ]
}
```

### 제목 결정 로직

우선순위 (높은 것부터):
1. h2 텍스트
2. h3 텍스트 (h2 없을 때)
3. 첫 번째 content 텍스트 (최대 100자)
4. 폴백: `"ChatGPT update {date}"`

최종 제목은 **200자**에서 잘림.

---

## 3. 테이블 스키마

### chatgpt_event

```sql
CREATE TABLE IF NOT EXISTS chatgpt_event (
    id          TEXT PRIMARY KEY,           -- UUID v4
    event_date  TEXT NOT NULL,              -- YYYY-MM-DD
    title       TEXT NOT NULL,              -- 최대 200자
    content     TEXT NOT NULL DEFAULT '',   -- 멀티라인 텍스트
    source_url  TEXT NOT NULL,              -- 고정 URL
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(event_date, title)
);

CREATE INDEX IF NOT EXISTS idx_chatgpt_event_date
    ON chatgpt_event(event_date DESC);
```

### 다른 제품 테이블과의 차이

| 컬럼 | chatgpt_event | gemini_event | update_event (공통) |
|------|--------------|-------------|-------------------|
| component | 없음 | O | O |
| detected_at | 없음 | O | O |
| title_ko | 없음 | O | - |
| summary_ko | 없음 (content로 대체) | O | O |
| summary_en | 없음 | O | O |
| tags | 없음 | O | O |
| severity | 없음 | O | O |
| evidence_excerpt | 없음 | O | O |
| raw_ref | 없음 | O | O |
| updated_at | 없음 | O | O |

> chatgpt_event는 **최소 컬럼 설계**. 태그·심각도 등 메타데이터는 VIEW에서 기본값으로 보충.

---

## 4. VIEW 매핑

### all_events VIEW (ChatGPT 부분)

```sql
CREATE VIEW IF NOT EXISTS all_events AS
SELECT
    id,
    'default'    AS component,
    event_date,
    created_at   AS detected_at,       -- created_at을 detected_at으로 매핑
    title,
    NULL         AS title_ko,
    content      AS summary_ko,        -- content → summary_ko
    NULL         AS summary_en,
    '[]'         AS tags,              -- 빈 배열
    1            AS severity,          -- 기본값 1 (최저)
    source_url,
    '[]'         AS evidence_excerpt,  -- 빈 배열
    '{}'         AS raw_ref,           -- 빈 객체
    created_at,
    created_at   AS updated_at,        -- updated_at 없으므로 created_at 재사용
    'chatgpt'    AS product
FROM chatgpt_event

UNION ALL
-- gemini_event, claude_code_event 등 ...
```

### 매핑 요약

| chatgpt_event 컬럼 | all_events 컬럼 | 변환 |
|---|---|---|
| id | id | 그대로 |
| (없음) | component | `'default'` 고정 |
| event_date | event_date | 그대로 |
| created_at | detected_at | 컬럼명 변경 |
| title | title | 그대로 |
| (없음) | title_ko | `NULL` |
| content | summary_ko | 컬럼명 변경 |
| (없음) | summary_en | `NULL` |
| (없음) | tags | `'[]'` |
| (없음) | severity | `1` |
| source_url | source_url | 그대로 |
| (없음) | evidence_excerpt | `'[]'` |
| (없음) | raw_ref | `'{}'` |
| created_at | created_at | 그대로 |
| created_at | updated_at | 재사용 |
| (없음) | product | `'chatgpt'` 고정 |

---

## 5. content 형식 규칙

### 생성 로직

```python
lines: list[str] = list(group["content"])       # p/ul 직접 텍스트
for sub in group["sub_sections"]:
    prefix = sub["heading"]                      # "Web", "iOS" 등
    for item in sub["items"]:
        lines.append(f"{prefix}: {item}")        # 플랫폼 접두사
content = "\n".join(lines)                       # 줄바꿈 결합
```

### 형식 예시

**서브섹션이 있는 경우:**
```
Web: Canvas is now available in the sidebar for all users
Web: Improved search results with better relevance
iOS: Fixed an issue where notifications were delayed
Android: Added support for voice input in all languages
```

**서브섹션이 없는 경우 (p/ul만):**
```
GPT-4.5 is now available in research preview for Plus, Pro, and Team users.
The model shows improved emotional intelligence and broader knowledge.
```

### 텍스트 정규화

| 규칙 | 설명 |
|------|------|
| HTML 태그 제거 | `.get_text(strip=True)` 사용 |
| 공백 정리 | 앞뒤 공백 strip |
| 빈 항목 스킵 | 빈 문자열은 content에 포함하지 않음 |
| li 추출 | 직계 자식 `<li>`만 (중첩 li 무시) |

---

## 6. 중복 방지

### DB 레벨
- `UNIQUE(event_date, title)` 제약조건
- `INSERT OR IGNORE`로 중복 시 무시

### 애플리케이션 레벨
- `check_duplicate()`: `difflib.SequenceMatcher` 사용
- **유사도 임계값: 0.7** (70% 이상 유사하면 중복 판정)
- 비교 대상: `(event_date, title)` 쌍

---

## 7. 관련 파일

| 파일 | 역할 |
|------|------|
| `scripts/parsers/chatgpt.py` | HTML 파싱 로직 |
| `scripts/parsers/__init__.py` | 태그 분류 (`classify_tags`) |
| `scripts/collect.py` | 수집·삽입 유틸리티 |
| `scripts/backfill/chatgpt.py` | 전체 재파싱·재삽입 |
| `apps/api/database.py` | 테이블 생성 + VIEW 정의 |
| `data/snapshots/chatgpt_latest.html` | 원본 HTML 스냅샷 |
