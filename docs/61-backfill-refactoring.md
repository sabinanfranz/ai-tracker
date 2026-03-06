# Backfill 리팩터링: 단일 파일 → 패키지 분리

> `scripts/backfill.py` 단일 파일을 `scripts/backfill/` 패키지로 분리한 리팩터링에 대한 설명 문서.

---

## 1. 변경 동기

기존 `scripts/backfill.py`는 4개 제품(ChatGPT, Gemini, Codex, Claude Code)의 백필 로직을 하나의 파일에 담고 있었다. 제품마다 다음 차이가 존재하여 단일 파일 유지보수가 어려워졌다:

| 차이점 | 예시 |
|--------|------|
| **DB 스키마** | ChatGPT는 5컬럼, Codex는 7컬럼, Gemini는 15컬럼 |
| **파서** | HTML 파서 3종 + Markdown 파서 1종 |
| **스냅샷 포맷** | `.html` 3개 + `.md` 1개 |
| **특수 로직** | Claude Code는 버전→날짜 수동 매핑, Gemini는 이중 레이아웃 처리 |

패키지 분리로 얻는 이점:

- **단일 책임**: 제품별 모듈이 자기 스키마·파서·스냅샷만 관리
- **독립 수정**: 한 제품의 파서 변경이 다른 제품에 영향을 주지 않음
- **테스트 용이**: 제품별 모듈을 독립적으로 테스트 가능

---

## 2. Before/After 구조

### Before (단일 파일)

```
scripts/
  backfill.py          # 모든 제품의 백필 로직 + CLI + 파서 호출
```

### After (패키지)

```
scripts/
  backfill/
    __init__.py        # 공통 유틸 + CLI 진입점 + run_backfill() 오케스트레이터
    __main__.py        # python -m scripts.backfill 지원
    chatgpt.py         # ChatGPT 백필 전략
    codex.py           # Codex 백필 전략
    gemini.py          # Gemini 백필 전략
    claude_code.py     # Claude Code 백필 전략
```

---

## 3. 아키텍처

### 3.1 모듈 역할

| 모듈 | 역할 |
|------|------|
| `__init__.py` | 공통 유틸(`_safe_print`, `clear_table`, `run_backfill`), CLI 진입점(`main`), 리포트 출력 |
| `__main__.py` | `python -m scripts.backfill` 실행 시 `main()` 호출 (2줄) |
| `chatgpt.py` | ChatGPT 스냅샷 로드 → `parse_chatgpt()` → `insert_events()` |
| `codex.py` | Codex 스냅샷 로드 → `parse_codex()` → `insert_events()` |
| `gemini.py` | Gemini 스냅샷 로드 → `parse_gemini()` → `insert_events()` |
| `claude_code.py` | Claude Code 스냅샷 로드 → `parse_claude_code()` → `insert_events()` |

### 3.2 의존성 흐름도

```
scripts/backfill/__init__.py
  ├── apps.api.database          (PRODUCT_TABLES, get_connection, init_db)
  └── run_backfill()
        ├── scripts.backfill.chatgpt.backfill()
        ├── scripts.backfill.codex.backfill()
        ├── scripts.backfill.gemini.backfill()
        └── scripts.backfill.claude_code.backfill()

scripts/backfill/{product}.py  (각 제품 모듈)
  ├── scripts.backfill           (_safe_print, clear_table, SNAPSHOTS_DIR)
  ├── scripts.collect            (insert_events)
  └── scripts.parsers.{product}  (parse_{product})
```

각 제품 모듈은 동일한 3-레이어 의존 구조를 따른다:

1. **`scripts.backfill`** — 공통 유틸 (`clear_table`, `_safe_print`, `SNAPSHOTS_DIR`)
2. **`scripts.parsers.{product}`** — 제품별 파서 (HTML/MD → `list[dict]`)
3. **`scripts.collect`** — DB 삽입 (`insert_events`)

---

## 4. 제품별 전략 비교표

| 항목 | ChatGPT | Codex | Gemini | Claude Code |
|------|---------|-------|--------|-------------|
| **DB 테이블** | `chatgpt_event` | `codex_event` | `gemini_event` | `claude_code_event` |
| **스키마 컬럼 수** | 5 (simple) | 7 (independent) | 15 (common, severity/tags 포함) | 7 (independent) |
| **스냅샷 파일** | `chatgpt_latest.html` | `codex_latest.html` | `gemini_latest.html` | `claude_code_latest.md` |
| **스냅샷 포맷** | HTML | HTML | HTML | Markdown |
| **파서 위치** | `scripts/parsers/chatgpt.py` | `scripts/parsers/codex.py` | `scripts/parsers/gemini.py` | `scripts/parsers/claude_code.py` |
| **특수 로직** | 영문 날짜 정규식 | `<time>` 태그 직접 추출 | 이중 레이아웃(2024 old / 2025+ new) | 버전→날짜 수동 매핑, 포함 버전 필터 |

