# Codex Event Enrichment Logic

This document describes the rules used to generate `title_updated` and `content_updated` for `codex_event` records.
These rules serve as the basis for future LLM/skill automation.

---

## 1. Title Generation Rules (`title_updated`)

### Format by `entry_type`

| entry_type | Format | Example |
|------------|--------|---------|
| `codex-cli` | `Codex CLI X.Y.Z: Top 2-3 changes` | `Codex CLI 0.107.0: Thread forking, voice device selection & multimodal custom tools` |
| `codex-app` | `Codex App X.Y: Top 2-3 changes` | `Codex App 26.226: MCP shortcuts, @mentions in reviews & rendering fixes` |
| `general` | `Original Title: Clarifying phrase` | `Introducing GPT-5.3-Codex: Most capable agentic coding model to date` |

### General Rules

1. **Preserve the original title** as a prefix (before the colon).
2. **Append a concise summary** (5-10 words) of the most impactful changes after a colon.
3. Use **ampersand (`&`)** to join the last two items in a list for readability.
4. **Capitalize properly**: Title case for product names, sentence case for descriptions.
5. **English only**.
6. If the original title is already descriptive (e.g., "Custom prompts deprecated"), still append a clarifier to add context.

### Edge Cases

- **Bug-fix-only releases** (e.g., CLI 0.101.0): Focus on the most significant fix. Example: `Codex CLI 0.101.0: Stable model resolution & memory pipeline fixes`.
- **Short announcements** (e.g., "Credits on ChatGPT Pro and Plus"): Append the key action. Example: `Credits on ChatGPT Pro and Plus: On-demand usage beyond plan limits`.
- **Model introductions**: Keep the model name, add key differentiator. Example: `Introducing GPT-5.3-Codex-Spark: Real-time coding at 1000+ tokens/sec`.
- **Already descriptive general titles**: Still append context if possible, but avoid redundancy.

---

## 2. Summary Generation Rules (`content_updated`)

### Structure (exactly 3 lines)

```
Line 1: Core change or announcement — WHAT happened (one sentence)
Line 2: Key features, improvements, or details — HOW/WHAT specifically (one sentence)
Line 3: Scope, impact, availability, or additional context (one sentence)
```

### Rules

1. **Exactly 3 lines** separated by `\n`. No blank lines, no bullet points.
2. **Each line is a complete sentence** ending with a period.
3. **Line 1 (What)**: Start with a verb or noun phrase describing the core change. For model releases, name the model. For CLI/app releases, state the headline feature.
4. **Line 2 (Details)**: List 2-4 specific features or changes using semicolons to separate items within the sentence.
5. **Line 3 (Scope)**: Cover availability (platforms, plans), bug fixes summary, migration notes, or broader impact.
6. **English only**, concise, no marketing language.
7. **No version numbers in the summary** unless referring to a different product/model.

### Examples by `entry_type`

#### codex-cli
```
Enables forking threads into sub-agents, adds microphone/speaker device selection for realtime voice sessions, and supports multimodal output from custom tools.
App server exposes richer model availability and upgrade metadata for plan-gated tooltips; memories are now configurable via codex debug clear-memories.
Bug fixes restore pending approvals on thread resume, fix duplicate assistant response printing, improve Windows Terminal diff colors, and harden MCP OAuth flows.
```

#### codex-app
```
Codex App 26.212 introduces GPT-5.3-Codex-Spark support and two new conversation features.
New features include conversation forking and a floating pop-out window for portable conversations.
Alpha testing for the Windows version of the Codex app is now open for sign-ups.
```

#### general
```
GPT-5.3-Codex is released combining GPT-5.2-Codex coding performance with stronger reasoning and professional knowledge.
Runs 25% faster for Codex users and improves collaboration with frequent progress updates and real-time steering responsiveness.
Available across the Codex app, CLI, IDE extension, and Codex Cloud for paid ChatGPT plans; API access coming soon.
```

