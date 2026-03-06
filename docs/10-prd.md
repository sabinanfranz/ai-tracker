# 10 — Product Requirements Document

## 문제 정의

### 현재 상황
- **분산된 정보**: ChatGPT, Gemini, Codex, Claude Code 등 주요 AI 제품들의 업데이트가 각각의 공식 채널(Release Notes, Changelog 등)에 흩어져 있음
- **추적 불가**: 여러 제품의 신기능·변경·버그 수정을 일괄 추적할 수 있는 단일 출처(SSOT)가 없음
- **의사결정 지연**: 개발자·사용자가 각 제품의 최신 변화를 파악하려면 4개 이상의 웹사이트를 순회해야 하므로 시간과 비용 낭비
- **FOMO 발생**: 중요도가 높은 Breaking Change나 새로운 기능을 놓칠 수 있음

---

## 대상 사용자

### 1. 일반 AI 팔로워 (User Type A)
- **정의**: AI 뉴스를 관심 있게 읽고, ChatGPT/Gemini 같은 대중적 도구를 활용하는 사용자
- **행동 패턴**: 주 1~2회 뉴스 확인, 새로운 AI 기능에 관심 높음
- **목표**: "최신 AI 트렌드를 10초 안에 파악하고 싶다"

### 2. AI 도구 개발자 (User Type B)
- **정의**: Claude Code, Codex, GPT API 등을 프로덕션 환경에서 사용하는 개발자
- **행동 패턴**: 매일 또는 주 3~5회 변경사항 확인, 특히 Breaking Change에 민감함
- **목표**: "우리 제품의 의존도가 높은 LLM/API의 변경을 놓치지 않고 싶다"

---

## 핵심 가치 제안

### 가치 명제
**"4개 AI 제품의 변경사항을 시간순 한 판에서, 중요도와 함의까지 10초 안에 파악"**

### 기대 효과
| 사용자 군 | 기대 효과 |
|----------|---------|
| 일반 팔로워 | 4개 웹사이트 순회 → 1개 타임라인 페이지 (90% 시간 단축) |
| 개발자 | 변경사항 놓침 감소, 정기적 재방문으로 신뢰도 높음 |
| 팀 공유 | "어제 뭐가 바뀜?" 질문에 대한 즉각적 답변 가능 |

---

## MVP 범위 (Must-have)

### 1. 데이터 수집 및 정규화
- **백필(Backfill)**: 4개 공식 소스에서 2025-01-01 이후의 모든 이벤트 파싱 (초회 1회)
- **증분(Incremental)**: 매일 자동으로 신규 이벤트 감지 및 추가
- **SSOT 지정**: 다음 4개 공식 채널만 유일 출처
  - ChatGPT: https://help.openai.com/en/articles/6825453-chatgpt-release-notes
  - Gemini (Apps): https://gemini.google/release-notes/
  - Codex: https://developers.openai.com/codex/changelog/
  - Claude Code: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

### 2. 타임라인 화면 (세로 레이아웃)
- **비주얼**: 세로 선(timeline spine) + 이벤트 점(dot) + 카드
- **카드 필드**:
  - 기본 정보: Date, Product 배지(색상), Title
  - 요약: Summary 2줄 (한국어/영문)
  - 메타: Tags (예: new_feature, breaking, bugfix), Severity 지표
  - 신뢰도: Source URL 링크, Evidence Excerpt (발췌 1~2줄)
- **상호작용**:
  - 접기/펼치기: "더 보기" 클릭 시 상세 정보 표시
    - What Changed (3 bullet points)
    - Impact/Action (개발자 대상)
    - Full Evidence (원본 텍스트 발췌)
  - Month Divider: 월별로 구분선 표시
  - Year 라벨: 연도별 구간 표시

### 3. 필터링 및 네비게이션
- **Sticky Filter Bar** (화면 상단 고정)
  - Product 토글 (4개 제품, 다중 선택 가능)
  - Tag 필터 (드롭다운 또는 칩: new_feature, breaking, bugfix, model, access, deprecation)
  - Severity 슬라이더 (1~5 범위)
- **Year Jump 컨트롤**: 2025, 2026, Latest 버튼 (섹션 스크롤 이동)
- **검색 제외**: MVP에서 키워드 검색은 미포함

