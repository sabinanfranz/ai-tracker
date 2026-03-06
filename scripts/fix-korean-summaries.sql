-- =============================================================
-- Fix Korean summaries: rewrite mixed EN/KO to natural Korean
-- Target: non-developer-friendly, clear descriptions
-- Skip: Gemini events (already well-translated)
-- =============================================================

BEGIN TRANSACTION;

-- ===================== Claude Code events =====================

UPDATE claude_code_event SET summary_ko = '코드 간소화(/simplify)와 일괄 처리(/batch) 명령어가 기본 포함되었습니다. 비용 확인 등 일부 명령어의 표시 오류가 수정되었습니다. 같은 저장소의 워크트리 간 프로젝트 설정과 자동 메모리가 공유됩니다.'
WHERE id = 'c5276fd0-a892-4566-9d1c-8881775bfa74';

UPDATE claude_code_event SET summary_ko = 'Claude가 유용한 정보를 자동으로 메모리에 저장합니다. 응답에서 코드 블록을 선택해 복사할 수 있는 /copy 명령어가 추가되었습니다. 복합 Bash 명령어의 자동 허용 제안이 더 정확해졌습니다.'
WHERE id = '1f6b3868-4b78-4455-9f69-09e1c591b063';

UPDATE claude_code_event SET summary_ko = 'MCP 서버 연결 시 OAuth 인증 성능이 개선되었습니다. --worktree(-w) 플래그로 독립된 작업 공간에서 Claude를 실행할 수 있습니다. 하위 에이전트도 격리된 워크트리에서 작업할 수 있습니다.'
WHERE id = '48bc1d7d-5c7e-4dd2-a8e0-6906d8ea5050';

UPDATE claude_code_event SET summary_ko = '파일 저장 시 마지막 빈 줄이 의도치 않게 삭제되던 문제가 수정되었습니다. Windows에서 줄 수가 항상 1로 표시되던 버그가 수정되었습니다. VS Code 플랜 미리보기가 자동 업데이트되고, 리뷰 준비 시에만 댓글을 달 수 있습니다.'
WHERE id = '4ecf1d61-2cad-47c6-ac85-c32a14100d91';

UPDATE claude_code_event SET summary_ko = 'Claude Sonnet 4.6 모델을 사용할 수 있습니다. 추가 디렉토리의 플러그인 설정 읽기가 지원됩니다. 스피너에 표시되는 팁 문구를 사용자가 직접 설정할 수 있습니다.'
WHERE id = '7262e3b5-075d-49cf-a6f2-ffbe1030c0f1';

UPDATE claude_code_event SET summary_ko = '앱 시작 속도가 개선되었습니다. 프롬프트 캐시 적중률이 높아져 응답이 빨라졌습니다. 적격 사용자에게 Opus 4.6 안내가 표시됩니다.'
WHERE id = '8a593078-3f62-4dcb-a9a8-f0806c80e223';

UPDATE claude_code_event SET summary_ko = 'Claude Code 안에서 또 다른 Claude Code를 실행하는 것을 방지합니다. Bedrock, Vertex, Foundry 사용자의 에이전트 팀 모델 식별자 오류가 수정되었습니다. 스트리밍 중 MCP 도구가 이미지를 반환할 때 발생하던 충돌이 수정되었습니다.'
WHERE id = '902ab057-6cef-4f58-8dc0-0a21ebd66e69';

UPDATE claude_code_event SET summary_ko = 'Opus 4.6에서 Fast 모드를 사용할 수 있습니다. 동일한 모델로 더 빠른 출력을 제공합니다.'
WHERE id = '559c91f1-db61-4a10-b212-f451b44a2775';

UPDATE claude_code_event SET summary_ko = 'tmux 에이전트 팀의 메시지 송수신 문제가 수정되었습니다. 현재 요금제에서 에이전트 팀을 사용할 수 없을 때 경고가 올바르게 표시됩니다. 멀티 에이전트 워크플로우용 TeammateIdle 및 TaskCompleted 훅 이벤트가 추가되었습니다.'
WHERE id = '6a443175-51d9-42e4-b140-58e1c27bfda0';

UPDATE claude_code_event SET summary_ko = 'Claude Opus 4.6 모델을 사용할 수 있습니다. 여러 에이전트가 협업하는 팀 기능이 실험 버전으로 추가되었습니다. Claude가 작업 중 자동으로 메모를 기록하고 활용합니다.'
WHERE id = 'eabb3c16-7a53-42d0-9041-3faeb06bfdc8';

UPDATE claude_code_event SET summary_ko = '종료 시 대화를 이어서 할 수 있는 방법이 안내됩니다. 일본어 IME의 전각 스페이스 입력이 체크박스 선택에서 지원됩니다. 대용량 PDF로 세션이 멈추는 문제가 수정되었습니다.'
WHERE id = 'ae2c770a-fe29-41c4-9523-b43b299c2db1';

