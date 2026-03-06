# 70 — 제품별 파이프라인 · 문서 · 스킬 매핑

> 4개 AI 제품(ChatGPT, Codex, Claude Code, Gemini)의 데이터 수집부터 한국어 enrichment까지,
> 각 단계에서 어떤 스크립트·문서·스킬이 관여하는지를 한눈에 정리한다.

---

## 1. 전체 파이프라인 흐름

```
[1] Collect          소스 페이지 fetch → 스냅샷 저장
[2] Parse            스냅샷 → 이벤트 파싱 → DB INSERT
[3] Enrich (EN)      영문 title_updated / content_updated 생성
[4] Enrich (KO)      한국어 title_updated_ko / content_updated_ko 생성
[5] Serve            FastAPI REST API → 프론트엔드 타임라인
```

**제품별 파이프라인 비교:**

```
            Collect    Parse     Enrich(EN)           Enrich(KO)           Serve
            ───────    ─────     ──────────           ──────────           ─────
ChatGPT     공통       독립       enrich_chatgpt.py    enrich_chatgpt_ko.py  공통 API
Codex       공통       독립       enrich_codex.py      enrich_codex_ko.py    공통 API
Claude Code 공통       독립       (없음)               enrich_claude_code_   공통 API
                                                      kor.py
Gemini      공통       독립       (없음)               enrich_gemini.py      공통 API
```

---

## 2. 공통 인프라

모든 제품이 공유하는 파일과 문서.

### 스크립트

| 파일 | 역할 |
|------|------|
| `scripts/collect.py` | 4개 소스 fetch + 스냅샷 저장 + 이벤트 INSERT 분기 |
| `scripts/backfill/__init__.py` | 전체 백필 오케스트레이터 + CLI |
| `scripts/backfill/__main__.py` | `python -m scripts.backfill` 진입점 |
| `scripts/parsers/__init__.py` | 공통 유틸 (`parse_en_date`, `classify_tags`) |
| `scripts/seed.py` | 개발용 시드 데이터 (~30개) |
| `scripts/generate_title_ko.py` | summary_ko → title_ko 헤드라인 생성 (전 제품) |
| `scripts/localize_data.py` | 영어 summary_ko → 한국어 변환 (Gemini 제외) |

### API / DB

| 파일 | 역할 |
|------|------|
| `apps/api/main.py` | FastAPI 앱 진입점 |
| `apps/api/database.py` | 4개 제품별 테이블 DDL + `all_events` VIEW |
| `apps/api/routers/events.py` | `GET /api/events`, `GET /api/events/{id}` |
| `apps/api/routers/meta.py` | `GET /api/products`, `GET /api/tags` |
| `apps/api/services/scorer.py` | 키워드 기반 severity 계산 (1~5) |

### 문서

| 문서 | 내용 |
|------|------|
| `docs/00-brief.md` | MVP 한 줄 요약, 제약조건, 가정, 이벤트 스키마 |
| `docs/10-prd.md` | PRD — 문제정의, 유저스토리, 성공기준, 리스크 |
| `docs/20-ux.md` | UX 플로우, 와이어프레임 |
| `docs/30-architecture.md` | 시스템 아키텍처, DB 스키마, API 계약 |
| `docs/40-backlog.md` | 유저스토리 + 우선순위 + 체크박스 |
| `docs/50-test-plan.md` | 수동 체크 + 자동 테스트 |
| `docs/90-log.md` | 결정사항, 트레이드오프 |
| `docs/data-pipeline.md` | 전체 데이터 파이프라인 통합 문서 (가장 포괄적) |
| `docs/60-pipeline-report.md` | 제품별 파이프라인 상세 보고서 |
| `docs/61-backfill-refactoring.md` | backfill.py → backfill/ 패키지 분리 설명 |

---

## 3. ChatGPT

### 개요

| 항목 | 값 |
|------|-----|
| 소스 URL | `https://help.openai.com/en/articles/6825453-chatgpt-release-notes` |
| 원문 언어 | **영어** |
| 스냅샷 포맷 | HTML |
| DB 테이블 | `chatgpt_event` (5컬럼, simple) |
| 이벤트 단위 | h2/h3 기능 블록 단위 |

