# 90 — Decision Log

## 결정 사항

| 날짜 | 결정 | 이유 | 대안 |
|------|------|------|------|
| 2026-03-02 | MVP에서 LLM 미사용, 규칙 기반 Severity만 적용 | 3일 내 데모 완성이 목표이므로 복잡도 최소화 | LangGraph로 요약/태깅 자동화 (v1.1) |
| 2026-03-02 | 로그인 없는 공개 페이지 | 타깃이 불특정 다수, 계정 시스템은 MVP에 불필요 | 관리자 인증 추가 (추후 검토) |
| 2026-03-02 | 엔티티는 update_event + source_snapshot 2개 | 증분 수집을 위해 해시 비교용 스냅샷 필요 | 이벤트만 저장 (증분 수집 불가) |
| 2026-03-02 | ~~Strategy 패턴 파서~~ → Claude Code 기반 수집 | Claude Code가 HTML/MD를 직접 이해하므로 파서 코드 불필요, 아키텍처 단순화 | Strategy 패턴 파서 (과도한 복잡도) |
| 2026-03-02 | FastAPI에서 정적 파일 직접 서빙 | 별도 웹서버 없이 단일 프로세스로 배포 단순화 | Nginx 별도 구성 (MVP에 과함) |
| 2026-03-02 | raw sqlite3 사용 (SQLAlchemy 없음) | MVP 의존성 최소화, 쿼리 직접 제어 | SQLAlchemy ORM (v1.1) |

## 트레이드오프

- SQLite 선택 → Railway 배포 시 파일 영속성 이슈 있지만, MVP 속도 우선
- 규칙 기반 Severity → 정확도 한계 있지만 LLM 의존성/비용 제거
- 공식 소스만 SSOT → 커버리지 한정적이지만 신뢰도 확보
- 바닐라 JS → 컴포넌트 관리 불편하지만 빌드 도구 없이 즉시 실행 가능
- IIFE 모듈 패턴 → ES Modules보다 호환성 우선

## 다음 할 일

- [x] ~~MODE=APPLY: US-001 (타임라인 E2E) 구현 시작~~
- [x] ~~시드 데이터 준비 (백필 전 수동 테스트용)~~
- [x] ~~US-002: Product 필터 동작 검증 + URL 동기화 + localStorage 저장~~
- [x] ~~US-003: Severity 필터 UI 추가~~
- [x] ~~US-004: 카드 펼치기 상세화 (What Changed bullets)~~
- [x] ~~US-006: 수집 툴킷 구현 (scripts/collect.py)~~
- [x] ~~실제 소스 fetch + 백필 (132개 이벤트)~~
- [ ] 브라우저 수동 QA 테스트

### mvp-clarify (2026-03-02)
- 결정: MVP는 LLM 없이 규칙 기반, 로그인 없는 공개 페이지, 3일 데모 마감
- 가정: 4개 공식 소스 파싱 가능, 이벤트+스냅샷 2 엔티티로 충분, Railway 배포 예정
- 다음 행동: docs/06-clarified-brief.md 기반으로 PLAN 모드 진입 (PRD → UX → 아키텍처 → 백로그)

### MODE=PLAN 완료 (2026-03-02)
- 생성 문서: 10-prd.md, 20-ux.md, 30-architecture.md, 40-backlog.md
- PRD: 유저스토리 8개(P0), 리스크 5개, 성공 기준 3개
- UX: 텍스트 와이어프레임 (데스크톱+모바일), 인터랙션 명세, 디자인 토큰
- 아키텍처: API 6개 엔드포인트, DB 테이블 2개, Strategy 패턴 파서, Severity 규칙
- 백로그: P0(8개 US, 216pt) + P1(6개) + P2(9개)
- 다음 행동: MODE=APPLY로 전환, US-001부터 세로 슬라이스 구현

### US-001 구현 완료 (2026-03-02)
- **Backend**: database.py, schemas.py, routers (events/meta), services (scorer), seed.py
- **Frontend**: index.html, style.css, api.js, card.js, filters.js, timeline.js, app.js
- **Tests**: 34 passed (test_health, test_api_events 18개, test_scorer 16개)
- **Seed data**: 29 events (chatgpt:11, claude_code:8, gemini:7, codex:6)
- **API 검증**: /api/events, /api/products, /api/tags 모두 정상 응답
- **정적 파일**: HTML/CSS/JS 5개 파일 모두 200 OK
- 서버: `uvicorn apps.api.main:app --port 8001` (포트 8000은 이미 사용 중)
- 다음 행동: 브라우저 QA → US-002/003 필터 고도화 → US-006 실제 파서 구현

### Multi-Rail Timeline Layout 구현 (2026-03-02)
- **요청**: 단일 세로 타임라인 → 4개 제품 레일 병렬 배치 (날짜축 + 4열 그리드)
- **변경 파일**: index.html, style.css, timeline.js (3개 파일, 프론트엔드만 수정)
- **구조**: CSS Grid 5열 (80px date-axis + 4x 1fr product rails)
- **HTML**: rail-header (sticky 제품 헤더) 추가, .timeline → .timeline-grid 변경
- **CSS**: 기존 단일 타임라인(선+점) 제거, 새 그리드 레이아웃 + 반응형 (태블릿 가로스크롤, 모바일 단일컬럼 폴백)
- **JS**: renderEvents() → groupByDate() + createDateRow() 리팩터링, 이벤트를 날짜별 그룹핑 후 제품 열에 배치
- **Backend**: 변경 없음, API 그대로 사용
- **Tests**: 34개 전부 통과 (기존 테스트 영향 없음)
- **검증**: 모든 정적 파일 200 OK, 32개 이벤트 정상 로드
- 다음 행동: 브라우저 QA → Product 필터 레일 숨김/표시 연동 → Severity 필터 UI