UPDATE claude_code_event SET summary_ko = 'PDF에서 특정 페이지 범위만 읽을 수 있습니다(예: 1~5페이지). 10페이지 이상의 PDF는 페이지 지정이 필요합니다. Slack 등 OAuth 서버를 위한 사전 설정된 인증 정보가 추가되었습니다. /debug 명령어로 세션 문제를 진단할 수 있습니다.'
WHERE id = 'd14edc77-6f81-4865-9290-1b9fe29843c0';

UPDATE claude_code_event SET summary_ko = '도구 호출 실패와 거부 내역이 디버그 로그에 기록됩니다. 게이트웨이 사용자의 컨텍스트 관리 오류가 수정되었습니다. --from-pr 플래그로 특정 GitHub PR과 연결된 세션을 이어서 진행할 수 있습니다.'
WHERE id = '4ff7ae0f-5c11-4403-83a5-0ca2985b5218';

UPDATE claude_code_event SET summary_ko = '대기 중 표시되는 스피너 문구를 사용자가 변경할 수 있습니다. 기업 프록시 환경에서의 mTLS 연결 문제가 수정되었습니다. 공유 시스템에서 사용자별 임시 디렉토리가 분리되어 권한 충돌이 방지됩니다.'
WHERE id = '7268fe4d-1d47-43a8-8a1d-f799df77e947';

UPDATE claude_code_event SET summary_ko = '일본어 IME 전각 숫자 입력이 옵션 선택에서 지원됩니다. 셸 자동완성 캐시 파일이 종료 시 잘리던 문제가 수정되었습니다. 도구 실행 중 중단된 세션을 재개할 때 발생하던 API 오류가 수정되었습니다.'
WHERE id = 'b30c352e-5b43-48af-a0e2-b8e949a3cee4';

UPDATE claude_code_event SET summary_ko = 'Vim 모드에서 방향키로 명령어 기록을 탐색할 수 있습니다. 외부 편집기 단축키(Ctrl+G)가 도움말 메뉴에 표시됩니다. PR 리뷰 상태(승인, 변경 요청, 대기 중 등)가 프롬프트 하단에 색상으로 표시됩니다.'
WHERE id = 'ebf5a6e1-c269-4d38-bb94-67a842ee52df';

UPDATE claude_code_event SET summary_ko = 'CLAUDE_CODE_ENABLE_TASKS 환경변수로 작업 관리 기능을 끌 수 있습니다. 사용자 정의 명령어에서 $0, $1 등으로 개별 인자를 참조할 수 있습니다. AVX 미지원 프로세서에서 발생하던 충돌이 수정되었습니다.'
WHERE id = '2597a441-8927-497e-a90c-4712a3d37124';

UPDATE claude_code_event SET summary_ko = 'claude remote-control 명령어로 외부 빌드 환경에서 로컬 환경을 제공할 수 있습니다. 플러그인 마켓플레이스의 기본 Git 타임아웃이 30초에서 120초로 늘어났습니다. 사용자 정의 npm 레지스트리와 특정 버전 고정 설치가 지원됩니다.'
WHERE id = '65fbe12e-9a32-43a9-a00a-b63eba1ec302';

UPDATE claude_code_event SET summary_ko = '키보드 단축키를 사용자가 직접 설정할 수 있습니다. 컨텍스트별 키 바인딩과 연속 키 조합(코드)을 지원합니다. /keybindings 명령어로 설정합니다.'
WHERE id = 'f08ffb41-90a8-4723-abb8-db073aefbe5b';

UPDATE claude_code_event SET summary_ko = '의존성 추적이 가능한 새로운 작업 관리 시스템이 추가되었습니다. 하위 에이전트를 많이 사용한 세션 재개 시 메모리 부족 충돌이 수정되었습니다. /compact 실행 후 ''남은 컨텍스트'' 경고가 사라지지 않던 문제가 수정되었습니다.'
WHERE id = 'a45935ef-4aee-4573-8853-d6c5e2de218e';

UPDATE claude_code_event SET summary_ko = 'Bash 모드에서 명령어 기록 기반 자동완성이 추가되었습니다(! 입력 후 Tab). 설치된 플러그인 목록에서 검색 기능을 사용할 수 있습니다. 플러그인을 특정 Git 커밋에 고정하여 정확한 버전을 설치할 수 있습니다.'
WHERE id = 'bc83bc0f-0732-40e4-a054-41becc626a4b';

UPDATE claude_code_event SET summary_ko = '저장소 초기화 및 유지보수를 위한 Setup 훅 이벤트가 추가되었습니다(--init, --maintenance 플래그로 실행). 로그인 시 브라우저가 열리지 않을 때 ''c'' 키로 OAuth URL을 복사할 수 있습니다. heredoc에 JavaScript 템플릿이 포함된 Bash 명령어 충돌이 수정되었습니다.'
WHERE id = '4c9c8bf2-10e8-4849-9def-de4e08c0c717';

