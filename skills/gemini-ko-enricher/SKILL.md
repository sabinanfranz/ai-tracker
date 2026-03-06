---
name: gemini-ko-enricher
description: |
  Gemini 이벤트 전용 한국어 enrichment 스킬.
  gemini_event 테이블의 title_ko(20~50자, ~해보세요!/~됩니다! 체)와
  content_ko(3줄 설명식 친근체)를 채운다.
  Use when: "gemini 한국어", "gemini enrichment", "title_ko", "gemini-ko-enricher"
  Note: gemini_event 전용. Codex는 ko-enricher, Claude Code는 claude-code-ko-enricher 사용.
---

# Gemini-Ko-Enricher: Gemini 이벤트 한국어 Enrichment

> **대상 테이블**: `gemini_event` 전용 (Codex는 `ko-enricher`, Claude Code는 `claude-code-ko-enricher` 사용)

`gemini_event` 테이블의 `title_ko`와 `content_ko`를
비개발자 대상 친근한 안내·권유형 한국어 문장으로 작성/갱신하는 워크플로.

## 스타일 규칙

See [references/style-guide.md](references/style-guide.md) for full specification.

Quick summary:
- **title_ko**: 20~50자, `~해보세요!` / `~됩니다!` / `~만나보세요!` 체, 사용자 관점 권유·안내형
- **content_ko**: 3줄, `\n` 구분, 각 줄 한 문장, 친근한 서술형(~해요/~돼요 체)
  - 1줄: 어떤 변화가 생겼는지
  - 2줄: 구체적으로 어떤 점이 좋아졌는지
  - 3줄: 사용자가 어떻게 활용하면 좋을지
- 고유명사(Gemini, Deep Research, Google 등)는 영어 유지
- 키워드 나열 금지 → 설명형 문장

## 워크플로

### 1. 진행 상황 확인

```bash
python -m scripts.enrich_gemini status
```

### 2. 대상 데이터 추출

```bash
python -m scripts.enrich_gemini generate > data/gemini_enrich_pending.json
```

미리보기(3건):
```bash
python -m scripts.enrich_gemini generate --limit 3
```

### 3. Enrichment 생성

`data/gemini_enrich_pending.json`을 읽고, 각 row에 대해 `title_ko`와 `content_ko`를 생성하여 `data/gemini_enrich_result.json`에 저장.

결과 JSON 형식:
```json
[
  {
    "id": "row-uuid",
    "title_ko": "안내·권유형 제목 (20~50자, ~해보세요!/~됩니다!)",
    "content_ko": "첫째 줄: 변화 설명.\n둘째 줄: 이점 안내.\n셋째 줄: 활용 권유."
  }
]
```

### 4. DB 반영

```bash
python -m scripts.enrich_gemini apply data/gemini_enrich_result.json
```

### 5. 검증

```bash
python skills/gemini-ko-enricher/scripts/validate.py
```

## 변환 예시

| title (원문) | title_ko |
|---|---|
| Temporary chats that won't appear in history | 기록에 남지 않는 임시 채팅 기능을 활용해서 더 자유롭게 대화해보세요! |
| Improved code generation accuracy | 이제 Gemini가 코드를 더 정확하게 작성해줍니다! |
| Deep Research for complex topics | Deep Research로 복잡한 주제도 깊이 있게 분석해보세요! |
| Gems custom AI experts | 나만의 AI 전문가 Gems를 만들어서 맞춤형 도움을 받아보세요! |
| Google Maps integration in Gemini | Gemini에서 Google Maps를 바로 활용할 수 있게 됐습니다! |

| content_ko 예시 |
|---|
| 임시 채팅 기능이 새로 추가되어 대화 기록에 남지 않는 자유로운 대화가 가능해요.\n민감한 내용이나 간단한 질문을 부담 없이 나눌 수 있어서 편리해요.\n설정에서 임시 채팅 모드를 켜고 편하게 사용해보세요. |

## 품질 체크리스트

- [ ] title_ko IS NULL 레코드 0건
- [ ] title_ko 길이 20~50자 범위 내
- [ ] content_ko `\n` 구분 3줄
- [ ] 어미: ~해보세요!/~됩니다!/~만나보세요! (title_ko), ~해요/~돼요 (content_ko)
- [ ] 고유명사 영어 유지
- [ ] 키워드 나열 패턴 없음
