"""Codex event English enrichment: generate/apply/seed.

CLI:
  python -m scripts.enrich_codex status
  python -m scripts.enrich_codex generate [--limit N] [--force]
  python -m scripts.enrich_codex apply <file.json>
  python -m scripts.enrich_codex seed
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tracker.db"

updates = [
    # --- codex-cli batch 1 ---
    ("05217f66-3397-4acb-9709-2e3d7859439a",
     "Codex CLI 0.96.0: Async compaction, rate limits & unified exec",
     "Introduces async thread compaction RPC, websocket rate limit signaling, and unified_exec on non-Windows platforms.\nAdds ETag/reasoning metadata parity, source-aware config debugging, and fixes Esc handling and thread listing.\nBug fixes cover tool injection atomicity and thread path validation; state DB migrated to versioned SQLite filenames."),
    ("1cf4d4f2-72d8-4d55-92a2-e129ee56408c",
     "Codex CLI 0.95.0: macOS app launch, personal skills & parallel shell",
     "Adds macOS Codex Desktop launch from CLI, personal skill loading from ~/.agents/skills, and remote skill download APIs.\n/plan gains inline prompts and image paste; shell tools run in parallel and receive CODEX_THREAD_ID; Linux sandbox gets vendored Bubblewrap.\nHardens Git safety, fixes interrupt/resume/approval bugs, and completes migration to rmcp-based protocol types."),
    ("6069260b-1421-45a7-8e0f-8051901d29dd",
     "Codex CLI 0.97.0: Session approvals, live skills & memory plumbing",
     "Adds session-scoped tool approvals, live skill file update detection, and mixed text/image dynamic tool outputs.\nIntroduces /debug-config TUI command, configurable log_dir, and initial thread memory summary persistence.\nFixes TUI picker jitter, restores working status indicator, and improves cloud requirements reliability with retries."),
    ("dc20b046-7a46-46ac-ab5c-40fa185985e3",
     "Codex CLI 0.98.0: GPT-5.3-Codex launch & steer mode stable",
     "Introduces GPT-5.3-Codex model and promotes steer mode to stable default with immediate Enter-send behavior.\nFixes TypeScript SDK resumeThread argument ordering, model-instruction handling on mid-conversation model changes, and remote compaction token estimation mismatch.\nRestores Pragmatic default personality and unifies collaboration mode naming across prompts, tools, and TUI."),
    ("736f5d2c-3117-4702-a796-c873b6e9329a",
     "Codex CLI 0.99.0: Concurrent shell, /statusline & enterprise controls",
     "Allows direct shell commands to run concurrently during active turns without interruption, and adds /statusline TUI footer configuration.\nAdds resume sort toggle, app-server steering/notification APIs, enterprise network/search restrictions via requirements.toml, and GIF/WebP image support.\nFixes Windows TUI startup, MCP server fail-fast, file-watcher spurious events, and heredoc approval mismatches; npm packaging reworked for platform binaries."),
    ("d93b36b5-76f1-46d0-a806-29f2d3d5dc76",
     "Codex CLI 0.100.0: JS REPL, multi-rate-limits & memory commands",
     "Adds experimental stateful JavaScript REPL runtime, support for multiple simultaneous rate limits, and redesigned websocket transport with split inbound/outbound architecture.\nIntroduces TUI memory management commands (/m_update, /m_drop), enables Apps SDK in ChatGPT connector, and promotes Linux/Windows sandbox with ReadOnlyAccess policy.\nFixes websocket output duplication, Windows paste reliability, and stale thread entries; codex-common split into focused utility crates."),
    ("962ebd4b-3b32-4644-a831-bb8e7c4295c0",
     "Codex CLI 0.101.0: Stable model resolution & memory pipeline fixes",
     "Fixes model resolution to preserve requested slug on prefix selection and excludes developer messages from phase-1 memory input.\nReduces memory phase processing concurrency to stabilize consolidation under load.\nCleans up phase-1 memory pipeline code paths with minor formatting and test-suite hygiene improvements."),
    # --- codex-cli batch 2 ---
    ("d62a88a4-89d1-4287-81c3-ee1c9a30cbeb",
     "Codex CLI 0.102.0: Unified permissions, network approvals & multi-agent roles",
     "Introduces unified permissions flow, structured network approval handling, and customizable multi-agent roles via config.\nKey additions: clearer permissions history in TUI, fuzzy file search with session-complete signaling, and model reroute notifications.\nBug fixes address remote image persistence, TUI accessibility regression, thread resume behavior, and js_repl stability across multiple areas."),
    ("44ec4d65-a698-40d7-8e7d-cd4c8cd39112",
     "Codex CLI 0.103.0: Richer app metadata & commit co-author hook",
     "Adds richer app listing responses with app_metadata, branding, and labels for more complete app cards.\nCommit co-author attribution now uses a Codex-managed prepare-commit-msg hook with command_attribution override support.\nRemote_models feature flag removed; Rust dependencies updated with toolchain rollback to 1.93.1 after CI breakage."),
    ("62d8c7d1-7694-412a-8a68-8493cfc4ff22",
     "Codex CLI 0.104.0: WebSocket proxy support & thread archive notifications",
     "Adds WS_PROXY/WSS_PROXY environment variable support for websocket proxying and thread archive/unarchive notifications in app-server v2.\nProtocol/core now carries distinct approval IDs for command approvals within a single shell execution flow.\nBug fixes cover Ctrl+C/D exit handling, false-positive safety-check downgrades, and Rust release workflow resilience."),
    ("232e86cc-1bc9-49eb-a5fd-ac4d1c04828d",
     "Codex CLI 0.105.0: Syntax highlighting, voice input & multi-agent CSV fan-out",
     "Delivers major TUI upgrades including syntax-highlighted code blocks, a live-preview theme picker, and spacebar-to-dictate voice transcription.\nMulti-agent workflows gain CSV-based fan-out with progress/ETA, sub-agent nicknames, and child-thread approval prompts; new /copy and /clear commands added.\nBug fixes address link wrapping, queued-message editing, @ parsing, websocket robustness, and Linux sandbox improvements; security policy published."),
    ("6fcaac4a-95a3-4441-a6fc-ca3a742cabbe",
     "Codex CLI 0.106.0: Direct install script, js_repl promoted & diff-based memory",
     "Adds a direct install script for macOS/Linux, promotes js_repl to /experimental, and improves memory with diff-based forgetting and usage-aware selection.\nApp-server v2 gains experimental thread-scoped realtime endpoints; 5.3-codex model made visible; request_user_input enabled in Default collaboration mode.\nBug fixes cover websocket retry on HTTP 400, zsh sandbox bypass, oversized input crashes, and sub-agent Ctrl-C handling; OTEL audit logging added."),
    ("760b6f35-03dc-49cb-a840-421459d690b0",
     "Codex CLI 0.107.0: Thread forking, voice device selection & multimodal custom tools",
     "Enables forking threads into sub-agents, adds microphone/speaker device selection for realtime voice sessions, and supports multimodal output from custom tools.\nApp server exposes richer model availability and upgrade metadata for plan-gated tooltips; memories are now configurable via codex debug clear-memories.\nBug fixes restore pending approvals on thread resume, fix duplicate assistant response printing, improve Windows Terminal diff colors, and harden MCP OAuth flows."),
    # --- codex-app ---
    ("0922ad18-d2cf-4282-a710-f6237a9645ac",
     "Codex App 26.212: GPT-5.3-Codex-Spark, conversation forking & Windows alpha",
     "Codex App 26.212 introduces GPT-5.3-Codex-Spark support and two new conversation features.\nNew features include conversation forking and a floating pop-out window for portable conversations.\nAlpha testing for the Windows version of the Codex app is now open for sign-ups."),
    ("2435d64b-97fe-490c-945e-cc8ccbb30583",
     "Codex App 26.203: Thread renaming & Sync renamed to Handoff",
     "Adds thread renaming via double-click and refines the handoff UI.\nSync has been renamed to Handoff with clearer source/destination stats displayed in the UI.\nFocus is on usability polish with additional performance improvements and bug fixes."),
    ("3ebbc680-8e5b-43c0-aba4-6584fa0873cf",
     "Codex App 26.217: Drag-to-reorder messages & fuzzy file search",
     "Adds drag-and-drop reordering for queued messages and a model downgrade warning.\nFile workflows are improved with fuzzy file search and better attachment recovery after restart.\nRelease also includes general performance improvements and bug fixes."),
    ("4179b99d-c5e6-4302-b6cb-d11f847a5bbd",
     "Codex App 26.206: File-reference OS reveal & large review handling",
     "Adds a file-reference action to reveal files directly in the OS file manager.\nLarge review handling is improved by removing the overall diff-size cap in the review pane.\nRelease includes additional performance improvements and bug fixes."),
    ("43cf9499-387b-411f-8ae5-76c2ead416d0",
     "Codex App 26.210: Branch search, plan mode guidance & parallel approvals",
     "Introduces branch search in the branch picker and parallel approval support.\nClearer guidance is shown when typing 'plan' in the composer to enter plan mode.\nRelease includes additional performance improvements and bug fixes."),
    ("7ef3c07f-8b56-45ca-a107-840806721c9b",
     "Codex App 26.226: MCP shortcuts, @mentions in reviews & rendering fixes",
     "Adds MCP shortcuts in the composer and @mention support in inline review comments.\nImprovements include better MCP tool call rendering and Mermaid diagram error handling.\nA bug where stopped terminal commands appeared as still running has also been fixed."),
    ("aa1cd5a0-f4de-4568-aeca-96af1047197d",
     "Codex App 26.208: MCP & personality in command palette, follow-up queuing",
     "Adds MCP and personality actions to the command palette for faster access.\nFollow-up behavior has been updated to queue by default rather than interrupt current work.\nRelease includes additional performance improvements and bug fixes."),
    ("ad558f1f-a157-4484-86a4-a9a80c0354b5",
     "Codex in ChatGPT iOS: Start tasks, view diffs & push PRs on mobile",
     "Codex is now available within the ChatGPT iOS app for mobile agent task management.\nUsers can start tasks, view diffs, and push pull requests directly from their iPhone.\nBrings Codex's core agentic workflow to mobile for use away from the desktop."),
    ("bb3090e0-7583-486a-b2ba-0af5137d5b87",
     "Introducing the Codex App: macOS desktop agent with parallel threads & Git",
     "The Codex app for macOS launches as a desktop interface for running agent threads in parallel.\nKey features include a project sidebar, worktree support, voice dictation, built-in Git tooling, skills, and automations.\nFor a limited time, Free and Go plans include Codex; Plus and above receive double rate limits across app, CLI, IDE, and cloud."),
    ("e9825c91-2894-4633-9cc6-a1e8a34f1fac",
     "Codex App 26.204: Zed/Textmate support & PDF preview in review panel",
     "Adds Zed and Textmate as editor options for opening files and folders.\nA PDF preview is now available directly in the review panel for easier document inspection.\nRelease focuses on performance improvements and bug fixes."),
    ("fc6f278f-a760-46ae-b6ce-7642c602845d",
     "Codex App 26.205: GPT-5.3-Codex, mid-turn steering & universal file attach",
     "Adds support for GPT-5.3-Codex and introduces mid-turn steering during agent runs.\nUsers can now submit messages while Codex is working to redirect its behavior in real time.\nAny file type can now be attached or dropped, and a flickering bug in the app has been fixed."),
    # --- general batch 1 ---
    ("12afca3a-1b41-48fc-b773-2e8e36e071f0",
     "Custom prompts deprecated: Replaced by reusable skills system",
     "Custom prompts feature has been deprecated in Codex.\nUsers should migrate to skills for reusable instructions and workflows instead.\nThis change affects all users relying on custom prompts for task automation."),
    ("23043efc-d8cd-4ba1-b4ed-f5eb4917fa31",
     "GPT-5.3-Codex in Cursor and VS Code: Phased API rollout begins",
     "GPT-5.3-Codex is now natively available in Cursor and VS Code editors.\nAPI access is rolling out to a limited set of customers under the Preparedness Framework with high security controls.\nFull API access will expand over the next few weeks as safety controls scale."),
    ("236ffb68-0d43-494b-8c4f-08f75211195e",
     "Introducing GPT-5.2-Codex: Advanced agentic coding model released",
     "GPT-5.2-Codex is released as the most advanced agentic coding model for complex real-world software engineering.\nIncludes context compaction for long-horizon work, stronger refactor/migration performance, improved Windows support, and enhanced cybersecurity capabilities.\nCLI and IDE Extension default to gpt-5.2-codex for signed-in ChatGPT users; API access coming soon."),
    ("3369bf37-4065-4626-b299-6da3073acdae",
     "Late August update: IDE integration, PR review & delegation features",
     "Codex now runs in the IDE with an interactive UI, one-click authentication, and seamless task hand-off to Codex web.\nIncludes PR intent checking, codebase reasoning, code execution for change validation, and mode/effort switching.\nEnables delegation of tasks from the IDE to cloud without leaving the editor."),
    ("38468637-7604-4a65-91d7-9a076415fb75",
     "GPT-5-Codex in the API: Available via Responses API and CLI",
     "GPT-5-Codex is now accessible through the Responses API and usable with an API key in the Codex CLI.\nThe model snapshot will be updated regularly and is priced the same as GPT-5.\nProvides developers direct API-level access to the Codex-optimized model."),
    ("3ca01ea2-8b9a-424a-987f-0eff98eac569",
     "GPT-5.2-Codex API availability: Now open to API users",
     "GPT-5.2-Codex is now available in the API and for users signing into Codex with an API key.\nDocumentation is available to guide developers on integrating and using GPT-5.2-Codex via the API.\nExpands access beyond ChatGPT-authenticated users to direct API consumers."),
    ("46678dc2-bedc-4849-b4c9-fd8f92dfcb7d",
     "Introducing GPT-5.1-Codex-Max: Frontier agentic model with extra-high reasoning",
     "GPT-5.1-Codex-Max is released as the new frontier agentic coding model built on an updated foundational reasoning model.\nFaster, more intelligent, and more token-efficient with training across software engineering, math, and research tasks; adds Extra High reasoning effort option.\nCLI and IDE Extension default to gpt-5.1-codex-max for ChatGPT users; API access coming soon."),
    ("61d8ac60-20f8-44e6-9392-ee6cea54655d",
     "June update: Internet access, PR updates, voice input & more",
     "Codex gains internet access during task execution, PR update capability on follow-up, and voice dictation for tasks.\nAdded binary file support, changelog links, iOS fixes, internationalization, improved error messages, and increased diff limit from 1MB to 5MB.\nInternet access is opt-in for Pro, Plus, and Business users; setup script duration extended to 10 minutes."),
    ("6d63057d-cade-4fba-8939-1dd821a370f2",
     "Introducing GPT-5.3-Codex: Most capable agentic coding model to date",
     "GPT-5.3-Codex is released combining GPT-5.2-Codex coding performance with stronger reasoning and professional knowledge.\nRuns 25% faster for Codex users and improves collaboration with frequent progress updates and real-time steering responsiveness.\nAvailable across the Codex app, CLI, IDE extension, and Codex Cloud for paid ChatGPT plans; API access coming soon."),
    ("6e47b5c5-31cc-4f20-a5af-a1ec197924e3",
     "Agent skills in Codex: Reusable instruction bundles now supported",
     "Codex now supports agent skills, which are reusable bundles of instructions, scripts, and resources for reliable task completion.\nSkills can be invoked explicitly via $skill-name or auto-selected by Codex; installable per-user or per-project in the repository.\nAvailable in both CLI and IDE extensions with built-in system skills including $skill-creator and $skill-installer."),
    ("6f4a7bf9-fa8b-4eb5-a5e2-37c5d66e0eb9",
     "Credits on ChatGPT Pro and Plus: On-demand usage beyond plan limits",
     "ChatGPT Plus and Pro users can now purchase on-demand credits for additional Codex usage beyond their plan's included allocation.\nProvides flexible access for users who exceed standard plan limits without requiring a plan upgrade.\nApplies to all Codex usage under Plus and Pro subscription tiers."),
    ("9e5c0dac-dca3-4892-b14c-221eb70b3230",
     "Introducing GPT-5-Codex: Agentic coding with cloud & IDE integration",
     "GPT-5-Codex is a GPT-5 variant optimized for agentic coding, available in the IDE extension and CLI for ChatGPT users.\nPowers cloud agent and GitHub Code Review; adds UI screenshot display for front-end tasks, session resume, and context compaction.\nBroadly integrated across Codex web, CLI, IDE, and GitHub to support the full software development lifecycle."),
    # --- general batch 2 ---
    ("7a2f2ab8-e025-45df-9666-a5c040af1f1f",
     "Introducing GPT-5.3-Codex-Spark: Real-time coding at 1000+ tokens/sec",
     "OpenAI releases GPT-5.3-Codex-Spark, a smaller real-time coding model built in partnership with Cerebras.\nDelivers 1000+ tokens/second, text-only with 128k context, available in ChatGPT Pro via Codex app, CLI, and IDE extension.\nResearch preview only; subject to model-specific usage limits and not available via API at launch."),
    ("8926b9e5-a5bb-4191-8834-5e612d5664a2",
     "Introducing Codex for Linear: Assign tasks via @Codex in issues",
     "Codex integrates natively with Linear, allowing users to assign or mention @Codex in issues to trigger cloud tasks.\nCodex posts progress updates back to Linear and provides a link to the completed task for review or PR opening.\nSupports both local MCP connection and a new direct Linear integration; documented in Codex for Linear docs."),
    ("8fe979ce-f9e7-4663-881e-7dba821dfaa0",
     "Reworked environment page: Faster setup with major latency reductions",
     "The Codex environment setup page has been reworked for faster, easier code execution configuration.\nAdded retry button, network indicators, git patch copy, unicode branch support; fixed secrets piping, emoji diffs, branch conflicts.\nReduced GitHub disconnects by 90%, PR creation latency by 35%, tool call latency by 50%, and task completion latency by 20%."),
    ("b7c3e4eb-3133-4570-b6e7-8e3723294bd0",
     "Best of N: Generate multiple simultaneous responses to explore solutions",
     "Codex can now generate multiple responses in parallel for a single task to help users find the best solution.\nAdded keyboard shortcuts (Cmd-/ or Ctrl+/), branch query parameter, loading indicator, and task cancellation support.\nImproved network access handling, setup script limits, and polished code diffs with option-click expand/collapse."),
    ("babe8b06-913e-435f-8178-a799a76a6b3b",
     "Codex is now GA: Slack integration, SDK, GitHub Action & admin tools",
     "Codex reaches general availability with three major additions: @Codex in Slack, the Codex SDK, and new admin tooling.\nSlack task assignment, TypeScript SDK for embedding the agent, new GitHub Action for CI/CD pipelines.\nAvailable on Plus, Pro, Business, Edu, and Enterprise plans; cloud task usage billing begins October 20."),
    ("bacded73-1fda-4474-813a-f024387c90ac",
     "GPT-5-Codex model update: More reliable edits & collaborative behavior",
     "A minor update to GPT-5-Codex improves reliability, safety, and efficiency of coding interactions.\nMore reliable apply_patch file edits, fewer destructive git actions, better handling of user edits in files.\nOverall 3% improvement in time and usage efficiency."),
    ("c8b71de1-cd3e-4a69-86ac-802a048a9f76",
     "Mid August update: Image prompts, 90% faster startup & auto-install",
     "Codex web gains image attachment support, container caching cuts startup from 48 seconds to 5 seconds, and auto-install defaults are added.\nImages usable for frontend or whiteboarding prompts; maintenance script available to update cached state.\nAuto-install for common package managers in unconfigured environments reduces new-environment test failures by 40%."),
    ("cb1e0a0d-fd78-4b77-9a78-2d052b6dffbd",
     "Introducing GPT-5-Codex-Mini: Cost-effective model with 4x more usage",
     "GPT-5-Codex-Mini launches as a smaller, more affordable alternative to GPT-5-Codex within ChatGPT subscriptions.\nProvides approximately 4x more usage; CLI and IDE Extension auto-suggest switching to mini at 90% of the 5-hour usage limit.\nConfigurable via config.toml or the /model slash command."),
    ("d1327fd4-394e-46c2-9551-f6864e23cca0",
     "Tag @Codex on GitHub Issues and PRs: Trigger tasks from GitHub",
     "Codex can now be mentioned via @codex on GitHub pull requests and issues to assign tasks or ask questions.\nSupports clarifying questions, follow-up requests, and code changes directly within PR threads.\nGitHub Issues support rounds out the workflow so tasks can be kicked off from any issue without context switching."),
    ("e19cd73a-0ae6-4993-a81b-b11513e1428f",
     "Introducing GPT-5.1-Codex and GPT-5.1-Codex-Mini: Optimized for long-running agentic tasks",
     "New gpt-5.1-codex and gpt-5.1-codex-mini models launch alongside the GPT-5.1 API, optimized for agentic coding.\nCLI and IDE Extension default to gpt-5.1-codex on macOS/Linux and gpt-5.1 on Windows.\nConfigurable via config.toml or the /model slash command."),
    ("e82c778a-6b83-4ce8-abdd-2a72604d433f",
     "Usage and credits fixes: Dashboard consistency & billing bugs resolved",
     "Minor fixes address several issues with Codex usage tracking and credit purchasing.\nUsage dashboards standardized to show limits remaining; fixed credit purchase blocks for iOS/Google Play subscribers and stale CLI usage display.\nBackend optimized to smooth usage distribution throughout the day."),
    ("eb2a697a-9d4c-40e3-b305-3d695de4fb21",
     "Web search enabled by default: Cached and live modes for local tasks",
     "Codex CLI and IDE Extension now enable web search by default for local tasks.\nDefaults to cached mode using OpenAI-maintained index; live mode available via --search flag or in --yolo/full-access sandboxes.\nConfigurable via web_search setting: 'cached' (default), 'live', or 'disabled'."),
    ("ffc35933-b6c8-4229-ac6c-a3939c8200dc",
     "Team Config: Shared settings, rules & skills across repos and machines",
     "Team Config introduces a layered configuration system to share Codex settings across teams and repositories.\nSupports shared config.toml defaults, rules/ for sandbox command controls, and skills/ for reusable workflows.\nLoads from .codex/ folders in cwd, parent dirs, repo root, user, and system paths; admins can enforce constraints via requirements.toml."),
    # --- batch 2026-03-05 ~ 2026-03-16 ---
    ("80c522d2-dbef-4dea-b76a-bc888f7d778e",
     "Codex App 26.305: Improved remote connections & Windows terminal fixes",
     "Improves remote connections with clearer connection errors, better status updates, and clearer host labels in thread and settings views.\nFixes copy and paste shortcuts in the integrated terminal on Windows.\nResolves an issue where archived pinned threads could not be unpinned."),
    ("2ede8f93-b5e2-434e-8cde-44e5e728b03c",
     "Codex CLI 0.112.0: @plugin mentions, model catalog picker & merged exec",
     "Adds @plugin mentions so users can reference plugins directly in chat and auto-include their associated MCP/app/skill context.\nIntroduces a new model-selection surface update so the latest model catalog changes are surfaced in the TUI picker flow.\nMerges execution environments and fixes multi-agent stability issues across plugin and tool workflows."),
    ("8f0cfc99-ea4d-4034-a747-642a58bad6d7",
     "Codex CLI 0.113.0: Runtime permissions requests & plugin marketplace",
     "Adds a built-in request_permissions tool so running turns can request additional permissions at runtime, with new TUI rendering for approval calls.\nExpands plugin workflows with curated marketplace discovery, richer plugin/list metadata, and install-time authorization.\nIntroduces runtime permission escalation for safer agentic execution without upfront full-access grants."),
    ("e3e58cdc-0a76-4013-8310-0861e1a8e034",
     "Codex CLI 0.114.0: Experimental code mode, hooks engine & healthz endpoints",
     "Adds an experimental code mode for more isolated coding workflows and an experimental hooks engine with SessionStart and Stop hook events.\nWebSocket app-server deployments now expose GET /readyz and GET /healthz on the same listener for easier health checking.\nImproves developer experience with isolated execution environments and lifecycle hook extensibility."),
    ("adab76d5-2e8a-4074-9510-ba48f029214e",
     "Codex App 26.311: Terminal reading & performance improvements",
     "Codex can now read the integrated terminal for the current thread, so it can check the status of a running development server or refer back to failed build output.\nEnables the agent to incorporate real-time terminal context while working alongside the user.\nRelease includes additional performance improvements and bug fixes."),
    ("3bcc9c9f-19e4-4590-ba1d-4fac811876c5",
     "Codex App 26.312: Custom themes, revamped automations & local/remote toggle",
     "Adds custom theme support with adjustable accent, background, and foreground colors plus UI and code font selection, shareable with friends.\nRevamped automations let users choose whether automations run locally or on a remote environment.\nDelivers a fully personalized workspace experience with visual customization and flexible automation control."),
    ("ea61ff3e-0431-493a-85a9-f03231c59212",
     "Codex CLI 0.115.0: Full-resolution image inspection & js_repl enhancements",
     "Supported models can now request full-resolution image inspection through both view_image and codex.emitImage for precision visual tasks.\njs_repl now exposes codex.cwd and codex.homeDir, and saved codex.tool/codex.emitImage calls are available across sessions.\nEnhances multimodal capabilities for visual debugging and persistent REPL state across coding sessions."),
    ("7a945a39-8f4e-4bae-aec2-3492c367cabb",
     "GPT-5.4 mini: Fast & efficient model for lightweight Codex tasks",
     "GPT-5.4 mini is now available in Codex as a fast, cost-efficient model for lighter coding tasks and subagents.\nIt improves over GPT-5 mini across coding, reasoning, image understanding, and tool use while running more than 2x faster at 30% of GPT-5.4 limit usage.\nAvailable across Codex app, CLI, IDE extension, web, and the API with multimodal input and 16k-token output support."),
    ("f60b6515-f155-4acf-aa83-e9baa07b7224",
     "Codex CLI 0.116.0: ChatGPT sign-in, plugin setup & user-prompt-submit hook",
     "App-server TUI now supports device-code ChatGPT sign-in during onboarding and can refresh existing tokens.\nPlugin setup is smoother with prompts for missing plugins, a configured suggestion allowlist, and remote install/uninstall sync.\nAdds a user-prompt-submit hook enabling prompts to be blocked or augmented before execution and before they enter history."),
]

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def cmd_generate(args: argparse.Namespace) -> None:
    conn = _connect()
    where = "1=1" if args.force else "title_updated IS NULL"
    sql = f"SELECT id, event_date, title, entry_type, version, body FROM codex_event WHERE {where} ORDER BY event_date DESC"
    if args.limit > 0:
        sql += f" LIMIT {args.limit}"
    rows = [dict(r) for r in conn.execute(sql).fetchall()]
    conn.close()
    out = open(sys.stdout.fileno(), "w", encoding="utf-8", closefd=False)
    json.dump(rows, out, ensure_ascii=False, indent=2)
    out.flush()
    print(file=sys.stderr)
    print(f"[enrich_codex] {len(rows)} row(s) pending", file=sys.stderr)


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
            "UPDATE codex_event SET title_updated = ?, content_updated = ?, updated_at = datetime('now') WHERE id = ?",
            (title, content, rid),
        )
        updated += 1
    conn.commit()
    conn.close()
    print(f"[enrich_codex] applied {updated}/{len(data)} row(s)")


def cmd_seed(_args: argparse.Namespace) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    updated = 0
    for record_id, title_upd, content_upd in updates:
        conn.execute(
            "UPDATE codex_event SET title_updated = ?, content_updated = ?, updated_at = datetime('now') WHERE id = ?",
            (title_upd, content_upd, record_id),
        )
        updated += 1
    conn.commit()
    conn.close()
    print(f"[enrich_codex] seed: {updated}/{len(updates)} records")


def cmd_status(_args: argparse.Namespace) -> None:
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM codex_event").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM codex_event WHERE title_updated IS NOT NULL").fetchone()[0]
    conn.close()
    print(f"[enrich_codex] total={total}  done={done}  pending={total - done}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Codex event English enrichment")
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