### 파이프라인 단계별 매핑

| 단계 | 스크립트 | 설명 |
|------|---------|------|
| **Collect** | `scripts/collect.py` | `chatgpt_latest.html` fetch |
| **Parse** | `scripts/parsers/chatgpt.py` | h1(날짜) → h2/h3(기능) → content 추출 |
| **Backfill** | `scripts/backfill/chatgpt.py` | 스냅샷 → 파서 → DB INSERT |
| **Localize** | `scripts/localize_data.py` | 영어 summary_ko → 한국어 변환 (동사 패턴 + 용어 치환) |
| **title_ko** | `scripts/generate_title_ko.py` | summary_ko에서 55자 헤드라인 생성 |
| **Enrich (EN)** | `scripts/enrich_chatgpt.py` | `title_updated`, `content_updated` 생성 |
| **Enrich (KO)** | `scripts/enrich_chatgpt_ko.py` | `title_updated_ko`, `content_updated_ko` 생성 |
| **INSERT** | `scripts/collect.py` → `_insert_chatgpt_event()` | `INSERT OR IGNORE` |

### 관련 문서

| 문서 | 내용 |
|------|------|
| `docs/31-chatgpt-schema.md` | ChatGPT HTML 구조, 파싱 전략, 테이블 스키마, VIEW 매핑 |
| `docs/32-chatgpt-enrichment-rules.md` | `title_updated` / `content_updated` 생성 규칙 (EN) — 8개 제목 패턴 분류(P1~P8), 변환 전략(T1~T9), 요약 규칙(C1~C8) |
| `docs/33-chatgpt-ko-enrichment-rules.md` | `title_updated_ko` / `content_updated_ko` 생성 규칙 (KO) — ~해요 체, 20~45자, 3줄 요약 |

### 관련 스킬

| 스킬 | 파일 | 역할 |
|------|------|------|
| **chatgpt-enricher** | `.claude/skills/chatgpt-enricher/SKILL.md` | EN enrichment (`title_updated`, `content_updated`) — 8개 제목 패턴(P1~P8), 변환 전략(T1~T9), 요약 규칙(C1~C8) |
| **chatgpt-ko-enricher** | `.claude/skills/chatgpt-ko-enricher/SKILL.md` | KO enrichment (`title_updated_ko`, `content_updated_ko`) — ~해요 체 제목 + ~습니다 체 3줄 요약 |

### 특이사항

- 릴리즈 노트가 **산문 형태**("We're rolling out...")로 되어 있어 `localize_data.py`의 동사 패턴 매칭률이 낮음
- `title_updated` 생성 시 8개 패턴 분류(VAGUE_PRODUCT_UPDATE, BARE_FEATURE_NAME 등)를 적용
- `content_updated`는 정확히 3줄, What / Details / Context 구조

### DB 스키마

```
chatgpt_event
├── id (PK)
├── event_date
├── title
├── content          ← 다른 제품의 summary_ko에 해당
├── source_url
├── created_at
├── title_updated    ← EN enrichment
├── content_updated  ← EN enrichment (3줄)
├── title_updated_ko ← KO enrichment
└── content_updated_ko ← KO enrichment (3줄)
```

---

## 4. Codex

### 개요

| 항목 | 값 |
|------|-----|
| 소스 URL | `https://developers.openai.com/codex/changelog/` |
| 원문 언어 | **영어** |
| 스냅샷 포맷 | HTML |
| DB 테이블 | `codex_event` (7+컬럼, independent) |
| 이벤트 단위 | `<li>` changelog 엔트리 단위 |

### 파이프라인 단계별 매핑

| 단계 | 스크립트 | 설명 |
|------|---------|------|
| **Collect** | `scripts/collect.py` | `codex_latest.html` fetch |
| **Parse** | `scripts/parsers/codex.py` | `<li>` → entry_type/version/body 추출 |
| **Backfill** | `scripts/backfill/codex.py` | 스냅샷 → 파서 → DB INSERT |
| **Enrich (EN)** | `scripts/enrich_codex.py` | `title_updated`, `content_updated` 생성 |
| **Enrich (KO)** | `scripts/enrich_codex_ko.py` | `title_updated_ko`, `content_updated_ko` 생성 |
| **INSERT** | `scripts/collect.py` → `_insert_codex_event()` | `INSERT OR IGNORE` |

