# 40 — Product Backlog

## P0 — Must Have (MVP, 2주 내)

### [US-001] 타임라인에서 최신 AI 업데이트 한눈에 보기

**As a** AI 뉴스 팔로워
**I want** 4개 AI 제품의 업데이트를 시간순으로 정렬된 타임라인에서 보고 싶다
**So that** 매일 아침 "어떤 일이 일어났는가?"를 10초 안에 파악할 수 있다

**Acceptance Criteria:**
- [ ] AC-001: 2025-01-01 이후의 모든 이벤트가 최신순(desc)으로 표시된다
- [ ] AC-002: 각 이벤트 카드에 Date, Product 배지(색상), Title, Summary(2줄), Tags, Severity 지표가 포함되어 있다
- [ ] AC-003: 세로 타임라인 선과 점(dot)이 SVG 또는 CSS로 올바르게 렌더링된다
- [ ] AC-004: 월별 Month Divider (예: "2025년 3월")가 타임라인에 표시된다
- [ ] AC-005: 데이터 로드 후 200ms 이내에 화면이 렌더링된다

**Definition of Done:**
- [ ] Backend: FastAPI `/api/events` 엔드포인트 구현 (필터링, 페이지네이션 지원)
- [ ] Frontend: 타임라인 HTML/CSS/JS 구현 (반응형 확인)
- [ ] Database: SQLite `update_events` 테이블 생성, 인덱싱 (event_date DESC)
- [ ] Data: 백필 데이터 4개 제품 × 2025~현재 입력 완료
- [ ] Test: 브라우저에서 스크롤 테스트 (Chrome, Firefox 최소)
- [ ] Docs: `docs/30-architecture.md` 스키마 섹션 완료

**Priority:** P0
**Estimate:** 40 포인트
**Assignee:** frontend-dev (화면), backend-dev (API), coordinator (데이터)

---

### [US-002] 제품별로 업데이트 필터링하기

**As a** 특정 제품(예: Claude Code)을 주로 쓰는 개발자
**I want** 관심 제품만 선택해서 볼 수 있다
**So that** 불필요한 정보를 걸러내고 내 의존도가 높은 제품의 변화에만 집중할 수 있다

**Acceptance Criteria:**
- [ ] AC-001: Sticky Filter Bar가 화면 상단에 고정되어 있다
- [ ] AC-002: 4개 제품(ChatGPT, Gemini, Codex, Claude Code) 토글이 있고, 다중 선택 가능하다
- [ ] AC-003: 토글 선택/해제 시 타임라인이 100ms 이내로 즉시 업데이트된다 (로딩 스피너 없음)
- [ ] AC-004: 필터 선택 상태가 URL 쿼리 파라미터에 반영된다 (예: `?products=chatgpt,claude_code`)
- [ ] AC-005: 페이지 새로고침 후에도 이전 필터 선택 상태가 유지된다 (localStorage)

**Definition of Done:**
- [ ] Frontend: Filter Bar UI (토글 버튼, 스타일)
- [ ] Frontend: 필터 상태 → URL 파라미터 동기화
- [ ] Frontend: localStorage에 필터 상태 저장/복원
- [ ] Backend: `/api/events?products=...` 쿼리 파라미터 지원
- [ ] Test: 필터 조합 테스트 (모두 선택, 하나만, 여러 개)

**Priority:** P0
**Estimate:** 20 포인트
**Assignee:** frontend-dev (UI), backend-dev (쿼리)

---

### [US-003] 심각한 변경(Breaking Change) 우선 식별하기

**As a** 프로덕션 환경의 LLM을 쓰는 개발자
**I want** Severity가 높은 이벤트(예: Breaking Change, API 폐기)를 즉시 찾을 수 있다
**So that** 서비스 장애를 사전에 방지하고 대응할 수 있다