UPDATE claude_code_event SET summary_ko = 'MCP 도구 자동 활성화 임계값을 auto:N 형식으로 설정할 수 있습니다. 플랜 파일 저장 경로를 plansDirectory 설정으로 변경할 수 있습니다. 질문 입력 시 외부 편집기(Ctrl+G)를 사용할 수 있습니다.'
WHERE id = '4492aa75-016b-4463-9546-35d9043fe6a3';

UPDATE claude_code_event SET summary_ko = '작업 소요 시간 표시를 숨기는 설정이 추가되었습니다. 권한 요청 수락 시 피드백을 남길 수 있습니다. 에이전트 작업 완료 알림에 최종 응답이 바로 표시되어 전체 기록을 열지 않아도 결과를 확인할 수 있습니다.'
WHERE id = 'e7edd9d7-39b4-48e2-b51a-62fbd654e4e3';

UPDATE claude_code_event SET summary_ko = '/config 명령어에서 설정을 검색할 수 있습니다. /doctor에 자동 업데이트 채널과 사용 가능한 버전 정보가 표시됩니다. /stats에서 기간별 통계를 볼 수 있습니다(최근 7일, 30일, 전체).'
WHERE id = '86ea9f53-500d-48d0-86dc-96a7c5cd27fa';

UPDATE claude_code_event SET summary_ko = '슬래시 명령어와 스킬이 통합되어 사용법이 단순해졌습니다. /config에서 릴리스 채널(stable/latest)을 전환할 수 있습니다. 도달할 수 없는 권한 규칙을 감지하고 /doctor에서 경고를 표시합니다.'
WHERE id = '809f8304-581d-4749-a522-a9e6412968e0';

UPDATE claude_code_event SET summary_ko = '터미널에 드래그한 이미지의 원본 경로 정보가 포함됩니다. iTerm 등 지원 터미널에서 파일 경로를 클릭하면 해당 파일이 열립니다. Windows Package Manager(winget)를 통한 설치가 지원됩니다.'
WHERE id = '5fdac431-5714-4ce8-9870-2a472fb91143';

UPDATE claude_code_event SET summary_ko = '스킬 파일을 수정하면 재시작 없이 즉시 반영됩니다. 스킬과 슬래시 명령어를 분리된 하위 에이전트에서 실행할 수 있습니다(context: fork). 스킬에 에이전트 유형을 지정하여 실행할 수 있습니다.'
WHERE id = '7b0448a9-db70-4f6d-9492-de0e493692b8';

UPDATE claude_code_event SET summary_ko = '코드 정의로 이동, 참조 찾기, 문서 조회 등 언어 서버(LSP) 기능이 추가되었습니다. Kitty, Alacritty, Zed, Warp 터미널 설정이 지원됩니다. /theme에서 Ctrl+T로 구문 강조를 켜거나 끌 수 있습니다.'
WHERE id = 'e7a25274-3d8f-4caa-84a0-db6d813f5ac5';

UPDATE claude_code_event SET summary_ko = '첨부 이미지를 클릭하면 기본 뷰어에서 열립니다. Alt+Y로 이전에 복사한 텍스트 기록을 순환하며 붙여넣을 수 있습니다. 플러그인 탐색 화면에서 검색 필터링이 가능합니다.'
WHERE id = 'c942dd81-a1ce-4607-87a8-e05d9851125a';

UPDATE claude_code_event SET summary_ko = 'Chrome 확장 프로그램과 연동하여 브라우저를 직접 제어할 수 있는 ''Claude in Chrome'' 베타 기능이 추가되었습니다. 터미널 깜빡임이 줄었습니다. 모바일 앱 다운로드용 QR 코드가 추가되었습니다.'
WHERE id = 'f3f548d5-8de7-4207-8ba1-811a48f4b0d7';

UPDATE claude_code_event SET summary_ko = '/config에서 프롬프트 제안 기능을 켜거나 끌 수 있습니다. /settings가 /config의 별칭으로 추가되었습니다. 경로 중간에서 @ 파일 참조가 잘못 표시되던 문제가 수정되었습니다.'
WHERE id = 'eeaa46b2-8cab-431c-b181-db6997cd717e';

UPDATE claude_code_event SET summary_ko = 'Enter 키로 프롬프트 제안을 바로 제출할 수 있습니다(Tab은 편집용). MCP 도구 권한에 와일드카드(mcp__server__*)를 사용할 수 있습니다. 마켓플레이스별 자동 업데이트를 개별 설정할 수 있습니다.'
WHERE id = '5663f63f-cc97-42d6-85a1-077a9a29e2af';

UPDATE claude_code_event SET summary_ko = 'Opus 4.5에서 사고(Thinking) 모드가 기본 활성화됩니다. 설정은 /config에서 변경할 수 있습니다. /permissions 명령어에 검색 기능(/ 단축키)이 추가되었습니다.'
WHERE id = '3fa7e47a-4ce5-4129-873b-01e80d2a314e';