### 관련 문서

| 문서 | 내용 |
|------|------|
| `docs/codex-parsing-strategy.md` | Codex HTML 구조, entry_type별 파싱 전략, 독립 스키마 설계 |
| `docs/65-codex-enrichment-logic.md` | EN/KO enrichment 규칙 — entry_type별(codex-cli/codex-app/general) 제목·요약 생성 + 한국어 의역 규칙 + 용어 매핑 |

### 관련 스킬

| 스킬 | 파일 | 역할 |
|------|------|------|
| **codex-enricher** | `skills/codex-enricher/SKILL.md` | EN enrichment (`title_updated`, `content_updated`) |
| **ko-enricher** | `skills/ko-enricher/SKILL.md` | KO enrichment (`title_updated_ko`, `content_updated_ko`) — 문장형 변환 |

### 특이사항

- 3가지 entry_type (`general`, `codex-app`, `codex-cli`)으로 구분되며, 각각 파싱·enrichment 전략이 다름
- `all_events` VIEW에서 **제외됨** — 독립 스키마의 `entry_type`/`body`가 공통 스키마와 호환 불가
- 체인지로그 형식("Added X", "Fixed Y")으로 한국어화 품질이 높음
- KO enrichment 시 키워드 나열형(A, B 및 C) → 문장형(~해요/~됐어요) 변환 규칙 적용

### DB 스키마

```
codex_event
├── id (PK)
├── event_date
├── title
├── entry_type       ← general | codex-app | codex-cli
├── version          ← app: "26.226", cli: "0.106.0", general: NULL
├── body             ← 구조화된 플레인 텍스트
├── source_url
├── created_at / updated_at
├── title_updated    ← EN enrichment
├── content_updated  ← EN enrichment (3줄)
├── title_updated_ko ← KO enrichment (문장형)
└── content_updated_ko ← KO enrichment (3줄)
```

---

## 5. Claude Code

### 개요

| 항목 | 값 |
|------|-----|
| 소스 URL | `https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md` |
| 원문 언어 | **영어** |
| 스냅샷 포맷 | Markdown |
| DB 테이블 | `claude_code_event` (7+컬럼, bullet-level) |
| 이벤트 단위 | **불릿 하나 = 이벤트 하나** (가장 세분화) |

### 파이프라인 단계별 매핑

| 단계 | 스크립트 | 설명 |
|------|---------|------|
| **Collect** | `scripts/collect.py` | `claude_code_latest.md` fetch (GitHub raw) |
| **Parse** | `scripts/parsers/claude_code.py` | `## X.Y.Z` → 불릿 분해 + npm 날짜 자동 조회 |
| **Backfill** | `scripts/backfill/claude_code.py` | 스냅샷 → 파서 → DB INSERT |
| **card_yn 분류** | `scripts/populate_card_yn.py` | 중요 변경사항 = `card_yn=1` 설정 |
| **classify** | `scripts/classify_other.py` | 분류 유틸 |
| **Enrich (KO)** | `scripts/enrich_claude_code_kor.py` | `title_kor`, `content_kor` 생성 (card_yn=1만) |
| **INSERT** | `scripts/collect.py` → `_insert_claude_code_event()` | `INSERT OR IGNORE` |

### 관련 문서

| 문서 | 내용 |
|------|------|
| `docs/62-claude-code-parsing.md` | 독립 스키마 도입 동기, bullet-level 파서 아키텍처, npm 날짜 자동화, change_type/subsystem 추출, VIEW 매핑 |
| `docs/60-card-kor-procedure.md` | 한국어 카드 번역 절차서 — title_kor(~해요 체, 30자), content_kor(불릿 3개), 검증 쿼리 |

### 관련 스킬

