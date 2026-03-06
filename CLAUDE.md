# CLAUDE.md — CCOS MVP Template

## 목표

MVP 한 줄 아이디어에서 출발해 아래 사이클을 빠르게 반복한다:

> **MVP 한 줄 → 기획(PRD/백로그) → UX(플로우/와이어프레임) → 설계(API/DB/LLM) → 구현(Front/Back/LLM) → 테스트**

---

## 기술 스택 (고정)

| 레이어 | 기술 |
|--------|------|
| Frontend | HTML / CSS / JS (바닐라 또는 경량 라이브러리) |
| Backend | FastAPI (Python) |
| Database | SQLite |
| LLM Orchestration | LangGraph |

---

## 디렉토리 소유권 (충돌 방지)

동시 작업 시 아래 소유권을 지킨다. 자기 영역 밖 파일은 직접 수정하지 않고, 담당자에게 요청한다.

| 경로 | 담당 |
|------|------|
| `apps/api/**` | backend-dev |
| `apps/web/**` | frontend-dev |
| `apps/llm/**` | llm-engineer |
| `docs/**` | product-manager, ux-designer, coordinator |
| `tests/**` | 각 담당 + coordinator |
| `scripts/**` | coordinator |

---

## 작업 원칙

1. **작은 diff** — 한 번에 한 가지만 바꾼다.
2. **실행 · 테스트 후 커밋** — 깨지는 코드를 main에 넣지 않는다.
3. **시크릿 절대 출력 금지** — API 키·토큰은 `.env`에만 보관하고, 로그·커밋·출력에 노출하지 않는다.
4. **문서 먼저** — 코드를 작성하기 전에 해당 docs 파일을 업데이트한다.

---

## 산출물 규격

| 파일 | 내용 |
|------|------|
| `docs/00-brief.md` | MVP 원문, 제약조건, 가정 |
| `docs/10-prd.md` | 문제, 대상, 가치, 범위, 비범위, 성공기준, 리스크 |
| `docs/20-ux.md` | 사용자 플로우, 화면 목록, 텍스트 와이어프레임 |
| `docs/30-architecture.md` | API 계약, DB 스키마, LangGraph 설계 |
| `docs/40-backlog.md` | 유저스토리 + 우선순위 + 체크박스 + DoD |
| `docs/50-test-plan.md` | 수동 체크 10개 + 자동 테스트 제안 |
| `docs/90-log.md` | 결정사항, 트레이드오프, 다음 할 일 |