UPDATE claude_code_event SET summary_ko = '컨텍스트 자동 압축이 즉시 실행됩니다. 에이전트와 Bash 명령이 비동기로 실행되며 메인 에이전트에 메시지를 보낼 수 있습니다. /stats에서 선호 모델, 사용 그래프, 연속 사용 기록 등 통계를 확인할 수 있습니다.'
WHERE id = '53cc3f21-410e-4349-9377-6ea31e25cc26';

UPDATE claude_code_event SET summary_ko = '백그라운드에서 에이전트를 실행하며 동시에 작업할 수 있습니다. 모든 슬래시 명령어를 비활성화하는 --disable-slash-commands 플래그가 추가되었습니다. 커밋 메시지의 공동 작성자 표시에 모델명이 포함됩니다.'
WHERE id = 'afe34bad-63ae-4d4e-b5a1-61614ba4436a';

UPDATE claude_code_event SET summary_ko = 'Claude Opus 4.5 모델이 추가되었습니다. 데스크톱용 Claude Code가 출시되었습니다. Opus 4.5 출시에 맞춰 사용량 한도가 업데이트되었습니다.'
WHERE id = '906d99eb-28cc-40c9-b670-9bc6b675d324';

UPDATE claude_code_event SET summary_ko = 'MCP 도구의 중첩 참조 입력 스키마 호출 문제가 수정되었습니다. 업그레이드 중 발생하던 불필요한 오류 메시지가 제거되었습니다. 심층 사고(Ultrathink) 텍스트 표시가 개선되었습니다.'
WHERE id = 'e62ccbe6-ca5b-499b-9c6b-13c78aec7c2a';

UPDATE claude_code_event SET summary_ko = 'claude --teleport의 오류 메시지와 유효성 검사가 개선되었습니다. /usage의 오류 처리가 개선되었습니다. 종료 시 히스토리가 기록되지 않던 경합 조건이 수정되었습니다.'
WHERE id = '3cf6ee7b-f6fb-4d34-9926-966818cca043';

UPDATE claude_code_event SET summary_ko = '사용자 정의 에이전트에 권한 모드를 설정할 수 있습니다. 훅에 도구 호출 ID가 포함되어 추적이 용이해졌습니다. 하위 에이전트에 자동 로드할 스킬을 선언할 수 있습니다.'
WHERE id = 'e58ff913-2c28-4532-9a8c-b06e53beb3f0';

UPDATE claude_code_event SET summary_ko = '프롬프트 기반 정지 훅에 사용할 모델을 지정할 수 있습니다. 사용자 설정의 슬래시 명령어가 중복 로드되던 문제가 수정되었습니다. 사용자 설정과 프로젝트 설정의 라벨이 올바르게 구분됩니다.'
WHERE id = 'd01014a5-df0e-49b4-9d2b-ae7e1f9bd7c0';

UPDATE claude_code_event SET summary_ko = '알림의 유휴 상태 판정 방식이 수정되었습니다. Notification 훅 이벤트에 매처 값이 추가되었습니다. 출력 스타일에 keep-coding-instructions 옵션이 추가되었습니다.'
WHERE id = 'b0cea1ba-b299-4481-bbea-d831149e3e50';

UPDATE claude_code_event SET summary_ko = 'macOS에서 키체인이 잠겨 API 키 오류가 발생하면 해결 방법을 안내합니다. 샌드박스 수준에서 위험한 명령어 실행을 차단하는 설정이 추가되었습니다. 사용자 정의 에이전트에 특정 도구를 차단하는 기능이 추가되었습니다.'
WHERE id = '1cdc60c4-fe14-407f-8110-c2760d8c0575';

UPDATE claude_code_event SET summary_ko = '플랜 모드에 전용 하위 에이전트가 도입되었습니다. Claude가 하위 에이전트를 이어서 실행할 수 있습니다. 하위 에이전트의 모델을 동적으로 선택할 수 있습니다.'
WHERE id = '87ae222f-f506-40c6-8808-9acee8a0b7f6';

UPDATE claude_code_event SET summary_ko = '권한 요청 화면이 새롭게 디자인되었습니다. 세션 재개 화면에서 브랜치별 필터링과 검색이 가능합니다. 디렉토리 @멘션 시 발생하던 오류가 수정되었습니다.'
WHERE id = 'e4f4be3f-ee32-4680-b081-5f87c3c1a21e';

UPDATE claude_code_event SET summary_ko = '프로젝트 수준 스킬이 로드되지 않던 문제가 수정되었습니다. 웹에서 CLI로의 텔레포트 기능이 지원됩니다. Linux와 Mac에서 Bash 도구의 샌드박스 모드가 출시되었습니다.'
WHERE id = 'c1612f80-39d8-46e1-82e8-beae43e6c089';

