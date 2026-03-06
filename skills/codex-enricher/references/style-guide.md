# English Enrichment Style Guide

## title_updated Rules

### Format
- Pattern: `"Product Version: Feature1, feature2 & feature3"`
- Use ampersand (`&`) before the last item, not "and"
- Product names: "Codex CLI 0.98.0", "Codex App 26.212", "GPT-5.3-Codex"

### Length
- Target: ~70 characters (min 40, max 90)

### Content
- Lead with the product name and version
- Colon separates product from feature summary
- Highlight 2-3 key features after the colon
- Use sentence case (capitalize first word after colon, proper nouns only)

### Proper Nouns
- Model names: GPT-5.3-Codex, GPT-5.2-Codex, GPT-5-Codex-Mini, etc.
- Protocols/tools: MCP, API, SDK, CLI, IDE, TUI, WebSocket
- Services: Slack, GitHub, Linear, ChatGPT, iOS
- Keep exact casing: macOS, npm, TypeScript, JavaScript

### Anti-patterns
- Too vague: "Various improvements and fixes"
- Too long: listing more than 3 features
- Missing version: "Codex update: ..." (should include version number)
- Wrong separator: "Feature1 and Feature2 and Feature3" (use commas + &)

## content_updated Rules

### Structure
- Exactly **3 sentences**
- Separated by `\n` (literal newline)
- Each sentence ~100-200 characters

### Sentence Roles
1. **Headline feature**: The most important new capability or change
2. **Secondary additions**: Supporting features, improvements, or integrations
3. **Fixes & maintenance**: Bug fixes, dependency updates, cleanup

### Tone
- Technical and factual
- Active voice preferred ("Adds...", "Introduces...", "Fixes...")
- No marketing language ("revolutionary", "game-changing")
- Specific over general ("fixes Ctrl+C exit handling" > "fixes various issues")

### Verb Patterns
- New features: "Introduces...", "Adds...", "Enables...", "Delivers..."
- Changes: "Promotes...", "Renames...", "Reworks..."
- Fixes: "Fixes...", "Resolves...", "Addresses..."
- Combined: "Bug fixes cover...", "Key additions:..."

## Real Examples from enrich_codex.py

### Codex CLI
```
Title: "Codex CLI 0.98.0: GPT-5.3-Codex launch & steer mode stable"
Content:
  "Introduces GPT-5.3-Codex model and promotes steer mode to stable default with immediate Enter-send behavior.
   Fixes TypeScript SDK resumeThread argument ordering, model-instruction handling on mid-conversation model changes, and remote compaction token estimation mismatch.
   Restores Pragmatic default personality and unifies collaboration mode naming across prompts, tools, and TUI."
```

### Codex App
```
Title: "Codex App 26.212: GPT-5.3-Codex-Spark, conversation forking & Windows alpha"
Content:
  "Codex App 26.212 introduces GPT-5.3-Codex-Spark support and two new conversation features.
   New features include conversation forking and a floating pop-out window for portable conversations.
   Alpha testing for the Windows version of the Codex app is now open for sign-ups."
```

### General / Product
```
Title: "Introducing GPT-5.3-Codex: Most capable agentic coding model to date"
Content:
  "GPT-5.3-Codex is released combining GPT-5.2-Codex coding performance with stronger reasoning and professional knowledge.
   Runs 25% faster for Codex users and improves collaboration with frequent progress updates and real-time steering responsiveness.
   Available across the Codex app, CLI, IDE extension, and Codex Cloud for paid ChatGPT plans; API access coming soon."
```