| 스킬 | 파일 | 역할 |
|------|------|------|
| **claude-code-card-classifier** | `.claude/skills/claude-code-card-classifier/SKILL.md` | card_yn 분류 — change_type + 정규식으로 카드뉴스 포함/제외 판정 |
| **claude-code-ko-enricher** | `skills/claude-code-ko-enricher/SKILL.md` | KO enrichment (`title_kor`, `content_kor`) — card_yn=1만 대상 |
| **changelog-classifier** | `.claude/skills/changelog-classifier.skill` | CHANGELOG.md 변경사항 분류 |

### 특이사항

- **영문 enrichment 스크립트가 없음** — 다른 3개 제품은 `enrich_*.py`(EN) + `enrich_*_ko.py`(KO) 쌍이 있지만, Claude Code는 `enrich_claude_code_kor.py`만 존재
- `card_yn` 플래그로 중요 변경사항만 선별하여 한국어 번역 대상으로 관리
- npm 레지스트리에서 버전→날짜 자동 조회 (24h 파일 캐시)
- `change_type` (added/fixed/improved 등) + `subsystem` (vscode/sdk/mcp 등) 자동 분류
- `populate_card_yn.py`, `classify_other.py`는 Claude Code 전용 유틸

### DB 스키마

```
claude_code_event
├── id (PK)
├── event_date       ← npm publish 날짜
├── title            ← 불릿 텍스트 그대로
├── version          ← "2.1.63"
├── change_type      ← added | fixed | improved | changed | removed | updated | deprecated | other
├── subsystem        ← vscode | sdk | mcp | hooks 등 (NULL 가능)
├── source_url
├── created_at / updated_at
├── card_yn          ← 중요 변경사항 플래그
├── title_kor        ← KO enrichment (~해요 체)
└── content_kor      ← KO enrichment (불릿 3개)
```

---

## 6. Gemini

### 개요

| 항목 | 값 |
|------|-----|
| 소스 URL | `https://gemini.google/release-notes/` |
| 원문 언어 | **한국어** (유일하게 한국어 소스) |
| 스냅샷 포맷 | HTML |
| DB 테이블 | `gemini_event` (15컬럼, common schema) |
| 이벤트 단위 | `_releaseNoteCard_` 단위 |

### 파이프라인 단계별 매핑

| 단계 | 스크립트 | 설명 |
|------|---------|------|
| **Collect** | `scripts/collect.py` | `gemini_latest.html` fetch |
| **Parse** | `scripts/parsers/gemini.py` | 이중 레이아웃(2024 old / 2025+ new) 처리 |
| **Backfill** | `scripts/backfill/gemini.py` | 스냅샷 → 파서 → DB INSERT |
| **title_ko 생성** | `scripts/generate_title_ko.py` | summary_ko에서 55자 헤드라인 (공통) |
| **Enrich (KO)** | `scripts/enrich_gemini.py` | `title_ko`, `content_ko` 생성 (JSON 기반 워크플로) |
| **INSERT** | `scripts/collect.py` → 공통 경로 | severity 자동 계산 포함 |

### 관련 문서

| 문서 | 내용 |
|------|------|
| `docs/enrich-gemini-procedure.md` | Gemini 한국어 enrichment 절차서 — title_ko(~해보세요!/~됩니다! 체), content_ko(3줄 친근체), JSON 워크플로 |

### 관련 스킬

| 스킬 | 파일 | 역할 |
|------|------|------|
| **gemini-ko-enricher** | `skills/gemini-ko-enricher/SKILL.md` | KO enrichment (`title_ko`, `content_ko`) — 안내·권유형 |

### 특이사항

- 유일하게 **한국어 소스**에서 파싱 → `localize_data.py` 완전히 건너뜀
- `summary_en`이 **영구적으로 NULL** (영어 원본 자체가 없음)
- tags/severity 계산이 **영어 키워드 기반**인데 텍스트는 한국어 → 정확도 저하 (모델명 등 영어 차용어만 매칭)
- HTML 구조가 **2가지** (OLD: `_releaseNoteCardBody_` / NEW: `_features_`)로 분기 처리
- KO enrichment가 **2개 스크립트에 분산** — `generate_title_ko.py`(공통 title_ko)와 `enrich_gemini.py`(전용 title_ko/content_ko)
- `enrich_gemini.py`는 JSON 파일 기반 워크플로 (generate → apply 패턴) — 다른 제품의 하드코딩 RECORDS 패턴과 다름
- 유일하게 공통 스키마(`_COMMON_COLS`) 사용 — severity, tags, evidence_excerpt 등 15컬럼 전부 보유

