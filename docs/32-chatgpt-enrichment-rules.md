# ChatGPT Event Enrichment Rules — `title_updated` & `content_updated`

> 이 문서는 `chatgpt_event` 테이블의 `title_updated`와 `content_updated` 컬럼을 생성하기 위한 정성적(qualitative) 로직을 정의한다.
> 추후 자동화 스킬로 전환될 예정이며, 수동 enrichment 시에도 이 규칙을 따른다.

---

## 1. 목적

ChatGPT 릴리즈 노트의 원본 제목(title)은 종종 모호하거나 마케팅 중심으로 작성되어, 제목만으로는 실제 변경 사항을 파악하기 어렵다.

| 문제 유형 | 원본 제목 예시 | 왜 문제인가 |
|-----------|---------------|------------|
| 막연한 제품명 | "Voice Updates" | 어떤 Voice 업데이트인지 알 수 없음 |
| 기능명만 나열 | "More visual responses" | 무엇이 시각적으로 바뀌었는지 불명 |
| 문장형 제목 | "Today, we're releasing GPT-5.2..." | 너무 길고 핵심이 묻힘 |
| 반복 제목 | "Retiring GPT-4o and other legacy models" (2회) | 날짜별 차이 불명 |
| 마케팅 슬로건 | "Your Year with ChatGPT" | 기능 변경인지 프로모션인지 불명 |

`title_updated`와 `content_updated`는 이러한 문제를 해결하여 UX/UI에서 한눈에 변경 사항을 파악할 수 있게 한다.

---

## 2. 제목 패턴 분류 (Title Quality Taxonomy)

원본 제목을 아래 8개 패턴으로 분류하고, 각 패턴에 맞는 변환 전략을 적용한다.

### P1: VAGUE_PRODUCT_UPDATE
- **특징**: 제품/기능명 + "Updates" / "Update" / "Improvements"
- **예시**: `"Voice Updates"`, `"Dictation Updates"`, `"Updates to deep research"`
- **문제**: 어떤 업데이트인지 전혀 알 수 없음
- **전략**: content에서 핵심 변경 사항을 추출하여 구체적 제목으로 교체

### P2: BARE_FEATURE_NAME
- **특징**: 기능명만 단독으로 사용
- **예시**: `"More visual responses"`, `"Health in ChatGPT"`, `"Shopping research in ChatGPT"`
- **문제**: 신규 출시인지, 업데이트인지, 폐기인지 불명
- **전략**: content에서 동작(launch/update/retire)을 파악하여 `"[동작]: [구체적 설명]"` 형태로

### P3: SENTENCE_AS_TITLE
- **특징**: 제목이 완전한 문장 또는 content 첫 줄과 동일
- **예시**: `"Today, we're releasing GPT-5.2, the next upgrade to the GPT-5 series..."`
- **문제**: 제목 역할을 못 하고 너무 길음
- **전략**: 핵심 주어+동사+목적어만 추출하여 80자 이내로 압축

### P4: ANNOUNCEMENT_HEADLINE
- **특징**: 이미 충분히 구체적인 발표형 제목
- **예시**: `"Introducing the Codex app"`, `"Interactive Code Blocks in ChatGPT"`
- **문제**: 비교적 양호하나, 구체적 기능 설명이 부족할 수 있음
- **전략**: content에서 1~2개 핵심 기능을 추가하여 보강

### P5: RETIREMENT_NOTICE
- **특징**: 모델/기능 폐기 공지
- **예시**: `"Retiring GPT-4o and other legacy models"`, `"Voice on macOS desktop app is retiring"`
- **문제**: 어떤 모델이 폐기되고 대체재가 무엇인지 불명
- **전략**: 폐기 대상 전체 목록 + 대체 모델/기능 + 시행일을 포함

### P6: MODEL_VERSION_UPDATE
- **특징**: 모델 버전 + 간단한 수식어
- **예시**: `"GPT-5.2 Instant Update"`, `"5.2 Personality System Prompt Update"`
- **문제**: 어떤 개선인지 구체적이지 않음
- **전략**: content에서 개선 내용(성능/스타일/안전성 등)을 추출