UPDATE claude_code_event SET summary_ko = 'MCP 도구 응답의 구조화된 콘텐츠(structuredContent)가 지원됩니다. 대화형 질문 도구가 추가되었습니다. 플랜 모드에서 Claude가 사용자에게 더 자주 질문합니다.'
WHERE id = '62cd0666-a9b8-4f31-877c-68d21794b155';

UPDATE claude_code_event SET summary_ko = 'Haiku 4.5가 모델 선택 목록에 추가되었습니다. Haiku 4.5는 플랜 모드에서 자동으로 Sonnet을, 실행에는 Haiku를 사용합니다.'
WHERE id = 'd7ebc8ef-88ee-4fe7-9a8e-33d8e5610326';

UPDATE claude_code_event SET summary_ko = 'MCP 서버를 @멘션으로 켜고 끄는 기능이 수정되었습니다. 인라인 환경 변수가 포함된 Bash 명령의 권한 검사가 개선되었습니다. 심층 사고 모드 전환 문제가 수정되었습니다.'
WHERE id = '053e86d5-ae32-49a3-ad7c-c3ac5a57a3a6';

UPDATE claude_code_event SET summary_ko = '플러그인 시스템이 출시되었습니다. 마켓플레이스에서 명령어, 에이전트, 훅, MCP 서버를 설치하여 Claude Code를 확장할 수 있습니다. 팀 협업을 위한 저장소 수준 플러그인 설정이 지원됩니다.'
WHERE id = 'f70707ef-b054-431e-bc32-c7ace0db5d72';

UPDATE claude_code_event SET summary_ko = '터미널 렌더러가 재작성되어 UI가 부드러워졌습니다. @멘션 또는 /mcp에서 MCP 서버를 켜고 끌 수 있습니다. Bash 모드에서 셸 명령어 자동완성이 추가되었습니다.'
WHERE id = 'e3933f85-a756-462a-892c-d5c263f65599';

UPDATE claude_code_event SET summary_ko = 'Bedrock의 기본 Sonnet 모델이 업데이트되었습니다. IDE에서 파일과 폴더를 드래그 앤 드롭으로 채팅에 추가할 수 있습니다. 사고 블록의 컨텍스트 카운팅이 수정되었습니다.'
WHERE id = 'a3e42218-45ce-4bcf-807b-77120c0ad270';

UPDATE claude_code_event SET summary_ko = 'IDE에서 한국어/일본어 입력 시 Enter와 Tab으로 메시지가 의도치 않게 전송되던 문제가 수정되었습니다. 로그인 화면에 ''터미널에서 열기'' 링크가 추가되었습니다. OAuth 만료 시 발생하던 오류가 수정되었습니다.'
WHERE id = '7909e916-310f-4578-a993-92f9e2001131';

UPDATE claude_code_event SET summary_ko = 'VS Code 전용 네이티브 확장이 출시되었습니다. 전체 앱 디자인이 새롭게 변경되었습니다. /rewind로 대화를 되돌려 코드 변경을 취소할 수 있습니다.'
WHERE id = '33527ea3-dafd-4280-bc36-286c6b6bf7b8';

-- ===================== Codex events =====================

UPDATE codex_event SET summary_ko = '작성기에 MCP 서버 바로가기와 설치 키워드 제안이 추가되었습니다. 인라인 리뷰 댓글에서 @멘션과 스킬 멘션을 사용할 수 있습니다. MCP 도구 호출 표시와 Mermaid 다이어그램 오류 처리가 개선되었습니다.'
WHERE id = '36430011-50ce-439e-98eb-27267dc27bda';

UPDATE codex_event SET summary_ko = 'macOS와 Linux용 직접 설치 스크립트가 GitHub 릴리스에 추가되었습니다. 앱 서버 v2에 실시간 스레드 엔드포인트가 실험적으로 추가되었습니다. js_repl이 실험 기능으로 승격되었으며 최소 Node 버전이 22.22.0으로 낮아졌습니다.'
WHERE id = '38b658da-88d6-46d9-9c2a-9fbfbade8380';

UPDATE codex_event SET summary_ko = 'TUI에서 코드 블록과 diff에 구문 강조가 적용됩니다. /theme 선택기로 실시간 미리보기가 가능합니다. 스페이스바를 길게 눌러 음성으로 프롬프트를 입력할 수 있습니다(개발 중). CSV 기반 다중 에이전트 워크플로우를 진행률과 함께 실행할 수 있습니다.'
WHERE id = '648f6049-b6b3-4e6d-a68c-6631bccf2b80';

UPDATE codex_event SET summary_ko = '웹소켓 프록시(WS_PROXY/WSS_PROXY) 환경변수가 지원됩니다. 스레드 보관/해제 시 앱 서버가 알림을 전송하여 폴링 없이 반응할 수 있습니다. 셸 명령어 승인에 고유 ID가 부여되어 여러 승인을 구분할 수 있습니다.'
WHERE id = 'e935441a-d7d4-4300-8ab5-79cd33e64d38';