**Acceptance Criteria:**
- [ ] AC-001: 각 카드에 Severity 지표가 색상으로 표시된다 (Red=5, Orange=4, Yellow=3, Green=2, Gray=1)
- [ ] AC-002: Filter Bar에 Severity 슬라이더(1~5) 또는 "High Priority만" 버튼이 있다
- [ ] AC-003: "breaking" 또는 "deprecation" 태그가 있는 이벤트는 Severity >= 4로 자동 할당된다
- [ ] AC-004: Severity 필터 적용 시 해당 수준 이상의 이벤트만 표시된다
- [ ] AC-005: 초기 로드 시 기본값은 Severity >= 1 (모두 보기)이다

**Definition of Done:**
- [ ] Backend: Severity 계산 로직 (규칙 기반)
  - Severity 5: breaking, critical_deprecation
  - Severity 4: deprecation, api_change, major_update
  - Severity 3: new_feature, model_update, improvement
  - Severity 2: bugfix, minor_update, access_expansion
  - Severity 1: announcement, other
- [ ] Frontend: 색상 코딩 (CSS)
- [ ] Frontend: Severity 필터 UI
- [ ] Backend: `/api/events?severity_min=4` 쿼리 지원

**Priority:** P0
**Estimate:** 16 포인트
**Assignee:** backend-dev (로직), frontend-dev (UI)

---

### [US-004] 이벤트 상세 정보 펼쳐보기

**As a** 흥미로운 업데이트의 세부사항을 알고 싶은 사용자
**I want** 카드의 "더 보기" 버튼을 눌러 "What Changed", "Impact", "Evidence"를 볼 수 있다
**So that** 간단한 요약만으로는 부족한 경우 원본 출처까지 추적할 수 있다

**Acceptance Criteria:**
- [ ] AC-001: 각 카드에 "더 보기" 또는 expand 아이콘이 있다
- [ ] AC-002: 클릭 시 카드가 펼쳐지고 다음 필드가 추가로 표시된다:
  - [ ] What Changed (3~5개 bullet point)
  - [ ] Impact/Action (개발자 대상 정보, 2~3줄)
  - [ ] Evidence Excerpt (원본에서 발췌한 2~3줄)
- [ ] AC-003: Source URL이 클릭 가능한 링크로 표시되고, 클릭 시 공식 Release Notes로 이동한다
- [ ] AC-004: 펼친/접은 상태가 URL fragment로 기록된다 (예: `#event-us-001`)
- [ ] AC-005: 펼친 카드의 상태가 sessionStorage에 저장되어 새로고침 후에도 유지된다

**Definition of Done:**
- [ ] Frontend: 카드 펼치기/접기 토글 (CSS 트랜지션)
- [ ] Frontend: 추가 필드 렌더링 (what_changed_bullets, impact, evidence_excerpt)
- [ ] Frontend: URL fragment 동기화
- [ ] Backend: 위 필드들이 `/api/events` 응답에 포함되어야 함
- [ ] Database: 해당 칼럼 추가 (what_changed_bullets, impact, evidence_excerpt)
- [ ] Test: 펼침/접기 다중 실행 테스트

**Priority:** P0
**Estimate:** 24 포인트
**Assignee:** frontend-dev (UI), backend-dev (API)

---

### [US-005] 특정 연도로 빠르게 이동하기

**As a** 2025년 초반의 변화만 보고 싶거나, 최신 이벤트로 점프하려는 사용자
**I want** 상단 Year Jump 버튼(2025, 2026, Latest)을 누르면 해당 섹션으로 스크롤된다
**So that** 긴 타임라인에서 원하는 시기의 이벤트를 빠르게 찾을 수 있다

**Acceptance Criteria:**
- [ ] AC-001: Filter Bar 옆에 Year Jump 버튼이 있다 (2025, 2026, Latest)
- [ ] AC-002: 버튼 클릭 시 해당 연도의 첫 이벤트로 부드러운 스크롤(scroll-behavior: smooth)이 동작한다
- [ ] AC-003: 현재 보고 있는 연도 버튼이 활성화(highlighted) 상태로 표시된다
- [ ] AC-004: 스크롤하는 동안 현재 보고 있는 연도가 자동으로 업데이트된다 (Intersection Observer)
- [ ] AC-005: 새로운 해가 시작되면(예: 2027-01-01 이벤트 수집) 버튼이 자동으로 추가된다

