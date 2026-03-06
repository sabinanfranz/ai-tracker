# Gemini 이벤트 한국어 Enrichment 절차서

## 개요

`gemini_event` 테이블의 영문 `title` + `content`를 기반으로 한국어 제목(`title_ko`)과 3줄 요약(`content_ko`)을 생성하여 DB에 저장한다. 외부 LLM API 호출 없이 Claude Code 세션에서 직접 수행.

## 작성 가이드라인

### title_ko (한국어 카드 제목) — 설명식 문장형
- **길이**: 20~50자
- **톤**: 사용자에게 말을 거는 친근한 안내·권유형
- **어미**: `~해보세요!` / `~됩니다!` / `~만나보세요!` 등 권유·안내형 어미 사용
- **내용**: 핵심 혜택을 사용자 관점의 문장으로 전달 (키워드 나열 금지)
- **예시**:
  - `"기록에 남지 않는 임시 채팅 기능을 활용해서 더 자유롭게 대화해보세요!"`
  - `"이제 Gemini가 코드를 더 정확하게 작성해줍니다!"`
  - `"Deep Research로 복잡한 주제도 깊이 있게 분석해보세요!"`

### content_ko (3줄 요약) — 설명식 친근체
- **형식**: 3줄, 각 줄 한 문장, `\n`으로 구분
- **톤**: 사용자 관점의 서술형 문장, 친근하고 이해하기 쉬운 표현
- **첫째 줄**: 이번에 어떤 변화가 생겼는지 쉽게 설명
- **둘째 줄**: 구체적으로 어떤 점이 좋아졌는지 안내
- **셋째 줄**: 사용자가 어떻게 활용하면 좋을지 권유

## 실행 절차

### 1. 진행 상황 확인

```bash
python -m scripts.enrich_gemini status
```

### 2. 대상 데이터 추출

```bash
# 전체 pending
python -m scripts.enrich_gemini generate > data/gemini_enrich_pending.json

# 3건만 미리보기
python -m scripts.enrich_gemini generate --limit 3
```

### 3. Claude Code 세션에서 enrichment 생성

Claude Code가 `data/gemini_enrich_pending.json`을 읽고, 각 row에 대해 `title_ko`와 `content_ko`를 생성하여 `data/gemini_enrich_result.json`에 저장.

결과 JSON 형식:
```json
[
  {
    "id": "row-uuid",
    "title_ko": "설명식 문장형 제목 (20~50자, ~해보세요!/~됩니다!)",
    "content_ko": "첫째 줄 요약.\n둘째 줄 요약.\n셋째 줄 요약."
  }
]
```

### 4. DB 반영

```bash
python -m scripts.enrich_gemini apply data/gemini_enrich_result.json
```

### 5. 검증

```bash
python -m scripts.enrich_gemini status
```

## 옵션 참조

| 옵션 | 설명 |
|------|------|
| `generate` | `title_ko IS NULL`인 row를 JSON 출력 |
| `generate --force` | 이미 enriched된 row 포함 |
| `generate --limit N` | 최대 N건만 출력 |
| `apply <file>` | JSON 파일을 읽어 DB UPDATE |
| `interactive` | stdin으로 한 건씩 처리 |
| `status` | 전체/완료/미완료 건수 출력 |