### 4. 데이터 모델 및 저장소
```json
{
  "id": "uuid",
  "product": "chatgpt | gemini | codex | claude_code",
  "component": "string (default: 'general')",
  "event_date": "YYYY-MM-DD",
  "detected_at": "YYYY-MM-DDTHH:mm:ssZ",
  "title": "string",
  "summary_ko": "string (요약, 2~3줄)",
  "summary_en": "string|null",
  "tags": ["new_feature", "model", "breaking", "deprecation", "access", "bugfix"],
  "severity": 1 (integer 1~5, 5=critical),
  "source_url": "https://...",
  "evidence_excerpt": ["발췌1", "발췌2"],
  "raw_ref": {
    "source_id": "chatgpt_release_notes | gemini_release_notes | ...",
    "section_key": "version 또는 heading anchor"
  }
}
```

### 5. 기술 스택 (MVP)
- **Frontend**: HTML + CSS + Vanilla JavaScript (React 미사용)
- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Orchestration**: LangGraph (현재 MVP에서는 규칙 기반 처리만, LLM 미사용)
- **배포**: Railway (또는 Vercel + Heroku)

---

## 비범위 (Out of scope)

### MVP 이후 버전 (v1.1+)에서 다룰 것
- **사용자 계정/인증**: 회원가입, 로그인, 개인 설정 저장 (공개 페이지 원칙)
- **실시간 알림**: 이메일, 슬랙, 푸시 알림 (매일 또는 주 단위 배치 처리)
- **커뮤니티 기능**: 댓글, 토론, 공유, 평가
- **LLM 자동 요약**: 긴 변경사항을 AI로 요약 (현재는 수동 정규화)
- **고급 검색**: 키워드 검색, 불리안 연산, 정규표현식
- **관리자 대시보드**: 자동 수집 상태 모니터링, 검수, 수동 편집
- **모바일 최적화**: 초기 버전은 데스크톱 중심 (반응형 기본은 제공)
- **다국어**: 초기는 한국어 + 영문 발췌만 (다른 언어는 추후)
- **개인화**: 사용자별 구독 제품 선택, 알람 커스터마이징
- **비교 기능**: 제품 간 변경 비교 분석
- **아카이브/태깅**: 사용자가 이벤트에 태그 추가하기

---

## 유저스토리

### [US-001] 타임라인에서 최신 AI 업데이트 한눈에 보기

**As a** AI 뉴스 팔로워
**I want** 4개 AI 제품의 업데이트를 시간순으로 정렬된 타임라인에서 보고 싶다
**So that** 매일 아침 "어떤 일이 일어났는가?"를 10초 안에 파악할 수 있다

**Acceptance Criteria:**
- [ ] 2025-01-01 이후의 모든 이벤트가 최신순으로 표시된다
- [ ] 각 이벤트 카드에 Date, Product 배지, Title, Summary(2줄), Tags가 포함되어 있다
- [ ] 세로 타임라인 선과 점(dot)이 올바르게 렌더링된다
- [ ] 월별 Divider가 타임라인에 표시된다

**Definition of Done:**
- [ ] Frontend 타임라인 렌더링 완료
- [ ] Backend API `/api/events` 구현 (필터링 지원)
- [ ] SQLite 테이블 생성 및 백필 데이터 입력
- [ ] 브라우저에서 스크롤 테스트 완료

**Priority:** P0

---

### [US-002] 제품별로 업데이트 필터링하기

**As a** 특정 제품(예: Claude Code)을 주로 쓰는 개발자
**I want** 관심 제품만 선택해서 볼 수 있다
**So that** 불필요한 정보를 걸러내고 내 의존도가 높은 제품의 변화에만 집중할 수 있다

**Acceptance Criteria:**
- [ ] Sticky Filter Bar 상단에 Product 토글이 있다 (ChatGPT, Gemini, Codex, Claude Code)
- [ ] 토글 선택/해제 시 타임라인이 즉시 업데이트된다 (로딩 없음)
- [ ] 다중 선택 가능 (예: Claude Code + Codex만)
- [ ] 필터 선택 상태가 URL에 반영된다 (공유 가능)

**Definition of Done:**
- [ ] Frontend Filter UI 구현
- [ ] Backend API 필터 파라미터 지원 (`?products=chatgpt,claude_code`)
- [ ] 필터 상태 localStorage에 저장 (새로고침 유지)

**Priority:** P0

---

### [US-003] 심각한 변경(Breaking Change) 우선 식별하기

**As a** 프로덕션 환경의 LLM을 쓰는 개발자
**I want** Severity가 높은 이벤트(예: Breaking Change, API 폐기)를 즉시 찾을 수 있다
**So that** 서비스 장애를 사전에 방지하고 대응할 수 있다

