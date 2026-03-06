# 00 — MVP Brief

## MVP 한 줄 요약

> 공식 Release Notes/Changelog에서 "변화(Added/Changed/Fixed/Deprecated)"를 매일 수집·정규화하고, 2025→현재까지를 세로 타임라인으로 제공하는 업데이트 트래커.

## 제약조건

- 스택: HTML/CSS/JS + FastAPI + SQLite + LangGraph
- 대상 제품: ChatGPT, Gemini, Codex, Claude Code (4개)
- 데이터 범위: 2025-01-01 ~ 현재
- 데이터 소스: 공식 Release Notes/Changelog만 (SSOT)
- 인원: Claude Code 에이전트 팀

## 가정

- [ ] 4개 공식 소스의 날짜 헤더/버전 블록이 규칙적이어서 파싱 가능
- [ ] 저작권 이슈로 원문 대량 복제는 불가 — 짧은 발췌 + 링크 중심
- [ ] MVP는 LLM 없이 규칙 기반 점수(Severity)만으로 충분
- [ ] 화면은 1개(세로 타임라인)로 MVP 종결

## 데이터 소스 (SSOT)

| 제품 | 소스 URL |
|------|----------|
| ChatGPT | https://help.openai.com/en/articles/6825453-chatgpt-release-notes |
| Gemini (Apps) | https://gemini.google/release-notes/ |
| Codex | https://developers.openai.com/codex/changelog/ |
| Claude Code | https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md |

## 핵심 화면: 세로 타임라인

- 하나의 세로 선 + 이벤트 점(dot) + 이벤트 카드
- 카드 필수 필드: Date, Product 배지, Title, Summary(2줄), Tags, Source 링크
- 카드 접기/펼치기: What changed(3 bullets), Impact/Action, Evidence(발췌 1~2줄)
- Sticky Filter Bar: Product 토글(4개), Tag 필터, Severity 슬라이더
- Jump 컨트롤: 2025, 2026, Latest
- Month Divider

## MVP 범위 (Must-have)

- 2025~현재 백필 + 매일 증분 수집
- 타임라인 화면 1개(선+점+카드)
- Product 필터 + Tag 필터 + Year Jump
- Source 링크 + (짧은) Evidence

## Nice-to-have (v1.1)

- "오늘/이번주 변화" 요약 배너
- 이메일/슬랙 알림(특히 Breaking만)
- 검색(키워드)
- 관리자 검수(자동 요약 품질 보정)

## 성공 기준

- 신뢰: 카드마다 source 링크/근거가 있다
- 재방문: "어제 대비 무엇이 바뀜?"을 10초 안에 확인 가능
- 완결성: 4개 제품의 2025~현재 이벤트가 누락 없이 이어진다

## 이벤트 스키마

```json
{
  "id": "uuid",
  "product": "chatgpt | gemini | codex | claude_code",
  "component": "default",
  "event_date": "YYYY-MM-DD",
  "detected_at": "YYYY-MM-DDTHH:mm:ssZ",
  "title": "string",
  "summary_ko": "string",
  "summary_en": "string|null",
  "tags": ["new_feature", "model", "breaking", "deprecation", "access", "bugfix"],
  "severity": 1,
  "source_url": "https://...",
  "evidence_excerpt": ["short line 1", "short line 2"],
  "raw_ref": {
    "source_id": "chatgpt_release_notes",
    "section_key": "heading anchor / version block id"
  }
}
```

## 데이터 파이프라인

- Backfill(1회): 4개 소스 2025-01-01 이후 전체 파싱
- Incremental(매일): 해시 변화 감지 → diff → 신규 이벤트 생성

## 리디자인 검토 사항

> 굳이 태그와 중요도가 다 필요할까? 비개발자부터 이제 막 클로드 코드를 쓰기 시작한 사람 정도가 궁금해할 정보와 필터 구조는 어떤 걸까?