### DB 스키마

```
gemini_event
├── id (PK)
├── component
├── event_date
├── detected_at
├── title            ← 영문 (한국어 소스에서 추출한 영문 feature title)
├── title_ko         ← KO enrichment (~해보세요! 체)
├── summary_ko       ← 한국어 원문 그대로
├── summary_en       ← 영구 NULL (영어 원본 없음)
├── tags             ← JSON 배열
├── severity         ← 1~5
├── source_url
├── evidence_excerpt ← JSON 배열
├── raw_ref          ← JSON 객체
├── created_at / updated_at
├── content_ko       ← KO enrichment (3줄 친근체)
```

---

## 7. 횡단 비교표

### 7-1. 파서 비교

| 항목 | ChatGPT | Codex | Claude Code | Gemini |
|------|---------|-------|-------------|--------|
| **소스 포맷** | HTML | HTML | Markdown | HTML |
| **파서 파일** | `parsers/chatgpt.py` | `parsers/codex.py` | `parsers/claude_code.py` | `parsers/gemini.py` |
| **이벤트 단위** | h2/h3 기능 블록 | `<li>` 엔트리 | 불릿(`- `) 하나 | `_releaseNoteCard_` |
| **날짜 추출** | h1 영문 날짜 정규식 | `<time>` 태그 | npm 레지스트리 자동 | h2 `YYYY.MM.DD` |
| **특수 처리** | 산문 → content 병합 | entry_type 3종 분기 | change_type/subsystem 분류 | 이중 레이아웃 분기 |

### 7-2. DB 스키마 비교

| 항목 | ChatGPT | Codex | Claude Code | Gemini |
|------|---------|-------|-------------|--------|
| **테이블** | `chatgpt_event` | `codex_event` | `claude_code_event` | `gemini_event` |
| **컬럼 수** | 5+enrichment | 7+enrichment | 7+enrichment | 15 (common) |
| **스키마 유형** | 독립 (simple) | 독립 (independent) | 독립 (bullet-level) | 공통 (common) |
| **고유 컬럼** | `content` | `entry_type`, `version`, `body` | `version`, `change_type`, `subsystem`, `card_yn` | `severity`, `tags`, `evidence_excerpt` |
| **`all_events` VIEW** | O (content→summary_ko) | **X** (제외됨) | O (change_type→component) | O (그대로) |

### 7-3. Enrichment 비교

| 항목 | ChatGPT | Codex | Claude Code | Gemini |
|------|---------|-------|-------------|--------|
| **EN 스크립트** | `enrich_chatgpt.py` | `enrich_codex.py` | **(없음)** | **(없음)** |
| **KO 스크립트** | `enrich_chatgpt_ko.py` | `enrich_codex_ko.py` | `enrich_claude_code_kor.py` | `enrich_gemini.py` |
| **EN 스킬** | `chatgpt-enricher` | `codex-enricher` | (없음) | (없음) |
| **KO 스킬** | `chatgpt-ko-enricher` | `ko-enricher` | `claude-code-ko-enricher` | `gemini-ko-enricher` |
| **KO 컬럼명** | `title_updated_ko` | `title_updated_ko` | `title_kor` | `title_ko` |
| **KO 어미** | ~해요 체 | ~해요/~됐어요 체 | ~해요/~됐어요 체 | ~해보세요!/~됩니다! 체 |
| **KO 본문 형식** | 3줄 (~습니다 체) | 3줄 (~습니다 체) | 불릿 3개 (`•`) | 3줄 (친근 서술체) |
| **EN 스킬 위치** | `.claude/skills/` | `skills/` + `.claude/skills/` | — | — |
| **KO 스킬 위치** | `.claude/skills/` | `skills/` + `.claude/skills/` | `skills/` + `.claude/skills/` | `skills/` + `.claude/skills/` |
| **EN 규칙 문서** | `docs/32-chatgpt-enrichment-rules.md` | `docs/65-codex-enrichment-logic.md` | (없음) | (없음) |
| **KO 규칙 문서** | `docs/33-chatgpt-ko-enrichment-rules.md` | `docs/65-codex-enrichment-logic.md` 6장 | `docs/60-card-kor-procedure.md` | `docs/enrich-gemini-procedure.md` |