---

## 3. Exception Handling

| Scenario | Rule |
|----------|------|
| Body is very short (< 100 chars) | Expand the title into context; Line 3 may describe the broader implication |
| No `[New Features]` section | Focus on bug fixes or the announcement itself |
| Multiple major features | Pick top 2-3 by impact for title; summarize all in content Line 2 |
| Model announcement with config instructions | Omit config instructions from summary; focus on capability and availability |
| Release with only chores/docs | Mention the most user-visible chore; note it as a maintenance release |

---

## 4. Before/After Examples

### codex-cli

| Field | Before | After |
|-------|--------|-------|
| title | `Codex CLI 0.107.0` | `Codex CLI 0.107.0: Thread forking, voice device selection & multimodal custom tools` |
| content | _(empty)_ | `Enables forking threads into sub-agents, adds microphone/speaker device selection for realtime voice sessions, and supports multimodal output from custom tools.\nApp server exposes richer model availability and upgrade metadata for plan-gated tooltips; memories are now configurable via codex debug clear-memories.\nBug fixes restore pending approvals on thread resume, fix duplicate assistant response printing, improve Windows Terminal diff colors, and harden MCP OAuth flows.` |

### codex-app

| Field | Before | After |
|-------|--------|-------|
| title | `Codex app 26.226` | `Codex App 26.226: MCP shortcuts, @mentions in reviews & rendering fixes` |
| content | _(empty)_ | `Adds MCP shortcuts in the composer and @mention support in inline review comments.\nImprovements include better MCP tool call rendering and Mermaid diagram error handling.\nA bug where stopped terminal commands appeared as still running has also been fixed.` |

### general

| Field | Before | After |
|-------|--------|-------|
| title | `Codex is now GA` | `Codex is now GA: Slack integration, SDK, GitHub Action & admin tools` |
| content | _(empty)_ | `Codex reaches general availability with three major additions: @Codex in Slack, the Codex SDK, and new admin tooling.\nSlack task assignment, TypeScript SDK for embedding the agent, new GitHub Action for CI/CD pipelines.\nAvailable on Plus, Pro, Business, Edu, and Enterprise plans; cloud task usage billing begins October 20.` |

---

## 5. LLM Prompt Conversion Guide

To automate this with an LLM, use the following prompt template:

```
You are enriching a Codex changelog entry.

Input:
- entry_type: {entry_type}
- title: {title}
- body: {body}

Generate:
1. title_updated: "{title}: <5-10 word summary of key changes>"
   - For codex-cli: "Codex CLI X.Y.Z: top 2-3 changes"
   - For codex-app: "Codex App X.Y: top 2-3 changes"
   - For general: keep original title, append clarifying phrase

2. content_updated: Exactly 3 lines separated by \n
   - Line 1: Core change (what)
   - Line 2: Key features/details (how)
   - Line 3: Scope/impact/availability (context)

Rules:
- English only, concise, no marketing language
- Each line is a complete sentence ending with a period
- No bullet points, no blank lines
- Use semicolons to separate items within a sentence
```

---

## 6. Korean Localization Rules (`title_updated_ko`, `content_updated_ko`)

### 6.1 Principles

- **의역 > 직역**: 단순 번역이 아니라, `title_updated`와 `content_updated`를 동시에 참고하여 비개발자가 이해할 수 있도록 의역한다.
- **비개발자 친화**: 기술 세부사항(PR 번호, 내부 모듈명)은 생략하고, 사용자 영향 중심으로 서술한다.
- **고유명사 유지**: GPT-5.3-Codex, MCP, TUI, CLI, IDE 등 고유명사는 영어 그대로 유지한다.

### 6.2 `title_updated_ko` Rules

1. `title_updated`(영어 요약)를 한글로 의역
2. 기술 용어는 비개발자가 이해할 수준으로 풀어쓰기
3. 고유명사는 영어 유지
4. 20자 내외 목표

### 6.3 `content_updated_ko` Rules