**Definition of Done:**
- [ ] Frontend: Year Jump 버튼 UI
- [ ] Frontend: 스크롤 이벤트 리스너 (Intersection Observer로 현재 연도 감지)
- [ ] Frontend: 버튼 클릭 시 smooth scroll
- [ ] Backend: 연도별 이벤트 그룹화 (응답 시 year_section 메타데이터)
- [ ] Test: 여러 연도로 점프 테스트

**Priority:** P0
**Estimate:** 16 포인트
**Assignee:** frontend-dev

---

### [US-006] 4개 공식 소스에서 2025 이후 전체 데이터 백필

**As a** 시스템 관리자 또는 초기 배포 담당자
**I want** ChatGPT, Gemini, Codex, Claude Code의 2025-01-01 이후 모든 이벤트를 자동으로 수집하고 정규화할 수 있다
**So that** MVP 런칭 시 처음부터 완전한 타임라인을 제공할 수 있다

**Acceptance Criteria:**
- [ ] AC-001: 4개 공식 소스 HTML/Markdown을 다운로드하는 파이썬 스크립트가 있다
- [ ] AC-002: 파싱 규칙이 설정 파일(`config/parser_rules.json`)로 분리되어 있다
- [ ] AC-003: 각 이벤트가 정규화되어 event_date, title, summary_ko, summary_en, tags, severity가 자동으로 할당된다
- [ ] AC-004: 추출된 이벤트가 SQLite `update_events` 테이블에 INSERT된다 (중복 제거)
- [ ] AC-005: 백필 완료 후 로그에 "Backfill completed: chatgpt=X, gemini=Y, codex=Z, claude_code=W" 메시지가 남는다
- [ ] AC-006: 스크립트 실행 후 타임라인에 4개 제품 이벤트가 모두 표시된다

**Definition of Done:**
- [ ] Backend: 4개 파서 구현 (HTML parsing with BeautifulSoup, Markdown parsing)
- [ ] Backend: 정규화 로직 (날짜, 제목, 요약 추출)
- [ ] Backend: SQLite 테이블 생성 및 스키마 정의
- [ ] Backend: 중복 제거 로직 (source_id + section_key 조합으로 유니크)
- [ ] Data: 각 제품별 샘플 데이터 10개 이상 수동 검증
- [ ] Docs: `docs/30-architecture.md`에 파이프라인 상세 문서화
- [ ] Script: `scripts/backfill.py` 또는 `scripts/sync_events.py`

**Priority:** P0
**Estimate:** 32 포인트
**Assignee:** backend-dev, coordinator

---

### [US-007] 매일 자동으로 신규 이벤트 수집

**As a** 신뢰하는 사용자
**I want** 매일 자동으로 4개 공식 소스가 갱신되고, 신규 이벤트가 타임라인에 추가되는 것을 확인할 수 있다
**So that** "이 정보가 최신인가?"라는 의심 없이 신뢰할 수 있다

**Acceptance Criteria:**
- [ ] AC-001: 매일 정해진 시간(기본값: UTC 00:00)에 백그라운드 수집 잡(job)이 자동 실행된다
- [ ] AC-002: 4개 소스를 다시 다운로드하고, 이전 content_hash와 비교한다
- [ ] AC-003: 변경이 감지되면 새로운 이벤트만 파싱하고 DB에 추가한다
- [ ] AC-004: 변경이 없으면 로그에 "No changes for {source_id}"만 기록된다
- [ ] AC-005: 수집 실패 시 로그에 에러 메시지를 남기고, 3시간 후 재시도한다
- [ ] AC-006: 페이지 하단에 "마지막 업데이트: 2026-03-02 14:30 UTC" 같은 정보가 표시된다
- [ ] AC-007: 수집 결과는 `source_snapshot` 테이블에 기록된다 (fetched_at, content_hash, status)

