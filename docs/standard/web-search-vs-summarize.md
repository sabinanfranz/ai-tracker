# 웹서치와 정리 노드를 분리하는 표준 가이드 (범용 버전)

이 문서는 **"웹에서 근거를 찾아오는 단계"**와 **"근거를 검증·정리·구조화하는 단계"**를 **노드(스텝)로 분리**해 운영할 때의 표준 원칙을 정리한 가이드입니다.
특히 **Gemini의 Google Search Grounding(= `google_search` 도구)**처럼 "LLM 호출 안에서 검색이 자동 수행되는" 유형을 기준으로, 어디까지를 분리하는 게 합리적인지까지 포함합니다.

---

## 0) 핵심 요약

* **Gemini `google_search`는 "검색-only API"가 아니라, LLM 호출(`generateContent`) 안에서 모델이 필요 시 검색→처리→근거 메타데이터 반환까지 수행하는 방식**이다.
* 그래서 **표준 권장 분리**는 보통 이렇게 간다:

&nbsp; 1. **(검색+생성) 1노드**: `google_search` enabled → 답변 + `groundingMetadata` 획득
&nbsp; 2. **(정리/표준화) 1노드**: `groundingMetadata` 파싱 → 출처/하이라이트/UI용 구조화

* 정말로 **"검색-only 노드"**를 만들고 싶다면, **Vertex의 "Grounding with your search API"**처럼 **외부 검색 엔진을 도구로 붙이는 방식**(또는 전통 RAG)을 써야 한다.

---

## 1) 왜 "웹서치"와 "정리"를 나누나

### 목표

* **정확도·최신성**: 근거 기반 답변(grounding)으로 환각 감소
* **추적 가능성**: "어떤 쿼리로 어떤 근거를 썼는지"를 로그/DB로 남겨 재현
* **UI/제품화**: 모델 출력(자유 텍스트)과 별개로 "출처 패널/하이라이트/근거 목록"을 안정적으로 렌더링

### 분리의 핵심 원칙

* **LLM 호출은 비결정적(변동/비용/지연/리스크)** → 가능한 한 "1번만"
* **정리·검증·중복제거는 결정적(규칙 기반 가능)** → **후처리 노드로 분리**해서 안정화

---

## 2) Gemini `google_search` 기반 표준 아키텍처

### 패턴 A (권장 기본): "검색+생성" 1노드 + "정리/표준화" 1노드

**Node A — GroundedGenerate (검색+생성)**
- 입력: 사용자 질문(또는 리서치 태스크)
- 동작: `generateContent`에 `google_search` tool 활성화 → 모델이 필요 시 자동 검색
- 출력: `answer_text` + `groundingMetadata` (+ 사용량 메타데이터 등)

**Node B — GroundingPostprocess (정리/표준화)**
- 입력: Node A 결과(JSON)
- 동작:
&nbsp; - URL 중복 제거 / 도메인 다양화
&nbsp; - `groundingSupports` 기반 하이라이트/인용 매핑
&nbsp; - UI 렌더용 `sources[]`, `citations[]`, `highlights[]` 생성

> 참고: `google_search`를 켠다고 항상 검색이 수행되는 건 아니며, 이때는 `groundingMetadata`가 없을 수 있다.

---

### 패턴 B (전제가 필요): "검색-only 노드" + "요약/구조화 노드"

- 전제: Gemini `google_search`는 "검색-only 분리 API"가 아니라 모델 내부 워크플로우.
- 따라서 검색-only가 꼭 필요하면:
&nbsp; - Vertex "Grounding with your search API"로 외부 검색 엔드포인트를 도구로 제공하거나
&nbsp; - 전통 RAG(검색 API 직접 호출 → 컨텍스트 구성 → LLM 합성)으로 설계한다.

---

## 3) "3단계 리서치 파이프라인" 표준 패턴 (범용)

### Step 1 — Entity Resolve (식별/정규화)
- 출력: `resolved_entity`, `aliases`, `as_of_date`, `evidence_urls[]`

### Step 2 — Evidence Harvest (근거 수집)
- 출력: `evidence_items[]` (문단 패러프레이즈 + URL + 발행일 + 출처 타입)
- Gemini `google_search`를 쓰면 Step 2는 "검색+생성" 노드가 자연스럽다.

### Step 3 — Verify & Synthesize (검증/정리/구조화)
- 출력: `top_strategies[]`, `conflicts[]`, `gaps[]` 등

---

## 4) 노드 경계 설계 표준 (I/O 계약)

### 공통 필드 (강력 권장)
- `schema_version`
- `as_of_date`
- `model`
- `tooling` (`google_search` 활성/사용 여부)
- `evidence_window`

### "정리 노드"는 결정적으로 만들기
- URL 정규화, 중복제거, 도메인 다양화, 인용 매핑 등은 규칙 기반으로.

---

## 5) 프롬프트(정책) 표준 규칙
- URL 없는 주장 출력 금지
- 근거 없는 수치/전략 창작 금지
- 가능한 1차 출처 우선

---

## 6) 모델 선택 표준 (Flash vs Pro)
- Flash: 수집/탐색/초기 정리
- Pro: 검증/충돌해소/최종 구조화

---

## 7) 운영 체크리스트
- URL이 모든 핵심 주장에 붙어 있는가?
- `webSearchQueries` 저장했는가?
- grounded result 여부(`groundingMetadata` 존재) 저장했는가?
- 정리 노드는 규칙 기반인가?
- Step2 캐시로 Step3 비용을 줄였는가?

---

## 8) 최소 권장 "표준 템플릿"
- 2노드: `GroundedGenerate(google_search)` → `GroundingPostprocess`
- 3노드: `EntityResolve` → `EvidenceHarvest(google_search)` → `Verify&Synthesize(Pro)`
- 검색-only가 꼭 필요하면: `ExternalSearch(API)` → `LLM Synthesize` (또는 Vertex your search API)