### P7: PLATFORM_EXPANSION
- **특징**: 특정 플랫폼으로의 확장/롤아웃
- **예시**: `"ChatGPT Images on Web and Mobile (iOS & Android)"`
- **문제**: 비교적 양호하나, 핵심 개선사항이 누락될 수 있음
- **전략**: 플랫폼 정보 유지 + 핵심 기능 개선사항 추가

### P8: POLICY_OR_TEST
- **특징**: 정책 변경, A/B 테스트, 연령 제한 등
- **예시**: `"Testing ads in ChatGPT (Free, Go)"`, `"Rolling out age prediction"`
- **문제**: 비교적 구체적이나, 영향 범위가 불명
- **전략**: 대상 사용자/플랜 + 구체적 영향을 명시

---

## 3. `title_updated` 생성 규칙

### 형식

```
[Subject]: [Key changes — max 80 chars total]
```

- 전체 길이: **최대 90자** (영문 기준)
- 구분자: 콜론(`:`) + 공백
- Subject: 제품/기능/모델명 (e.g., `ChatGPT Voice`, `GPT-5.2`, `Deep Research`)
- Key changes: 동사로 시작하는 핵심 변경 사항

### T1: 구체적 동작 동사로 시작

원본이 모호할수록 content에서 핵심 동사를 추출한다.

| 동작 유형 | 사용할 동사 |
|-----------|------------|
| 신규 출시 | Launch, Introduce, Release, Add |
| 기능 개선 | Improve, Enhance, Upgrade, Expand |
| 모델 업데이트 | Update, Upgrade, Promote |
| 폐기/종료 | Retire, Remove, Deprecate, Sunset |
| 설정 변경 | Enable, Configure, Adjust |
| 버그 수정 | Fix, Resolve, Restore |
| 확장 | Expand, Roll out, Extend |
| 테스트 | Test, Pilot, Experiment |

**예시**:
- `"Voice Updates"` → `"ChatGPT Voice: Improve instruction following & fix custom instruction echo bug"`
- `"More visual responses"` → `"ChatGPT Responses: Add at-a-glance visuals for stats, conversions & quick lookups"`

### T2: Subject 선택 우선순위

1. **모델명** (GPT-5.2, o4-mini 등) — 모델 관련 변경일 때
2. **기능명** (Voice, Deep Research, Images, Tasks 등) — 기능 업데이트일 때
3. **ChatGPT** — 범용 플랫폼 변경일 때
4. **제품명 + 플랫폼** (ChatGPT Web, ChatGPT iOS 등) — 플랫폼 특정일 때

### T3: 복수 변경 사항 처리

content에 여러 변경이 포함된 경우:
- 가장 중요한 1~2개만 제목에 포함
- `&`로 연결 (comma가 아닌 ampersand)
- 3개 이상이면 가장 큰 변경 + `& more`

**예시**:
- `"ChatGPT updates: Better file uploads, easier copying, and more reliable long chats"` → `"ChatGPT Web: Increase file upload limit to 20 & improve long chat reliability"`

### T4: 날짜/버전 중복 제목 구별

같은 제목이 여러 날짜에 걸쳐 반복되는 경우 (e.g., `"Retiring GPT-4o..."` 1/29 vs 2/13):
- 예고 공지: `"[Subject]: Announce retirement (effective [date])"`
- 실행 공지: `"[Subject]: Complete retirement of [models]"`

### T5: 마케팅/프로모션 이벤트

content가 기능 변경이 아닌 프로모션인 경우:
- `"Your Year with ChatGPT"` → `"ChatGPT: Launch personalized 2025 year-in-review experience"`
- 동작 동사를 사용하되, 프로모션 성격을 명시

### T6: 문장형 제목 압축

원본 제목이 문장인 경우:
1. 주어(Subject)를 추출
2. 핵심 동사를 추출
3. `[Subject]: [동사] [목적어]` 형태로 재구성

**예시**:
- `"Today, we're releasing GPT-5.2, the next upgrade..."` → `"GPT-5.2: Launch smarter model with improved work & learning capabilities"`

### T7: 파서 아티팩트 정리

HTML 태그, 불완전한 문장, 깨진 인코딩이 포함된 경우:
- 모든 HTML/마크다운 태그 제거
- 깨진 문자 교체 또는 제거
- 의미를 보존하면서 깨끗한 텍스트로 재작성

### T8: 약어 및 용어 일관성

