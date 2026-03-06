---
name: claude-code-ko-enricher
description: |
  Claude Code 이벤트 전용 한국어 카드 번역 스킬.
  claude_code_event 테이블의 card_yn=1 레코드에
  title_kor(~해요/~됐어요 체, 30자)와 content_kor(• 불릿 3개)를 채운다.
  Use when: (1) claude_code_event의 title_kor가 NULL인 card_yn=1 레코드가 있을 때,
  (2) 새 Claude Code 릴리즈 후 한국어 카드 번역이 필요할 때,
  (3) "클코 한국어", "claude code 한국어", "카드 번역", "title_kor", "content_kor" 키워드가 등장할 때.
  Note: 이 스킬은 claude_code_event 테이블 전용. Codex는 ko-enricher, ChatGPT는 chatgpt-ko-enricher 스킬 사용.
---

# Claude-Code-Ko-Enricher: Claude Code 카드 한국어 번역

> **대상 테이블**: `claude_code_event` 전용 (`card_yn = 1` 레코드만)

`claude_code_event` 테이블의 `title_kor`와 `content_kor`를
비개발자 대상 친근한 설명형 한국어 문장으로 작성/갱신하는 워크플로.

## 스타일 규칙

See [references/style-guide.md](references/style-guide.md) for full specification.

Quick summary:
- **title_kor**: 30자 내외, `~해요`/`~됐어요` 체, 사용자 관점
- **content_kor**: `•` 불릿 3개, `\n` 구분, 기술 용어에 괄호 해설
- 고유명사(Claude Code, MCP, VSCode 등)는 영어 유지
- change_type별 어미: added→추가됐어요, changed→개선됐어요, removed→제거됐어요, deprecated→곧 사라져요

## 워크플로

### 1. 대상 파악

```bash
sqlite3 data/tracker.db "SELECT id, title, change_type FROM claude_code_event WHERE card_yn=1 AND title_kor IS NULL ORDER BY event_date DESC;"
```

### 2. 스크립트 수정

`scripts/enrich_claude_code_kor.py`의 `RECORDS` 리스트에 튜플 추가:

```python
("uuid-here", "기능이 추가됐어요", "• 불릿1 설명.\n• 불릿2 설명.\n• 불릿3 설명."),
```

### 3. 실행

```bash
PYTHONUTF8=1 python scripts/enrich_claude_code_kor.py
```

### 4. 검증

```bash
PYTHONUTF8=1 python skills/claude-code-ko-enricher/scripts/validate.py
```

Or manually:

```sql
-- card_yn=1인데 title_kor 비어있는 레코드 (0이어야 정상)
SELECT COUNT(*) FROM claude_code_event WHERE card_yn=1 AND title_kor IS NULL;

-- content_kor 불릿 3개 미만 (0이어야 정상)
SELECT COUNT(*) FROM claude_code_event
WHERE card_yn=1 AND (LENGTH(content_kor) - LENGTH(REPLACE(content_kor, '•', ''))) < 3;

-- card_yn=0인데 title_kor 채워진 레코드 (0이어야 정상)
SELECT COUNT(*) FROM claude_code_event WHERE card_yn=0 AND title_kor IS NOT NULL;
```

### 5. 품질 체크리스트

- [ ] card_yn=1 전체 title_kor NOT NULL
- [ ] title_kor 30자 이내
- [ ] content_kor `•` 불릿 3개
- [ ] change_type에 맞는 어미 사용
- [ ] 고유명사 영어 유지
- [ ] 기술 용어에 괄호 해설 포함
- [ ] card_yn=0 레코드는 NULL 유지

## 변환 예시

| change_type | title (원문) | title_kor |
|---|---|---|
| added | Add MCP server support | MCP 서버 지원이 추가됐어요 |
| changed | Improve terminal rendering performance | 터미널 렌더링 성능이 개선됐어요 |
| removed | Remove legacy auth flow | 이전 인증 방식이 제거됐어요 |
| deprecated | Deprecate old config format | 이전 설정 형식이 곧 사라져요 |
| other | Release v1.0.30 | 새 버전 v1.0.30이 출시됐어요 |

| content_kor 예시 |
|---|
| • MCP(Model Context Protocol) 서버와의 연결을 지원해요. 외부 도구를 쉽게 연동할 수 있어요.\n• 서버 설정은 JSON 파일로 관리하며, 여러 서버를 동시에 연결할 수 있어요.\n• 기존 도구와 충돌 없이 작동하도록 네임스페이스(namespace)가 자동 분리돼요. |