**Acceptance Criteria:**
- [ ] 각 카드에 Severity 지표(색상: Red=5, Orange=4, Yellow=3, Green=1)가 표시된다
- [ ] Filter Bar에 "Severity 5만" 또는 슬라이더(1~5)가 있다
- [ ] "breaking" 태그가 있는 이벤트는 Severity >= 4로 표시된다
- [ ] Severity 높은 순으로 정렬 옵션 제공 (선택)

**Definition of Done:**
- [ ] Severity 계산 로직 (규칙 기반, LLM 미사용)
- [ ] Frontend 색상 코딩
- [ ] 필터 UI 추가

**Priority:** P0

---

### [US-004] 이벤트 상세 정보 펼쳐보기

**As a** 흥미로운 업데이트의 세부사항을 알고 싶은 사용자
**I want** 카드의 "더 보기" 버튼을 눌러 "What Changed", "Impact", "Evidence"를 볼 수 있다
**So that** 간단한 요약만으로는 부족한 경우 원본 출처까지 추적할 수 있다

**Acceptance Criteria:**
- [ ] 카드 클릭 또는 "더 보기" 버튼으로 펼쳐진다
- [ ] 펼친 상태에서 다음을 표시:
  - [ ] What Changed (3개 bullet point)
  - [ ] Impact/Action (개발자 대상 정보)
  - [ ] Evidence Excerpt (원본에서 2~3줄 발췌)
- [ ] Source URL 클릭 시 공식 Release Notes로 이동한다
- [ ] 펼친 상태가 URL hash에 기록된다

**Definition of Done:**
- [ ] Frontend 펼치기/접기 토글
- [ ] 추가 필드 (what_changed_bullets, impact, evidence_excerpt) DB에 저장

**Priority:** P0

---

### [US-005] 특정 연도로 빠르게 이동하기

**As a** 2025년 초반의 변화만 보고 싶거나, 최신 이벤트로 점프하려는 사용자
**I want** 상단 Year Jump 버튼(2025, 2026, Latest)을 누르면 해당 섹션으로 스크롤된다
**So that** 긴 타임라인에서 원하는 시기의 이벤트를 빠르게 찾을 수 있다

**Acceptance Criteria:**
- [ ] Filter Bar 옆에 "2025", "2026", "Latest" 버튼이 있다
- [ ] 버튼 클릭 시 부드러운 스크롤 또는 즉시 점프한다
- [ ] 현재 보고 있는 연도가 하이라이트된다
- [ ] 새로운 년도가 시작되면 자동으로 버튼이 추가된다

**Definition of Done:**
- [ ] Frontend 버튼 UI 및 스크롤 로직
- [ ] Year 구분 로직 (이벤트를 연도별로 그룹화)

**Priority:** P0

---

### [US-006] 태그로 관심 카테고리 필터링하기

**As a** "새로운 모델" 또는 "접근성 개선"처럼 특정 주제에만 관심 있는 사용자
**I want** Tag 필터(new_feature, bugfix, model, breaking, deprecation, access)로 카테고리를 선택할 수 있다
**So that** 내가 관심 있는 주제의 변화만 집중해서 볼 수 있다

**Acceptance Criteria:**
- [ ] Filter Bar에 Tag 칩 또는 드롭다운이 있다
- [ ] 다중 선택 가능
- [ ] 기본값은 "모두 선택"
- [ ] 선택한 태그를 URL에 저장할 수 있다

**Definition of Done:**
- [ ] Frontend Tag 필터 UI
- [ ] Backend 필터 쿼리 (`?tags=new_feature,breaking`)

**Priority:** P1

---

### [US-007] 신규 데이터가 자동으로 수집되는 것 확인

**As a** 신뢰하는 사용자
**I want** 매일 4개 공식 소스가 자동으로 갱신되는지 알 수 있다
**So that** "이 정보가 최신인가?"라는 의심 없이 신뢰할 수 있다

**Acceptance Criteria:**
- [ ] 페이지 하단에 "마지막 업데이트: 2026-03-02 14:30 UTC" 같은 정보가 표시된다
- [ ] 매일 정해진 시간(예: UTC 00:00)에 백그라운드 수집 잡(job)이 실행된다
- [ ] 해시 변화가 감지되지 않으면 "No changes" 로그
- [ ] 수집 실패 시 로그에 남고, 다음 시도는 3시간 후