| 원본 표현 | 통일 표현 |
|-----------|----------|
| ChatGPT Voice, Voice mode | ChatGPT Voice |
| deep research, Deep Research | Deep Research |
| GPT-5.2 (Instant), GPT-5.2 Instant | GPT-5.2 Instant |
| iOS & Android, mobile | Mobile (iOS & Android) |
| macOS desktop app | ChatGPT macOS |

### T9: 원본 제목이 이미 충분히 좋은 경우

아래 조건을 모두 만족하면 원본 제목을 그대로 사용 (`title_updated = title`):
- 80자 이내
- 구체적 기능/모델명 포함
- 동작(출시/개선/폐기)이 명확
- HTML/인코딩 문제 없음

**예시**: `"Interactive Code Blocks in ChatGPT"` — 이미 충분히 구체적

---

## 4. `content_updated` 생성 규칙

### 형식

정확히 **3줄**, 줄바꿈(`\n`)으로 구분. 각 줄은 완전한 영어 문장.

```
[Line 1: WHAT — 핵심 변경 사항]
[Line 2: DETAILS — 구체적 기능/수치/대상]
[Line 3: CONTEXT — 배경, 이전 상태, 영향 범위]
```

- 각 줄: **40~80 단어** (너무 짧으면 정보 부족, 너무 길면 요약 아님)
- 총 길이: **120~240 단어**
- 언어: **영어** (한국어 번역은 별도 파이프라인에서 처리)

### C1: Line 1 — WHAT (핵심 변경)

- 가장 큰 변경 사항 1개를 한 문장으로 요약
- 주어는 제품/기능명, 동사는 현재형 또는 과거형
- 사용자 관점에서 "무엇이 달라지는가"에 초점

**예시**:
```
ChatGPT Voice now better follows user instructions and uses tools like web search more effectively to provide improved responses.
```

### C2: Line 2 — DETAILS (구체적 사항)

- 수치, 대상 플랫폼, 적용 플랜, 기술적 세부사항
- Line 1에서 다루지 못한 2~3번째 중요 변경도 여기서 포함
- 가능하면 구체적 숫자/버전/날짜를 포함

**예시**:
```
The update applies to the standard Voice mode (not Advanced Voice), is available to all paid users, and also fixes a bug where Voice would sometimes repeat back custom instructions verbatim.
```

### C3: Line 3 — CONTEXT (배경/영향)

- 이전 상태와의 비교 (before/after)
- 영향 받는 사용자 그룹
- 향후 계획이나 관련 변경 사항 언급
- 없으면 경쟁 맥락이나 산업 트렌드 언급

**예시**:
```
This is the second Voice update in January 2026, following the December integration of Voice into the main chat interface; the instruction-following improvement addresses a top user complaint from community feedback.
```

### C4: 빈약한 content 처리

원본 content가 1~2줄로 매우 짧은 경우:
- Line 1: content 전체를 paraphrase
- Line 2: 제목에서 추가 정보 추출
- Line 3: 해당 기능의 이전 상태 또는 일반적 맥락 제공
- **추측하지 말 것** — 정보가 없으면 `"No additional details were provided in the release note."` 사용

### C5: 다중 변경 번들 처리

하나의 이벤트에 3개 이상의 독립적 변경이 포함된 경우:
- Line 1: 가장 중요한 변경에 집중
- Line 2: 나머지 변경을 comma-separated list로 요약
- Line 3: 전체 번들의 맥락 제공

**예시** (2026-02-13 "ChatGPT updates: Better file uploads..."):
```
ChatGPT now supports uploading up to 20 files in a single message, doubling the previous limit of 10 for easier document analysis and multi-file comparison.
Additional improvements include a new copy button on code blocks for one-click copying, better handling of long conversations that previously lost context, and improved error recovery during extended sessions.
These quality-of-life updates focus on power-user workflows and address long-standing requests from the ChatGPT community; they apply to all plans on web.
```

### C6: 모델 업데이트 content 구조

모델 버전 업데이트 (GPT-5.2 등)의 경우:
- Line 1: 성능/품질 변화의 핵심
- Line 2: 구체적 벤치마크, 사용 가능 플랜, API 영향
- Line 3: 이전 버전과의 차이, 마이그레이션 영향

### C7: 폐기(Retirement) content 구조