### 7-4. 한국어화 방식 비교

```
           원본 언어   localize_data.py   summary_en     KO enrichment 방식
           ─────────   ────────────────   ──────────     ──────────────────
ChatGPT    영어        패턴+용어 치환     원본 영어 백업  스킬 기반 (chatgpt-ko-enricher)
Codex      영어        패턴+용어 치환     원본 영어 백업  스킬 기반 (ko-enricher)
Claude     영어        패턴+용어 치환     원본 영어 백업  스킬 기반 (claude-code-ko-enricher)
Gemini     한국어      건너뜀             영구 NULL      스킬 기반 (gemini-ko-enricher)
```

---

## 8. 비대칭 포인트 요약

### 8-1. Claude Code에 EN enrichment 없음

다른 3개 제품은 `enrich_*.py`(EN) + `enrich_*_ko.py`(KO) 쌍이 있지만, Claude Code는 `enrich_claude_code_kor.py`(KO)만 존재한다. 이는 Claude Code가 불릿 단위로 이벤트를 관리하여 원문 불릿 텍스트 자체가 충분히 설명적이기 때문이다.

### 8-2. Gemini의 KO 처리가 2개 스크립트에 분산

| 스크립트 | 역할 | 생성 컬럼 |
|---------|------|----------|
| `scripts/generate_title_ko.py` | summary_ko → 55자 헤드라인 | `title_ko` (공통) |
| `scripts/enrich_gemini.py` | JSON 워크플로 기반 전용 enrichment | `title_ko`, `content_ko` (전용) |

`enrich_gemini.py`가 `title_ko`를 덮어쓸 수 있으므로 `generate_title_ko.py`의 결과가 최종이 아닐 수 있다.

### 8-3. Claude Code 전용 유틸

| 스크립트 | 역할 |
|---------|------|
| `scripts/populate_card_yn.py` | 중요 변경사항 `card_yn=1` 설정 |
| `scripts/classify_other.py` | 분류 유틸 |

이 2개 스크립트는 Claude Code 전용이며, 다른 제품에는 이런 사전 필터링 단계가 없다.

### 8-4. Codex가 `all_events` VIEW에서 제외

4개 제품 중 유일하게 Codex만 `all_events` VIEW에 포함되지 않는다. `entry_type`/`body` 컬럼이 공통 스키마와 호환되지 않기 때문이다.

### 8-5. KO 컬럼명 불일치

| 제품 | 제목 컬럼 | 본문 컬럼 |
|------|----------|----------|
| ChatGPT | `title_updated_ko` | `content_updated_ko` |
| Codex | `title_updated_ko` | `content_updated_ko` |
| Claude Code | `title_kor` | `content_kor` |
| Gemini | `title_ko` | `content_ko` |

3가지 네이밍 컨벤션이 혼재한다.

### 8-6. KO enrichment 스크립트 패턴 불일치

| 제품 | 패턴 | 설명 |
|------|------|------|
| ChatGPT | 하드코딩 RECORDS | `enrich_chatgpt_ko.py`에 튜플 직접 작성 |
| Codex | 하드코딩 RECORDS | `enrich_codex_ko.py`에 튜플 직접 작성 |
| Claude Code | 하드코딩 RECORDS | `enrich_claude_code_kor.py`에 튜플 직접 작성 |
| Gemini | **JSON 워크플로** | `generate` → JSON 파일 → `apply` 패턴 |

Gemini만 JSON 파일 기반 워크플로를 사용하고, 나머지 3개는 스크립트에 값을 하드코딩한다.

---