**Definition of Done:**
- [ ] Backend 스케줄러 (FastAPI + APScheduler 또는 Celery)
- [ ] 소스별 content_hash 비교 로직
- [ ] Logging (CloudWatch 또는 로컬 파일)

**Priority:** P1

---

### [US-008] 브라우저에서 타임라인 부드럽게 탐색

**As a** 아무 특별한 기술 없이 웹사이트를 쓰는 사람
**I want** 스크롤, 필터, 펼치기가 모두 버벅임 없이 빠르게 동작한다
**So that** 편리한 경험을 할 수 있다

**Acceptance Criteria:**
- [ ] 초기 로드 시간 < 2초 (Lighthouse Performance > 80)
- [ ] 필터/펼치기 시 지연 < 100ms (로딩 스피너 없음)
- [ ] 1000개 이벤트 렌더링 시에도 스크롤 부드러움
- [ ] 모바일(작은 화면) 테스트 완료

**Definition of Done:**
- [ ] Lighthouse 측정
- [ ] Virtual Scrolling 고려 (이벤트 많을 경우)
- [ ] CSS 최적화 (inline style 최소화)

**Priority:** P1

---

## 성공 기준 (KPI)

### 신뢰도 (Trust)
| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 모든 카드 source_url 존재 | 100% | 데이터 검증 스크립트 |
| Evidence excerpt 표시 비율 | 100% | 대상 제품별 spot check |
| 원본 출처 유효성 검사 | 월 1회 수동 검증 | Selenium 테스트 |

### 완결성 (Completeness)
| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 2025-01-01 이후 이벤트 누락 여부 | 0% 누락 | 각 공식 소스와 수동 비교 |
| 신규 이벤트 감지 지연 시간 | < 24시간 | 로그 분석 |
| 4개 제품 모두 > 50개 이벤트 표시 | Yes | 카운트 확인 |

### 사용성 (Usability)
| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 초기 로드 시간 | < 2초 | Lighthouse, DevTools |
| 필터/펼치기 응답 시간 | < 100ms | 수동 측정 |
| "10초 안에 최신 변화 파악" 가능 | Yes (사용성 테스트) | 5명 사용자 테스트 |

### 재방문율 (Re-engagement)
| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 이벤트 카드 클릭율 (펼치기) | > 30% | Google Analytics |
| 필터 사용 비율 | > 40% | Event tracking |
| 하루 방문자 수(3개월 후) | > 100 | Analytics |

---

## 리스크 및 완화 방안

### 1. 파싱 규칙 변경 리스크
| 항목 | 설명 |
|------|------|
| **리스크** | ChatGPT/Gemini 공식 채널의 HTML 구조가 예고 없이 변경되면 파싱 실패 |
| **영향도** | 높음 (데이터 수집 중단) |
| **확률** | 중간 (연 1~2회 예상) |
| **완화 방안** | • 파싱 규칙을 설정 파일로 분리 (하드코딩 피함)<br/>• 변경 감지 후 alert 구조 (content_hash 비교)<br/>• 실패 시 이전 버전으로 롤백하는 fallback<br/>• 월 1회 수동 검증 프로세스 |

### 2. 데이터 정확성 리스크
| 항목 | 설명 |
|------|------|
| **리스크** | 규칙 기반 Severity/Tag 할당이 사용자 기대치와 맞지 않음 (예: Breaking이 아닌데 Breaking으로 표시) |
| **영향도** | 중간 (신뢰도 감소) |
| **확률** | 높음 (초기 버전) |
| **완화 방안** | • Severity/Tag 규칙을 명확히 문서화<br/>• 시작 단계에서 품질 spot check (매주 5~10개 수동 검증)<br/>• 사용자 피드백 채널 (간단한 "이 분류가 맞나?" 투표)<br/>• v1.1에서 관리자 검수 대시보드 도입 |

### 3. 저작권 위반 리스크
| 항목 | 설명 |
|------|------|
| **리스크** | 공식 Release Notes의 원문을 대량 복제하면 저작권 위반 가능성 |
| **영향도** | 높음 (법적 이슈) |
| **확률** | 낮음 (저작권 공정 이용 범위) |
| **완화 방안** | • Evidence excerpt는 2~3줄만 (공정 이용)<br/>• 모든 카드에 Source URL 명시 (원본 링크)<br/>• 약관에 "공정 이용" 명시<br/>• 실제 배포 전 법무 검토 |