모델/기능 폐기 공지의 경우:
- Line 1: 폐기 대상 전체 목록 + 시행일
- Line 2: 대체 모델/기능 + 마이그레이션 경로
- Line 3: API 영향 여부 + 사용자 필요 조치

**예시** (2026-02-13 "Retiring GPT-4o..."):
```
OpenAI retires GPT-4o, GPT-4.1, GPT-4.1 mini, o4-mini, and GPT-5 (Instant and Thinking) from ChatGPT effective February 13, 2026.
No API changes are included in this retirement; API users retain access to these models. ChatGPT users are automatically migrated to GPT-5.2 as the default model.
This follows the January 29 advance notice and completes the planned consolidation of the GPT model lineup around the GPT-5.2 series; GPT-5.2 Thinking replaces all retired reasoning models.
```

### C8: HTML/마크업 정리

- 모든 HTML 태그 제거 (`<br>`, `<a>`, `<strong>` 등)
- 마크다운 링크는 텍스트만 유지 (`[text](url)` → `text`)
- 특수문자 정규화 (`\xa0` → space, `—` 유지, `"` → `"`)
- 줄 내 불필요한 공백 제거

---

## 5. Edge Case 처리

### E1: 같은 날짜에 동일한 제목

`UNIQUE(event_date, title)` 제약으로 불가능하지만, 유사한 제목이 같은 날 존재할 수 있음.
- 각 이벤트의 content를 읽어 구별되는 제목을 생성
- `title_updated`에 구체적 차이점을 반영

### E2: 예고 → 실행 쌍

동일한 주제가 예고(advance notice)와 실행(effective date)으로 나뉜 경우:
- 예고: `"[Subject]: Announce [action] effective [date]"`
- 실행: `"[Subject]: [action] now in effect"`
- `content_updated` Line 3에서 쌍을 상호 참조

### E3: 롤아웃 단계

점진적 롤아웃(gradual rollout)인 경우:
- 제목에 대상 그룹 명시: `"[Subject]: Roll out to [Free/Plus/Pro] users"`
- content Line 2에 롤아웃 범위/일정 명시

### E4: 되돌림(Revert) 이벤트

이전 변경을 되돌리는 경우:
- `"[Subject]: Revert [previous change] due to [reason]"`
- content Line 3에 원래 변경의 날짜/내용 참조

### E5: content가 비어있는 경우

극히 드물지만 content가 빈 문자열인 경우:
- `title_updated`: 원본 제목을 규칙 T1~T9에 따라 정리
- `content_updated`: `"[title] was announced with no additional details.\nNo specific features, changes, or timeline were provided in the release note.\nRefer to the source URL for any subsequent updates or clarifications."`

---

## 6. 변환 예시 (Before → After)

### 예시 1: VAGUE_PRODUCT_UPDATE

**원본**:
- title: `"Voice Updates"`
- content: `"We're making an update to ChatGPT Voice for paid users that improves its ability to follow user instructions, as well as fixes a bug where Voice can sometimes repeat back custom instructions."`

**변환**:
- title_updated: `"ChatGPT Voice: Improve instruction following & fix custom instruction echo bug"`
- content_updated:
  ```
  ChatGPT Voice now better follows user instructions and resolves a bug where custom instructions were sometimes repeated back verbatim.
  This update targets the standard Voice mode for paid users and does not affect Advanced Voice mode.
  This is part of ongoing Voice improvements following the November 2025 integration of Voice into the main chat interface.
  ```

### 예시 2: SENTENCE_AS_TITLE

**원본**:
- title: `"Today, we're releasingGPT-5.2, the next upgrade to the GPT-5 series. GPT-5.2 is smarter and more use"`
- content: `"Today, we're releasingGPT-5.2, the next upgrade to the GPT-5 series. GPT-5.2 is smarter and more useful for both work and learning..."`

**변환**:
- title_updated: `"GPT-5.2: Launch smarter GPT-5 series upgrade for work & learning"`
- content_updated:
  ```
  OpenAI releases GPT-5.2 as the next upgrade in the GPT-5 series, offering improved intelligence and usefulness for work and learning tasks.
  Like GPT-5.1, GPT-5.2 is available in both Instant and Thinking variants and maintains compatibility with existing ChatGPT and API workflows.
  GPT-5.2 replaces GPT-5.1 as the default model; the upgrade continues OpenAI's pattern of iterative improvements within the GPT-5 generation.
  ```

