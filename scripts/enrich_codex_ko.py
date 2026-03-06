"""Codex event Korean enrichment: generate/apply/seed.

CLI:
  python -m scripts.enrich_codex_ko status
  python -m scripts.enrich_codex_ko generate [--limit N] [--force]
  python -m scripts.enrich_codex_ko apply <file.json>
  python -m scripts.enrich_codex_ko seed
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tracker.db"

# fmt: off
RECORDS: list[tuple[str, str, str]] = [
    # (id, title_updated_ko, content_updated_ko)
    (
        "05217f66-3397-4acb-9709-2e3d7859439a",
        "대화를 자동 압축하고, 속도 제한 알림과 통합 실행 환경이 추가됐어요",
        "비동기 대화 압축, 웹소켓 속도 제한 알림, 비Windows 플랫폼 통합 실행 기능이 추가되었습니다.\n"
        "메타데이터 일관성 개선, 설정 디버깅 강화, Esc 키 처리 및 대화 목록 표시가 수정되었습니다.\n"
        "도구 주입의 안정성과 경로 검증이 개선되었으며, 상태 데이터베이스가 버전별 파일로 전환되었습니다.",
    ),
    (
        "0922ad18-d2cf-4282-a710-f6237a9645ac",
        "GPT-5.3-Codex-Spark가 추가되고, 대화를 나눠서 진행할 수 있어요",
        "Codex 앱 26.212에 GPT-5.3-Codex-Spark 지원과 두 가지 새 대화 기능이 추가되었습니다.\n"
        "대화 분기 기능과 떠다니는 팝아웃 창으로 대화를 자유롭게 이동할 수 있습니다.\n"
        "Windows 버전 Codex 앱의 알파 테스트 신청이 시작되었습니다.",
    ),
    (
        "12afca3a-1b41-48fc-b773-2e8e36e071f0",
        "기존 프롬프트 대신 재사용 가능한 스킬 시스템이 도입됐어요",
        "Codex의 사용자 지정 프롬프트 기능이 중단되었습니다.\n"
        "재사용 가능한 명령과 워크플로를 위해 스킬 기능으로 전환해야 합니다.\n"
        "작업 자동화에 사용자 지정 프롬프트를 사용하던 모든 사용자에게 영향을 줍니다.",
    ),
    (
        "1cf4d4f2-72d8-4d55-92a2-e129ee56408c",
        "macOS에서 앱을 바로 열 수 있고, 나만의 스킬을 저장할 수 있어요",
        "macOS에서 CLI로 Codex 데스크톱 실행, 개인 스킬 불러오기, 원격 스킬 다운로드가 추가되었습니다.\n"
        "플랜 모드에 이미지 붙여넣기 지원, 셸 도구 병렬 실행, Linux 샌드박스가 개선되었습니다.\n"
        "Git 안전성 강화, 중단/재개/승인 관련 버그 수정, 프로토콜 전환이 완료되었습니다.",
    ),
    (
        "23043efc-d8cd-4ba1-b4ed-f5eb4917fa31",
        "GPT-5.3-Codex API가 단계적으로 개발자에게 열리기 시작해요",
        "GPT-5.3-Codex가 Cursor와 VS Code 편집기에서 바로 사용 가능해졌습니다.\n"
        "높은 보안 통제 하에 제한된 고객에게 API 접근이 단계적으로 제공됩니다.\n"
        "안전 조치가 확대됨에 따라 향후 몇 주 내에 전체 API 접근이 확장될 예정입니다.",
    ),
    (
        "232e86cc-1bc9-49eb-a5fd-ac4d1c04828d",
        "코드가 색상으로 구분되고, 음성 입력과 다중 작업 분배가 가능해졌어요",
        "코드 블록 구문 강조, 실시간 미리보기 테마 선택, 스페이스바 음성 입력 등 화면 개선이 이루어졌습니다.\n"
        "다중 에이전트 워크플로에 CSV 분배, 진행률 표시, 하위 에이전트 별명 기능이 추가되었습니다.\n"
        "링크 줄바꿈, 메시지 편집, 웹소켓 안정성, Linux 샌드박스 등 다수의 버그가 수정되었습니다.",
    ),
    (
        "236ffb68-0d43-494b-8c4f-08f75211195e",
        "실전 개발에 특화된 GPT-5.2-Codex 모델이 새로 나왔어요",
        "GPT-5.2-Codex가 복잡한 실전 소프트웨어 개발용 최고급 에이전트 코딩 모델로 출시되었습니다.\n"
        "장시간 작업을 위한 맥락 압축, 리팩토링 성능 강화, Windows 지원 개선, 보안 기능이 향상되었습니다.\n"
        "ChatGPT 유료 사용자의 CLI 및 IDE 확장에 기본 적용되며, API 접근은 곧 제공됩니다.",
    ),
    (
        "2435d64b-97fe-490c-945e-cc8ccbb30583",
        "대화 제목을 직접 바꿀 수 있고, 작업 전달 화면이 개선됐어요",
        "더블 클릭으로 대화 이름을 변경할 수 있게 되었으며, 인계 화면이 개선되었습니다.\n"
        "Sync 기능이 Handoff로 이름이 변경되고, 출발/도착 정보가 더 명확히 표시됩니다.\n"
        "사용성 개선과 함께 성능 향상 및 버그 수정이 포함되었습니다.",
    ),
    (
        "3369bf37-4065-4626-b299-6da3073acdae",
        "편집기 안에서 바로 Codex를 쓰고, 클라우드로 작업을 넘길 수 있어요",
        "Codex가 IDE 내에서 대화형 화면, 원클릭 인증, 웹으로의 원활한 작업 인계를 지원합니다.\n"
        "PR 의도 확인, 코드베이스 분석, 변경 사항 검증 실행, 모드 전환 기능이 포함됩니다.\n"
        "편집기를 떠나지 않고도 IDE에서 클라우드로 작업을 위임할 수 있습니다.",
    ),
    (
        "38468637-7604-4a65-91d7-9a076415fb75",
        "GPT-5-Codex를 API와 명령줄에서 직접 사용할 수 있어요",
        "GPT-5-Codex를 Responses API와 Codex CLI에서 API 키로 사용할 수 있게 되었습니다.\n"
        "모델은 정기적으로 업데이트되며 GPT-5와 동일한 가격으로 제공됩니다.\n"
        "개발자에게 Codex 최적화 모델에 대한 직접적인 API 접근을 제공합니다.",
    ),
    (
        "3ca01ea2-8b9a-424a-987f-0eff98eac569",
        "GPT-5.2-Codex를 API 키로도 사용할 수 있게 됐어요",
        "GPT-5.2-Codex를 API와 API 키 로그인 사용자도 이용할 수 있게 되었습니다.\n"
        "API를 통한 통합 및 사용 안내 문서가 제공됩니다.\n"
        "ChatGPT 인증 사용자 외에 직접 API 사용자에게도 접근이 확대되었습니다.",
    ),
    (
        "3ebbc680-8e5b-43c0-aba4-6584fa0873cf",
        "대기 메시지를 드래그로 정렬하고, 파일을 이름 일부로 찾을 수 있어요",
        "대기 중인 메시지를 드래그로 순서 변경할 수 있으며 모델 다운그레이드 경고가 추가되었습니다.\n"
        "유사 파일 검색과 재시작 후 첨부파일 복구가 개선되었습니다.\n"
        "전반적인 성능 향상 및 버그 수정이 포함되었습니다.",
    ),
    (
        "4179b99d-c5e6-4302-b6cb-d11f847a5bbd",
        "파일을 탐색기에서 바로 열 수 있고, 큰 변경 사항도 한눈에 봐요",
        "파일 참조 시 운영체제 파일 탐색기에서 바로 열 수 있는 기능이 추가되었습니다.\n"
        "리뷰 패널에서 전체 변경 크기 제한이 제거되어 대용량 리뷰 처리가 개선되었습니다.\n"
        "추가적인 성능 향상 및 버그 수정이 포함되었습니다.",
    ),
    (
        "43cf9499-387b-411f-8ae5-76c2ead416d0",
        "브랜치를 검색으로 빠르게 찾고, 계획 모드 안내가 더 친절해졌어요",
        "브랜치 선택기에 검색 기능과 병렬 승인 지원이 추가되었습니다.\n"
        "작성창에 'plan'을 입력하면 플랜 모드 진입 안내가 더 명확히 표시됩니다.\n"
        "추가적인 성능 향상 및 버그 수정이 포함되었습니다.",
    ),
    (
        "44ec4d65-a698-40d7-8e7d-cd4c8cd39112",
        "앱 정보가 더 풍부해지고, 커밋에 공동 저자가 자동 표기돼요",
        "앱 목록에 메타데이터, 브랜딩, 라벨이 추가되어 앱 카드가 더 풍부해졌습니다.\n"
        "커밋 시 공동 저자 표기가 Codex 관리 훅을 통해 자동으로 처리됩니다.\n"
        "일부 기능 플래그 제거 및 의존성 업데이트가 포함되었습니다.",
    ),
    (
        "46678dc2-bedc-4849-b4c9-fd8f92dfcb7d",
        "더 깊이 생각하는 GPT-5.1-Codex-Max 모델이 나왔어요",
        "GPT-5.1-Codex-Max가 강화된 추론 기반의 최신 에이전트 코딩 모델로 출시되었습니다.\n"
        "더 빠르고 지능적이며, 소프트웨어 공학·수학·연구 분야에 최적화된 초고급 추론 옵션이 추가되었습니다.\n"
        "ChatGPT 사용자의 CLI 및 IDE에 기본 적용되며, API 접근은 곧 제공됩니다.",
    ),
    (
        "6069260b-1421-45a7-8e0f-8051901d29dd",
        "세션 단위로 도구를 승인하고, 대화 기억 저장이 시작됐어요",
        "세션 범위 도구 승인, 실시간 스킬 파일 감지, 텍스트/이미지 혼합 출력이 추가되었습니다.\n"
        "디버그 설정 명령, 로그 경로 설정, 대화 메모리 요약 저장 기능이 도입되었습니다.\n"
        "화면 선택기 떨림 수정, 작업 상태 표시 복구, 클라우드 안정성이 개선되었습니다.",
    ),
    (
        "61d8ac60-20f8-44e6-9392-ee6cea54655d",
        "작업 중 인터넷을 쓸 수 있고, 음성 입력과 PR 수정이 가능해졌어요",
        "Codex가 작업 중 인터넷 접속, 후속 PR 업데이트, 음성 입력 기능을 갖추게 되었습니다.\n"
        "바이너리 파일 지원, 변경 이력 링크, iOS 수정, 다국어 지원, 오류 메시지 개선이 추가되었습니다.\n"
        "인터넷 접속은 Pro, Plus, Business 사용자가 선택 가능하며, 설정 시간이 10분으로 확장되었습니다.",
    ),
    (
        "62d8c7d1-7694-412a-8a68-8493cfc4ff22",
        "프록시 환경에서도 접속되고, 대화 보관 시 알림을 받아요",
        "웹소켓 프록시 환경 변수 지원과 대화 보관/복원 알림 기능이 추가되었습니다.\n"
        "셸 실행 흐름 내 명령 승인에 고유 ID가 부여되어 승인 추적이 명확해졌습니다.\n"
        "Ctrl+C/D 종료 처리, 잘못된 안전 검사 경고, 배포 안정성 관련 버그가 수정되었습니다.",
    ),
    (
        "6d63057d-cade-4fba-8939-1dd821a370f2",
        "가장 똑똑하고 25% 빨라진 GPT-5.3-Codex가 출시됐어요",
        "GPT-5.3-Codex가 GPT-5.2-Codex의 코딩 성능에 더 강한 추론과 전문 지식을 결합하여 출시되었습니다.\n"
        "Codex 사용자에게 25% 빠르며, 실시간 진행 상황 공유와 즉각적인 방향 조정이 가능합니다.\n"
        "Codex 앱, CLI, IDE, 클라우드에서 유료 ChatGPT 요금제로 사용 가능하며, API는 곧 제공됩니다.",
    ),
    (
        "6e47b5c5-31cc-4f20-a5af-a1ec197924e3",
        "자주 쓰는 명령을 스킬로 묶어 반복 사용할 수 있어요",
        "Codex에 에이전트 스킬이 도입되어, 명령·스크립트·리소스를 묶어 재사용할 수 있습니다.\n"
        "스킬은 이름으로 직접 호출하거나 Codex가 자동 선택하며, 사용자별 또는 프로젝트별 설치가 가능합니다.\n"
        "CLI와 IDE 확장 모두에서 사용 가능하며, 스킬 생성기와 설치기가 기본 제공됩니다.",
    ),
    (
        "6f4a7bf9-fa8b-4eb5-a5e2-37c5d66e0eb9",
        "요금제 한도를 넘어도 크레딧을 사서 계속 쓸 수 있어요",
        "ChatGPT Plus와 Pro 사용자가 요금제 한도 초과 시 추가 크레딧을 구매할 수 있습니다.\n"
        "요금제 업그레이드 없이도 한도를 초과하여 유연하게 사용할 수 있습니다.\n"
        "Plus 및 Pro 구독의 모든 Codex 사용에 적용됩니다.",
    ),
    (
        "6fcaac4a-95a3-4441-a6fc-ca3a742cabbe",
        "설치가 간편해지고, 메모리 관리가 더 스마트해졌어요",
        "macOS/Linux용 직접 설치 스크립트가 추가되고, 메모리가 차이 기반 삭제 방식으로 개선되었습니다.\n"
        "실시간 대화 엔드포인트, 5.3-codex 모델 표시, 기본 협업 모드에서 사용자 입력 요청이 활성화되었습니다.\n"
        "웹소켓 재시도, 대용량 입력 충돌, 하위 에이전트 중단 처리 등 다수의 버그가 수정되었습니다.",
    ),
    (
        "736f5d2c-3117-4702-a796-c873b6e9329a",
        "작업 중에도 명령어를 동시에 실행하고, 기업용 제한 설정이 추가됐어요",
        "활성 작업 중에도 셸 명령을 동시에 실행할 수 있으며, 상태 표시줄 설정이 추가되었습니다.\n"
        "기업용 네트워크/검색 제한, GIF/WebP 이미지 지원, 재개 정렬 전환이 추가되었습니다.\n"
        "Windows 시작, MCP 서버, 파일 감시, 패키지 배포 관련 다수의 버그가 수정되었습니다.",
    ),
    (
        "760b6f35-03dc-49cb-a840-421459d690b0",
        "대화를 여러 갈래로 나누고, 마이크와 스피커를 직접 고를 수 있어요",
        "대화를 하위 에이전트로 분기하고, 실시간 음성 세션에서 마이크/스피커를 선택할 수 있습니다.\n"
        "모델 가용성과 업그레이드 안내가 강화되었으며, 메모리 관리가 설정 가능해졌습니다.\n"
        "대화 재개 시 승인 복원, 중복 응답, Windows 색상, MCP 인증 관련 버그가 수정되었습니다.",
    ),
    (
        "7a2f2ab8-e025-45df-9666-a5c040af1f1f",
        "초당 1000개 이상 생성하는 초고속 코딩 모델이 나왔어요",
        "OpenAI가 Cerebras와 협력하여 만든 실시간 소형 코딩 모델 GPT-5.3-Codex-Spark를 출시했습니다.\n"
        "초당 1000개 이상의 토큰을 생성하며, 128k 맥락의 텍스트 전용으로 ChatGPT Pro에서 사용 가능합니다.\n"
        "연구 미리보기 단계이며, 출시 시 API 접근은 제공되지 않습니다.",
    ),
    (
        "7ef3c07f-8b56-45ca-a107-840806721c9b",
        "MCP 도구를 단축키로 빠르게 쓰고, 리뷰에서 @멘션이 가능해요",
        "작성창에 MCP 단축키와 인라인 리뷰 댓글에 @멘션 지원이 추가되었습니다.\n"
        "MCP 도구 호출 표시와 Mermaid 다이어그램 오류 처리가 개선되었습니다.\n"
        "중지된 터미널 명령이 계속 실행 중으로 표시되는 버그가 수정되었습니다.",
    ),
    (
        "8926b9e5-a5bb-4191-8834-5e612d5664a2",
        "Linear 이슈에서 @Codex를 태그하면 자동으로 작업이 시작돼요",
        "Codex가 Linear과 연동되어, 이슈에서 @Codex를 멘션하여 클라우드 작업을 시작할 수 있습니다.\n"
        "Codex가 Linear에 진행 상황을 업데이트하고 완료된 작업의 링크를 제공합니다.\n"
        "로컬 MCP 연결과 직접 Linear 연동을 모두 지원합니다.",
    ),
    (
        "8fe979ce-f9e7-4663-881e-7dba821dfaa0",
        "환경 설정이 훨씬 빨라지고, 주요 지연이 크게 줄었어요",
        "Codex 환경 설정 페이지가 더 빠르고 쉽게 개편되었습니다.\n"
        "재시도 버튼, 네트워크 표시기, Git 패치 복사, 유니코드 브랜치 지원이 추가되었습니다.\n"
        "GitHub 연결 끊김 90%, PR 생성 지연 35%, 도구 호출 지연 50%, 작업 완료 지연 20% 감소했습니다.",
    ),
    (
        "962ebd4b-3b32-4644-a831-bb8e7c4295c0",
        "모델 선택이 더 정확해지고, 메모리 처리가 안정화됐어요",
        "모델 선택 시 요청된 이름이 올바르게 유지되도록 수정되었습니다.\n"
        "메모리 처리 동시성을 줄여 높은 부하에서도 안정적으로 통합되도록 개선되었습니다.\n"
        "메모리 파이프라인 코드 정리 및 테스트 관련 소규모 개선이 포함되었습니다.",
    ),
    (
        "9e5c0dac-dca3-4892-b14c-221eb70b3230",
        "IDE와 클라우드 모두에서 쓸 수 있는 GPT-5-Codex가 나왔어요",
        "GPT-5-Codex는 에이전트 코딩에 최적화된 GPT-5 변형으로, IDE와 CLI에서 사용 가능합니다.\n"
        "클라우드 에이전트와 GitHub 코드 리뷰를 지원하며, 화면 캡처, 세션 재개, 맥락 압축이 추가되었습니다.\n"
        "Codex 웹, CLI, IDE, GitHub에 폭넓게 통합되어 전체 소프트웨어 개발 과정을 지원합니다.",
    ),
    (
        "aa1cd5a0-f4de-4568-aeca-96af1047197d",
        "명령 팔레트에서 MCP와 성격을 바로 바꾸고, 후속 요청이 순서대로 처리돼요",
        "명령 팔레트에 MCP와 성격 설정 바로가기가 추가되어 접근이 빨라졌습니다.\n"
        "후속 작업이 기본적으로 대기열에 추가되어 현재 작업을 중단하지 않습니다.\n"
        "추가적인 성능 향상 및 버그 수정이 포함되었습니다.",
    ),
    (
        "ad558f1f-a157-4484-86a4-a9a80c0354b5",
        "iPhone에서도 Codex로 작업하고 PR을 올릴 수 있어요",
        "ChatGPT iOS 앱에서 Codex를 사용하여 모바일로 에이전트 작업을 관리할 수 있습니다.\n"
        "iPhone에서 직접 작업 시작, 변경 사항 확인, 풀 리퀘스트 푸시가 가능합니다.\n"
        "데스크톱 없이도 모바일에서 Codex의 핵심 에이전트 워크플로를 사용할 수 있습니다.",
    ),
    (
        "b7c3e4eb-3133-4570-b6e7-8e3723294bd0",
        "하나의 질문에 여러 답변을 동시에 받아 최선을 고를 수 있어요",
        "하나의 작업에 대해 여러 응답을 동시에 생성하여 최적의 해결책을 찾을 수 있습니다.\n"
        "키보드 단축키, 브랜치 조회, 로딩 표시기, 작업 취소 기능이 추가되었습니다.\n"
        "네트워크 접근 처리, 설정 스크립트 제한, 코드 변경 확인 화면이 개선되었습니다.",
    ),
    (
        "babe8b06-913e-435f-8178-a799a76a6b3b",
        "Codex가 정식 출시되고, Slack·SDK·GitHub Action이 추가됐어요",
        "Codex가 정식 출시되며 Slack @Codex, Codex SDK, 관리 도구 세 가지가 추가되었습니다.\n"
        "Slack 작업 할당, 에이전트 내장용 TypeScript SDK, CI/CD용 GitHub Action이 제공됩니다.\n"
        "Plus, Pro, Business, Edu, Enterprise 요금제에서 사용 가능하며, 클라우드 과금은 10월 20일 시작됩니다.",
    ),
    (
        "bacded73-1fda-4474-813a-f024387c90ac",
        "파일 편집이 더 안정적이고, 위험한 작업이 줄었어요",
        "GPT-5-Codex의 소규모 업데이트로 코딩 상호작용의 신뢰성, 안전성, 효율성이 개선되었습니다.\n"
        "파일 편집의 안정성 향상, 위험한 Git 작업 감소, 사용자 편집 처리가 개선되었습니다.\n"
        "전체적으로 시간 및 사용 효율이 3% 향상되었습니다.",
    ),
    (
        "bb3090e0-7583-486a-b2ba-0af5137d5b87",
        "macOS 전용 데스크톱 앱이 출시돼 여러 작업을 동시에 돌려요",
        "macOS용 Codex 앱이 병렬 에이전트 작업을 지원하는 데스크톱 인터페이스로 출시되었습니다.\n"
        "프로젝트 사이드바, 작업트리 지원, 음성 입력, Git 도구, 스킬, 자동화가 주요 기능입니다.\n"
        "한시적으로 Free/Go 요금제에 Codex가 포함되며, Plus 이상은 모든 환경에서 2배 사용 한도를 받습니다.",
    ),
    (
        "c8b71de1-cd3e-4a69-86ac-802a048a9f76",
        "이미지를 첨부해서 지시하고, 시작 시간이 90% 단축됐어요",
        "Codex 웹에 이미지 첨부가 지원되며, 캐시로 시작 시간이 48초에서 5초로 90% 단축되었습니다.\n"
        "이미지를 프론트엔드 또는 화이트보드 작업에 활용할 수 있습니다.\n"
        "미설정 환경에서 자동 설치가 기본 적용되어 새 환경 테스트 실패가 40% 감소했습니다.",
    ),
    (
        "cb1e0a0d-fd78-4b77-9a78-2d052b6dffbd",
        "4배 더 쓸 수 있는 저렴한 GPT-5-Codex-Mini가 나왔어요",
        "GPT-5-Codex-Mini가 GPT-5-Codex보다 저렴하고 약 4배 더 많은 사용량을 제공합니다.\n"
        "5시간 사용 한도의 90%에 도달하면 CLI와 IDE가 자동으로 미니 모델 전환을 제안합니다.\n"
        "config.toml 또는 /model 명령으로 설정할 수 있습니다.",
    ),
    (
        "d1327fd4-394e-46c2-9551-f6864e23cca0",
        "GitHub PR이나 이슈에서 @codex를 태그하면 바로 작업이 시작돼요",
        "GitHub PR과 이슈에서 @codex를 멘션하여 작업을 할당하거나 질문할 수 있습니다.\n"
        "PR 대화에서 직접 추가 질문, 후속 요청, 코드 변경을 지원합니다.\n"
        "GitHub 이슈 지원으로 어떤 이슈에서든 화면 전환 없이 작업을 시작할 수 있습니다.",
    ),
    (
        "d62a88a4-89d1-4287-81c3-ee1c9a30cbeb",
        "권한 관리가 하나로 통합되고, 에이전트별 역할을 설정할 수 있어요",
        "통합 권한 흐름, 구조화된 네트워크 승인 처리, 설정 가능한 다중 에이전트 역할이 도입되었습니다.\n"
        "권한 이력 명확화, 유사 파일 검색, 모델 전환 알림 등이 주요 추가 사항입니다.\n"
        "원격 이미지, 접근성, 대화 재개, JS REPL 안정성 관련 버그가 수정되었습니다.",
    ),
    (
        "d93b36b5-76f1-46d0-a806-29f2d3d5dc76",
        "JavaScript를 바로 실행하고, 메모리를 명령으로 관리할 수 있어요",
        "실험적 JavaScript REPL, 다중 속도 제한 지원, 웹소켓 통신 재설계가 추가되었습니다.\n"
        "메모리 관리 명령(/m_update, /m_drop), ChatGPT 앱 SDK, Linux/Windows 샌드박스가 개선되었습니다.\n"
        "웹소켓 중복 출력, Windows 붙여넣기, 오래된 대화 항목 관련 버그가 수정되었습니다.",
    ),
    (
        "dc20b046-7a46-46ac-ab5c-40fa185985e3",
        "GPT-5.3-Codex가 나오고, 작업 중 방향 전환 기능이 안정화됐어요",
        "GPT-5.3-Codex 모델이 출시되고, 조종 모드가 Enter 키 즉시 전송으로 안정화되었습니다.\n"
        "TypeScript SDK 인수 순서, 대화 중 모델 변경 시 명령 처리, 토큰 계산 관련 버그가 수정되었습니다.\n"
        "기본 성격이 실용적 모드로 복원되고, 협업 모드 명칭이 전체적으로 통일되었습니다.",
    ),
    (
        "e19cd73a-0ae6-4993-a81b-b11513e1428f",
        "오래 걸리는 개발 작업에 최적화된 새 모델이 나왔어요",
        "에이전트 코딩에 최적화된 gpt-5.1-codex 및 gpt-5.1-codex-mini 모델이 출시되었습니다.\n"
        "CLI와 IDE 확장이 macOS/Linux에서는 gpt-5.1-codex, Windows에서는 gpt-5.1로 기본 설정됩니다.\n"
        "config.toml 또는 /model 명령으로 변경할 수 있습니다.",
    ),
    (
        "e82c778a-6b83-4ce8-abdd-2a72604d433f",
        "사용량 대시보드가 통일되고, 크레딧 구매 오류가 해결됐어요",
        "Codex 사용량 추적과 크레딧 구매 관련 여러 문제가 해결되었습니다.\n"
        "사용량 대시보드가 잔여 한도를 표준화하여 표시하며, iOS/Google Play 구매 차단이 수정되었습니다.\n"
        "백엔드가 최적화되어 하루 동안 사용량이 더 균등하게 분배됩니다.",
    ),
    (
        "e9825c91-2894-4633-9cc6-a1e8a34f1fac",
        "Zed와 Textmate 편집기가 추가되고, 리뷰에서 PDF를 바로 볼 수 있어요",
        "파일 열기 옵션에 Zed와 Textmate 편집기가 추가되었습니다.\n"
        "리뷰 패널에서 PDF를 직접 미리볼 수 있어 문서 확인이 편리해졌습니다.\n"
        "성능 향상 및 버그 수정에 중점을 둔 릴리스입니다.",
    ),
    (
        "eb2a697a-9d4c-40e3-b305-3d695de4fb21",
        "로컬 작업에서 웹 검색이 기본 제공되고, 실시간 모드도 선택 가능해요",
        "Codex CLI와 IDE 확장에서 로컬 작업 시 웹 검색이 기본 활성화되었습니다.\n"
        "OpenAI 인덱스 기반 캐시 모드가 기본이며, 실시간 모드는 --search 옵션으로 사용 가능합니다.\n"
        "web_search 설정으로 캐시, 실시간, 비활성화 중 선택할 수 있습니다.",
    ),
    (
        "fc6f278f-a760-46ae-b6ce-7642c602845d",
        "GPT-5.3-Codex가 추가되고, 작업 중간에 방향을 바꿀 수 있어요",
        "GPT-5.3-Codex 지원이 추가되고, 에이전트 작업 중 방향 조정이 가능해졌습니다.\n"
        "Codex가 작업 중일 때 메시지를 보내 실시간으로 동작을 변경할 수 있습니다.\n"
        "모든 파일 형식을 첨부하거나 드롭할 수 있으며, 앱 깜빡임 버그가 수정되었습니다.",
    ),
    (
        "ffc35933-b6c8-4229-ac6c-a3939c8200dc",
        "팀원끼리 Codex 설정과 스킬을 쉽게 공유할 수 있어요",
        "팀 설정으로 계층형 구성 시스템을 통해 팀과 저장소 간 Codex 설정을 공유할 수 있습니다.\n"
        "공유 설정 파일, 샌드박스 명령 규칙, 재사용 가능한 워크플로 스킬을 지원합니다.\n"
        "현재 폴더부터 시스템 경로까지 .codex/ 폴더를 탐색하며, 관리자가 제약 조건을 강제할 수 있습니다.",
    ),
]
# fmt: on


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def cmd_generate(args: argparse.Namespace) -> None:
    conn = _connect()
    where = "1=1" if args.force else "title_updated_ko IS NULL"
    sql = f"SELECT id, event_date, title, title_updated, content_updated FROM codex_event WHERE {where} ORDER BY event_date DESC"
    if args.limit > 0:
        sql += f" LIMIT {args.limit}"
    rows = [dict(r) for r in conn.execute(sql).fetchall()]
    conn.close()
    out = open(sys.stdout.fileno(), "w", encoding="utf-8", closefd=False)
    json.dump(rows, out, ensure_ascii=False, indent=2)
    out.flush()
    print(file=sys.stderr)
    print(f"[enrich_codex_ko] {len(rows)} row(s) pending", file=sys.stderr)


def cmd_apply(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"[error] file not found: {path}", file=sys.stderr)
        sys.exit(1)
    data: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    conn = _connect()
    updated = 0
    for item in data:
        rid = item.get("id")
        title_ko = item.get("title_updated_ko")
        content_ko = item.get("content_updated_ko")
        if not rid or not title_ko or not content_ko:
            print(f"[skip] incomplete: {rid}", file=sys.stderr)
            continue
        conn.execute(
            "UPDATE codex_event SET title_updated_ko = ?, content_updated_ko = ?, updated_at = datetime('now') WHERE id = ?",
            (title_ko, content_ko, rid),
        )
        updated += 1
    conn.commit()
    conn.close()
    print(f"[enrich_codex_ko] applied {updated}/{len(data)} row(s)")


def cmd_seed(_args: argparse.Namespace) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    for record_id, title_ko, content_ko in RECORDS:
        cur.execute(
            "UPDATE codex_event SET title_updated_ko = ?, content_updated_ko = ? WHERE id = ?",
            (title_ko, content_ko, record_id),
        )
    conn.commit()
    updated = cur.execute(
        "SELECT COUNT(*) FROM codex_event WHERE title_updated_ko IS NOT NULL"
    ).fetchone()[0]
    conn.close()
    print(f"[enrich_codex_ko] seed: {updated} records")


def cmd_status(_args: argparse.Namespace) -> None:
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM codex_event").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM codex_event WHERE title_updated_ko IS NOT NULL").fetchone()[0]
    conn.close()
    print(f"[enrich_codex_ko] total={total}  done={done}  pending={total - done}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Codex event Korean enrichment")
    sub = parser.add_subparsers(dest="command")

    p_gen = sub.add_parser("generate", help="Output pending rows as JSON")
    p_gen.add_argument("--limit", type=int, default=0)
    p_gen.add_argument("--force", action="store_true")

    p_apply = sub.add_parser("apply", help="Apply enrichment JSON to DB")
    p_apply.add_argument("file", help="Path to enrichment JSON file")

    sub.add_parser("seed", help="Apply hardcoded historical data")
    sub.add_parser("status", help="Show enrichment progress")

    args = parser.parse_args()
    cmd = args.command
    if cmd == "generate":
        cmd_generate(args)
    elif cmd == "apply":
        cmd_apply(args)
    elif cmd == "seed":
        cmd_seed(args)
    elif cmd == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