**Definition of Done:**
- [ ] Backend: APScheduler 또는 Celery 기반 스케줄러 구현
- [ ] Backend: 증분 수집 로직 (content_hash 비교 및 diff)
- [ ] Backend: 에러 처리 및 재시도 로직
- [ ] Database: `source_snapshot` 테이블 생성
- [ ] Frontend: "마지막 업데이트" 타임스탬프 표시
- [ ] Logging: CloudWatch 또는 로컬 파일 기반 로깅
- [ ] Deployment: Railway 또는 Heroku 스케줄러 설정

**Priority:** P0
**Estimate:** 28 포인트
**Assignee:** backend-dev, coordinator

---

### [US-008] 브라우저에서 타임라인 부드럽게 탐색

**As a** 아무 특별한 기술 없이 웹사이트를 쓰는 사람
**I want** 스크롤, 필터, 펼치기가 모두 버벅임 없이 빠르게 동작한다
**So that** 편리한 경험을 할 수 있다

**Acceptance Criteria:**
- [ ] AC-001: 초기 페이지 로드 시간(DOMContentLoaded) < 1초
- [ ] AC-002: 초기 화면 렌더링(LCP) < 2초
- [ ] AC-003: 필터/펼치기 시 응답 지연 < 100ms (로딩 스피너 불필요)
- [ ] AC-004: 1000개 이벤트 렌더링 시에도 스크롤 부드러움 (60fps)
- [ ] AC-005: Lighthouse Performance 점수 >= 80
- [ ] AC-006: 모바일(태블릿, 스마트폰) 화면에서도 동작 확인 (반응형)
- [ ] AC-007: 스크린 리더(ARIA labels) 기본 지원

**Definition of Done:**
- [ ] Frontend: CSS 최적화 (inline style 최소화, 클래스 활용)
- [ ] Frontend: JavaScript 번들 최소화 (테이프(tree-shaking), 미사용 코드 제거)
- [ ] Frontend: Virtual Scrolling 고려 (또는 lazy loading)
- [ ] Frontend: 반응형 디자인 테스트 (375px, 768px, 1920px)
- [ ] Test: Lighthouse 측정 및 개선
- [ ] Test: Chrome DevTools Performance 프로파일링
- [ ] Test: 모바일 기기에서 수동 테스트(또는 BrowserStack)

**Priority:** P0
**Estimate:** 20 포인트
**Assignee:** frontend-dev

---

## P1 — Should Have (v1.0+ 또는 MVP 후 연장)

### [US-009] 태그로 관심 카테고리 필터링하기

**As a** "새로운 모델" 또는 "접근성 개선"처럼 특정 주제에만 관심 있는 사용자
**I want** Tag 필터(new_feature, bugfix, model, breaking, deprecation, access)로 카테고리를 선택할 수 있다
**So that** 내가 관심 있는 주제의 변화만 집중해서 볼 수 있다

**Acceptance Criteria:**
- [ ] AC-001: Filter Bar에 Tag 칩 또는 드롭다운이 있다
- [ ] AC-002: 다중 선택 가능 (Ctrl+Click 또는 체크박스)
- [ ] AC-003: 기본값은 "모두 선택"
- [ ] AC-004: 선택한 태그 조합을 URL에 저장 (예: `?tags=new_feature,breaking`)
- [ ] AC-005: Product 필터와 함께 조합 적용 가능

**Definition of Done:**
- [ ] Frontend: Tag 필터 UI (칩 또는 드롭다운)
- [ ] Backend: `/api/events?tags=...` 쿼리 지원
- [ ] Test: 여러 태그 조합 테스트

**Priority:** P1
**Estimate:** 12 포인트
**Assignee:** frontend-dev, backend-dev

---

### [US-010] 키워드로 검색하기

**As a** 특정 주제(예: "Vision", "GPT-4o", "Context Window")를 찾고 싶은 사용자
**I want** 검색창에 키워드를 입력하여 제목, 요약, 태그에서 매칭되는 이벤트를 찾을 수 있다
**So that** 4개 제품의 변경 중 내가 관심 있는 것만 빠르게 찾을 수 있다

