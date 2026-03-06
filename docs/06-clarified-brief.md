# Clarified Brief

## 요약

ChatGPT, Gemini, Codex, Claude Code 4개 AI 제품의 공식 Release Notes/Changelog를 매일 수집·정규화하여, 2025-01-01부터 현재까지의 모든 변경사항을 하나의 세로 타임라인(선+점+카드) UI로 제공하는 공개 웹 트래커. 일반 사용자는 GPT/Gemini 중심으로, 개발자는 Claude Code/Codex 중심으로 "무엇이 바뀌었고 왜 중요한지"를 한 판에서 확인하여 FOMO를 해소한다. MVP는 LLM 없이 규칙 기반으로 동작하며, 로그인 없는 공개 페이지로 3일 내 데모 완성을 목표로 한다.

## 타깃 · 문제 · 핵심가치

- **타깃**: (A) AI 뉴스를 팔로잉하는 일반 사용자 (GPT/Gemini 관심) + (B) AI 도구를 쓰는 개발자 (Claude Code/Codex 관심)
- **문제**: 여러 AI 제품에서 신기능이 쏟아지는데, 소스가 분산되어 한 눈에 안 보이고 추적이 안 됨 → 함의 파악 불가 → FOMO 발생
- **핵심가치**: "4개 AI 제품의 변경사항을 시간순 한 판에서, 중요도와 함의까지 10초 안에 파악"

## MVP 범위 (우선순위 포함)

1. **타임라인 + 카드 렌더링** — 세로 선+점+카드 UI, 카드 접기/펼치기, Month Divider, Year 라벨
2. **Product·Tag 필터 + Year Jump** — Sticky Filter Bar (Product 토글 4개, Tag 필터), Jump 컨트롤 (2025/2026/Latest)
3. **백필 데이터 적재** — 4개 공식 소스에서 2025-01-01 이후 이벤트 파싱·적재 + 매일 증분 수집(해시 비교)

## Out of scope

- 사용자 계정 / 로그인 / 회원가입
- 댓글 / 커뮤니티 / 소셜 기능
- 실시간 푸시 알림 / 슬랙·이메일 노티
- LLM 기반 자동 요약 (v1.1 이후)
- 키워드 검색 (v1.1 이후)
- 관리자 검수 대시보드 (v1.1 이후)

## 데이터 모델 (엔티티 목록)

| 엔티티 | 주요 필드 | 비고 |
|--------|----------|------|
| **update_event** | id(uuid), product, component, event_date, detected_at, title, summary_ko, summary_en, tags(JSON), severity(int), source_url, evidence_excerpt(JSON), raw_ref(JSON) | 타임라인 카드 1:1 대응 |
| **source_snapshot** | id, source_id(chatgpt/gemini/codex/claude_code), fetched_at, content_hash, raw_content(TEXT), status(success/fail) | 증분 수집용 해시 비교 기준 |

## API 초안

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/events` | 이벤트 목록 조회 (query: product, tag, severity, year, offset, limit) |
| GET | `/api/events/{id}` | 이벤트 상세 (펼치기용 detail) |
| GET | `/api/products` | 제품 목록 + 각 제품별 이벤트 수 |
| GET | `/api/tags` | 태그 목록 + 각 태그별 이벤트 수 |
| POST | `/api/admin/collect` | 수동 수집 트리거 (관리자용, 인증 없이 단순 엔드포인트) |
| GET | `/api/admin/snapshots` | 최근 스냅샷 상태 확인 |

## LLM 사용 위치

- **사용 여부**: MVP에서는 사용하지 않음
- **용도**: 없음 (규칙 기반 Severity 점수 + 수동 태깅으로 대체)
- **허용 오류 수준**: N/A
- **v1.1 후보**: summary 자동 생성, 태그 자동 분류에 LangGraph 도입 검토

## 성공 기준 + 데모 정의

- **지표**:
  - 신뢰: 모든 카드에 source_url + evidence_excerpt가 존재
  - 재방문: 최신 이벤트를 10초 안에 확인 가능 (첫 로드 → 최신 카드까지)
  - 완결성: 4개 제품의 2025-01-01~현재 이벤트가 누락 없이 표시
- **데모 마감**: 3일 이내
- **데모 정의**: 4개 제품의 2025년 전체 이벤트가 타임라인에 렌더링되고, Product 필터·Tag 필터·카드 접기/펼치기가 동작하면 성공

## Open Questions (남은 불확실성)

1. 각 소스 페이지의 파싱 규칙이 변경될 경우 유지보수 전략은? (셀렉터/정규식 깨짐 대응)
2. 관리자 수집 트리거(`/api/admin/collect`)에 최소한의 인증(API key 등)을 넣을지, 완전 공개로 둘지
3. Railway 배포 시 SQLite 파일 영속성 확보 방안 (볼륨 마운트 또는 별도 DB 전환 시점)
4. Gemini/ChatGPT 등 동적 렌더링 페이지의 경우 headless browser가 필요한지, 정적 HTML 파싱으로 충분한지
5. 이벤트 수가 수백 개 이상일 때 무한 스크롤 vs 페이지네이션 vs 가상 스크롤 중 어떤 방식이 적합한지