1. `content_updated`(영어 3줄)를 한글 3줄로 의역
2. 각 줄은 비개발자가 읽고 "이번에 뭐가 바뀌었구나" 파악 가능해야 함
3. 기술 세부사항(PR 번호, 내부 모듈명)은 생략, 사용자 영향 중심
4. 줄 구조 유지: What / Details / Scope

### 6.4 Term Mapping Table

| English | Korean |
|---------|--------|
| Thread forking | 대화 분기 |
| WebSocket proxy | 웹소켓 프록시 지원 |
| Multi-agent CSV fan-out | 다중 에이전트 CSV 분배 |
| Syntax highlighting | 코드 구문 강조 |
| Voice input / dictation | 음성 입력 |
| Steer mode | 조종 모드 |
| Mid-turn steering | 중간 개입 조종 |
| Reusable skills | 재사용 가능한 스킬 |
| Custom prompts deprecated | 사용자 지정 프롬프트 중단 |
| Handoff | 인계 |
| Fuzzy file search | 유사 파일 검색 |
| Rate limits | 속도 제한 |
| Session-scoped approvals | 세션 범위 승인 |
| Concurrent shell | 동시 셸 실행 |
| Context compaction | 맥락 압축 |

### 6.5 Before/After Examples

#### codex-cli

| Field | English (title_updated) | Korean (title_updated_ko) |
|-------|------------------------|--------------------------|
| title | Thread forking, voice device selection & multimodal custom tools | 대화 분기, 음성 장치 선택 및 멀티모달 도구 출력 |

| Field | English (content_updated) | Korean (content_updated_ko) |
|-------|--------------------------|----------------------------|
| Line 1 | Enables forking threads into sub-agents... | 대화를 하위 에이전트로 분기하고, 실시간 음성 세션에서 마이크/스피커를 선택할 수 있습니다. |
| Line 2 | App server exposes richer model availability... | 모델 가용성과 업그레이드 안내가 강화되었으며, 메모리 관리가 설정 가능해졌습니다. |
| Line 3 | Bug fixes restore pending approvals... | 대화 재개 시 승인 복원, 중복 응답, Windows 색상, MCP 인증 관련 버그가 수정되었습니다. |

#### general

| Field | English (title_updated) | Korean (title_updated_ko) |
|-------|------------------------|--------------------------|
| title | Replaced by reusable skills system | 재사용 가능한 스킬 시스템으로 대체 |
| title | Most capable agentic coding model to date | 역대 최고 성능의 에이전트 코딩 모델 |

### 6.6 LLM Prompt Conversion Guide (Korean)

```
You are localizing a Codex changelog entry into Korean for non-developers.

Input:
- title_updated: {title_updated}
- content_updated: {content_updated}

Generate:
1. title_updated_ko: Korean paraphrase of title_updated (~20 chars)
   - Simplify technical terms for non-developers
   - Keep proper nouns (GPT-5.3-Codex, MCP, TUI) in English
   - Focus on user impact, not internal details

2. content_updated_ko: Korean paraphrase of content_updated (exactly 3 lines)
   - Line 1: 핵심 변경 사항 (What)
   - Line 2: 주요 기능/세부 사항 (Details)
   - Line 3: 범위/영향/가용성 (Scope)

Rules:
- 의역 > 직역 (paraphrase, don't translate literally)
- 비개발자가 "이번에 뭐가 바뀌었구나" 파악 가능해야 함
- PR 번호, 내부 모듈명 등 기술 세부사항 생략
- 각 줄은 완전한 문장, 마침표로 끝남
- 줄바꿈(\n)으로 구분, 빈 줄 없음
```

---

## 7. Statistics

- Total records enriched: 49
- By entry_type: codex-cli (13), codex-app (11), general (25)
- Average title_updated length: ~60 characters
- All content_updated entries follow the 3-line structure
- All 49 records have title_updated_ko and content_updated_ko populated