**Acceptance Criteria:**
- [ ] AC-001: Filter Bar에 검색창이 있다
- [ ] AC-002: 키워드 입력 후 Enter 또는 실시간 검색(debounced)
- [ ] AC-003: 제목, 요약, 태그에서 case-insensitive 매칭
- [ ] AC-004: 매칭된 부분이 하이라이트된다(선택사항)
- [ ] AC-005: 검색 쿼리가 URL에 저장된다

**Definition of Done:**
- [ ] Frontend: 검색창 UI
- [ ] Backend: `/api/events?q=...` 엔드포인트 (FTS 또는 LIKE 쿼리)
- [ ] Database: SQLite FTS 테이블 고려 (성능 향상)
- [ ] Test: 다양한 키워드 테스트

**Priority:** P1
**Estimate:** 16 포인트
**Assignee:** backend-dev (search logic), frontend-dev (UI)

---

### [US-011] 최신 이벤트를 배너로 강조 표시

**As a** 매일 한 번씩 사이트를 방문하는 사용자
**I want** 오늘 또는 이번주의 새로운 이벤트를 상단 배너에서 한눈에 볼 수 있다
**So that** "오늘 뭐가 바뀌었나?"를 빠르게 파악할 수 있다

**Acceptance Criteria:**
- [ ] AC-001: 페이지 상단에 "어제의 업데이트 (3개)", "이번주의 업데이트 (12개)" 배너
- [ ] AC-002: 배너 클릭 시 해당 필터가 자동 적용되고 타임라인이 업데이트된다
- [ ] AC-003: 배너는 닫을 수 있다 (X 버튼)
- [ ] AC-004: 새로고침 후에도 배너 상태가 유지된다 (localStorage)

**Definition of Done:**
- [ ] Frontend: 배너 UI
- [ ] Backend: 최신 N일 이벤트를 `/api/events/recent` 엔드포인트로 제공
- [ ] Test: 배너 클릭 후 필터 적용 확인

**Priority:** P1
**Estimate:** 12 포인트
**Assignee:** frontend-dev, backend-dev

---

### [US-012] Product별로 색상이 일관되게 표시되기

**As a** 자주 방문하는 사용자
**I want** ChatGPT는 항상 파란색, Gemini는 초록색처럼 제품별 색상이 일관되게 사용되기를 원한다
**So that** 빠르게 제품을 시각적으로 구분할 수 있다

**Acceptance Criteria:**
- [ ] AC-001: 4개 제품이 각각 고유 색상이 할당된다 (CSS 변수)
- [ ] AC-002: 배지, 타임라인 점(dot), 필터 토글 모두 일관된 색상
- [ ] AC-003: 색상 대비가 WCAG AA 이상을 만족한다

**Definition of Done:**
- [ ] Frontend: CSS 색상 변수 정의 (`:root`)
- [ ] Frontend: 모든 UI 요소에 적용
- [ ] Test: 색상 대비 검사 (WAVE, AXE)

**Priority:** P1
**Estimate:** 8 포인트
**Assignee:** frontend-dev

---

### [US-013] 데이터 파싱 규칙을 설정 파일로 관리

**As a** 개발자
**I want** 파싱 규칙을 소스 코드 대신 설정 파일(`config/parser_rules.json`)로 관리하고 싶다
**So that** 소스 구조 변경 시 빠르게 대응할 수 있다 (코드 변경 없음)

**Acceptance Criteria:**
- [ ] AC-001: `config/parser_rules.json` 파일이 있고, 4개 제품별 규칙이 정의되어 있다
- [ ] AC-002: 규칙 형식: { "source_id": "chatgpt_release_notes", "selectors": {...}, "date_format": "..." }
- [ ] AC-003: 파서가 설정 파일을 읽어 동적으로 규칙을 적용한다
- [ ] AC-004: 규칙 변경 후 재배포 없이 스케줄러 재시작만으로 적용된다

**Definition of Done:**
- [ ] Backend: 설정 파일 로더 구현
- [ ] Backend: 동적 파서 생성
- [ ] Config: 4개 소스별 규칙 정의 (초기 버전)

