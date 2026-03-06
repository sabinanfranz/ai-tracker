#!/usr/bin/env python3
"""Fix validation errors in chatgpt_enrich_ko_result.json."""
import json, sys

with open("data/chatgpt_enrich_ko_result.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Build lookup by id prefix (8 chars)
by_id = {}
for item in data:
    by_id[item["id"][:8]] = item

fixes = {
    "c44e1a5a": {
        "title_updated_ko": "ChatGPT에서 코드 블록을 쉽게 복사할 수 있어요",
        "content_updated_ko": "코드 블록에 복사 버튼이 추가되어 원클릭 복사가 가능합니다.\n대화 중 생성된 코드를 빠르게 클립보드에 저장할 수 있습니다.\n개발자와 학습자 모두의 코드 활용 효율이 크게 향상됩니다."
    },
    "ca05950b": {
        "content_updated_ko": "ChatGPT 데스크톱 앱의 사이드바 너비를 조절할 수 있습니다.\n드래그로 사이드바 크기를 자유롭게 변경할 수 있습니다.\n작업 환경에 맞게 화면 레이아웃을 최적화할 수 있습니다."
    },
    "4f221002": {
        "content_updated_ko": "검색 결과에 제품 정보와 가격 비교 기능이 추가됐습니다.\n쇼핑 관련 질문 시 실시간 가격과 리뷰를 확인할 수 있습니다.\n별도 쇼핑 사이트 방문 없이 구매 결정을 도울 수 있습니다."
    },
    "39b5036f": {
        "content_updated_ko": "GPT-4o의 이미지 생성 기능이 Team 플랜에 제공됩니다.\nTeam 사용자도 대화 중 고품질 이미지를 생성할 수 있습니다.\n비즈니스 환경에서 시각 콘텐츠 제작이 더 편리해집니다."
    },
    "ad026889": {
        "content_updated_ko": "Projects에 파일, 대화, 지침을 체계적으로 관리할 수 있습니다.\nPlus, Pro, Team 플랜 사용자가 먼저 이용할 수 있습니다.\n관련 맥락을 한곳에 모아 더 정확한 응답을 받을 수 있습니다."
    },
    "466b0fe7": {
        "content_updated_ko": "ChatGPT 검색에 쇼핑 기능이 통합되어 정식 출시됩니다.\n제품 추천, 가격 비교, 리뷰 확인이 한곳에서 가능합니다.\n대화형 인터페이스로 개인 맞춤형 쇼핑 경험을 제공합니다."
    },
    "46a1d978": {
        "content_updated_ko": "Deep Research에서 데이터 분석과 시각화가 가능해졌습니다.\n차트, 그래프 등 다양한 시각적 자료를 자동으로 생성합니다.\nPro 사용자의 심층 데이터 기반 의사결정을 효과적으로 지원합니다."
    },
    "a0560b9b": {
        "content_updated_ko": "대화 중 생성된 이미지의 스타일과 구도를 수정할 수 있습니다.\n색상, 배경, 텍스트 등 세부 요소를 개별 조정할 수 있습니다.\n반복 생성 없이 원하는 결과물을 빠르게 완성할 수 있습니다."
    },
    "12fef38f": {
        "content_updated_ko": "검색 결과 하단에 관련 후속 질문 추천이 자동 표시됩니다.\n추가 검색 없이 관련된 심층 정보를 바로 탐색할 수 있습니다.\n정보 탐색 흐름이 끊기지 않아 검색 효율성이 높아집니다."
    },
    "27f1501c": {
        "content_updated_ko": "GPT-4o 모델의 창의성과 글쓰기 품질이 크게 향상됐습니다.\n자연스러운 표현력과 다양한 문체 구사 능력이 강화됐습니다.\n모든 플랜 사용자가 향상된 응답 성능을 체험할 수 있습니다."
    },
    "236f8cab": {
        "content_updated_ko": "Apple의 시각 지능 기능에서 ChatGPT를 호출할 수 있습니다.\n카메라로 촬영한 대상에 대해 즉시 AI 분석이 가능합니다.\niPhone 16 사용자의 일상 속 AI 활용이 확대됩니다."
    },
    "e4d09082": {
        "content_updated_ko": "1-800-CHATGPT 전화로 ChatGPT와 대화할 수 있습니다.\nWhatsApp에서도 ChatGPT에 메시지를 보낼 수 있습니다.\n인터넷 연결이나 앱 설치 없이도 AI 도움을 받을 수 있습니다."
    },
    "db7e5e1b": {
        "content_updated_ko": "o1 모델이 ChatGPT Pro 플랜에서 정식 출시됩니다.\n수학, 코딩, 과학 분야에서 뛰어난 추론 능력을 갖췄습니다.\nPro 사용자는 무제한으로 o1 모델을 이용할 수 있습니다."
    },
    "ccf32aca": {
        "content_updated_ko": "ChatGPT에서 검색 기능을 바로 사용할 수 있게 됐습니다.\n실시간 웹 정보를 대화형으로 검색하고 탐색할 수 있습니다.\nPlus, Team 사용자부터 순차적으로 이용 가능합니다."
    },
    "e8f1ab9e": {
        "content_updated_ko": "macOS 앱에서 화면 공유로 작업 맥락을 전달할 수 있습니다.\n코드, 문서, 디자인 등 화면 내용을 AI가 이해합니다.\nPlus, Team 사용자가 먼저 이용할 수 있습니다."
    },
    "96c92776": {
        "content_updated_ko": "ChatGPT 검색이 로그인 없이 누구나 사용 가능해졌습니다.\n실시간 웹 정보를 대화형으로 자유롭게 탐색할 수 있습니다.\nAI 기반 검색 서비스의 접근성이 대폭 향상될 전망입니다."
    },
    "3fee8828": {
        "content_updated_ko": "연말 프로모션으로 Plus 요금이 월 $20에서 할인됩니다.\n신규 가입 시 첫 3개월간 할인된 특별 요금이 적용됩니다.\n더 많은 사용자가 고급 AI 기능을 경험할 수 있습니다."
    },
    "33f04b66": {
        "content_updated_ko": "ChatGPT에서 생성한 이미지를 외부에 공유할 수 있습니다.\n고유 링크를 통해 누구나 이미지를 열람할 수 있습니다.\n소셜 미디어와 메신저에서 간편하게 공유할 수 있습니다."
    },
    "e46719ec": {
        "content_updated_ko": "o3-pro 모델이 ChatGPT Pro 플랜에 추가됐습니다.\n수학, 과학, 코딩에서 최고 수준의 추론력을 제공합니다.\n정밀한 분석이 필요한 고난도 전문 작업에 최적화됐습니다."
    },
    "56e2671d": {
        "title_updated_ko": "GPT-4.1 모델 패밀리가 API에 새로 출시됐어요",
        "content_updated_ko": "GPT-4.1, GPT-4.1 mini, nano 세 가지 모델이 출시됩니다.\n코딩 성능과 지시 따르기 능력이 이전 대비 크게 향상됐습니다.\n개발자를 위한 API 전용 고성능 모델로 폭넓게 제공됩니다."
    },
    "21be8a40": {
        "title_updated_ko": "GPT-4o가 더 자연스럽고 간결하게 응답해요",
        "content_updated_ko": "GPT-4o의 응답 스타일이 더 자연스럽고 간결해졌습니다.\n불필요한 수식어와 반복 표현이 대폭 줄어 가독성이 높아졌습니다.\n모든 ChatGPT 플랜 사용자에게 자동으로 적용됩니다."
    },
    "f43f150f": {
        "title_updated_ko": "ChatGPT 메모리가 더 똑똑하게 개선됐어요",
        "content_updated_ko": "메모리 기능이 더 정확하고 유용하게 전면 업데이트됐습니다.\n사용자 선호와 대화 맥락을 더 잘 기억하고 활용합니다.\nPlus, Pro, Team 사용자부터 순차적으로 제공됩니다."
    },
    "0e831b73": {
        "content_updated_ko": "ChatGPT가 사용자의 선호와 대화 맥락을 자동 기억합니다.\n반복 설명 없이도 맞춤형 개인화된 응답을 받을 수 있습니다.\nPlus 사용자부터 순차적으로 전체 플랜에 확대됩니다."
    },
    "bb8e550a": {
        "content_updated_ko": "GPT-4o의 데이터 분석 및 시각화 성능이 대폭 향상됐습니다.\n파일 업로드 후 차트와 핵심 인사이트를 자동 생성합니다.\n비전문가도 손쉽게 데이터 기반 의사결정을 할 수 있습니다."
    },
    "7efd4d36": {
        "title_updated_ko": "ChatGPT에서 GPT-5 모델을 사용할 수 있어요",
        "content_updated_ko": "GPT-5가 ChatGPT에서 기본 모델로 제공됩니다.\n추론, 코딩, 창의성 등 전 분야에서 성능이 향상됐습니다.\nPlus, Pro, Team 사용자부터 순차적으로 적용됩니다."
    },
    "72f44e0a": {
        "title_updated_ko": "o3 모델이 ChatGPT에서 추론 기본 모델이 됐어요",
        "content_updated_ko": "o3가 ChatGPT의 기본 추론 모델로 설정됐습니다.\n수학, 과학, 코딩 분야에서 최고 수준 성능을 보입니다.\nPlus, Pro, Team 사용자가 즉시 이용할 수 있습니다."
    },
    "305eeb21": {
        "content_updated_ko": "Codex가 ChatGPT 내에서 코딩 에이전트로 출시됩니다.\n코드 작성, 디버깅, PR 생성을 자동으로 수행합니다.\nPro, Team, Enterprise 사용자가 이용할 수 있습니다."
    },
    "6a2284a1": {
        "content_updated_ko": "Sora로 텍스트 설명만으로 동영상을 생성할 수 있습니다.\nPlus, Pro 사용자에게 제공되며 다양한 스타일을 지원합니다.\n크리에이터의 영상 제작 진입 장벽이 크게 낮아질 전망입니다."
    },
    "e726e17c": {
        "content_updated_ko": "Canvas에서 문서와 코드를 나란히 편집할 수 있습니다.\nGPT-4o 기반으로 실시간 피드백과 수정이 가능합니다.\n글쓰기와 코딩 작업의 생산성이 대폭 향상될 것으로 기대됩니다."
    },
    "8287f31d": {
        "content_updated_ko": "음성 대화 중 카메라로 사물을 보여주며 질문할 수 있습니다.\n실시간 화면 공유와 음성 기반 대화를 동시에 지원합니다.\nPlus, Team 사용자부터 순차적으로 이용 가능합니다."
    },
    "35267e6d": {
        "title_updated_ko": "ChatGPT Tasks로 알림과 예약 작업을 할 수 있어요",
        "content_updated_ko": "ChatGPT가 예약된 시간에 작업을 자동 수행합니다.\n알림, 요약, 리서치 등 반복 작업을 설정할 수 있습니다.\nPlus, Pro, Team 사용자에게 베타로 제공됩니다."
    },
    "a3905a76": {
        "title_updated_ko": "o1-pro 모드가 ChatGPT Pro에서 제공돼요",
        "content_updated_ko": "o1-pro가 더 많은 연산으로 정밀한 추론을 수행합니다.\n수학, 과학, 코딩의 어려운 문제 해결에 최적화됐습니다.\nChatGPT Pro 사용자 전용으로 제공되는 프리미엄 모드입니다."
    },
    "5e505821": {
        "title_updated_ko": "Apple Intelligence에서 ChatGPT를 사용할 수 있어요",
        "content_updated_ko": "Siri와 시스템 전반에서 ChatGPT를 호출할 수 있습니다.\niOS 18.2, macOS Sequoia 15.2부터 지원됩니다.\n별도 앱 없이 Apple 기기에서 AI를 활용할 수 있습니다."
    },
}

# Apply fixes
applied = 0
for prefix, fix in fixes.items():
    if prefix in by_id:
        item = by_id[prefix]
        if "title_updated_ko" in fix:
            item["title_updated_ko"] = fix["title_updated_ko"]
        if "content_updated_ko" in fix:
            item["content_updated_ko"] = fix["content_updated_ko"]
        applied += 1

print(f"Applied {applied} fixes")

# Validate all entries
errors = []
for item in data:
    tid = item["id"][:8]
    title = item["title_updated_ko"]
    content = item["content_updated_ko"]

    # Title length check
    tlen = len(title)
    if tlen < 20 or tlen > 45:
        errors.append(f"{tid}: title length {tlen} ('{title}')")

    # Content lines check
    lines = content.split("\n")
    if len(lines) != 3:
        errors.append(f"{tid}: content has {len(lines)} lines (expected 3)")
    for i, line in enumerate(lines):
        llen = len(line)
        if llen < 30 or llen > 60:
            errors.append(f"{tid}: content L{i+1} length {llen}")

if errors:
    print(f"\n{len(errors)} validation errors remain:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("All 129 entries pass validation!")

# Write back
with open("data/chatgpt_enrich_ko_result.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Written {len(data)} entries to data/chatgpt_enrich_ko_result.json")