### 수집 아키텍처 변경 + collect.py 구현 (2026-03-02)
- **결정**: APScheduler/Strategy 패턴 파서 → Claude Code 기반 수동 수집으로 전환
- **이유**: Claude Code가 HTML/MD를 직접 이해하므로 파서 코드 불필요, 아키텍처 대폭 단순화
- **산출물**: scripts/collect.py (7개 함수 + CLI), tests/test_collect.py (15개 테스트)
- **Tests**: 49 passed (기존 34 + 신규 15)
- **CLI**: `python -m scripts.collect` (fetch 4소스) / `--status` (상태만 조회)
- **문서**: docs/30-architecture.md 업데이트 (파서/admin 관련 섹션 제거, 수집 툴킷 추가)
- 다음 행동: 실제 소스 fetch 테스트 → 스냅샷 기반 이벤트 추출 → US-002/003 필터 고도화

### US-002 + US-003 필터 고도화 (2026-03-02)
- **US-002 (localStorage)**: 필터 변경 시 `ai_tracker_filters` 키로 localStorage 저장, URL 없으면 localStorage에서 복원, resetAll 시 클리어
- **US-003 (Severity 필터 UI)**: All / 2+ / 3+ / 4+ / 5 버튼 5개 추가, severity 색상 인디케이터, 모바일 반응형 포함
- **변경 파일**: index.html (severity 섹션 추가), style.css (severity-btn 스타일), filters.js (localStorage + severity 로직)
- **Tests**: 49 passed (변경 없음, 프론트엔드만 수정)
- 다음 행동: 브라우저 수동 QA → US-004 카드 펼치기 상세화 → 실제 소스 fetch

### US-004 카드 펼치기 상세화 (2026-03-02)
- **What Changed**: evidence_excerpt → bullet list (`<ul>` + `<li>`) 변환, 파란 배경 블록
- **Impact**: summary_en (우선) 또는 summary_ko 표시, 초록 배경 강조 블록
- **Source & Meta**: 원본 링크 + detected 타임스탬프 + raw_ref 정보
- **변경 파일**: card.js (createExpandedContent 리팩터링), style.css (what-changed-list, impact-block, source-meta 추가)
- **Tests**: 49 passed
- 다음 행동: 브라우저 수동 QA → 실제 소스 fetch 테스트

### 실제 데이터 백필 완료 (2026-03-02)
- **소스 fetch**: 3/4 성공 (ChatGPT 403 차단, Gemini/Codex/Claude Code 정상)
- **스냅샷**: gemini_latest.html (305KB), codex_latest.html (973KB), claude_code_latest.md (118KB)
- **백필 스크립트**: `scripts/backfill.py` 생성 (parse_codex, parse_gemini, parse_claude_code)
- **삽입 결과**: 132개 실제 이벤트 (codex:48, claude_code:54, gemini:30)
- **날짜 범위**: 2025-01-30 ~ 2026-03-01
- **Severity 분포**: sev5=1, sev4=8, sev3=10, sev2=100, sev1=13
- **ChatGPT**: 공식 페이지가 직접 HTTP 접근 차단 (403). 추후 대안 필요
- **Tests**: 49 passed
- 다음 행동: 브라우저 QA (http://localhost:8001) → ChatGPT 데이터 대안 → 성능 최적화

### 한국어 로컬라이제이션 완료 (2026-03-02)
- **UI 한국어화**: index.html, card.js, filters.js, timeline.js — 50개+ 영어 문자열을 한국어로 번역
  - 헤더: "AI 업데이트 트래커", 필터: "제품/태그/중요도", 카드: "상세 보기/접기"
  - 빈 상태: "검색 결과가 없습니다", 에러: "문제가 발생했습니다"
  - Severity: "치명적/높음/보통/낮음/정보"
- **백엔드 태그 라벨**: meta.py TAG_LABELS 한국어화 + "improvement"(개선) 태그 추가 (총 7개)
- **Gemini 파서 수정**: 2025+ 카드의 HTML 구조 변경 대응 (`_features_` div)
  - 수정 전: 30개 이벤트 모두 제목="Gemini update YYYY-MM-DD", 요약=빈 문자열
  - 수정 후: 실제 한국어 제목/요약/증거 추출 (원래 한국어 페이지)
- **데이터 한국어화**: scripts/localize_data.py 생성, Codex+Claude Code 102개 이벤트 요약 변환
  - 패턴 매칭(Added→추가됨, Fixed→수정됨 등) + 기술용어 치환
  - 영어 원문은 summary_en 필드에 백업
- **Tests**: 63 passed (신규 22: Gemini 파서 테스트)
- 다음 행동: 브라우저 수동 QA → ChatGPT 데이터 대안