### 예시 3: BARE_FEATURE_NAME

**원본**:
- title: `"Health in ChatGPT"`
- content: `"We're starting to roll out Health, a dedicated space in ChatGPT for health and wellness conversations. You can securely connect medical records, Apple Health and supported wellness apps..."`

**변환**:
- title_updated: `"ChatGPT Health: Launch dedicated space for health & wellness with medical record integration"`
- content_updated:
  ```
  ChatGPT introduces Health, a dedicated space for health and wellness conversations that securely connects to medical records, Apple Health, and supported wellness apps.
  Users can get personalized health answers grounded in their own medical data, with conversations kept private and secure within the Health section.
  This marks ChatGPT's first dedicated vertical feature for healthcare, rolling out gradually to eligible users as part of OpenAI's push into domain-specific experiences.
  ```

### 예시 4: RETIREMENT_NOTICE (예고)

**원본**:
- title: `"Retiring GPT-4o and other legacy models"` (2026-01-29)
- content: `"On February 13, 2026, alongside the previously announced retirement of GPT-5 (Instant and Thinking), we will retire GPT-4o, GPT-4.1, GPT-4.1 mini, and OpenAI o4-mini from ChatGPT..."`

**변환**:
- title_updated: `"Legacy Models: Announce retirement of GPT-4o, GPT-4.1 & o4-mini effective Feb 13"`
- content_updated:
  ```
  OpenAI announces that GPT-4o, GPT-4.1, GPT-4.1 mini, and o4-mini will be retired from ChatGPT on February 13, 2026, alongside the previously announced GPT-5 Instant and Thinking retirement.
  API access to these models remains unchanged; the retirement applies only to the ChatGPT consumer product. Users will be automatically migrated to GPT-5.2.
  This advance notice gives users two weeks to prepare; a follow-up announcement on February 13 will confirm the completion of the retirement.
  ```

### 예시 5: POLICY_OR_TEST

**원본**:
- title: `"Testing ads in ChatGPT (Free, Go)"`
- content: `"We're beginning to roll out a test for ads in ChatGPT in the U.S. for logged-in adults on the Free and Go tiers..."`

**변환**:
- title_updated: `"ChatGPT Ads: Begin ad test for Free & Go tier users in the U.S."`
- content_updated:
  ```
  OpenAI begins testing advertisements in ChatGPT for logged-in adult users on the Free and Go tiers in the United States.
  Plus, Pro, Business, Enterprise, and Education plans are excluded from the ad test; ads appear as contextual suggestions within conversations.
  This is OpenAI's first public ad experiment in ChatGPT, potentially opening a new revenue stream beyond subscription plans.
  ```

---

## 7. 품질 체크리스트

`title_updated` 생성 후 아래 항목을 확인:

- [ ] 90자 이내인가?
- [ ] Subject + 콜론 형식인가? (원본이 이미 좋은 경우 예외)
- [ ] 구체적 동작 동사가 포함되어 있는가?
- [ ] content를 읽지 않고도 변경 내용을 파악할 수 있는가?
- [ ] HTML/특수문자가 정리되었는가?
- [ ] 동일 날짜의 다른 이벤트와 구별되는가?

`content_updated` 생성 후 아래 항목을 확인:

- [ ] 정확히 3줄인가?
- [ ] Line 1은 WHAT, Line 2는 DETAILS, Line 3은 CONTEXT인가?
- [ ] 각 줄이 40~80 단어인가?
- [ ] 원본에 없는 정보를 추측하지 않았는가?
- [ ] HTML/마크업이 모두 제거되었는가?
- [ ] 영어로 작성되었는가?

---

## 8. 스킬 전환 시 참고사항

이 규칙을 자동화 스킬로 전환할 때:

1. **패턴 분류 자동화**: title 키워드 매칭으로 P1~P8 자동 분류
2. **프롬프트 템플릿**: 각 패턴별 LLM 프롬프트 템플릿 준비
3. **품질 검증**: 생성 후 길이/형식 자동 검증
4. **배치 처리**: 5개 단위로 처리하고, 이전 배치 결과를 few-shot example로 활용
5. **fallback**: LLM 실패 시 규칙 기반(T1~T9, C1~C8) 로직으로 대체