**Priority:** P1
**Estimate:** 12 포인트
**Assignee:** backend-dev, coordinator

---

### [US-014] Source 신뢰도 점수 표시(선택)

**As a** 정보 출처를 중요시하는 사용자
**I want** 각 카드의 evidence 신뢰도를 (원본 링크 유무, 발췌 품질 등) 별점이나 배지로 표시할 수 있다
**So that** 어느 정도 신뢰할 수 있는지 판단할 수 있다

**Acceptance Criteria:**
- [ ] AC-001: 각 카드에 "Source Confidence: High/Medium/Low" 배지
- [ ] AC-002: Source URL 존재 → High, 발췌만 있음 → Medium, 수동 입력 → Low
- [ ] AC-003: Tooltip으로 신뢰도 기준을 설명

**Definition of Done:**
- [ ] Backend: 신뢰도 계산 로직
- [ ] Frontend: 배지 UI 및 Tooltip

**Priority:** P1
**Estimate:** 8 포인트
**Assignee:** backend-dev (로직), frontend-dev (UI)

---

## P2 — Nice to Have (v1.1+)

- [ ] **US-020**: 이메일/Slack 알림 (특히 Breaking Change)
- [ ] **US-021**: 관리자 검수 대시보드 (자동 요약 품질 보정)
- [ ] **US-022**: 사용자 개인 구독 설정 (특정 제품/태그만 알림)
- [ ] **US-023**: CSV/JSON 내보내기
- [ ] **US-024**: 다국어 지원 (스페인어, 일본어 등)
- [ ] **US-025**: 모바일 앱 (PWA 또는 네이티브)
- [ ] **US-026**: 제품 간 변경 비교 분석 (예: "모두 Context Window 증가")
- [ ] **US-027**: 사용자 평가 및 댓글 (커뮤니티)
- [ ] **US-028**: AI 요약 (LLM으로 한국어 요약 생성)

---

## 우선순위 요약

| 스토리 | 제목 | Priority | Estimate | 담당 | 상태 |
|--------|------|----------|----------|------|------|
| US-001 | 타임라인에서 최신 업데이트 보기 | P0 | 40 | frontend, backend, coordinator | TODO |
| US-002 | 제품별 필터링 | P0 | 20 | frontend, backend | TODO |
| US-003 | Severity 필터 | P0 | 16 | backend, frontend | TODO |
| US-004 | 카드 펼쳐보기 | P0 | 24 | frontend, backend | TODO |
| US-005 | Year Jump | P0 | 16 | frontend | TODO |
| US-006 | 백필 데이터 수집 | P0 | 32 | backend, coordinator | TODO |
| US-007 | 매일 자동 수집 | P0 | 28 | backend, coordinator | TODO |
| US-008 | 성능 최적화 | P0 | 20 | frontend | TODO |
| US-009 | 태그 필터 | P1 | 12 | frontend, backend | TODO |
| US-010 | 키워드 검색 | P1 | 16 | backend, frontend | TODO |
| US-011 | 최신 이벤트 배너 | P1 | 12 | frontend, backend | TODO |
| US-012 | 제품 색상 일관성 | P1 | 8 | frontend | TODO |
| US-013 | 파싱 규칙 설정화 | P1 | 12 | backend, coordinator | TODO |
| US-014 | Source 신뢰도 | P1 | 8 | backend, frontend | TODO |

**MVP P0 총 포인트: 216 포인트 (2주 내)**
**P1 추가 포인트: 68 포인트 (v1.0+ 또는 연장)**

---

## 추가 작업 (정의되지 않음, 협의 필요)

- [ ] **Deployment Setup**: Railway/Heroku 초기 설정, 환경 변수, DB 마이그레이션
- [ ] **Monitoring & Logging**: Sentry, CloudWatch, 알람 설정
- [ ] **Documentation**: API 명세(OpenAPI/Swagger), 개발 가이드, 배포 가이드
- [ ] **QA & Testing**: 수동 테스트 계획, 자동 테스트 작성
- [ ] **UI/UX Design**: 와이어프레임, 프로토타입 (Figma)