---

## 5. 공통 유틸 API (`scripts/backfill/__init__.py`)

### `_safe_print(text: str) -> None`

Windows 터미널(cp949/utf-8)에서 유니코드 출력 시 `UnicodeEncodeError`를 방지한다. 에러 발생 시 ASCII로 대체 출력한다.

### `clear_table(product: str) -> int`

지정 제품의 이벤트 테이블에서 모든 행을 삭제한다. `PRODUCT_TABLES` dict를 참조하여 테이블명을 결정한다. 삭제된 행 수를 반환한다.

```python
clear_table("gemini")  # gemini_event 테이블 전체 삭제, 삭제 건수 반환
```

### `run_backfill(product: str, *, reparse: bool = False) -> dict`

단일 제품의 백필을 실행한다. 내부적으로 해당 제품 모듈의 `backfill()` 함수를 호출한다.

- `reparse=False` (기본): INSERT OR IGNORE — 기존 데이터 보존
- `reparse=True`: 기존 데이터 삭제 후 재삽입

반환값: `{"parsed": int, "inserted": int, "skipped": int, "error"?: str}`

---

## 6. CLI 사용법

실행 명령: `python -m scripts.backfill [옵션]`

| 플래그 | 동작 모드 | 기존 데이터 처리 |
|--------|----------|----------------|
| (없음) | 전체 제품 백필 | INSERT OR IGNORE (기존 보존) |
| `--chatgpt` | ChatGPT만 재백필 | DELETE + 재삽입 |
| `--codex` | Codex만 재백필 | DELETE + 재삽입 |
| `--gemini` | Gemini만 재백필 | DELETE + 재삽입 |
| `--claude-code` | Claude Code만 재백필 | DELETE + 재삽입 |
| `--all` | 전체 제품 재백필 | DELETE + 재삽입 (제품별 순차) |

**동작 차이:**

- **플래그 없음**: 4개 제품을 순차 실행하며, 이미 존재하는 이벤트는 건너뛴다 (`INSERT OR IGNORE`). 전체 리포트를 출력한다.
- **제품별 플래그**: 해당 제품의 기존 이벤트를 모두 삭제한 후 다시 파싱·삽입한다. 단일 제품 리포트를 출력한다.
- **`--all`**: 4개 제품 각각에 대해 삭제 + 재삽입을 순차적으로 수행한다.

---

## 7. 데이터 흐름

```
data/snapshots/{product}_latest.{html|md}
  │
  ▼
scripts/parsers/{product}.py :: parse_{product}()
  │  HTML/MD → list[dict] 변환
  ▼
scripts/backfill/{product}.py :: backfill()
  │  reparse=True 이면 clear_table() 먼저 실행
  ▼
scripts/collect.py :: insert_events()
  │  DB INSERT (OR IGNORE)
  ▼
data/tracker.db :: {product}_event 테이블
```

각 제품 모듈의 `backfill()` 함수는 동일한 패턴을 따른다:

1. `reparse=True`이면 `clear_table(product)` 호출
2. 스냅샷 파일 존재 여부 확인
3. 파일을 UTF-8로 읽기
4. 제품별 파서 호출 (`parse_{product}()`)
5. 파싱 결과가 비어있으면 즉시 반환
6. `insert_events(events)` 호출
7. `{"parsed", "inserted", "skipped"}` dict 반환

---

## 8. 변경 영향 범위

### 변경된 파일

| 파일 | 변경 내용 |
|------|----------|
| `scripts/backfill.py` | **삭제** — 패키지로 대체 |
| `scripts/backfill/__init__.py` | **신규** — 공통 유틸 + CLI + 오케스트레이터 |
| `scripts/backfill/__main__.py` | **신규** — `python -m` 실행 지원 |
| `scripts/backfill/chatgpt.py` | **신규** — ChatGPT 백필 전략 |
| `scripts/backfill/codex.py` | **신규** — Codex 백필 전략 |
| `scripts/backfill/gemini.py` | **신규** — Gemini 백필 전략 |
| `scripts/backfill/claude_code.py` | **신규** — Claude Code 백필 전략 |

### 변경되지 않은 파일

| 파일 | 이유 |
|------|------|
| `scripts/parsers/` | 파서 로직은 이미 별도 패키지로 분리되어 있었음 |
| `scripts/collect.py` | `insert_events()` API 변경 없음 |
| `apps/api/database.py` | `PRODUCT_TABLES`, `get_connection`, `init_db` API 변경 없음 |
| `scripts/generate_title_ko.py` | backfill과 독립적 |
| `apps/api/` | API 서빙 레이어는 backfill과 무관 |

### 외부 인터페이스 호환성

- **CLI 명령어**: `python -m scripts.backfill [옵션]` — 변경 없음
- **DB 스키마**: 변경 없음
- **파서 출력 형식**: 변경 없음