UPDATE codex_event SET summary_ko = '대기 중인 메시지를 드래그 앤 드롭으로 순서를 바꿀 수 있습니다. 선택한 모델이 하위 모델로 변경될 때 경고가 표시됩니다. 퍼지 파일 검색과 재시작 후 첨부 파일 복구가 개선되었습니다.'
WHERE id = 'c230ec56-a428-4870-947c-07a426e3679b';

UPDATE codex_event SET summary_ko = '앱 목록에 메타데이터, 브랜딩, 라벨 등 더 풍부한 정보가 포함됩니다. 커밋 공동 작성자 표시가 Codex 관리 훅 방식으로 변경되었습니다. remote_models 기능 플래그가 제거되어 모델 선택 안정성이 향상되었습니다.'
WHERE id = '409ba026-ea69-4c4d-91d7-1e1bf3cb38a2';

UPDATE codex_event SET summary_ko = '권한 관리가 통합되어 TUI에서 권한 내역을 더 명확하게 확인할 수 있습니다. 네트워크 승인 시 호스트/프로토콜 정보가 자세히 표시됩니다. 다중 에이전트 역할을 설정으로 사용자화할 수 있습니다.'
WHERE id = 'eb486ccc-46a3-45bd-9f3e-e482fece65cc';

UPDATE codex_event SET summary_ko = 'GPT-5.3-Codex-Spark 모델이 지원됩니다. 대화 분기(forking) 기능이 추가되었습니다. 대화를 별도 창으로 분리하는 팝아웃 기능이 추가되었습니다.'
WHERE id = '27916b9e-9be8-419f-881c-1fd030f99821';

UPDATE codex_event SET summary_ko = 'GPT-5.3-Codex-Spark 모델이 출시되었습니다. CLI에서 codex --model gpt-5.3-codex-spark으로, IDE와 앱에서는 모델 선택기에서 선택하여 사용할 수 있습니다.'
WHERE id = '8b221bac-d82c-4fc4-acbd-4c78ad3dbb8d';

UPDATE codex_event SET summary_ko = '모델 선택 시 요청한 모델명이 그대로 유지되어 안정적입니다. 메모리 입력에서 개발자 메시지가 제외되어 불필요한 내용이 줄었습니다. 메모리 처리의 동시 실행이 줄어 안정성이 향상되었습니다.'
WHERE id = '7199f262-a3f7-45a6-aef4-606c70fe6ce1';

UPDATE codex_event SET summary_ko = '상태를 유지하는 실험적 JavaScript REPL 런타임이 추가되었습니다. 여러 사용량 제한을 동시에 표시할 수 있습니다. 앱 서버에 웹소켓 전송이 재도입되었습니다.'
WHERE id = '5ccf2909-885b-44cf-b0b8-3bc92715443f';

UPDATE codex_event SET summary_ko = '작업 중에도 셸 명령어를 동시에 실행할 수 있습니다. /statusline으로 TUI 하단에 표시할 정보를 대화형으로 설정할 수 있습니다. 세션 재개 선택기에서 정렬 순서를 변경할 수 있습니다.'
WHERE id = '390c6b6e-8faa-482a-920d-d9f5785485d2';

UPDATE codex_event SET summary_ko = '브랜치 선택기에서 검색 기능이 추가되었습니다. 작성기에 ''plan''을 입력하면 플랜 모드 진입 안내가 표시됩니다. 병렬 승인이 지원됩니다.'
WHERE id = 'eee02094-5f65-4249-8521-2fc093bed347';

UPDATE codex_event SET summary_ko = 'Cursor와 VS Code에서 GPT-5.3-Codex 모델을 사용할 수 있습니다.'
WHERE id = '44ed30e1-cc9c-4077-9382-fd653f56ba71';

UPDATE codex_event SET summary_ko = '명령 팔레트에 MCP와 성격 설정 액션이 추가되었습니다. 후속 메시지가 기본적으로 큐에 대기됩니다. 성능 개선 및 버그 수정이 포함되었습니다.'
WHERE id = '1d5fcfe1-0e78-4c29-9f1d-ec3e2daa084a';

UPDATE codex_event SET summary_ko = '파일 참조에서 OS 파일 관리자로 바로 열 수 있는 기능이 추가되었습니다. 대용량 리뷰의 diff 크기 제한이 제거되어 큰 변경사항도 볼 수 있습니다.'
WHERE id = '9041edf7-cde6-4527-b303-ffad54b88197';

UPDATE codex_event SET summary_ko = 'GPT-5.3-Codex 모델이 지원됩니다. 작업 중에 메시지를 보내 Codex의 방향을 조정할 수 있습니다(미드턴 스티어링). 모든 파일 유형을 첨부하거나 드롭할 수 있습니다.'
WHERE id = 'a3b5a0c5-47df-4eef-a843-8c22e8b9cd93';