## 9. 스킬 전체 목록

스킬은 2곳에 분산 저장되어 있다: 프로젝트 루트 `skills/`와 `.claude/skills/`. 일부 스킬은 양쪽 모두에 존재한다.

| 스킬 이름 | 대상 제품 | 유형 | `skills/` | `.claude/skills/` |
|-----------|----------|------|-----------|-------------------|
| `chatgpt-enricher` | ChatGPT | EN enrichment | — | O |
| `chatgpt-ko-enricher` | ChatGPT | KO enrichment | — | O |
| `codex-enricher` | Codex | EN enrichment | O | O |
| `ko-enricher` | Codex | KO enrichment | O | O |
| `claude-code-ko-enricher` | Claude Code | KO enrichment | O | O |
| `gemini-ko-enricher` | Gemini | KO enrichment | O | — |
| `changelog-classifier` | Claude Code | 분류 | — | O |

### `.claude/skills/` 전용 비-enrichment 스킬

| 스킬 이름 | 역할 |
|-----------|------|
| `mvp-new` | MVP 신규 프로젝트 생성 |
| `mvp-next` | MVP 다음 단계 진행 |
| `mvp-demo` | MVP 데모 |
| `mvp-clarify` | MVP 요구사항 명확화 |
| `langgraph-dev` | LangGraph 개발 |
| `langgraph-optimize` | LangGraph 최적화 |
| `langgraph-coach` | LangGraph 코칭 |
| `docs-sync` | 문서 동기화 |
| `llm-mvp` | LLM MVP 개발 |
| `llm-context-pack` | LLM 컨텍스트 패킹 |
| `gemini-grounding-nodes` | Gemini Grounding 노드 구현 |

### 스킬 커버리지 매트릭스

```
              EN enrichment 스킬   KO enrichment 스킬   분류 스킬
              ─────────────────   ─────────────────   ─────────
ChatGPT       chatgpt-enricher    chatgpt-ko-enricher (없음)
Codex         codex-enricher      ko-enricher         (없음)
Claude Code   (없음)              claude-code-ko-     changelog-
                                  enricher            classifier
Gemini        (없음)              gemini-ko-enricher  (없음)
```

> ChatGPT와 Codex가 EN+KO enrichment 스킬을 모두 보유. Claude Code와 Gemini는 KO 스킬만 존재.

---

## 10. 문서 전체 인덱스

| 문서 | 관련 제품 | 카테고리 |
|------|----------|---------|
| `docs/00-brief.md` | 전체 | 기획 |
| `docs/05-clarify-questions.md` | 전체 | 기획 |
| `docs/06-clarified-brief.md` | 전체 | 기획 |
| `docs/10-prd.md` | 전체 | 기획 |
| `docs/20-ux.md` | 전체 | UX |
| `docs/30-architecture.md` | 전체 | 설계 |
| `docs/31-chatgpt-schema.md` | **ChatGPT** | 설계 |
| `docs/32-chatgpt-enrichment-rules.md` | **ChatGPT** | Enrichment (EN) |
| `docs/33-chatgpt-ko-enrichment-rules.md` | **ChatGPT** | Enrichment (KO) |
| `docs/40-backlog.md` | 전체 | 관리 |
| `docs/50-test-plan.md` | 전체 | 테스트 |
| `docs/60-card-kor-procedure.md` | **Claude Code** | Enrichment (KO) |
| `docs/60-pipeline-report.md` | 전체 | 파이프라인 |
| `docs/61-backfill-refactoring.md` | 전체 | 리팩터링 |
| `docs/62-claude-code-parsing.md` | **Claude Code** | 설계 |
| `docs/65-codex-enrichment-logic.md` | **Codex** | Enrichment (EN+KO) |
| `docs/90-log.md` | 전체 | 로그 |
| `docs/codex-parsing-strategy.md` | **Codex** | 설계 |
| `docs/data-pipeline.md` | 전체 | 파이프라인 (통합) |
| `docs/enrich-gemini-procedure.md` | **Gemini** | Enrichment (KO) |
| `docs/standard/web-search-vs-summarize.md` | 전체 | 표준 |
