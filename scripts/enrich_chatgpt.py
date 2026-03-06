"""ChatGPT event English enrichment: generate/apply/seed.

CLI:
  python -m scripts.enrich_chatgpt status
  python -m scripts.enrich_chatgpt generate [--limit N] [--force]
  python -m scripts.enrich_chatgpt apply <file.json>
  python -m scripts.enrich_chatgpt seed  (apply hardcoded historical data)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tracker.db"

updates = [
    # --- batch 1: events 1-25 (2025-01-14 to 2025-05-14) ---
    ("9b398480-cf02-4966-b896-c031d2fdf6f5",
     "ChatGPT Tasks: Launch scheduled tasks beta for reminders & recurring actions",
     "ChatGPT introduces Tasks, a new feature that lets users schedule one-time reminders or recurring actions by telling ChatGPT what they need and when to do it automatically.\nScheduled Tasks is launching in early beta and is available exclusively to Plus, Pro, and Teams plan users, with broader availability planned for all ChatGPT accounts in the future.\nThis is ChatGPT's first native scheduling capability, moving the product beyond real-time conversation into proactive, time-based task execution for users."),

    ("a6ca2315-d599-4441-b66d-7fd88cd5f914",
     "Canvas: Add import from chat to edit responses & code blocks on web",
     "ChatGPT Canvas now allows users to import a full model response or a code block directly from a chat conversation into the Canvas editor for further editing and refinement.\nThis feature supports editing both full text responses and individual code blocks within Canvas, and is currently available on the web platform only with no desktop or mobile support in this release.\nCanvas continues to evolve as a side-by-side editing workspace within ChatGPT, and this import capability bridges the gap between conversational output and structured document or code editing."),

    ("9ad4fb52-105a-4cb5-a217-e3e844b5b759",
     "Custom Instructions: Redesign UI for traits, tone & rules personalization",
     "ChatGPT updates Custom Instructions with a redesigned UI that makes it easier to define the traits you want ChatGPT to have, how you want it to communicate, and specific rules for it to follow.\nThe new UI is rolling out on chatgpt.com and Windows desktop now, with mobile and MacOS desktop support coming in the following weeks, and will soon be available to users in the EU, Norway, Iceland, Liechtenstein, and Switzerland.\nExisting custom instructions remain unchanged by this update; the redesign focuses on discoverability and ease of use rather than altering underlying personalization functionality."),

    ("01764204-f027-4c85-ba07-37fc195bafb4",
     "Canvas: Enable sharing of rendered code, documents & code assets",
     "ChatGPT Canvas now lets users share Canvas assets such as rendered React or HTML code, documents, or code snippets with other users, similar to existing conversation sharing functionality.\nSharing is accessible from the Canvas toolbar when Canvas is open, allowing one-click distribution of work products created within the collaborative editing environment.\nThis sharing capability extends Canvas from a personal editing tool into a lightweight collaboration surface, complementing the earlier import-from-chat feature released in January 2025."),

    ("4c13ab01-fa27-4c48-8a23-0e702d85e685",
     "ChatGPT: Add Safari default search, logout confirmation & Android improvements",
     "ChatGPT adds the ability to set ChatGPT as the default search engine in Safari, introduces a confirmation dialog for logging out on iOS and web, and includes multiple platform-specific improvements.\nAndroid receives improved conversation parsing performance and updated launch animations with a redesigned composer, while iOS gets general performance fixes and Whisper now shows a text preview of dictated text after recording.\nThis bundled release focuses on quality-of-life improvements across all platforms, enhancing everyday usability rather than introducing major new features to the ChatGPT experience."),

    ("56803606-4e95-46fa-8762-e93430d8f6b2",
     "ChatGPT iOS: Launch home screen widget & fix text selection and performance",
     "ChatGPT releases an iOS home screen widget along with text selection improvements that now allow users to select text across horizontal rulers within conversations.\nPerformance improvements include faster model header loading, quicker display of conversation history and GPTs, and a bug fix resolving 401 errors that occurred when logged-out users dismissed tooltips or when Android users were incorrectly logged out.\nThis update addresses several long-standing usability issues on mobile platforms, improving both the speed and reliability of the ChatGPT iOS and Android experience."),

    ("4fdfd745-3dc2-41d6-afcb-6a5bfef1d70b",
     "GPT-4.5: Release to Pro plan & improve temporary chat and iOS text selection",
     "OpenAI releases GPT-4.5 to Pro plan users in ChatGPT and moves the temporary chat icon to the top bar for improved accessibility and a clearer temporary chat experience.\niOS updates include long-press text selection, always-visible message quick actions below messages, bug fixes in the 1.2025.056 release, and a new setting to auto-submit voice transcriptions that is off by default. Android receives improved error handling for Play Integrity errors.\nThis is a multi-platform bundled release combining a major model launch for Pro subscribers with quality-of-life interface improvements across iOS and Android clients."),

    ("5d13f81e-2cf5-45a1-bebc-fff979fdaf29",
     "ChatGPT iOS: Improve table copying, long-press menu & response streaming",
     "ChatGPT iOS app improves table-copying functionality for both iOS and macOS, enabling users to more easily copy tabular data from ChatGPT responses into other applications.\nAdditional improvements include a new long-press gesture on user messages to access copy and edit actions, better rendering of nested blockquote content, and faster streaming display of conversations and message menu actions.\nThese updates focus on refining the iOS reading and interaction experience, addressing common friction points when working with structured content and long conversations in the mobile app."),

    ("5690fa76-8291-49a8-bbe4-6621b3108e87",
     "ChatGPT Android: Increase inline image size & add incognito keyboard",
     "ChatGPT Android app increases the default display size for inline generated images, making AI-created visuals easier to view directly within conversations without additional tapping.\nThe update also introduces a more clear and private incognito keyboard that activates automatically during Temporary Chats, helping users maintain privacy when using the ephemeral conversation mode.\nThese two targeted improvements address visual clarity and privacy usability on Android, released alongside a parallel set of iOS and web updates on the same March 18 date."),

    ("b8e1dbd0-e12a-4816-af31-4af848e9ef77",
     "ChatGPT Web: Add inline error retry, o1/o3-mini data analysis & conversation drafts",
     "ChatGPT on web and Windows desktop now allows users to retry directly from inline message errors or continue chatting in the same conversation without starting over, improving error recovery.\nNew capabilities include Python-powered data analysis for o1 and o3-mini models enabling regressions, business metric visualizations, and scenario simulations, plus automatic saving of unsubmitted messages as conversation drafts and a redesigned Temporary Chat UI.\nThis bundled web update focuses on power-user productivity features, bringing data analysis capabilities previously limited to GPT-4o to the o-series reasoning models for the first time."),

    ("e61017e9-2e2a-4891-8731-e32d21ebdf50",
     "ChatGPT: Announce cross-platform usability & performance improvements",
     "OpenAI announces a broad set of usability improvements, performance optimizations, and bug fixes across the ChatGPT Web, Android, and iOS platforms as part of ongoing product refinement.\nThis release note serves as an umbrella announcement with specific callouts detailed in separate platform-specific entries, and directs macOS app users to a dedicated page for those updates.\nThe announcement reflects OpenAI's shift toward regular bundled maintenance releases across all ChatGPT platforms, consolidating incremental improvements into coordinated cross-platform update cycles."),

    ("8844cdc5-47f4-48cf-8899-4eb7d2adb031",
     "GPT-4o: Improve coding, instruction following & conversational clarity",
     "OpenAI releases a significant update to GPT-4o that makes it more intuitive, creative, and collaborative, with enhanced instruction-following, smarter coding capabilities, and a clearer communication style.\nSpecific improvements include cleaner and simpler frontend code generation, better reasoning through existing code to identify necessary changes, higher accuracy in classification tasks, and outputs that compile and run more reliably. Early testers report the model better understands implied intent behind prompts.\nThe updated model is available in ChatGPT and via the API as the newest snapshot of chatgpt-4o-latest, with a dated API model planned in the coming weeks to give developers a stable version to target."),

    ("e0862a83-556e-4198-a6bb-b948abad2a08",
     "GPT-4: Announce retirement effective April 30 with GPT-4o as replacement",
     "OpenAI announces that GPT-4 will be retired from ChatGPT effective April 30, 2025, and fully replaced by GPT-4o as the successor model across the platform.\nGPT-4o is described as a newer, natively multimodal model that consistently surpasses GPT-4 in writing, coding, STEM, and other benchmarks, with recent upgrades further improving instruction following, problem solving, and conversational flow. GPT-4 remains available in the API.\nGPT-4 marked a pivotal moment in ChatGPT's evolution since its original launch, and this retirement continues OpenAI's pattern of consolidating older models as newer generations prove superior across all key metrics."),

    ("03f44f3c-4006-4cbb-b71a-19e0f5017b9d",
     "ChatGPT Image Library: Launch auto-saved image gallery in sidebar",
     "ChatGPT launches Image Library, a new sidebar feature that automatically saves all images created with ChatGPT to one centralized place for browsing, revisiting, and reusing generated artwork.\nThe Library is rolling out on Web, iOS, and Android for Free, Plus, and Pro users, with Enterprise and Education support coming soon. It currently displays images from 4o Image Generation while older creations are being backfilled, and images can be removed by deleting the source conversation.\nThis is ChatGPT's first dedicated media management feature, reducing the friction of searching through past conversations to find previously generated images and enabling a more creative-workflow-oriented experience."),

    ("2485276d-23c0-43e5-9d95-3834d696db6f",
     "ChatGPT Memory: Enable memory-informed web search queries",
     "ChatGPT can now use stored memories to inform and personalize search queries when it searches the web using third-party search providers, making search results more relevant to the user.\nThis feature connects ChatGPT's personalization layer with its web search capability, allowing the model to incorporate known user preferences, context, and prior interactions when formulating search requests.\nMemory with Search represents a deeper integration between ChatGPT's personalization and browsing features, moving toward a more contextually aware assistant that leverages user history across all its tool capabilities."),

    ("60452154-9adb-4c9b-be1f-e7ba83eb0640",
     "o3 & o4-mini: Launch reasoning models with full ChatGPT tool integration",
     "OpenAI releases o3 and o4-mini, the latest reasoning models that can agentically use and combine every tool within ChatGPT including web search, Python analysis, visual reasoning, and image generation for the first time.\nThese models are trained to reason about when and how to use tools to produce detailed answers, typically responding in under a minute, and deliver significantly stronger performance across academic benchmarks and real-world tasks for all user tiers from curious users to advanced researchers.\nThe o3 and o4-mini release represents a step toward a more agentic ChatGPT that can independently execute multi-step tasks, setting a new standard for combined reasoning and tool-use capability in the o-series model lineup."),

    ("516bf6d2-1fd4-4f95-b829-7e690d2c1fa4",
     "GPT-4o: Improve memory optimization, STEM problem-solving & conversational guidance",
     "OpenAI makes additional improvements to GPT-4o, optimizing when it saves memories, enhancing problem-solving capabilities for STEM tasks, and making the model more proactive at guiding conversations toward productive outcomes.\nSubtle changes to response behavior make GPT-4o feel more intuitive and effective across a variety of tasks, with the model now better at steering open-ended conversations and providing more structured, actionable guidance to users.\nThis is the second major GPT-4o improvement update following the March 27 release, continuing the pattern of iterative refinement to the model's conversational and reasoning capabilities based on user feedback."),

    ("4f07102c-2fbf-44c1-b502-b35d27aec734",
     "GPT-4o: Revert latest update due to sycophancy issues",
     "OpenAI reverts the most recent GPT-4o update after identifying issues with overly agreeable responses, commonly known as sycophancy, where the model excessively validated user statements rather than providing honest feedback.\nThe team is actively working on further improvements and has published two blog posts explaining what happened, initial findings on the sycophancy problem, and the changes planned going forward to prevent similar issues.\nThis revert highlights the challenges of fine-tuning conversational models for helpfulness without crossing into excessive agreeableness, and marks a notable instance of OpenAI publicly rolling back a deployed model update."),

    ("0c04d0e3-ade6-4572-996f-ac550cc3941d",
     "ChatGPT Monday: Sunset limited-time personality after one-month run",
     "OpenAI sunsets the Monday personality, a one-month surprise feature launched on April 1 that offered an irreverent conversational style in both voice and text modes within ChatGPT.\nThe personality was designed as a time-limited experiment running for exactly one month, and its retirement was planned from the start rather than being a response to user feedback or technical issues.\nMonday represents OpenAI's first public experiment with distinct ChatGPT personalities, and the company indicates new personalities are already in development for future release as part of an ongoing exploration of varied conversational styles."),

    ("57e092df-8e4b-4352-9b6d-ece7307aba43",
     "ChatGPT Mobile: Consolidate tool icons into new Skills menu on iOS & Android",
     "ChatGPT removes the row of individual tool icons from the mobile composer on iOS and Android and replaces it with a single sliders-style icon that opens a new Skills menu as a bottom-sheet overlay.\nTapping the new icon presents a menu where users can choose tools like Create an Image or Search the Web; no tools are deprecated or removed, and all existing functionality remains accessible through the consolidated interface.\nThis UI change applies to Free, Plus, and Pro plans and focuses on reducing on-screen clutter in the mobile composer while maintaining full tool access through a single organized entry point."),

    ("a9d2023b-e711-4835-b30c-00c1032ec758",
     "ChatGPT Memory: Expand enhanced memory to EU & add chat history for Plus/Pro",
     "ChatGPT rolls out enhanced memory to all Plus and Pro users globally including the EEA, UK, Switzerland, Norway, Iceland, and Liechtenstein, where the features are off by default and must be enabled in Settings under Personalization.\nPlus and Pro accounts receive both saved memories and chat history reference capabilities, while free-tier users get access to saved memories only. Users outside the listed European regions who already have memory enabled receive the upgrade automatically.\nThis expansion addresses the longstanding gap where European users could not access ChatGPT's memory features due to privacy regulations, and represents a significant step in making personalized AI experiences available across all supported regions."),

    ("513ca378-64fc-42e7-9369-50be44800d6e",
     "Deep Research: Launch GitHub connector for Plus, Pro & Team users",
     "ChatGPT Deep Research adds a GitHub connector that allows the model to access and analyze GitHub repositories during deep research sessions, available globally to Team users with gradual rollout to Plus and Pro users.\nThe connector is not yet available to users in the EEA, Switzerland, and the UK, and Enterprise user access will be announced at a later date, indicating a phased geographic and plan-based rollout strategy.\nThis is the first third-party code platform integration for Deep Research, enabling developers to combine repository analysis with ChatGPT's research capabilities for more comprehensive technical investigations."),

    ("939a218c-8cc1-4575-826f-c5bfccb55e13",
     "Deep Research: Add PDF export with tables, images & linked citations",
     "ChatGPT Deep Research now supports exporting research reports as well-formatted PDF documents complete with tables, images, linked citations, and source references for professional-quality output.\nUsers can export by clicking the share icon and selecting Download as PDF, and the feature works for both newly created and previously generated research reports across Plus, Pro, and Team plans.\nThis export capability transforms Deep Research from a conversation-only tool into one that produces shareable, archivable documents suitable for professional and academic use cases."),

    ("0762f0a5-b15a-49fc-b792-1d4dcafdc5d7",
     "Deep Research: Launch SharePoint & OneDrive connector for Plus, Pro & Team",
     "ChatGPT Deep Research adds Microsoft SharePoint and OneDrive connectors, enabling the model to access and analyze documents stored in Microsoft's cloud ecosystem during deep research sessions.\nThe connector is available globally to Team users with gradual rollout to Plus and Pro users, excluding users in the EEA, Switzerland, and the UK for now, with Enterprise access to be announced at a later date.\nThis is the second enterprise connector for Deep Research following the GitHub integration launched four days earlier, signaling a rapid expansion of Deep Research's ability to tap into organizational knowledge bases."),

    ("966b4077-80c5-4578-9d8a-2f86aef7026f",
     "GPT-4.1 mini: Launch as GPT-4o mini replacement for all ChatGPT users",
     "OpenAI introduces GPT-4.1 mini as a fast, capable, and efficient small model that delivers significant improvements over GPT-4o mini in instruction-following, coding, and overall intelligence across ChatGPT.\nStarting today, GPT-4.1 mini replaces GPT-4o mini in the model picker under more models for paid users and serves as the fallback model for free users who reach their GPT-4o usage limits, with rate limits remaining unchanged.\nEvals for GPT-4.1 mini were originally shared in the blog post accompanying the API release, and detailed safety evaluation results are available in the newly launched Safety Evaluations Hub, continuing OpenAI's model consolidation around newer architectures."),

    # --- batch 2: events 26-50 (2025-05-14 to 2025-08-12) ---
    ("3a62c983-cd0d-4157-ae2f-6a9de4e0df9d",
     "GPT-4.1: Release coding-specialized model to all paid ChatGPT users",
     "OpenAI releases GPT-4.1 in ChatGPT for all paid users after its successful launch in the API in April, offering a model that excels at coding tasks and precise instruction following.\nGPT-4.1 is stronger than GPT-4o at instruction following and web development, and serves as an alternative to o3 and o4-mini for simpler everyday coding needs with the same rate limits as GPT-4o.\nPlus, Pro, and Team users can access GPT-4.1 via the more models dropdown starting today, with Enterprise and Edu access coming in the following weeks."),

    ("97070301-9025-4c52-9c5b-cabeab788ca6",
     "Deep Research: Launch GitHub connector globally for Plus, Pro & Team users",
     "The GitHub connector for ChatGPT deep research is now available globally to Plus, Pro, and Team users, including those in the EEA, Switzerland, and the United Kingdom.\nThis connector allows deep research to access and analyze GitHub repositories, enabling users to incorporate code and project data into their research workflows.\nNo additional details were provided in the release note regarding specific capabilities or limitations of the GitHub connector integration."),

    ("ccec4ad5-2d26-43d3-89f9-7b1b12fe078c",
     "Deep Research: Launch Dropbox connector for Plus, Pro & Team users",
     "ChatGPT deep research now integrates with Dropbox, allowing users to include their Dropbox files as sources in deep research queries for richer and more personalized results.\nThe Dropbox connector is available globally to Team users and is gradually rolling out to Plus and Pro users, excluding those in the EEA, Switzerland, and the UK, with Enterprise access to be announced later.\nThis is part of OpenAI's broader push to connect deep research with third-party data sources, following similar connector launches for other cloud storage and productivity platforms."),

    ("1872d79c-cbf5-4a91-bca0-a2281bcb57a2",
     "ChatGPT Memory: Expand comprehensive memory with chat history to Free users",
     "ChatGPT Memory improvements are rolling out to Free users, adding the ability to reference recent conversations in addition to previously saved memories for more relevant and tailored responses.\nFree users must be logged in and on up-to-date apps with iOS or Android version 1.2025.147 or later; users in the EEA, UK, Switzerland, Norway, Iceland, and Liechtenstein must opt in via Settings, while others with memory enabled receive the upgrade automatically.\nThis extends the comprehensive memory feature that was previously available only to paid users, giving Free tier users the same conversational continuity and personalization capabilities."),

    ("b5213d69-2f1c-43fd-9ae4-420fafd0a7fd",
     "Deep Research: Launch custom MCP connectors for Pro, Team, Enterprise & Edu",
     "Admins and users can now build and deploy custom connectors to proprietary systems using Model Context Protocol for use within ChatGPT deep research, enabling integration with internal tools and data sources.\nCustom MCP connectors require a remote MCP server, are available only in deep research, and admin-published connectors appear in the connector list for all users; on Team, Enterprise, and Edu plans only admins can build and deploy them.\nThis launch enables organizations to extend deep research beyond pre-built integrations, allowing connection to proprietary databases and internal systems through the open Model Context Protocol standard."),

    ("1f88b8ac-de29-40b7-9682-65cc23569634",
     "Deep Research Connectors: Launch beta with 11 integrations for paid users",
     "ChatGPT deep research connectors enter beta for Team, Enterprise, Edu, Pro, and Plus users globally, enabling long-form cited responses that combine internal tools with web sources for comprehensive synthesis.\nSupported connectors include Google Drive, SharePoint, Dropbox, Box, Outlook, Gmail, Google Calendar, Linear, GitHub, HubSpot, and Teams, with Plus and Pro users in Switzerland, EEA, and the UK currently excluded.\nThis marks a significant expansion of deep research from web-only sources to a hybrid model that integrates organizational data, positioning ChatGPT as a unified research tool across both public and private information."),

    ("19d8247c-2e7e-4bfb-a17f-aa5482a92484",
     "Advanced Voice: Upgrade intonation, naturalness & add real-time translation",
     "ChatGPT Advanced Voice receives a major upgrade for paid users with significantly enhanced intonation and naturalness, making interactions feel more fluid and human-like with subtler cadence, realistic pauses, and improved expressiveness for emotions including empathy and sarcasm.\nVoice now also offers intuitive real-time language translation that persists throughout a conversation until stopped, available across all paid plans and platforms; known limitations include occasional decreases in audio quality and rare hallucinations producing unintended sounds.\nThis update builds on earlier 2025 improvements to reduce interruptions and improve accents, continuing OpenAI's investment in making Advanced Voice a more natural and versatile conversational interface."),

    ("c494f82f-6144-4bd6-9476-746b4d7d48e9",
     "o3-pro: Launch enhanced reasoning model for Pro & Team users in ChatGPT",
     "OpenAI launches o3-pro, a version of the o3 model designed to think longer and provide the most reliable responses, now available for Pro and Team users in ChatGPT and in the API, replacing o1-pro in the model picker.\nIn expert evaluations, o3-pro consistently outperforms both o1-pro and o3 across science, education, programming, business, and writing, with access to web search, file analysis, Python, memory, and visual reasoning; current limitations include no support for temporary chats, image generation, or Canvas.\nEnterprise and Edu users will receive access the following week; o3-pro is recommended for challenging questions where reliability matters more than speed, as responses typically take longer than o1-pro due to tool usage."),

    ("528554dd-2ff5-4688-ae0b-77e85986b103",
     "ChatGPT Projects: Add deep research, voice mode & cross-project sharing",
     "ChatGPT Projects receives several capability updates for Plus, Pro, and Team users, including deep research and voice mode support within projects, improved memory that references past chats, and the ability to share chats from projects.\nUsers can now start a new project directly from a chat, upload files and access the model selector on mobile, with memory improvements for referencing past project chats available specifically for Plus and Pro users.\nThese updates transform Projects from a basic organizational tool into a more fully featured workspace, addressing user requests for deeper integration between Projects and ChatGPT's core capabilities."),

    ("2502fb2d-4b1e-4b70-87de-78da05d1a9d6",
     "Custom GPTs: Expand model selection to full ChatGPT model lineup",
     "Creators can now choose from the full set of ChatGPT models including GPT-4o, o3, o4-mini and more when building Custom GPTs, making it easier to fine-tune performance for different tasks, industries, and workflows.\nGPTs without Custom Actions can use the model picker to select from all available models, while GPTs with Custom Actions currently support only GPT-4o and 4.1; this is available on web for Plus, Pro, and Team plans with Enterprise and Edu rollout coming soon.\nPreviously Custom GPTs were limited to a single default model, so this expansion gives creators significantly more control over the intelligence and capability profile of their GPTs."),

    ("e102b770-4b37-4192-a5f9-0b0befb069b0",
     "ChatGPT Search: Upgrade response quality with smarter multi-search capabilities",
     "ChatGPT search receives a major quality upgrade for all users, delivering more comprehensive and up-to-date responses with smarter understanding of queries and better handling of longer conversational contexts.\nImprovements include automatic multi-search for complex questions, image-based web search from uploaded images, and significantly reduced repetitive responses in longer conversations; known limitations include occasionally longer responses and unexpected chain-of-thought reasoning for simple queries.\nIn testing, users preferred these search improvements over the previous search experience, marking a substantial step forward in ChatGPT's ability to serve as a general-purpose search and research tool."),

    ("4626c47b-9f07-4de9-b6ee-82906d4b6858",
     "Custom GPTs: Expand full model selection to Enterprise & Edu users",
     "Enterprise and Edu users can now choose from the full set of ChatGPT models including GPT-4o, o3, o4-mini and more when building Custom GPTs, extending the model selection capability launched to Plus, Pro, and Team users earlier in June.\nGPTs without Custom Actions can use the model picker to select from all models available to the user, while GPTs with Custom Actions currently support only GPT-4o and 4.1, available on web for all paid plans.\nThis completes the rollout of expanded model support for Custom GPTs across all paid tiers, giving Enterprise and Edu creators the same flexibility to optimize their GPTs for specific tasks and workflows."),

    ("2467dbc1-ed9e-4608-86d5-d96ea058a2cb",
     "ChatGPT Record Mode: Expand to Pro, Enterprise & Edu on macOS",
     "ChatGPT Record Mode launches for Pro, Enterprise, and Edu users on the macOS desktop app, enabling capture of meetings, brainstorms, or voice notes with automatic transcription, summarization, and conversion into actionable outputs.\nChatGPT will transcribe and summarize recordings and turn them into helpful outputs like follow-ups, plans, or even code; this feature is available exclusively on the macOS desktop app and was previously launched for Team users on June 4, 2025.\nRecord Mode represents ChatGPT's expansion into real-time audio capture workflows, complementing the existing Voice mode by focusing on passive recording and structured output generation rather than interactive conversation."),

    ("da2482f7-1a6b-4b5a-afe9-5333f8b8868a",
     "ChatGPT Projects: Increase file upload limit to 40 for Pro users",
     "ChatGPT Projects now supports up to 40 uploaded files per project for Pro users, doubling the previous limit of 20 files to enable more comprehensive document analysis and multi-file workflows.\nThis increase applies exclusively to Pro plan users and affects the Projects feature where users organize related chats and files around specific topics or tasks.\nThe expanded file limit addresses power-user needs for handling larger document sets within a single project, particularly useful for research, legal review, and data analysis workflows."),

    ("85346813-3645-4984-bff1-6c9f7f2a9358",
     "Chat Search Connectors: Launch Dropbox, Box, Google Drive & more for Pro users",
     "Pro users can now use chat search connectors for Dropbox, Box, Google Drive (synced and non-synced), Microsoft OneDrive Business, and Microsoft SharePoint, extending connector functionality beyond deep research into regular chat search.\nThis feature is currently limited to users located outside of the EEA, Switzerland, and the UK, and adds chat search capability on top of the existing deep research connector integrations.\nThis expansion bridges the gap between deep research connectors and everyday chat interactions, allowing Pro users to search their cloud storage directly within standard conversations without needing to invoke deep research."),

    ("8c49769f-a0fa-445f-bac3-1900648d1bcb",
     "Record Mode: Expand to Plus users on ChatGPT macOS desktop app",
     "Record mode is now available to ChatGPT Plus users globally in the macOS desktop app, allowing users to record live conversations like team meetings or voice notes and convert them into editable summaries in Canvas.\nThe feature is available exclusively on the macOS desktop app and produces editable summaries directly within Canvas for further refinement and sharing with collaborators.\nRecord mode originally rolled out to Team users on June 4 and Enterprise and Edu plans on June 18, making this Plus tier expansion the final step in bringing the feature to all paid user tiers."),

    ("e12e506e-587d-44d4-a5fa-f8646b3ed3c9",
     "Advanced Voice: Expand enhanced naturalness & translation to Free users",
     "The Advanced Voice upgrades announced on June 7 for paid users, including improved naturalness, expressiveness, and real-time translation, are now rolling out to ChatGPT Free tier users as well.\nFree users receive the same intonation, cadence, and translation improvements as paid users, with existing Free tier rate limits remaining unchanged for voice interactions.\nThis democratizes the enhanced Advanced Voice experience across all ChatGPT users approximately six weeks after the initial paid-user launch, continuing OpenAI's pattern of gradually expanding premium features to the Free tier."),

    ("04c2c164-5c56-4a42-a1ee-1b09284065a5",
     "Chat Search Connectors: Add HubSpot & custom MCP connectors for Pro users",
     "Pro users can now use chat search with HubSpot and custom connectors built on Model Context Protocol, expanding the chat search connector ecosystem beyond the initial cloud storage integrations to include CRM and custom data sources.\nThis feature is currently limited to users located outside of the EEA, Switzerland, and the UK, and extends HubSpot and MCP connector support from deep research into regular chat search workflows.\nThe addition of MCP support for chat search is particularly significant as it allows organizations to connect proprietary systems to everyday ChatGPT conversations, not just deep research sessions."),

    ("ee3a97e3-2dfb-4f82-ae39-533ae87904ef",
     "Connectors: Add Canva & Notion for chat search & deep research for Pro users",
     "Pro users can now connect to Canva and Notion for both regular chat search and deep research, enabling direct access to design assets and knowledge base content within ChatGPT conversations.\nThis feature is currently limited to users located outside of the EEA, Switzerland, and the UK and adds two new integrations to the growing list of supported third-party connectors.\nThe addition of Canva and Notion expands the connector ecosystem beyond traditional cloud storage and productivity tools into design and knowledge management platforms, broadening the types of workflows ChatGPT can support."),

    ("1423386d-c65b-43e7-91a6-c52cc0691185",
     "ChatGPT Study Mode: Launch interactive Socratic learning experience for all users",
     "ChatGPT introduces Study Mode, a new interactive learning experience that uses Socratic-style questioning to help users build deeper understanding of any topic by guiding them toward answers rather than providing them directly.\nStudy Mode is available to Free, Plus, Pro, and Teams users globally across iOS, Android, web, and desktop, with Edu plans expanding in coming weeks; it personalizes responses using memory, supports uploaded images and PDFs, and works with any available model.\nStudy Mode is powered by custom system instructions rather than dedicated model training, meaning behavior may be inconsistent across conversations; OpenAI plans to train this behavior directly into main models after learning what works best through iteration and user feedback."),

    ("29c41eaf-d801-485a-bf95-18b0e73bae36",
     "ChatGPT Voice: Expand access, add Custom GPT support & retire Standard Voice",
     "ChatGPT Voice receives major updates including near-unlimited use for Plus users, expanded hours for Free users, Custom GPT integration, and the announcement that Standard Voice Mode will be retired in 30 days to unify all users onto the latest voice experience.\nFor paid users, Voice now adapts to instructions by adjusting speaking style including length, speed, and tone to fit the moment, making it more flexible and context-aware for different conversational needs.\nThe retirement of Standard Voice Mode represents a significant simplification of ChatGPT's voice offerings, consolidating two separate voice experiences into a single unified Advanced Voice interface for all users."),

    ("8e133194-90e0-4e31-8ba5-ed6bc341a70c",
     "ChatGPT: Add customizable accent colors for conversation UI",
     "ChatGPT now allows users to set a custom accent color that applies across the interface, including conversation bubbles, the Voice button, and highlighted text, adding a new layer of visual personalization.\nOn web, the setting is available under the profile icon in Settings under the General tab via the Accent color dropdown; on iOS and Android, it is found under the profile icon in Personalization under Color Scheme.\nThis is a cosmetic personalization feature that complements the existing theme and display settings, giving users more control over the visual identity of their ChatGPT interface."),

    ("04b3a06b-2273-453c-be0c-bf8d500f13a5",
     "ChatGPT: Launch four distinct personality options for response style",
     "ChatGPT introduces four distinct personality options alongside the Default personality in the Customize ChatGPT settings, allowing users to choose how ChatGPT communicates with them across different conversational styles and tones.\nThe four new personalities are Cynic (sarcastic and blunt with wit), Robot (precise and emotionless), Listener (warm and reflective with calm clarity), and Nerd (playful and curious with clear explanations); these personalities do not apply to Voice mode.\nThis feature gives users direct control over ChatGPT's conversational persona, moving beyond system-prompt customization to offer predefined style profiles that can be selected with a single setting change."),

    ("cda28a5c-4b34-4ae0-879b-e57055f6c4df",
     "GPT-5: Launch unified flagship model as new default for all ChatGPT users",
     "GPT-5 is rolling out to all ChatGPT users on Plus, Pro, Team, and Free plans worldwide across web, mobile, and desktop as the new default flagship model, replacing the previous multi-model system with a single auto-switching architecture that combines the best of previous models.\nPaid users on Plus, Pro, and Team tiers have access to the model picker to manually select GPT-5 or GPT-5 Thinking, while Pro and Team users additionally get GPT-5 Thinking Pro for complex tasks requiring higher accuracy; Enterprise and Edu plans will receive access soon.\nGPT-5 represents a fundamental shift in ChatGPT's model architecture from multiple specialized models to a single smart and fast unified model, simplifying the user experience while maintaining top-tier performance across all task types."),

    ("53c6b0d3-2a32-4d9b-9dee-430c53a7d99d",
     "ChatGPT Images: Improve generation efficiency for Free tier users",
     "OpenAI rolls out a small update to image generation for ChatGPT Free tier users that makes its performance more efficient, improving the speed or resource usage of image creation for non-paying users.\nNo additional details were provided in the release note regarding specific changes to image quality, supported formats, rate limits, or the technical nature of the efficiency improvement.\nThis incremental update suggests ongoing optimization of the image generation pipeline for Free tier users, who typically face more constrained rate limits and feature access compared to paid plans."),

    # --- batch 3: events 51-75 (2025-08-11 to 2025-10-13) ---
    ("bdf2ddf0-3bc5-4262-8f30-c47aff95bb2d",
     "ChatGPT Connectors: Expand Plus & Pro chat connectors with Box, Dropbox & more",
     "ChatGPT expands connector availability so Plus users can now search Box, Canva, Dropbox, HubSpot, Notion, Microsoft SharePoint, and Microsoft Teams directly in chat, while Pro users gain Microsoft Teams and GitHub.\nRollout begins immediately with all eligible accounts gaining access in the coming days; connectors are enabled via Settings, Connectors, Connect and remain in beta with Enterprise and Edu plans defaulted off, requiring admin activation.\nConnectors were previously limited to deep research usage, and this expansion brings them into regular chat for the first time on Plus and Pro tiers; availability excludes EEA, Switzerland, and the UK."),

    ("fb893bd0-e209-4e8b-bc4c-2d65ed8d0c0d",
     "ChatGPT Connectors: Launch Gmail, Google Calendar & Contacts for Pro users in chat",
     "ChatGPT adds Gmail, Google Calendar, and Google Contacts as connectors that Pro users can enable for automatic referencing in regular chat conversations, eliminating the need to manually select them each time.\nThis capability is part of GPT-5 and begins rolling out to Pro users globally this week, with Plus, Team, Enterprise, and Edu plans following in coming weeks; users who already have Gmail or Google Calendar enabled for deep research can now also use them in chat.\nFor deep research, each connector must still be enabled separately and selected per request; this update represents the first time Google workspace connectors are available in standard chat mode alongside the existing deep research integration."),

    ("89ad1d05-58ca-467e-bcb9-a1b12eeb5e8d",
     "GPT-5: Add Auto/Fast/Thinking mode selector & increase Plus rate limits",
     "GPT-5 now offers three selectable modes in the model picker, Auto, Fast, and Thinking, giving users explicit control over reasoning depth and response speed for each conversation.\nChatGPT Plus users receive 3,000 messages per week with GPT-5 Thinking and overflow capacity on GPT-5 Thinking mini, with a 196k token context limit; GPT-4o returns to the model picker for all paid users by default alongside a new Show additional models toggle exposing o3, o4-mini, 4.1, and GPT-5 Thinking mini.\nThis update responds to user demand for more granular model control and restores access to legacy models that were previously removed from the picker; GPT-4.5 remains exclusive to Pro users due to GPU constraints."),

    ("f2e07409-f1bb-4fa1-88f2-a6039921fb13",
     "ChatGPT Connectors: Expand Gmail, Google Calendar & Contacts to Plus users",
     "Gmail, Google Calendar, and Google Contacts connectors in ChatGPT are now available to Plus users globally, with access being granted to all eligible accounts throughout the day of the announcement.\nThis expansion follows the initial Pro-only launch on August 12, 2025, and extends the same automatic referencing capabilities in chat that Pro users received the previous day.\nThe rollout to Plus users represents the second phase of Google workspace connector availability, with Team, Enterprise, and Edu plans expected to follow in coming weeks as announced in the original Pro launch."),

    ("dec54402-6fea-4b84-8973-336ac01dfd5d",
     "GPT-5: Update default personality to be warmer & more approachable",
     "OpenAI updates GPT-5's default personality to be warmer and more familiar, responding to user feedback that the initial version felt too reserved and professional in everyday conversations.\nThe warmth adjustments include small acknowledgements like Good question or Great start and brief recognition of user circumstances; OpenAI distinguishes this from sycophancy, defined as excessive insincere flattery, and confirms internal evals show no increase in sycophantic behavior compared to the previous personality.\nThis change addresses a top user complaint since GPT-5's launch and continues OpenAI's ongoing research challenge of balancing warmth with authenticity; further personality updates are planned as the team iterates on the model's conversational style."),

    ("8c301fea-e37c-42f7-94db-9570a1fc30b7",
     "ChatGPT Go: Launch low-cost subscription plan in India at 399 rupees per month",
     "OpenAI launches ChatGPT Go, a new low-cost subscription plan initially available exclusively in India, priced at 399 rupees per month including GST for users seeking more capability than the free tier.\nChatGPT Go includes everything in the Free plan plus more messages, larger file uploads, expanded image generation, access to advanced data analysis, and longer memory for more personalized responses; it is available on web, mobile for iOS and Android, and desktop for macOS and Windows.\nThis geo-restricted launch in India marks OpenAI's first region-specific affordable tier, targeting price-sensitive markets where the standard Plus subscription may be cost-prohibitive; subscriptions can be made via credit card or UPI."),

    ("2ee74e3d-2f44-4816-9032-88face517a6d",
     "ChatGPT Projects: Add project-only memory for focused, self-contained workspaces",
     "ChatGPT introduces project-only memory as a new option when creating projects, allowing users to create focused self-contained workspaces where the model uses only conversations within that project for context and ignores saved memories from outside.\nWith project-only memory enabled, ChatGPT will not carry anything from the project into future chats outside of it, creating isolation useful for long-running or sensitive work; Personal Memory must be enabled in Settings for the feature to function.\nThis feature is initially available only on the ChatGPT website and Windows app, with support for mobile on iOS and Android and the macOS app following in coming weeks; it addresses user requests for better context separation between different work streams."),

    ("fff63217-0535-4a33-aeb1-d5f9881929d2",
     "Codex: Expand to IDE, CLI sign-in & GitHub code reviews for Plus and Pro",
     "Codex now works across terminals, IDEs, the web, GitHub, and the ChatGPT iOS app, with a unified ChatGPT account connecting all environments so developers can work seamlessly between local and cloud without losing state.\nKey updates include a new IDE extension for VS Code, Cursor, and other VS Code forks for previewing local changes, ChatGPT sign-in for both IDE and CLI eliminating API key setup, seamless local-to-cloud task handoff, a refreshed CLI with new commands and bug fixes, and automatic code reviews on GitHub PRs with the ability to mention @codex for reviews and suggested fixes.\nAll future Codex product information and updates will be announced on the new developers.openai.com/codex site, consolidating documentation and guides for getting started with Codex across all supported environments."),

    ("4f00882a-1b4e-49ae-9d78-878ef420d26d",
     "ChatGPT Projects: Expand to Free tier with updated file upload limits across all plans",
     "ChatGPT Projects, which bring chats and files into one organized place, are now available on the Free tier with support for up to five file uploads per project, extending a previously paid-only feature to all users.\nFile upload limits have been updated across all paid tiers: Plus, Go, and Edu now support up to 25 files per project, while Pro, Business, and Enterprise support up to 40 files per project; new customization options including colors and icons are available for all plans.\nThis expansion to the Free tier significantly broadens project accessibility and follows the recent addition of project-only memory, continuing OpenAI's strategy of making organizational features available across all subscription levels."),

    ("de5e87a4-e97a-4f2b-ad82-a67d1779ca21",
     "ChatGPT Web: Add conversation branching to explore alternate directions",
     "ChatGPT now supports conversation branching on the web, allowing users to start a separate conversation from any message point without losing the original thread, enabling exploration of different response directions.\nTo use the feature, users hover over any message, click the More actions menu represented by three dots, and select Branch in new chat to create a new conversation starting from that point in the original thread.\nThis feature is available immediately for all logged-in users on the web platform and addresses a long-requested capability for users who want to explore alternative approaches or follow up on specific points without disrupting their main conversation flow."),

    ("02856521-f60c-4549-a7a0-e580630fdf13",
     "ChatGPT Voice: Retain Standard Voice mode & expand Advanced Voice access",
     "OpenAI reverses the planned retirement of Standard Voice Mode, deciding to keep it available after hearing user feedback that Standard Voice holds special value for some users and the transition to Advanced Voice needs further refinement.\nAdvanced Voice Mode access has been expanded from minutes per day to hours for Free users and near-unlimited use for Plus users; Standard Voice was originally scheduled for retirement following a 30-day sunset period announced the previous month.\nThis decision reflects OpenAI's responsiveness to community feedback and signals that more improvements to Voice capabilities are coming soon, with the goal of ensuring the eventual transition from Standard to Advanced Voice feels right for all users."),

    ("ac18ef2d-37a2-4821-9b1e-f945e440b4bb",
     "Codex: Introduce GPT-5-Codex model optimized for agentic coding tasks",
     "OpenAI introduces GPT-5-Codex, a GPT-5 variant specifically optimized for agentic coding tasks within Codex, available as the default model for cloud tasks and code review and selectable for local workflows via the CLI and IDE extension.\nGPT-5-Codex is designed for coding-focused work in Codex and Codex-like environments, while standard GPT-5 remains the recommended choice for general non-coding tasks; the model is not currently supported in ChatGPT or the API.\nThis specialized variant represents OpenAI's strategy of creating task-optimized model derivatives, similar to how GPT-4o mini serves specific use cases, and follows the recent Codex expansion to IDE extensions, CLI sign-in, and GitHub code reviews for Plus and Pro users."),

    ("3fb936a9-78a5-4625-aeca-a7f51c0c24d7",
     "ChatGPT Settings: Move personalization controls into unified Settings panel",
     "ChatGPT consolidates personalization management by moving it from a separate modal into the main Settings panel, allowing users to manage personalization, choose a ChatGPT personality, add custom instructions, and update Memory all from Settings then Personalization.\nThe change streamlines the user experience by reducing the number of separate interfaces needed to configure ChatGPT behavior, placing all personalization options alongside other account settings in a single unified location.\nThis UI consolidation follows other recent settings improvements and reflects OpenAI's ongoing effort to simplify navigation as ChatGPT gains more configurable features like project-only memory, personality adjustments, and expanded custom instructions."),

    ("b136a8f8-5373-4fbe-9571-29b68fc9f68e",
     "ChatGPT Search: Improve factuality, shopping detection & answer formatting",
     "ChatGPT search receives further improvements focused on three key areas: reduced hallucinations for better factuality, improved shopping intent detection that shows products only when relevant, and better answer formatting for quick understanding without sacrificing detail.\nThe factuality improvements reduce incorrect information in search-grounded answers, while the shopping detection update ensures product results appear when users have purchasing intent and stay hidden during general informational queries to keep results focused.\nThese search quality improvements continue OpenAI's ongoing investment in making ChatGPT a more reliable alternative to traditional search engines, building on previous search updates that added source citations and expanded web browsing capabilities."),

    ("aa1aba04-ac0b-4987-8631-ac80437b4f43",
     "GPT-5 Thinking: Add four-level thinking time toggle for Plus, Business & Pro users",
     "ChatGPT introduces a thinking time toggle in the message composer for GPT-5 Thinking mode, giving Plus, Business, and Pro users explicit control over how long the model reasons before responding, balancing speed against depth.\nPlus and Business users can choose between Standard, the new default balancing speed and intelligence, and Extended, the previous default; Pro users get two additional options with Light for the fastest responses and Heavy for the deepest reasoning on difficult questions.\nThe toggle is live on chatgpt.com with web preferences not yet syncing to mobile; iOS and Android support is planned for coming weeks, addressing user feedback that GPT-5 Thinking responses sometimes took longer than desired for simpler queries."),

    ("72ededa7-1111-4904-979b-39ed49f8940c",
     "Advanced Voice: Improve quality & reduce latency for GPT-4o mini powered mode",
     "OpenAI improves the quality and latency of responses for the version of Advanced Voice Mode that is powered by GPT-4o mini, delivering faster and higher-quality voice interactions for users on that model variant.\nNo additional details were provided in the release note regarding specific latency reduction metrics, affected platforms, or rollout timeline for the quality and latency improvements to the GPT-4o mini voice experience.\nThis update targets the GPT-4o mini variant of Advanced Voice, which serves as a lighter-weight alternative to the full Advanced Voice experience, and follows the recent decision to retain Standard Voice Mode while continuing to improve Advanced Voice capabilities."),

    ("52dfd0d8-a99f-4869-a12f-941377762a12",
     "ChatGPT Go: Expand low-cost subscription plan to Indonesia at Rp 75,000 per month",
     "ChatGPT Go, OpenAI's low-cost subscription plan, launches in Indonesia at Rp 75,000 per month, marking the second country to receive the affordable tier after India's initial launch in August 2025.\nThe plan includes everything in the Free tier plus more messages, larger file uploads, expanded image generation, access to advanced data analysis, and longer memory for more personalized responses; it is available on web, mobile for iOS and Android, and desktop for macOS and Windows.\nThis expansion to Indonesia continues OpenAI's strategy of launching region-specific affordable subscription tiers in price-sensitive markets across Asia, following the successful India launch approximately one month earlier."),

    ("2ddddcb1-11bc-4541-bea5-82af85922b2f",
     "ChatGPT Pulse: Launch daily personalized briefing experience for Pro users on mobile",
     "OpenAI launches ChatGPT Pulse as an early preview for Pro users on iOS and Android, a new experience where ChatGPT proactively delivers personalized focused updates once daily based on asynchronous overnight research synthesizing the user's memory, chat history, and direct feedback.\nUpdates are delivered as visual summaries users can scan at a glance or dive deeper into, with each topic opening into more detail for follow-up questions; users can shape content with thumbs up or down ratings or the curate feature, and save any item into a chat for future reference.\nAs a preview feature, Pulse has limitations including occasionally showing irrelevant suggestions such as tips for already-completed projects; it requires saved memory and chat history to be enabled and can be switched off anytime in settings, representing ChatGPT's first proactive information delivery feature."),

    ("a0737c4e-d8e9-4673-9d6a-4897eae2f720",
     "ChatGPT Shopping: Launch Instant Checkout & Agentic Commerce Protocol with Stripe",
     "OpenAI introduces Instant Checkout in ChatGPT and the Agentic Commerce Protocol built with Stripe, enabling users to purchase products directly within chat conversations starting with U.S. Etsy sellers, with over one million Shopify merchants coming soon.\nInstant Checkout works by ChatGPT finding organic unsponsored product results, ranking merchants by inventory, price, quality, and primary seller status, then allowing users to confirm shipping and payment details and pay in one tap; payment goes directly from the user to the merchant, not through OpenAI, and users must give explicit confirmation.\nThe Agentic Commerce Protocol gives merchants and developers a standardized way to build agentic commerce experiences connecting to ChatGPT's 700 million plus weekly active users; this represents OpenAI's first direct commerce integration and is available to Plus, Pro, and Free users in the United States."),

    ("8fe1bbe0-acce-4e58-b2ba-198bbaee2ea5",
     "ChatGPT: Launch global parental controls with content protections & usage limits",
     "OpenAI rolls out parental controls globally in ChatGPT, allowing parents or guardians to connect accounts with their teens and manage settings including content protections, feature restrictions, and usage limits starting on the web with mobile support coming soon.\nParents can set quiet hours, disable voice mode, turn off memory, remove image generation, and opt out of model training for their teen's account; connected teens automatically receive additional content protections such as reduced graphic content and viral challenge filtering which parents can optionally disable.\nParents do not have access to their teen's conversations except in rare cases where the system and trained reviewers detect possible signs of serious safety risk, in which case parents may be notified by email, SMS, or push notification with only the information needed to support their teen's safety."),

    ("0bd52ecb-4544-4816-a333-f6b852a4547e",
     "GPT-5 Instant: Update distress detection & crisis response with expert guidance",
     "OpenAI updates GPT-5 Instant to better recognize and support people in moments of distress, training the model to more accurately detect and respond to potential signs of mental and emotional distress with guidance from mental health experts for de-escalation and crisis resource referral.\nGPT-5 Instant now performs as well as GPT-5 Thinking on distress-related questions, and when GPT-5 Auto or a non-reasoning model is selected, the real-time router directs sensitive conversation parts to GPT-5 Instant for faster helpful responses; ChatGPT continues to tell users which model is active when asked.\nThis safety-focused update builds on OpenAI's recently shared approach of using real-time routing to direct sensitive conversations to appropriate models, and represents ongoing efforts to make GPT-5 both smarter and safer across all interaction modes."),

    ("53e5a5a3-6afb-4c2d-90e5-1cd9ccc3acff",
     "Codex: Add Slack integration, SDK for programmatic control & updated rate pricing",
     "Codex expands its platform capabilities with three key updates: Slack integration for team collaboration, a new Codex SDK for programmatic control of coding tasks, and updated rate pricing for Codex usage across supported plans.\nNo additional details were provided in the release note regarding specific SDK capabilities, Slack integration features, or the nature of the rate changes; users are directed to the Help Center article on Codex and the Codex developer documentation for more information.\nThese updates continue the rapid expansion of Codex's integration footprint following the recent additions of IDE extensions, CLI sign-in, GitHub code reviews, and the GPT-5-Codex model, positioning Codex as a comprehensive multi-platform coding assistant."),

    ("19253066-7f02-4e22-bfb1-199fdb86c2ea",
     "ChatGPT Go: Expand to 16 additional countries with platform-specific availability",
     "ChatGPT Go, OpenAI's low-cost subscription plan, expands to 16 additional countries, significantly broadening the affordable tier's global availability beyond the initial launches in India and Indonesia.\nThe plan includes everything in the Free tier plus more messages, larger file uploads, expanded image generation, advanced data analysis, and longer memory; it is available on web, mobile for iOS and Android, and desktop for macOS and Windows, with the exception that iOS subscriptions are not currently available in Cambodia, Laos, and Nepal.\nThis major geographic expansion marks the largest single rollout of ChatGPT Go since its India debut in August 2025, continuing OpenAI's strategy of making ChatGPT more accessible in price-sensitive markets across multiple regions."),

    ("faa1fd1e-341f-4c6f-8e2e-fce09f0f2f10",
     "ChatGPT Connectors: Add Notion & Linear as synced connectors for Pro users",
     "ChatGPT adds Notion and Linear as synced connectors for Pro users, enabling secure indexing of Notion pages and Linear issues and discussions so ChatGPT can automatically reference the content when relevant in chat conversations.\nUsers can enable sync for Notion and Linear from their Connector settings after first connecting to each service; once synced, ChatGPT indexes the content and automatically references it when relevant, eliminating the need to manually paste or upload information from these project management tools.\nThis addition expands the growing list of synced connectors available to Pro users and brings two widely-used productivity tools into ChatGPT's automatic context system, following earlier connector launches for Google Workspace, Slack, and other enterprise services."),

    ("eb4a8cad-fd80-4e80-a7a5-91ac075ca11b",
     "ChatGPT Slack: Launch bidirectional Slack connector & dedicated ChatGPT app for Slack",
     "OpenAI introduces two new Slack integrations: a connector that brings Slack context into ChatGPT conversations including chat, Deep Research, and Agent Mode, and a dedicated ChatGPT app for Slack that enables one-on-one chat with ChatGPT in a dedicated sidebar within the Slack interface.\nThe ChatGPT app for Slack supports summarizing threads into action items, drafting replies, and searching accessible messages and files, with semantic search available for Slack Business+ or Enterprise+ plans with AI enabled and keyword search for all other plans; chats started in Slack also appear in the ChatGPT sidebar for cross-platform continuity.\nBoth integrations are available to Plus, Pro, Business, and Enterprise or Education customers, with the app requiring a paid Slack account and the connector needing to be enabled before app installation; this represents ChatGPT's deepest enterprise messaging integration to date."),

    # --- batch 4: events 76-100 (2025-10-14 to 2025-12-18) ---
    ("a3ee1772-92cb-4312-aba4-d2c9b0e18115",
     "ChatGPT Go: Expand low-cost plan to 89 countries with 71 new additions",
     "ChatGPT Go, OpenAI's low-cost subscription plan, is now available in 71 additional countries, bringing total global coverage to 89 countries for affordable AI access.\nThe plan includes everything in the Free tier plus more messages, larger file uploads, expanded image generation, advanced data analysis, and longer memory for more personalized responses across web, mobile, and desktop.\nChatGPT Go subscriptions are temporarily unavailable on iOS in Cambodia, Laos, and Nepal, though web and Android subscriptions remain accessible in those regions."),

    ("90e3d1dd-c54d-479b-a67e-1bd52a6f03e8",
     "ChatGPT Memory: Add automatic memory management with prioritization & search",
     "ChatGPT now automatically manages saved memories by keeping the most relevant details prioritized and moving less important ones to the background, preventing the memory-full state.\nThe system considers factors like recency and conversation frequency to decide which memories stay top of mind, and users can now search saved memories and sort them by newest or oldest.\nUsers retain full control and can turn off automatic management, manually prioritize or deprioritize specific memories, and view or restore prior versions; the feature is rolling out to Plus and Pro users globally on web."),

    ("5290706c-8569-4348-adfc-c130f05fa729",
     "GPT-5 Instant: Upgrade default model for signed-out users",
     "OpenAI updates the default model for signed-out ChatGPT users to GPT-5 Instant, giving unauthenticated visitors access to higher-quality responses without requiring an account.\nThis change applies to all users who access ChatGPT without logging in, upgrading them from the previous default model to the more capable GPT-5 Instant variant.\nThe move broadens access to GPT-5 level intelligence for casual and first-time users, aligning with OpenAI's strategy to showcase stronger model capabilities to a wider audience."),

    ("e10bfc3b-5e3f-4f77-923b-08c7de49a22c",
     "ChatGPT Projects: Launch shared projects for collaborative AI workflows",
     "ChatGPT now supports shared projects, allowing users to collaborate by sharing chats, uploaded files, and custom instructions so that responses are informed by the group's collective knowledge.\nProject sharing is available to all plans globally on web, iOS, and Android with varying limits: Pro users get up to 40 files and 100 collaborators, Plus and Go users get 25 files and 10 collaborators, and Free users get 5 files and 5 collaborators.\nOwners can set visibility to invite-only or anyone with a link and change settings at any time; use cases include group work, content creation, reporting, and collaborative research."),

    ("790083fc-78ef-4c40-8563-7441258c663f",
     "ChatGPT Go: Launch low-cost subscription plan in Brazil",
     "ChatGPT Go, OpenAI's low-cost subscription plan, is now launching in Brazil, giving Brazilian users access to an affordable tier beyond the free plan.\nThe plan includes everything in the Free tier plus more messages, larger file uploads, expanded image generation, advanced data analysis, and longer memory for more personalized responses.\nChatGPT Go is available on web, mobile for iOS and Android, and desktop for macOS and Windows; Brazil joins the growing list of countries with access to this affordable plan."),

    ("80e6e864-0f19-42fc-a7cc-72b3184ecf4c",
     "ChatGPT Pulse: Launch proactive daily research summaries on web",
     "ChatGPT Pulse is now available on web and rolling out to Atlas for Pro users, delivering asynchronous research based on past chats, memory, and feedback once a day.\nPulse proactively generates visual summaries that users can scan at a glance, expand for more detail, save for later, or use as a starting point for follow-up questions the next day.\nThis feature represents a shift toward proactive AI assistance where ChatGPT initiates helpful research rather than waiting for user prompts, currently exclusive to Pro plan subscribers."),

    ("912be4dd-daa0-46b5-b5ee-6f7bf7929f5b",
     "Codex & Sora: Introduce purchasable credits for flexible usage beyond plan limits",
     "OpenAI introduces purchasable credits for additional usage in Codex and Sora, allowing users who hit their included limits to seamlessly buy more capacity directly within each product.\nUsers can purchase additional credits from the Codex dashboard or buy more video generations in the Sora app, available across Free, Go, Plus, and Pro plans.\nThis marks OpenAI's move toward a consumption-based pricing layer on top of existing subscriptions, giving power users a way to continue working without waiting for limit resets."),

    ("cc07b4a4-f379-4ad2-9576-a274aa981f93",
     "ChatGPT Go: Expand to 8 European countries reaching 98 total",
     "ChatGPT Go expands to eight additional European countries including Austria, Czech Republic, Denmark, Norway, Poland, Portugal, Spain, and Sweden, bringing total global coverage to 98 countries.\nThe plan includes everything in the Free tier plus more messages, larger file uploads, expanded image generation, advanced data analysis, and longer memory for personalized responses across all platforms.\nThis European expansion follows the earlier rollout to 71 countries in October 2025 and the Brazil launch, continuing OpenAI's strategy to make affordable AI access available worldwide."),

    ("acbc4d2b-3532-4d90-9fb6-86aeaf080177",
     "ChatGPT Go India: Launch free 12-month promotional offer for eligible users",
     "Eligible customers in India can redeem 12 months of ChatGPT Go at no cost, available to new users, free plan users, and current ChatGPT Go subscribers with one redemption per account.\nRedemption is available on ChatGPT web and the Android app via Google Play, with the Apple App Store option arriving the following week; a payment method such as credit card or UPI is required.\nExisting ChatGPT Go subscribers may receive the promotion automatically at the end of their billing cycle; as of January 21, 2026, the promotional offer has ended."),

    ("a8d87aba-b7b9-4fc7-b59e-90b71c2ae5d2",
     "ChatGPT: Add mid-query interrupt to refine long-running requests without restart",
     "ChatGPT now allows users to interrupt long-running queries such as deep research or GPT-5 Pro to refine their request mid-stream without restarting or losing progress.\nUsers can click an update button in the sidebar and send new information as a message, and the model will adjust its approach based on the updated requirements in real time.\nThis feature addresses a common frustration where users had to wait for lengthy queries to complete before correcting or adding context, making complex research workflows significantly more flexible."),

    ("e2d1e7ef-7291-43cc-81bb-4c5c4604c29c",
     "ChatGPT Personalization: Apply custom instructions to all existing chats instantly",
     "Changes to ChatGPT personality or custom instructions now apply immediately across all conversations, including existing ones, eliminating the need to start a new thread for updated settings.\nPreviously, any modifications to personalization settings in Settings then Personalization only took effect in newly created conversations, leaving older chats with outdated instructions.\nThis quality-of-life update ensures a consistent experience across the entire chat history and addresses a long-standing user request for retroactive personalization changes."),

    ("014bbb52-78e6-443e-b27f-cc973186bf70",
     "ChatGPT Tone: Add updated presets & granular controls for response style",
     "ChatGPT introduces updated tone presets including Default, Friendly, Efficient, Professional, Candid, and Quirky, with Cynical and Nerdy still available, plus experimental granular controls over conciseness, warmth, scannability, and emoji frequency.\nPersonalization changes now apply across all chats immediately including existing conversations, and GPT-5.1 models follow custom instructions and style preferences more reliably than previous versions.\nThis update builds on the earlier personalization improvement that made settings retroactive, expanding the range of customization options and improving model adherence to user-defined communication preferences."),

    ("dc8cb2b1-8f3e-49fd-8f95-5bafb480fc79",
     "GPT-5.1: Launch Instant & Thinking upgrades with adaptive reasoning",
     "OpenAI updates GPT-5 to GPT-5.1 Instant and GPT-5.1 Thinking, delivering smarter and more conversational answers with light adaptive reasoning for tough questions on Instant and more precise thinking-time allocation on Thinking.\nGPT-5.1 rolls out first to paid users including Pro, Plus, Go, and Business, then to free and logged-out users, with Enterprise and Edu receiving a temporary early-access toggle; API availability follows as gpt-5.1-chat-latest and gpt-5.1.\nGPT-5 models remain accessible for three months under the Legacy models dropdown, and GPT-5.1 Auto continues to route each query to the best model, ensuring a smooth transition path for all users."),

    ("29fe2e60-1205-4821-b1d4-989050df4266",
     "ChatGPT: Pilot group chats for multi-user conversations in four countries",
     "ChatGPT begins piloting group chats that allow multiple users and ChatGPT to participate in the same conversation for collaborative planning, decision-making, and project work.\nThe pilot is rolling out on ChatGPT Web, iOS, and Android in New Zealand, Japan, South Korea, and Taiwan, with early feedback informing future expansion to more regions and plans.\nThis marks ChatGPT's first multi-user real-time chat feature, enabling collaborative use cases where ChatGPT helps with search, summarization, content generation, and keeping all participants aligned."),

    ("a3a71ad3-32e0-4bc9-8315-e1bfa333128e",
     "GPT-5.1 Pro: Launch upgraded model with improved clarity & complex task performance",
     "OpenAI updates GPT-5 Pro to GPT-5.1 Pro, with early testers consistently preferring it over GPT-5 Pro, rating it especially highly for writing help, data science, and business questions.\nGPT-5.1 Pro is available immediately for all ChatGPT Pro users in the model picker, while GPT-5 Pro remains accessible as a legacy model for 90 days before retirement.\nTesters highlighted improved clarity, relevance, and structure in responses, continuing the GPT-5.1 series rollout that previously brought Instant and Thinking upgrades to all paid tiers."),

    ("b10b316a-b644-486f-b5aa-f186e0ecc07d",
     "ChatGPT Shopping: Launch Instant Checkout with Shopify merchants",
     "ChatGPT now supports Instant Checkout with Shopify merchants starting with Spanx, Skims, and Glossier, allowing users to complete purchases directly within the chat interface.\nWhen a product from a supported Shopify merchant is available, users can confirm shipping and payment details and buy without leaving the conversation; the feature is available for logged-in Plus, Pro, and Free users in the US.\nThis expands ChatGPT's commerce capabilities from product recommendations to end-to-end purchasing, deepening the integration between conversational AI and e-commerce transactions."),

    ("ae410456-4887-495a-bb5f-effa0901283f",
     "ChatGPT Responses: Add inline web images for visual context in answers",
     "ChatGPT now includes more inline images from the web alongside text responses to help users quickly understand topics like well-known people, places, and products with visual context.\nImages are placed beside relevant paragraphs when visuals add clarity, and users can click any image to view it in original dimensions with source attribution; the feature works with GPT-5.1 responses.\nThese improvements are gradually rolling out globally across all ChatGPT plans on web, iOS, and Android, enhancing the richness of conversational answers with contextual visual information."),

    ("983aff63-9d0d-49ba-ae60-11a09f81ba0d",
     "ChatGPT Shopping Research: Launch interactive product discovery & buyer's guides",
     "ChatGPT introduces Shopping Research, an interactive experience that helps users find products by asking clarifying questions, researching across the internet, reviewing quality sources, and building personalized buyer's guides.\nThe feature is available on ChatGPT Web, iOS, and Android for logged-in Free, Go, Plus, and Pro users, with nearly unlimited usage across plans through the holiday season to assist with seasonal shopping.\nShopping Research leverages past conversations and memory to deliver personalized recommendations with options, tradeoffs, and purchase links, marking a significant expansion of ChatGPT's commerce and product discovery capabilities."),

    ("8783268f-9809-42a6-bfa6-2c75455550c4",
     "ChatGPT Voice: Integrate voice into main chat with text & visual streaming",
     "ChatGPT Voice is now integrated directly into the main chat interface, allowing users to speak, listen, and see their conversation simultaneously without switching to a separate mode.\nSpoken answers stream alongside text, image search results, and widgets like maps and weather in the same chat thread; users can type back when they cannot talk, share photos to discuss aloud, and refer back to earlier messages without interruption.\nThis update rolls out to all users globally on the ChatGPT mobile app and chatgpt.com; users who prefer the original standalone Voice experience can switch back anytime by enabling Separate mode in Settings."),

    ("5fbe1721-aa9f-4b88-946f-7cec3b3035c3",
     "GPT-5.2: Launch smarter GPT-5 series upgrade for work & learning",
     "OpenAI releases GPT-5.2 as the next upgrade in the GPT-5 series, offering improved intelligence and usefulness for work and learning while retaining the conversational tone introduced in GPT-5.1.\nGPT-5.2 Instant improves info-seeking, how-tos, technical writing, and translation; GPT-5.2 Thinking excels at spreadsheet formatting, financial modeling, coding, and long document summarization; GPT-5.2 Pro delivers fewer major errors across complex domains; all three share an August 2025 knowledge cutoff.\nAutomatic model switching for reasoning is removed for free and Go users who now default to GPT-5.2 Instant with manual Thinking selection available; this continues OpenAI's pattern of iterative improvements within the GPT-5 generation."),

    ("6cad9b74-8522-4569-a3b5-3066c62fa1fd",
     "ChatGPT macOS: Announce Voice retirement effective January 15, 2026",
     "OpenAI is retiring the Voice experience in the ChatGPT macOS desktop app effective January 15, 2026, to focus development on more unified and improved voice experiences across other platforms.\nVoice will continue to be available on chatgpt.com, iOS, Android, and the Windows app; no other ChatGPT features on macOS are affected by this change.\nThis retirement follows the recent integration of Voice into the main chat interface on other platforms, suggesting a strategic consolidation of voice capabilities away from the standalone macOS implementation."),

    ("158eb6ac-5f43-4b27-bedd-f60a6b30112c",
     "ChatGPT Images: Launch improved image generation on web & mobile with gallery",
     "OpenAI introduces a new and improved version of ChatGPT Images powered by their best image generation model yet, with precise instruction following and editing capabilities for both everyday edits and creative transformations.\nAll generated images are automatically saved under My Images at chatgpt.com/images, providing a single place to browse, revisit, and reuse creations without searching through past conversations; available on Free, Go, Plus, Edu, and Pro plans.\nBusiness and Enterprise plan support is coming soon; this update represents a significant upgrade to ChatGPT's visual creation capabilities, making AI image generation more useful and accessible across consumer tiers."),

    ("29ce9ab9-719a-48e1-99b5-a2baceddcda6",
     "ChatGPT Pulse: Integrate Tasks management into Pulse for Pro users",
     "Tasks, which let users set up automated prompts that ChatGPT runs on their behalf, can now be managed directly within the Pulse interface for a unified experience.\nUsers can see all tasks in one place in Pulse, create tasks either in chat or in Pulse, and edit or review tasks in Pulse at any time after creation for flexible workflow management.\nPulse remains exclusive to ChatGPT Pro users; this integration consolidates proactive AI features by combining daily research summaries with scheduled task management in a single hub."),

    ("6f0a8d16-a3a0-40ed-9cb2-41ec4ac9e61c",
     "ChatGPT: Add pinned chats for quick access across all platforms",
     "ChatGPT now allows users to pin conversations to the top of their chat list for quick access to important or frequently used threads, available on iOS, Android, Web, and Atlas.\nOn web, users can hover over a chat in the left-hand sidebar, click the three-dot menu, and select Pin chat; on mobile, a long-press on any chat reveals the Pin chat option.\nThis quality-of-life feature addresses a common request for better chat organization, making it easier to return to key conversations without scrolling through a long history."),

    ("5fa1428d-8894-495b-aff2-188846a1c3b7",
     "ChatGPT Apps: Launch app directory with third-party integrations & developer submissions",
     "ChatGPT introduces an app directory where users can browse and add approved third-party apps that work directly inside conversations, offering interactive in-chat experiences and secure connections to external services.\nConnectors now appear in the directory as apps under unified terminology, and developers can submit their own apps for review and publication to reach a broader set of ChatGPT users.\nApps are available to all logged-in ChatGPT users with availability and functionality varying by plan and region; this marks a significant platform expansion enabling an ecosystem of third-party integrations within ChatGPT."),

    # --- batch 5: events 101-122 (2025-12-19 to 2026-02-25) ---
    ("78bc7d32-5e6e-4c00-87c2-1a38f129c370",
     "ChatGPT Personalization: Add granular characteristic controls for warmth, enthusiasm & formatting",
     "ChatGPT now allows users to individually adjust specific response characteristics beyond selecting a base style and tone preset, providing more granular control over how the model communicates.\nFrom the personalization pane in settings, users can independently tune warmth level, enthusiasm level, use of headers and lists, and use of emojis, each on a separate sliding scale.\nThis builds on the earlier base style and tone preset system, giving users finer control over ChatGPT's personality without changing their overall style selection."),

    ("dd55201b-b9d4-4f2f-a291-3f4acf76a224",
     "ChatGPT: Launch personalized 2025 year-in-review experience",
     "OpenAI rolls out Your Year with ChatGPT, an optional personalized end-of-year experience that reflects on how users interacted with ChatGPT throughout 2025, highlighting conversation themes and usage statistics.\nThe experience is available to Free, Plus, and Pro users in the United States, United Kingdom, Canada, Australia, and New Zealand, as well as Go, Plus, and Pro users in India, and requires Memory and Reference Chat History to be enabled with a minimum activity threshold.\nThis is a gradual rollout available in English only at launch and is not available on Business, Enterprise, or Edu plans; users with very limited activity will only see basic chat statistics."),

    ("e142b892-81d1-4c7a-ab53-949481d6be94",
     "ChatGPT Health: Launch dedicated space for health & wellness with medical record integration",
     "ChatGPT introduces Health, a dedicated space for health and wellness conversations that securely connects to medical records, Apple Health, and supported wellness apps so answers can be grounded in personal health data.\nHealth appears as a new sidebar space with conversations, memory, and files kept separate from regular ChatGPT and not used for foundation model training; it is available on web and iOS for Free, Go, Plus, and Pro users in supported countries excluding the EEA, Switzerland, and the UK.\nThis marks ChatGPT's first dedicated vertical feature for healthcare, rolling out initially to a small group of early users with a waitlist for broader access and Android support coming soon."),

    ("2f52c662-86bb-46d8-a0ea-8f28d231b866",
     "ChatGPT Dictation: Reduce empty transcriptions & improve accuracy for all users",
     "ChatGPT improves its dictation capabilities for all logged-in users, significantly reducing the occurrence of empty transcriptions and delivering more accurate speech-to-text results across the platform.\nThe update targets the core dictation input feature used when composing messages, addressing reliability issues where transcriptions would sometimes return blank or incomplete results for all user tiers.\nNo additional details were provided in the release note regarding specific accuracy benchmarks or platform availability beyond the improvement applying to all logged-in ChatGPT users."),

    ("e488e0a3-2419-4c13-9aa9-87c59c498426",
     "ChatGPT Memory: Improve detail retrieval from past chats for Plus & Pro users",
     "ChatGPT can now more reliably find specific details from past chats when reference chat history is enabled, with any past chat used to answer a question appearing as a clickable source for reviewing original context.\nThis memory improvement is available globally for Plus and Pro users and surfaces past conversations as cited sources directly within responses, making it easy to open and verify the original context behind retrieved information.\nThis enhancement builds on the reference chat history feature by adding source attribution, addressing user requests for better traceability when ChatGPT draws on previous conversation history."),

    ("d8b5bb91-917e-486b-b5cc-3422e535367a",
     "ChatGPT: Roll out age prediction model with teen safeguards",
     "OpenAI rolls out an age prediction model on ChatGPT consumer plans to determine whether an account likely belongs to someone under 18, enabling the application of appropriate experience settings and safeguards for teen users.\nThe model analyzes behavioral and account-level signals including account age, typical activity times, usage patterns over time, and stated age; adults incorrectly placed in the under-18 experience can verify their age via a selfie through Persona in Settings.\nThis rollout is part of OpenAI's broader effort to implement age-appropriate safety measures on ChatGPT, allowing users to check whether safeguards have been applied and verify their age at any time through the account settings."),

    ("38b495d0-406c-4a1f-874b-a054f95ac3fd",
     "ChatGPT Voice: Improve instruction following & fix custom instruction echo bug",
     "ChatGPT Voice now better follows user instructions and resolves a bug where custom instructions were sometimes repeated back verbatim during voice conversations with paid users.\nThis update targets the standard Voice mode for paid users and does not affect Advanced Voice mode; it addresses both instruction adherence and the specific bug of echoing custom instructions aloud.\nThis is part of ongoing Voice improvements in January 2026, addressing a top user complaint about instruction-following quality and a known bug that exposed custom instruction text during voice sessions."),

    ("525b41f5-329e-4213-85fd-c3764725c001",
     "GPT-5.2 Instant: Update default personality to be more conversational & context-adaptive",
     "OpenAI updates GPT-5.2 Instant's default personality to be more conversational and better at adapting its tone contextually, making exchanges feel smoother and more natural for users across all interactions.\nUsers can still select a different base style and tone for ChatGPT and tune individual characteristics like warmth and emoji use within the Personalization menu in settings, preserving full customization over the updated default.\nThis personality update refines GPT-5.2 Instant's communication style following the December 2025 introduction of detailed characteristic controls, continuing the trend of making model responses feel less robotic and more adaptive."),

    ("fd02701e-7f70-4694-9da9-cf2fd196ba28",
     "ChatGPT Voice: Improve search response quality with better shopping results",
     "ChatGPT Voice now delivers more complete and up-to-date answers when performing search queries, including improved access to shopping results for product-related questions during voice conversations.\nThe improvement applies to search responses specifically within Voice mode, enhancing the quality and freshness of information returned when users ask questions that require real-time web data or shopping comparisons.\nNo additional details were provided in the release note regarding specific platform availability or plan restrictions; this follows the January 20 Voice update that improved instruction following."),

    ("4dd98c36-34d7-4259-9c60-c41107900a30",
     "Legacy Models: Announce retirement of GPT-4o, GPT-4.1 & o4-mini effective Feb 13",
     "OpenAI announces that GPT-4o, GPT-4.1, GPT-4.1 mini, and o4-mini will be retired from ChatGPT on February 13, 2026, alongside the previously announced retirement of GPT-5 Instant and Thinking variants.\nThere are no API changes included in this retirement announcement; the retirement applies only to the ChatGPT consumer product, and users should refer to the associated blog post and help center for migration details.\nThis advance notice gives users two weeks to prepare for the transition; a follow-up announcement on February 13 will confirm the completion of the retirement and consolidation around the GPT-5.2 model series."),

    ("466dffa6-6437-4023-b942-b07741bef4d6",
     "ChatGPT Responses: Add at-a-glance visuals for stats, conversions & quick lookups",
     "ChatGPT responses are now more visual and easier to scan, with everyday questions generating at-a-glance visual elements for tasks like checking sports stats, converting units, or performing quick calculations.\nAnswers now highlight important people, places, products, and ideas with tappable highlights that open a side panel containing key facts and trusted sources, eliminating the need for follow-up questions to understand context.\nThis visual enhancement is rolling out globally on iOS, Android, and web, representing a significant shift in how ChatGPT presents information by moving beyond plain text toward richer inline visual formatting."),

    ("34d48540-40dd-49a6-8f93-32fab3a229fd",
     "Codex App: Launch macOS command center for parallel coding agents",
     "OpenAI releases the Codex app for macOS, a command center for managing multiple coding agents in parallel that supports long-horizon and background tasks, clean diff reviews from isolated worktrees, and reusable skills and automations.\nThe app is available with ChatGPT plans that include Codex access, with a limited-time promotion giving Free and Go users included trial limits and Plus and Pro users double the standard Codex rate limits.\nThis marks the first standalone desktop application for Codex, expanding beyond the browser-based ChatGPT interface to provide developers with a dedicated tool for managing autonomous coding workflows."),

    ("33073ed6-9175-4616-b23f-b86dbb9ab4c6",
     "GPT-5.2 Thinking: Restore Extended thinking level after inadvertent reduction",
     "OpenAI restores the Extended thinking level for GPT-5.2 Thinking to its prior setting on February 4, 2026, correcting an inadvertent reduction that occurred during the January 10 Standard and Light thinking time adjustments.\nThe timeline includes a January 10 reduction of Standard and Light thinking times that unintentionally lowered Extended, a February 3 further Standard reduction based on testing, and the February 4 restoration of Extended to its original level.\nOpenAI periodically adjusts default thinking times based on experiments balancing answer quality and response speed; the thinking level toggle introduced in September 2025 allows users to choose between lighter faster responses and more extended reasoning."),

    ("041aedba-386f-49b1-9199-88515d68e340",
     "ChatGPT Ads: Begin ad test for Free & Go tier users in the U.S.",
     "OpenAI begins testing advertisements in ChatGPT for logged-in adult users on the Free and Go tiers in the United States, starting with a subset of users and expanding over the coming weeks based on learnings.\nPlus, Pro, Business, Enterprise, and Education plans are excluded from ads; ads are clearly labeled as sponsored, visually separated from organic answers, and do not appear in chats about sensitive or regulated topics including health, mental health, or politics.\nThis is OpenAI's first public advertising experiment in ChatGPT, with strong privacy controls ensuring advertisers never see user chats or personal details and users can dismiss ads, delete ad data, and manage personalization at any time."),

    ("69cac6b0-fcdf-4b21-b5c1-750cdfb33739",
     "GPT-5.2 Instant: Improve response style with more measured tone & clearer answers",
     "OpenAI updates GPT-5.2 Instant in both ChatGPT and the API to improve response style and quality, with responses that are more measured and grounded in tone and more contextually appropriate to the conversation.\nThe model now tends to output clearer and more relevant answers to advice-seeking and how-to questions, more reliably placing the most important information upfront rather than burying key details in longer explanations.\nThis update applies to both ChatGPT and the API simultaneously, refining the personality and communication style changes introduced in the January 22 personality system prompt update for GPT-5.2 Instant."),

    ("bc09f506-853e-439e-9a07-28a99daadb84",
     "Deep Research: Add source filtering, editable plans & fullscreen report view",
     "OpenAI introduces improvements to deep research in ChatGPT that enable users to focus research on specific websites and a larger collection of connected apps as trusted sources, producing more accurate and credible reports with greater control.\nA redesigned sidebar entry point and fullscreen report view make it easier to start, review, and manage research in one place, with the ability to create and edit a research plan before it begins and adjust direction mid-run.\nThis update is rolling out to Plus and Pro users first with Free and Go users following in the coming days, building on the existing deep research capability with significantly enhanced user control over the research process."),

    ("8aace443-dd5a-4b11-b6cf-4b6500c5a08c",
     "ChatGPT Voice: Improve instruction following & search tool usage for free-tier model",
     "ChatGPT Voice receives an update that improves its ability to follow user instructions and make better use of tools like web search to provide more accurate and helpful responses during voice conversations.\nThis update applies specifically to the version of Voice primarily used by free ChatGPT plan users and by Plus users when their main model limits are reached, rather than the primary paid-tier Voice experience.\nThis is the second Voice update in early 2026 following the January 20 improvement for paid users, extending similar instruction-following and tool-usage enhancements to the free-tier voice model."),

    ("b1ee794d-0e03-424d-a82c-736e9b49d2d4",
     "ChatGPT Web: Increase file upload limit to 20 & improve long chat reliability",
     "ChatGPT now supports uploading up to 20 files in a single message on web, doubling the previous limit of 10, making it easier to analyze document sets, compare multiple files, or provide broader context in one message.\nAdditional improvements include expanded file type support for text and code formats on web, cleaner Select All behavior for copying chat transcripts, quick tools in the Android composer, a simplified Android composer layout, iOS performance enhancements, and reduced interruption rates in long Thinking chats.\nThese quality-of-life updates span web, iOS, and Android platforms, focusing on power-user workflows and addressing long-standing community requests for better file handling, copying, and reliability during extended sessions."),

    ("b233b59c-a980-4853-b452-9b5c62e2316e",
     "Legacy Models: Complete retirement of GPT-4o, GPT-4.1, o4-mini & GPT-5 from ChatGPT",
     "OpenAI retires GPT-4o, GPT-4.1, GPT-4.1 mini, and o4-mini from ChatGPT effective February 13, 2026, alongside the previously announced retirement of GPT-5 Instant and Thinking variants.\nNo API changes are included in this retirement; API users retain access to these models while ChatGPT users are automatically migrated to GPT-5.2 as the default model going forward.\nThis follows the January 29 advance notice and completes the planned consolidation of the GPT model lineup around the GPT-5.2 series, with GPT-5.2 Thinking replacing all retired reasoning model options."),

    ("14f8201e-f600-43b7-a262-e2acbbbf76bd",
     "ChatGPT Code Blocks: Add inline editing, diagram preview & split-screen view",
     "ChatGPT improves Code Blocks to be more interactive, allowing users to write, edit, and preview code directly within the chat interface in a single integrated experience without switching to external tools.\nNew capabilities include inline text editing within code blocks, direct preview of diagrams and mini applications inside the chat, and split-screen views for reviewing code side by side with conversation context.\nThis enhancement transforms code blocks from static read-only output into an interactive development surface, reducing the need to copy code to external editors for basic modifications and previews."),

    ("a68de45c-c6c5-4209-b886-849d918cdf34",
     "GPT-5.2 Thinking: Expand context window to 256k tokens with 128k input and output",
     "ChatGPT now offers a total context window of 256k tokens when users manually select the Thinking mode, doubling the maximum output capacity with 128k input tokens and 128k max output tokens available.\nThe previous total context window was 196k tokens; the expansion to 256k tokens applies specifically when Thinking is manually selected by the user rather than automatically applied by the system.\nThis context window increase enables significantly longer reasoning chains and more comprehensive outputs for complex tasks, addressing user demand for extended generation capacity in knowledge-intensive and analytical workflows."),

    ("c63438d7-e068-42f7-9e29-7e700f7976ad",
     "ChatGPT Projects: Add sources from apps, chats & ad-hoc text inputs",
     "ChatGPT Projects now makes it easier to build a living knowledge base by adding sources from wherever context already lives, including connected apps, previous conversations, and quick text inputs pasted directly into projects.\nUsers can paste links to Slack channels or Google Drive files and folders as project sources, save useful ChatGPT responses from chats into projects as reusable knowledge, and add ad-hoc text notes, briefs, or reference material for instant context capture.\nThis update significantly expands how users populate project knowledge bases beyond manual document uploads, integrating with external productivity tools and leveraging existing ChatGPT conversation history as a source of reusable context."),
]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def cmd_generate(args: argparse.Namespace) -> None:
    conn = _connect()
    where = "1=1" if args.force else "title_updated IS NULL"
    sql = f"SELECT id, event_date, title, content FROM chatgpt_event WHERE {where} ORDER BY event_date DESC"
    if args.limit > 0:
        sql += f" LIMIT {args.limit}"
    rows = [dict(r) for r in conn.execute(sql).fetchall()]
    conn.close()
    out = open(sys.stdout.fileno(), "w", encoding="utf-8", closefd=False)
    json.dump(rows, out, ensure_ascii=False, indent=2)
    out.flush()
    print(file=sys.stderr)
    print(f"[enrich_chatgpt] {len(rows)} row(s) pending", file=sys.stderr)


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
        title = item.get("title_updated")
        content = item.get("content_updated")
        if not rid or not title or not content:
            print(f"[skip] incomplete: {rid}", file=sys.stderr)
            continue
        conn.execute(
            "UPDATE chatgpt_event SET title_updated = ?, content_updated = ?, updated_at = datetime('now') WHERE id = ?",
            (title, content, rid),
        )
        updated += 1
    conn.commit()
    conn.close()
    print(f"[enrich_chatgpt] applied {updated}/{len(data)} row(s)")


def cmd_seed(_args: argparse.Namespace) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    updated = skipped = missing = 0
    for event_id, title_upd, content_upd in updates:
        row = conn.execute("SELECT id FROM chatgpt_event WHERE id = ?", (event_id,)).fetchone()
        if not row:
            missing += 1
            continue
        conn.execute(
            "UPDATE chatgpt_event SET title_updated = ?, content_updated = ?, updated_at = datetime('now') WHERE id = ?",
            (title_upd, content_upd, event_id),
        )
        updated += 1
    conn.commit()
    conn.close()
    print(f"[enrich_chatgpt] seed: {updated} updated, {missing} missing")


def cmd_status(_args: argparse.Namespace) -> None:
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM chatgpt_event").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM chatgpt_event WHERE title_updated IS NOT NULL").fetchone()[0]
    conn.close()
    print(f"[enrich_chatgpt] total={total}  done={done}  pending={total - done}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ChatGPT event English enrichment")
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