UPDATE codex_event SET summary_ko = 'GPT-5.3-Codex 모델이 출시되었습니다. CLI, IDE 확장, Codex 앱의 모델 선택기에서 사용할 수 있습니다.'
WHERE id = 'b5219536-97b7-48e2-b10a-c5c913b72d85';

UPDATE codex_event SET summary_ko = 'GPT-5.3-Codex 모델이 도입되었습니다. 스티어 모드가 안정화되어 기본 활성화됩니다(Enter로 즉시 전송, Tab으로 큐에 추가). TypeScript SDK의 세션 재개 시 이미지 관련 오류가 수정되었습니다.'
WHERE id = 'd494b446-c43d-4d7f-a085-a9fe9dac6b30';

UPDATE codex_event SET summary_ko = 'MCP/앱 도구 승인에 세션 내 ''허용하고 기억'' 옵션이 추가되어 같은 도구를 반복 승인하지 않아도 됩니다. 스킬 파일 변경이 재시작 없이 감지됩니다. 앱 서버에서 텍스트와 이미지가 혼합된 도구 출력이 지원됩니다.'
WHERE id = '75e4702c-01db-4f39-bf46-dcb9b4d69776';

UPDATE codex_event SET summary_ko = 'Zed와 TextMate로 파일과 폴더를 여는 옵션이 추가되었습니다. 리뷰 패널에서 PDF 미리보기가 가능합니다. 성능이 개선되었습니다.'
WHERE id = 'f28ad913-54e4-46b6-a300-b02d96dd39cd';

UPDATE codex_event SET summary_ko = '앱 서버 API에 스레드 압축(compact) 기능이 추가되어 클라이언트에서 즉시 시작할 수 있습니다. 웹소켓을 통한 사용량 제한 알림이 추가되었습니다. Windows를 제외한 모든 플랫폼에서 통합 실행(unified_exec)이 활성화되었습니다.'
WHERE id = '0abbfa00-1fdb-4ad3-89fe-828b625e4176';

UPDATE codex_event SET summary_ko = 'macOS에서 codex app 명령으로 데스크톱 앱을 실행할 수 있습니다(미설치 시 자동 다운로드). 개인 스킬 폴더(~/.agents/skills)에서 스킬을 로드할 수 있습니다. /plan에 인라인 프롬프트와 이미지 붙여넣기가 지원됩니다.'
WHERE id = 'cba008b8-5073-4e47-a70a-14f0fb87bd10';

UPDATE codex_event SET summary_ko = '스레드 목록에서 더블클릭으로 이름을 변경할 수 있습니다. Sync이 Handoff로 이름이 바뀌고 전송 통계가 더 명확해졌습니다. 성능 개선 및 버그 수정이 포함되었습니다.'
WHERE id = '5e6809cb-5d5e-4863-93dd-560de7418dbf';

UPDATE codex_event SET summary_ko = 'Codex 데스크톱 앱이 출시되었습니다. 여러 프로젝트를 동시에 작업할 수 있으며, 워크트리 지원과 음성 입력 기능을 제공합니다.'
WHERE id = '41b3e9e0-a8ab-47cd-8dcd-8a024aad088f';

UPDATE codex_event SET summary_ko = 'Codex에서 웹 검색이 기본 활성화되었습니다. 캐시된 결과(기본값), 실시간 검색, 비활성화 중 선택할 수 있습니다.'
WHERE id = 'c4279ad3-85d5-4348-8eb7-d4d558472c5c';

UPDATE codex_event SET summary_ko = '팀 전체가 공유하는 설정을 config.toml, 명령어 규칙(rules/), 재사용 가능한 워크플로우(skills/)로 관리할 수 있습니다.'
WHERE id = '6c2ae295-36a6-4e80-901a-b9ee4b49c512';

UPDATE codex_event SET summary_ko = '커스텀 프롬프트 기능이 더 이상 지원되지 않습니다(Deprecated).'
WHERE id = '9dde83d5-82d6-4b58-a42a-c3a7f26a1431';

UPDATE codex_event SET summary_ko = 'GPT-5.2-Codex 모델을 API에서 사용할 수 있습니다.'
WHERE id = 'a3d80dd5-ac69-4ea4-9350-eaf95f938d74';

UPDATE codex_event SET summary_ko = 'GPT-5.2-Codex 모델이 출시되었습니다.'
WHERE id = '2a02a9fa-e1f5-4256-9f10-034bfaf80e7a';

UPDATE codex_event SET summary_ko = 'Codex에서 에이전트 스킬 기능을 사용할 수 있습니다. 재사용 가능한 워크플로우를 정의하고 에이전트에 적용할 수 있습니다.'
WHERE id = '1b48d06f-f595-43a7-b8b0-f69ef2f82975';

