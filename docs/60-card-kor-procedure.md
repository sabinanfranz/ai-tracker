# Claude Code 카드 한국어 번역 절차서

## 1. 개요

| 항목 | 내용 |
|------|------|
| 목적 | `claude_code_event` 테이블의 `card_yn=1` 레코드에 한국어 제목(`title_kor`)과 본문(`content_kor`)을 채운다 |
| 대상 테이블 | `claude_code_event` |
| 대상 조건 | `card_yn = 1` |
| 결과물 컬럼 | `title_kor`, `content_kor` |
| 스크립트 | `scripts/enrich_claude_code_kor.py` |

---

## 2. 번역 스타일 규칙

### title_kor

- **길이**: 30자 내외 (최대 40자)
- **어투**: `~해요` / `~됐어요` 체 (친근한 설명체)
- **관점**: 사용자 관점 (개발자가 아닌 사용자에게 말하듯)
- **고유명사**: 영어 그대로 유지 (Claude Code, MCP, VSCode 등)
- **change_type별 뉘앙스**:

| change_type | 어미 패턴 | 예시 |
|-------------|-----------|------|
| added | ~추가됐어요 | "MCP 서버 지원이 추가됐어요" |
| changed | ~변경됐어요 / ~개선됐어요 | "터미널 출력이 개선됐어요" |
| removed | ~제거됐어요 | "레거시 API가 제거됐어요" |
| deprecated | ~곧 사라져요 | "이전 설정 방식이 곧 사라져요" |
| other | ~됐어요 / ~돼요 | "새 버전이 출시됐어요" |

### content_kor

- **형식**: 불릿 3개, `•` 접두사, `\n` 구분
- **각 불릿**: 1~2문장, 기술 용어에 괄호 해설 추가
- **예시**:
  ```
  • MCP(Model Context Protocol) 서버와의 연결을 지원해요. 외부 도구를 쉽게 연동할 수 있어요.
  • 서버 설정은 JSON 파일로 관리하며, 여러 서버를 동시에 연결할 수 있어요.
  • 기존 도구와 충돌 없이 작동하도록 네임스페이스(namespace)가 자동 분리돼요.
  ```

---

## 3. 스크립트 구조

`scripts/enrich_claude_code_kor.py`는 **하드코딩 RECORDS 패턴**을 사용한다.

```python
RECORDS = [
    ("uuid-1", "title_kor 값", "• 불릿1\n• 불릿2\n• 불릿3"),
    ("uuid-2", "title_kor 값", "• 불릿1\n• 불릿2\n• 불릿3"),
    # ...
]

def main():
    conn = sqlite3.connect(DB_PATH)
    updated = 0
    for rec_id, title_kor, content_kor in RECORDS:
        cur = conn.execute(
            "UPDATE claude_code_event SET title_kor=?, content_kor=?, updated_at=datetime('now') WHERE id=?",
            (title_kor, content_kor, rec_id),
        )
        updated += cur.rowcount
    conn.commit()
    conn.close()
    print(f"Updated {updated}/{len(RECORDS)} records.")
```

### 왜 하드코딩인가?

- LLM 호출 비용 없이 반복 실행 가능
- 번역 품질을 사람이 직접 검수 가능
- 동일 결과 보장 (멱등성)

---

## 4. 실행 방법

```bash
# 프로젝트 루트에서 실행
PYTHONUTF8=1 python scripts/enrich_claude_code_kor.py
```

- Windows에서는 `PYTHONUTF8=1` 환경변수가 필요 (한글 출력 깨짐 방지)
- 멱등성 보장: 여러 번 실행해도 안전

---

## 5. 검증 쿼리

스크립트 실행 후 아래 4개 쿼리로 결과를 검증한다.

```sql
-- 1) card_yn=1인데 title_kor가 비어있는 레코드 (0이어야 정상)
SELECT COUNT(*) FROM claude_code_event
WHERE card_yn = 1 AND title_kor IS NULL;

-- 2) content_kor에 불릿이 3개 미만인 레코드 (0이어야 정상)
SELECT COUNT(*) FROM claude_code_event
WHERE card_yn = 1
  AND (LENGTH(content_kor) - LENGTH(REPLACE(content_kor, '•', ''))) < 3;

-- 3) card_yn=0인데 title_kor가 채워진 레코드 (0이어야 정상)
SELECT COUNT(*) FROM claude_code_event
WHERE card_yn = 0 AND title_kor IS NOT NULL;

-- 4) 샘플 확인
SELECT id, title, title_kor, content_kor
FROM claude_code_event
WHERE card_yn = 1
ORDER BY event_date DESC
LIMIT 5;
```

---

## 6. 신규 이벤트 추가 시 절차

새로운 Claude Code 릴리즈가 발생하면:

1. **크롤링**: `scripts/crawl_claude_code.py` 실행 → 새 레코드가 `claude_code_event`에 삽입됨
2. **카드 분류**: `card_yn` 값 설정 (중요 변경사항 = 1)
3. **번역 추가**: `scripts/enrich_claude_code_kor.py`에 새 RECORDS 튜플 추가
   ```python
   ("new-uuid", "새 기능이 추가됐어요", "• 불릿1\n• 불릿2\n• 불릿3"),
   ```
4. **실행**: `PYTHONUTF8=1 python scripts/enrich_claude_code_kor.py`
5. **검증**: 위 검증 쿼리 4개 실행

### 체크리스트

- [ ] title_kor 30자 이내
- [ ] content_kor 불릿 3개 (`•` 접두사)
- [ ] change_type에 맞는 어미 사용
- [ ] 고유명사 영어 유지
- [ ] 기술 용어에 괄호 해설 포함