### 4. 크롤링 차단 리스크
| 항목 | 설명 |
|------|------|
| **리스크** | 자동 수집 스크립트가 공식 채널(GitHub, Google 서버)에 의해 Rate Limited 또는 차단될 수 있음 |
| **영향도** | 높음 (데이터 수집 중단) |
| **확률** | 낮음 (공식 Changelog는 크롤링 친화적) |
| **완화 방안** | • User-Agent 설정 및 정중한 요청 헤더<br/>• Rate limiting: 최대 초당 1회 요청<br/>• 요청 간 지연 (1~3초)<br/>• GitHub API(Claude Code) 사용, RSS feed 활용(가능시)<br/>• 실패 시 메뉴얼 입력 대체 경로 |

### 5. 성능 저하 리스크 (스케일)
| 항목 | 설명 |
|------|------|
| **리스크** | 시간이 지남에 따라 이벤트가 누적되어(연 1000+) 타임라인 렌더링이 느려질 수 있음 |
| **영향도** | 중간 (사용성 감소) |
| **확률** | 중간 (6개월 이후) |
| **완화 방안** | • Virtual scrolling 도입 (초기 개발 시 아키텍처로 설계)<br/>• 페이지네이션 또는 "이전 이벤트 더 보기" 버튼<br/>• DB 인덱싱 (event_date, product)<br/>• CDN 캐싱 (정적 자산 + API 응답 캐시)<br/>• 모니터링: Sentry, CloudWatch 등 |

---

## 제약조건

### 기술
- **Stack**: HTML/CSS/JS (Vanilla) + FastAPI + SQLite + LangGraph
- **배포 환경**: Railway (또는 Vercel + Heroku)
- **브라우저 지원**: Chrome, Firefox, Safari (모던 브라우저, IE11 미지원)

### 데이터
- **백필 범위**: 2025-01-01 ~ 현재 (과거 이벤트는 제외)
- **대상 제품**: ChatGPT, Gemini, Codex, Claude Code (4개 고정)
- **소스**: 공식 Release Notes/Changelog만 (SSOT 원칙)
- **저장소**: SQLite (단일 파일, 100MB 이하 초기)

### 팀
- **인원**: Claude Code 에이전트 팀 (product-manager, ux-designer, backend-dev, frontend-dev, llm-engineer, coordinator)
- **소유권**: docs/는 product-manager, ux-designer 담당 / 코드는 해당 dev 담당
- **MVP 기간**: 2주 내 배포 (backfill + 화면 + 필터)

### 인증/보안
- **인증**: 없음 (공개 페이지, 읽기만 제공)
- **관리자 수집 트리거**: 인증된 관리 엔드포인트 `/api/admin/sync` (초기는 수동 또는 스케줄러)
- **API 보호**: Rate limiting, CORS 설정

---

## 부록: 데이터 파이프라인 개요

### Backfill (초회, 1회 실행)
```
1. 4개 공식 소스에서 HTML/Markdown 다운로드
2. 규칙 기반 파서 적용 (날짜, 제목, 내용 추출)
3. 이벤트 객체 생성 (title, summary_ko, tags, severity, evidence)
4. SQLite에 일괄 INSERT
```

### Incremental (매일, 자동 스케줄러)
```
1. 4개 소스 재다운로드
2. 이전 content_hash와 비교
3. 변경 있으면 diff 파싱
4. 신규 이벤트만 추출 후 INSERT
5. 수집 시각 기록 (detected_at)
```

### API 계약 (Backend)
```
GET /api/events
  Params: ?products=chatgpt,claude_code&tags=new_feature&severity_min=3&limit=50&offset=0
  Response: { "total": 234, "items": [...], "last_updated": "2026-03-02T14:30:00Z" }

GET /api/events/{id}
  Response: { ...full event details... }

POST /api/admin/sync (protected)
  Body: { "source_ids": ["chatgpt_release_notes"] }
  Response: { "synced": 5, "errors": [] }
```

---

## 다음 단계

1. **UX 설계** (`docs/20-ux.md`): 타임라인 와이어프레임, 화면 흐름도 작성
2. **아키텍처** (`docs/30-architecture.md`): API 상세 계약, DB 스키마, LangGraph 설계
3. **백로그** (`docs/40-backlog.md`): 유저스토리를 태스크로 세분화 (US별 5~8개 태스크)
4. **테스트 계획** (`docs/50-test-plan.md`): 수동 체크리스트 10개, 자동 테스트 케이스