UPDATE codex_event SET summary_ko = 'GPT-5.1-Codex-Max 모델이 출시되었습니다. 최대 성능의 코딩 전용 모델입니다.'
WHERE id = '972212fb-6fb9-40a8-b006-5ea764b967be';

UPDATE codex_event SET summary_ko = 'GPT-5.1-Codex와 GPT-5.1-Codex-Mini 모델이 출시되었습니다.'
WHERE id = '97836092-61aa-4264-b10a-5e31374a6889';

UPDATE codex_event SET summary_ko = 'GPT-5-Codex-Mini 모델이 출시되었습니다. 경량화된 코딩 전용 모델입니다.'
WHERE id = 'd1562e7d-5af7-4a84-8f6b-bdf99377c3bb';

UPDATE codex_event SET summary_ko = 'GPT-5-Codex 모델이 업데이트되었습니다. 파일 편집 안정성이 향상되고, git reset 같은 위험한 작업이 줄었으며, 사용자 편집을 더 잘 반영합니다.'
WHERE id = '4c4f9d93-4dc5-4a03-a9f2-f9f17cacb5b2';

UPDATE codex_event SET summary_ko = 'ChatGPT Pro와 Plus 요금제에 크레딧 시스템이 적용되었습니다.'
WHERE id = '8d9eebdd-9a93-475a-b436-c9a609ef2774';

UPDATE codex_event SET summary_ko = 'GitHub 이슈와 PR에서 @Codex를 태그하여 Codex에 작업을 요청할 수 있습니다.'
WHERE id = 'e3379500-6ac9-4fc8-b23c-8a836d55d5e5';

UPDATE codex_event SET summary_ko = 'Codex가 정식 출시(GA)되었습니다. 누구나 사용할 수 있습니다.'
WHERE id = '92fc5268-31d3-4e87-8ab1-cb9405539e6c';

UPDATE codex_event SET summary_ko = 'GPT-5-Codex 모델을 API에서 사용할 수 있습니다.'
WHERE id = '23b78f11-54be-4510-a395-6b7b1fd030b7';

UPDATE codex_event SET summary_ko = 'GPT-5-Codex 모델이 출시되었습니다. codex resume으로 이전 세션을 이어서 할 수 있습니다. 컨텍스트 한도에 도달하면 자동으로 요약됩니다.'
WHERE id = '1d032f1d-8f96-4a72-8dcb-ad748c0813d8';

UPDATE codex_event SET summary_ko = '8월 말 정기 업데이트입니다.'
WHERE id = '81d20013-ccf8-419e-9d09-0b449f5b460d';

UPDATE codex_event SET summary_ko = '8월 중순 정기 업데이트입니다.'
WHERE id = 'f4f85c3a-ea91-4113-a683-46dcf4a58555';

UPDATE codex_event SET summary_ko = '키보드 단축키 목록 페이지가 추가되었습니다(macOS: ⌘-/, 기타: Ctrl+/). 브랜치 쿼리 파라미터가 지원됩니다. 컨테이너 설정 중 로딩 표시가 추가되었습니다.'
WHERE id = 'a356eba2-82e3-4945-91aa-ae75d4e8a4be';

UPDATE codex_event SET summary_ko = '실패한 작업을 재시도하는 버튼이 추가되었습니다. 설정 후 네트워크 없이 에이전트가 실행됨을 알리는 표시가 추가되었습니다. PR 푸시 후 Git 패치를 복사하는 옵션이 추가되었습니다.'
WHERE id = '8c1bf2fc-7cf1-43a8-88ce-eaa01b047e96';

UPDATE codex_event SET summary_ko = 'ChatGPT iOS 앱에서 Codex를 사용할 수 있습니다.'
WHERE id = 'd229467c-e14f-4fc4-a638-cd6712ba3b6e';

UPDATE codex_event SET summary_ko = '프로필 메뉴에서 변경 로그 링크가 추가되었습니다. 바이너리 파일의 패치 적용이 지원됩니다. iOS에서 후속 작업이 중복 표시되던 문제가 수정되었습니다.'
WHERE id = '4fbb8129-f913-4bd7-9bd0-839b0477a4ba';

UPDATE codex_event SET summary_ko = '모든 사용량 대시보드가 ''남은 한도'' 표시로 통일되었습니다. iOS/Google Play 구독자가 크레딧을 구매할 수 없던 문제가 수정되었습니다. CLI에서 최신 사용량 정보가 자동으로 갱신됩니다.'
WHERE id = '730d3c43-14f3-425e-87ee-0a002db7cd70';

UPDATE codex_event SET summary_ko = 'Codex for Linear가 출시되었습니다. Linear 이슈에서 Codex를 사용하여 작업을 자동화할 수 있습니다.'
WHERE id = '2e125f95-dac5-41c2-bc5d-5c9b942145dd';

COMMIT;
