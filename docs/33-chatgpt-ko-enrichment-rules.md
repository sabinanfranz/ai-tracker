# ChatGPT 한국어 Enrichment 작업 절차

ChatGPT 릴리즈 노트의 영어 enrichment(`title_updated`, `content_updated`)를 한국어 문장형 제목(`title_updated_ko`)과 세 줄 요약(`content_updated_ko`)으로 변환하는 규칙.

> **적용 범위**: `chatgpt_event` 테이블 전용. Codex, Gemini, Claude Code 등 다른 제품에는 별도 규칙이 있다.

---

## 1. title_updated_ko 규칙

### 형식
- **문장형 설명** (헤드라인이 아닌 한 줄 설명)
- 예: "프로젝트에 앱, 대화, 텍스트를 소스로 추가할 수 있어요"

### 어미
- `~해요` 체 (해요체)
- 예: "~할 수 있어요", "~가 추가됐어요", "~이 개선됐어요", "~가 출시됐어요"

### 길이
- **20~45자** (한국어 기준)

### 변환 방식
- `title_updated`의 `[Subject]: [Action]` 형식을 한국어 문장으로 풀어서 재구성
- `title_updated`와 `content_updated`를 **함께 읽고** 의미를 파악
- 단순 번역이 아니라 핵심 가치를 한 문장으로 전달

### 예시

| title_updated | title_updated_ko |
|---|---|
| `ChatGPT Projects: Add sources from apps, chats & ad-hoc text` | 프로젝트에 앱, 대화, 텍스트를 소스로 추가할 수 있어요 |
| `GPT-5.2 Thinking: Expand context window to 256k tokens` | GPT-5.2 Thinking의 컨텍스트 창이 256k 토큰으로 확장됐어요 |
| `ChatGPT Search: Launch as default search engine on Safari` | ChatGPT 검색을 Safari 기본 검색엔진으로 설정할 수 있어요 |

---

## 2. content_updated_ko 규칙

### 형식
- **정확히 3줄**, `\n`으로 구분
- 각 줄 **30~60자** (한국어 기준)

### 어미
- `~습니다` 체 (합쇼체)

### 3줄 구조

| 줄 | 역할 | 설명 |
|---|---|---|
| Line 1 | **핵심 변경 (WHAT)** | 무엇이 바뀌었는지 한 문장 |
| Line 2 | **구체적 사항 (DETAILS)** | 수치, 플랜, 플랫폼, 모델명 등 세부 정보 |
| Line 3 | **배경/영향 (CONTEXT)** | 왜 중요한지, 누구에게 영향이 있는지 |

### 예시

```
ChatGPT 프로젝트에 앱, 대화, 직접 입력 텍스트를 소스로 추가할 수 있습니다.
소스는 프로젝트 지식 기반에 통합되며, 관련 대화에서 자동으로 참조됩니다.
프로젝트를 살아있는 지식 베이스로 발전시켜 맥락 기반 응답 품질이 향상됩니다.
```

---

## 3. 용어 처리 기준

### 영문 유지 (번역하지 않음)

| 카테고리 | 예시 |
|---|---|
| 모델명 | GPT-4o, GPT-4.5, GPT-5, GPT-5.2, o1, o3, o3-pro, o4-mini |
| 플랜명 | Free, Plus, Pro, Go, Team, Enterprise, Edu, Business |
| 플랫폼 | iOS, Android, Web, macOS, Windows, Safari, Chrome |
| 기술 용어 | API, SDK, MCP, DALL·E, Canvas, Operator, Deep Research |
| 고유 기능명 | Sora, Codex, Projects, Connectors, Tasks |

### 한국어 변환

| 영문 | 한국어 |
|---|---|
| Voice / Voice mode | 음성 / 음성 모드 |
| Search | 검색 |
| Memory | 메모리 |
| Custom Instructions | 사용자 지정 지침 |
| Code Blocks | 코드 블록 |
| File uploads | 파일 업로드 |
| Image generation | 이미지 생성 |
| Reasoning | 추론 |
| Context window | 컨텍스트 창 |
| Scheduled tasks | 예약 작업 |
| Shortcuts | 단축키 |
| Settings | 설정 |
| Notifications | 알림 |
| Dark mode | 다크 모드 |
| Sidebar | 사이드바 |
| System prompt | 시스템 프롬프트 |
| Token | 토큰 |

### 혼합 표기 (문맥에 따라)

| 영문 | 기본 표기 | 비고 |
|---|---|---|
| Deep Research | Deep Research | 고유명사로 유지 |
| Temporary chat | 임시 대화 | 일반 용어이므로 번역 |
| Structured Outputs | Structured Outputs | API 기능명이므로 유지 |
| Shared links | 공유 링크 | 일반 용어이므로 번역 |

---

## 4. 숫자/날짜 처리

- 숫자: 원문 그대로 (`256k`, `50%`, `1M`)
- 날짜: 원문 형식 유지
- 버전: 원문 그대로 (`GPT-4o`, `v1.2`)

---

## 5. 품질 체크리스트

- [ ] title_updated_ko가 20~45자인가?
- [ ] title_updated_ko가 `~해요` 체인가?
- [ ] content_updated_ko가 정확히 3줄인가?
- [ ] content_updated_ko 각 줄이 30~60자인가?
- [ ] content_updated_ko가 `~습니다` 체인가?
- [ ] Line 1이 WHAT, Line 2가 DETAILS, Line 3이 CONTEXT인가?
- [ ] 모델명/플랜명/플랫폼이 영문 유지되었는가?
- [ ] 단순 번역이 아니라 의미 파악 후 재구성했는가?
