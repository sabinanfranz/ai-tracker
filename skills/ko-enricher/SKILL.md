---
name: ko-enricher
description: |
  Codex 이벤트 전용 한국어 친절 문장형 로컬라이제이션 스킬.
  codex_event 테이블의 title_updated_ko / content_updated_ko를
  비개발자가 읽기 쉬운 설명형 문장(~해요/~됐어요/~있어요 체)으로 변환한다.
  Use when: (1) codex_event의 title_updated_ko가 키워드 나열형이라 문장형으로 바꿔야 할 때,
  (2) 새 codex_event 레코드에 한국어 제목/본문을 추가할 때,
  (3) "한국어화", "ko enrichment", "title_updated_ko", "Korean localization" 키워드가 등장할 때.
  Note: 이 스킬은 codex_event 테이블 전용. ChatGPT 이벤트는 chatgpt-ko-enricher 스킬을 사용할 것.
---

# Ko-Enricher: Codex 이벤트 한국어 친절 문장형 변환

> **대상 테이블**: `codex_event` 전용 (ChatGPT 이벤트는 `chatgpt-ko-enricher` 스킬 사용)

`codex_event` 테이블의 `title_updated_ko`와 `content_updated_ko`를
비개발자 대상 설명형 한국어 문장으로 작성/갱신하는 워크플로.

## 스타일 규칙

See [references/style-guide.md](references/style-guide.md) for full specification.

Quick summary:
- 키워드 나열 금지 → **설명형 문장** (~해요/~됐어요/~있어요 체)
- 각 변경의 **사용자 관점 영향**을 한 문장으로 전달
- 고유명사(GPT-5.3-Codex, MCP 등)는 영어 유지
- `title_updated_ko`: 40자 내외
- `content_updated_ko`: 3문장, ~습니다 체

## 워크플로

### 1. 대상 파악

```bash
sqlite3 data/tracker.db "SELECT id, title_updated, title_updated_ko FROM codex_event WHERE title_updated_ko IS NULL OR title_updated_ko LIKE '%및%' ORDER BY date DESC;"
```

- `IS NULL` → 신규 레코드
- 키워드 나열 패턴(A, B 및 C) → 문장형 교체 대상

### 2. 스크립트 수정

`scripts/enrich_codex_ko.py`의 `RECORDS` 리스트에서:
- **신규**: 튜플 `(id, title_updated_ko, content_updated_ko)` 추가
- **교체**: 기존 `title_updated_ko` 값을 문장형으로 변경
- `content_updated_ko`는 변경 불필요 시 기존 값 유지

### 3. 실행

```bash
python scripts/enrich_codex_ko.py
```

### 4. 검증

```bash
sqlite3 data/tracker.db "SELECT COUNT(*) FROM codex_event WHERE title_updated_ko IS NOT NULL;"
sqlite3 data/tracker.db "SELECT title_updated_ko FROM codex_event WHERE title_updated_ko IS NOT NULL LIMIT 5;"
sqlite3 data/tracker.db "SELECT COUNT(*) FROM codex_event WHERE content_updated_ko IS NOT NULL;"
```

### 5. 품질 체크리스트

- [ ] 모든 title_updated_ko NOT NULL
- [ ] 키워드 나열형(A, B 및 C) 패턴 없음
- [ ] ~해요/~됐어요/~있어요 어미 사용
- [ ] 고유명사 영어 유지
- [ ] content_updated_ko 기존 값 변경 없음

## 변환 예시

| Before (키워드 나열) | After (문장형) |
|---|---|
| 브랜치 검색, 플랜 모드 안내 및 병렬 승인 | 브랜치를 검색으로 빠르게 찾고, 계획 모드 안내가 더 친절해졌어요 |
| 고급 에이전트 코딩 모델 출시 | 실전 개발에 특화된 GPT-5.2-Codex 모델이 새로 나왔어요 |
| 대시보드 일관성 및 결제 오류 해결 | 사용량 대시보드가 통일되고, 크레딧 구매 오류가 해결됐어요 |
| 4배 더 많은 사용량의 경제적 모델 | 4배 더 쓸 수 있는 저렴한 GPT-5-Codex-Mini가 나왔어요 |
| 초고급 추론 에이전트 코딩 모델 | 더 깊이 생각하는 GPT-5.1-Codex-Max 모델이 나왔어요 |
