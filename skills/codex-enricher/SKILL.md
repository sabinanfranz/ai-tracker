---
name: codex-enricher
description: |
  Codex event English enrichment skill. Populates title_updated and content_updated
  for codex_event records with concise, technically accurate summaries.
  Use when: (1) title_updated is NULL for codex_event records,
  (2) new codex_event records need English title/content,
  (3) "enrich codex", "title_updated", "English enrichment", "영어 enrich" keywords appear.
---

# Codex-Enricher: English Enrichment for Codex Events

Populates `title_updated` and `content_updated` columns in the `codex_event` table
with concise, technically precise English summaries.

## Style Rules

See [references/style-guide.md](references/style-guide.md) for full specification.

Quick summary:
- **title_updated**: `"Product Version: Feature1, feature2 & feature3"` format, ~70 chars
- **content_updated**: Exactly 3 sentences, `\n`-separated, technical detail (~200 chars each)
- Proper nouns preserved as-is (GPT-5.3-Codex, MCP, etc.)

## Workflow

### 1. Identify Targets

```bash
sqlite3 data/tracker.db "SELECT id, title, date FROM codex_event WHERE title_updated IS NULL ORDER BY date DESC;"
```

### 2. Update Script

Edit `scripts/enrich_codex.py` — add tuples to the `updates` list:

```python
("uuid-here",
 "Product Version: Short feature summary with ampersand",
 "First sentence describes the headline feature.\nSecond sentence covers secondary additions.\nThird sentence notes bug fixes and maintenance."),
```

### 3. Execute

```bash
PYTHONUTF8=1 python scripts/enrich_codex.py
```

### 4. Validate

```bash
PYTHONUTF8=1 python skills/codex-enricher/scripts/validate.py
```

Or manually:

```bash
sqlite3 data/tracker.db "SELECT COUNT(*) FROM codex_event WHERE title_updated IS NOT NULL;"
sqlite3 data/tracker.db "SELECT title_updated FROM codex_event WHERE title_updated IS NOT NULL LIMIT 5;"
```

### 5. Quality Checklist

- [ ] All title_updated NOT NULL
- [ ] Title follows `"Product Version: ..."` pattern, ~70 chars
- [ ] content_updated has exactly 3 sentences (`\n`-separated)
- [ ] Proper nouns preserved in English
- [ ] No keyword-only titles (must be descriptive)

## Examples

| title (raw) | title_updated |
|---|---|
| codex-cli v0.98.0 | Codex CLI 0.98.0: GPT-5.3-Codex launch & steer mode stable |
| codex-app 26.212 | Codex App 26.212: GPT-5.3-Codex-Spark, conversation forking & Windows alpha |
| GPT-5.2-Codex release | Introducing GPT-5.2-Codex: Advanced agentic coding model released |

| content_updated example |
|---|
| Introduces GPT-5.3-Codex model and promotes steer mode to stable default with immediate Enter-send behavior.\nFixes TypeScript SDK resumeThread argument ordering, model-instruction handling on mid-conversation model changes, and remote compaction token estimation mismatch.\nRestores Pragmatic default personality and unifies collaboration mode naming across prompts, tools, and TUI. |
