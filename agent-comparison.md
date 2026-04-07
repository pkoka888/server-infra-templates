# Complete Agent Customization Reference

## Overview

Comprehensive comparison of customization systems across:
- **Cline** (saoudrizwan.claude-dev) - https://docs.cline.bot
- **Kilo** (kilocode.kilo-code) - https://kilo.ai/docs
- **OpenCode/Oh-My-OpenAgent** (omo) - https://github.com/code-yeongyu/oh-my-openagent (48K stars)

---

## Part 1: Complete Directory/File Matrix

### CLINE (saoudrizwan.claude-dev)

| Path | Type | Impact | Auto-detected | What Happens If Missing |
|------|------|--------|---------------|------------------------|
| `.cline/skills/` | dir | ✅ HIGH | Yes | Skills not loaded |
| `.cline/skills/*/SKILL.md` | file | ✅ HIGH | Yes | Skill not available |
| `.cline/skills/*/docs/` | dir | ⚠️ MEDIUM | Yes (lazy) | Docs not accessible |
| `.cline/skills/*/templates/` | dir | ⚠️ MEDIUM | Yes (lazy) | Templates not accessible |
| `.cline/skills/*/scripts/` | dir | ⚠️ MEDIUM | Yes (lazy) | Scripts not executable |
| `.clinerules/` | dir | ✅ HIGH | Yes | Rules not loaded |
| `.clinerules/*.md` | file | ✅ HIGH | Yes | Rule not applied |
| `.clinerules/workflows/` | dir | ✅ HIGH | Yes | Workflows not available |
| `.clinerules/workflows/*.md` | file | ✅ HIGH | Yes | Workflow can't run |
| `.clinerules/hooks/` | dir | ✅ HIGH | Yes | Hooks not registered |
| `.clinerules/hooks/*.sh` | file | ✅ HIGH | Yes | Hook doesn't run |
| `.claude/skills/` | dir | ✅ HIGH | Yes | Claude compat skills missing |
| `.claude/commands/` | dir | ✅ HIGH | Yes | Slash commands missing |
| `.claude/settings.json` | file | ✅ HIGH | Yes | Hook config not loaded |
| `.claude/hooks/` | dir | ✅ HIGH | Yes | Claude hooks missing |
| `.agents/skills/` | dir | ✅ HIGH | Yes | OpenAgent skills missing |
| `.cursorrules` | file | ✅ HIGH | Yes | Cursor rules ignored |
| `.cursorrules/` | dir | ✅ HIGH | Yes | Cursor rules ignored |
| `.windsurfrules` | file | ✅ HIGH | Yes | Windsurf rules ignored |
| `AGENTS.md` | file | ✅ HIGH | Yes | Standard instructions ignored |
| `.clineignore` | file | ✅ HIGH | Yes | No file exclusion |
| `CLAUDE.md` | file | ⚠️ MEDIUM | No | Different purpose (not rules) |
| `.github/` | dir | ❌ NONE | No | Ignored |

### KILO (kilocode.kilo-code)

| Path | Type | Impact | Auto-detected | What Happens If Missing |
|------|------|--------|---------------|------------------------|
| `.kilo/` | dir | ✅ HIGH | Yes | Config not found |
| `.kilo/kilo.jsonc` | file | ✅ HIGH | Yes | Config not loaded |
| `.kilo/kilo.json` | file | ✅ HIGH | Yes | Legacy config ignored |
| `.kilo/skills/` | dir | ✅ HIGH | Yes | Project skills missing |
| `.kilo/skills/*/SKILL.md` | file | ✅ HIGH | Yes | Skill not available |
| `.kilo/skills/*/docs/` | dir | ⚠️ MEDIUM | Yes (lazy) | Docs not accessible |
| `.kilo/skills/*/templates/` | dir | ⚠️ MEDIUM | Yes (lazy) | Templates not accessible |
| `.kilo/skills/*/scripts/` | dir | ⚠️ MEDIUM | Yes (lazy) | Scripts not executable |
| `.kilo/commands/` | dir | ✅ HIGH | Yes | Slash commands missing |
| `.kilo/commands/*.md` | file | ✅ HIGH | Yes | Command can't run |
| `.kilo/rules/` | dir | ✅ HIGH | Yes | Custom rules missing |
| `.kilo/rules/*.md` | file | ✅ HIGH | Yes | Rule not applied |
| `.kilocode/` | dir | ⚠️ MEDIUM | Yes (migration) | Legacy config ignored |
| `.kilocode/kilo.json` | file | ⚠️ MEDIUM | Yes | Legacy config ignored |
| `.kilocode/skills/` | dir | ⚠️ MEDIUM | Yes | Legacy skills missing |
| `.kilocodeignore` | file | ✅ HIGH | Yes | No file exclusion |
| `.claude/skills/` | dir | ✅ HIGH | Yes | Claude compat skills missing |
| `.claude/commands/` | dir | ✅ HIGH | Yes | Claude commands missing |
| `.claude/settings.json` | file | ✅ HIGH | Yes | Hook config missing |
| `.agents/skills/` | dir | ✅ HIGH | Yes | OpenAgent skills missing |
| `AGENTS.md` | file | ✅ HIGH | Yes | Standard instructions ignored |
| `CLAUDE.md` | file | ✅ HIGH | Yes | Claude compat instructions |
| `CONTEXT.md` | file | ⚠️ MEDIUM | Yes | Additional context ignored |
| `~/.config/kilo/` | dir | ✅ HIGH | Yes | Global config missing |
| `~/.kilo/skills/` | dir | ✅ HIGH | Yes | Global skills missing |
| `~/.kilo/commands/` | dir | ✅ HIGH | Yes | Global commands missing |

### OPENCODE / OH-MY-OPENAGENT (omo)

| Path | Type | Impact | Auto-detected | What Happens If Missing |
|------|------|--------|---------------|------------------------|
| `.opencode/` | dir | ✅ HIGH | Yes | Config not found |
| `oh-my-opencode.jsonc` | file | ✅ HIGH | Yes | Main config not loaded |
| `oh-my-openagent.jsonc` | file | ✅ HIGH | Yes | New config not loaded |
| `.opencode/skills/` | dir | ✅ HIGH | Yes | Project skills missing |
| `.opencode/skills/*/SKILL.md` | file | ✅ HIGH | Yes | Skill not available |
| `.opencode/commands/` | dir | ✅ HIGH | Yes | Commands missing |
| `.opencode/commands/*.md` | file | ✅ HIGH | Yes | Command can't run |
| `.opencode/hooks/` | dir | ✅ HIGH | Yes | Custom hooks missing |
| `.opencode/hooks/*.ts` | file | ✅ HIGH | Yes | Hook doesn't run |
| `.claude/skills/` | dir | ✅ HIGH | Yes | Claude compat skills |
| `.claude/commands/` | dir | ✅ HIGH | Yes | Claude compat commands |
| `.claude/settings.json` | file | ✅ HIGH | Yes | Claude hooks config |
| `.claude/hooks/` | dir | ✅ HIGH | Yes | Claude hooks |
| `.agents/skills/` | dir | ✅ HIGH | Yes | OpenAgent skills |
| `~/.config/opencode/` | dir | ✅ HIGH | Yes | Global config missing |
| `~/.config/opencode/skills/` | dir | ✅ HIGH | Yes | Global skills missing |
| `~/.agents/skills/` | dir | ✅ HIGH | Yes | User OpenAgent skills |
| `AGENTS.md` | dir | ✅ HIGH | Yes | Instructions ignored |

---

## Part 2: Skills Format Comparison

### CLINE Skills
```yaml
---
name: my-skill              # Recommended to match directory
description: Do X. Use when user asks to do X.  # Max 1024 chars
---

# Instructions
...
```

**Location Priority:**
```
1. .cline/skills/                    [PROJECT - HIGHEST]
2. .clinerules/skills/              [PROJECT]
3. .claude/skills/                  [PROJECT - Claude compat]
4. .agents/skills/                  [PROJECT - OpenAgent]
5. ~/.cline/skills/                  [GLOBAL]
```

**If skill in config but not in dir:** Not applicable (Cline uses directory-based skills)

---

### KILO Skills
```yaml
---
name: my-skill              # MUST match directory name EXACTLY!
description: Do X. Use when user asks to do X.  # Max 1024 chars
license: Apache-2.0        # Optional
metadata:                   # Optional
  author: example
  version: 1.0.0
---

# Instructions
...
```

**Location Priority:**
```
1. .kilo/skills/                    [PROJECT - HIGHEST]
2. .claude/skills/                  [PROJECT - Claude compat]
3. .agents/skills/                  [PROJECT - OpenAgent]
4. ~/.kilo/skills/                  [GLOBAL]
5. skills.paths in kilo.jsonc       [CONFIG]
6. skills.urls in kilo.jsonc         [REMOTE]
```

**If skill in config but not in dir:** Kilo loads skills from paths specified in config. If path exists but is empty, no skills loaded. Remote URLs fetched at session start (5s timeout).

---

### OPENCODE/OMO Skills
```yaml
---
name: my-skill              # MUST match directory name
description: Do X. Use when user asks to do X.
mcp:                        # Optional - embed MCP servers
  my-mcp:
    command: npx
    args: ["-y", "my-mcp-server"]
---

# Instructions
...
```

**Location Priority:**
```
1. .opencode/skills/                    [PROJECT - HIGHEST]
2. ~/.config/opencode/skills/           [GLOBAL]
3. .claude/skills/                      [PROJECT - Claude compat]
4. .agents/skills/                      [PROJECT - OpenAgent]
5. ~/.agents/skills/                    [USER - OpenAgent]
```

**If skill in config but not in dir:** OMO also supports skill embedding via MCP config.

---

## Part 3: Commands/Workflows Comparison

### CLINE
- **Location:** `.clinerules/workflows/*.md` (invoke with `/filename.md`)
- **Format:** Markdown with frontmatter
- **Location (global):** `~/Documents/Cline/Workflows/`

### KILO
- **Location:** `.kilo/commands/*.md` (invoke with `/filename`)
- **Format:** Markdown with YAML frontmatter
```yaml
---
description: Submit a pull request with checks
agent: code
model: claude-sonnet-4-20250514
---
# Workflow content
```
- **Location (global):** `~/.config/kilo/commands/`

### OPENCODE/OMO
- **Location:** `.opencode/commands/*.md` (invoke with `/command`)
- **Built-in commands:**
  - `/init-deep` - Generate hierarchical AGENTS.md
  - `/ralph-loop` - Self-referential development loop
  - `/ulw-loop` - Ultra-work loop
  - `/refactor` - Intelligent refactoring
  - `/start-work` - Execute Prometheus plan
  - `/handoff` - Create context summary

---

## Part 4: Hooks Comparison

### CLINE
- **Location:** `.clinerules/hooks/*.sh`
- **Config:** `.claude/settings.json`
```json
{
  "hooks": {
    "SessionStart": [{ "hooks": [{ "type": "command", "command": "./hook.sh" }] }],
    "PreTask": [...],
    "PostTask": [...]
  }
}
```
- **Events:** SessionStart, PreTask, PostTask, PreReadFile, PostReadFile, PreEditFile, PostEditFile

### KILO
- **Hooks:** Currently NOT supported as of v7.1 (feature request: #5827)
- **Alternative:** Custom Instructions via `instructions` key in config

### OPENCODE/OMO - MOST ADVANCED
- **Location:** `.opencode/hooks/*.ts` or config file
- **Built-in hooks (30+):**
  - `directory-agents-injector` - Auto-inject AGENTS.md
  - `directory-readme-injector` - Auto-inject README.md
  - `rules-injector` - Inject rules on conditions
  - `keyword-detector` - Detect keywords (ultrawork, search, analyze)
  - `think-mode` - Auto-detect thinking needs
  - `ralph-loop` - Self-referential loop
  - `session-recovery` - Recover from errors
  - `runtime-fallback` - Automatic model fallback
  - `comment-checker` - Reduce excessive comments
  - `auto-update-checker` - Check for updates
  - And many more...
- **Disable hooks:** `"disabled_hooks": ["hook-name"]`

---

## Part 5: Configuration Files

### CLINE
- No central config file
- Settings via VSCode settings UI

### KILO
```jsonc
{
  "$schema": "https://app.kilo.ai/config.json",
  "mcp": { ... },
  "skills": { "paths": [], "urls": [] },
  "modes": { ... },
  "instructions": [],
  "agent": { "skills": [], "subagentTypes": [] }
}
```
- Config locations: `.kilo/kilo.jsonc` (project), `~/.kilo/kilo.jsonc` (global)

### OPENCODE/OMO
```jsonc
{
  "agents": { ... },
  "categories": { ... },
  "skills": { ... },
  "disabled_skills": [],
  "ralph_loop": { "enabled": true },
  "browser_automation_engine": { "provider": "agent-browser" }
}
```
- Config: `oh-my-opencode.jsonc` or `oh-my-openagent.jsonc`

---

## Part 6: Decision Matrix

### If File/Folder Not Found

| Agent | File | Behavior |
|-------|------|----------|
| **Cline** | `.cline/skills/` | Silent skip, no skills |
| **Cline** | `.clinerules/` | Silent skip, no rules |
| **Cline** | `.clinerules/workflows/*.md` | `/workflow` command not available |
| **Cline** | `.clinerules/hooks/*.sh` | Hook not registered |
| **Kilo** | `.kilo/` | Uses default config |
| **Kilo** | `.kilo/skills/` | Silent skip, no project skills |
| **Kilo** | `.kilo/commands/*.md` | Slash command not available |
| **Kilo** | `skills.urls` | Silent skip (5s timeout) |
| **OpenCode** | `.opencode/` | Uses default config |
| **OpenCode** | `.opencode/skills/` | Silent skip |
| **OpenCode** | Config file | Shows warning, uses defaults |

---

## Part 7: Shared Compatibility

| Location | Cline | Kilo | OpenCode |
|----------|-------|------|----------|
| `.claude/skills/` | ✅ | ✅ | ✅ |
| `.claude/commands/` | ✅ | ✅ | ✅ |
| `.claude/settings.json` | ✅ | ✅ | ✅ |
| `.agents/skills/` | ✅ | ✅ | ✅ |
| `AGENTS.md` | ✅ | ✅ | ✅ |

---

## Part 8: OpenCode/OMO Advanced Features

### Agents (11 specialized agents)
| Agent | Model | Purpose |
|-------|-------|---------|
| **Sisyphus** | claude-opus-4-6 | Default orchestrator |
| **Hephaestus** | gpt-5.4 | Autonomous deep worker |
| **Oracle** | gpt-5.4 | Architecture decisions, code review |
| **Librarian** | minimax-m2.7 | Multi-repo analysis |
| **Explore** | grok-code-fast-1 | Fast codebase exploration |
| **Multimodal-Looker** | gpt-5.4 | Visual content specialist |
| **Prometheus** | claude-opus-4-6 | Strategic planner |
| **Metis** | claude-opus-4-6 | Plan consultant |
| **Momus** | gpt-5.4 | Plan reviewer |
| **Atlas** | claude-sonnet-4-6 | Todo-list orchestrator |
| **Sisyphus-Junior** | varies | Category-spawned executor |

### Categories
| Category | Model | Use Case |
|----------|-------|----------|
| `visual-engineering` | gemini-3.1-pro | Frontend, UI/UX |
| `ultrabrain` | gpt-5.4 (xhigh) | Deep reasoning |
| `deep` | gpt-5.4 (medium) | Autonomous problem-solving |
| `artistry` | gemini-3.1-pro (high) | Creative tasks |
| `quick` | gpt-5.4-mini | Simple modifications |
| `writing` | gemini-3-flash | Documentation |

### Built-in Skills
- `git-master` - Git expert (commit, rebase, squash)
- `playwright` - Browser automation
- `frontend-ui-ux` - UI/UX design

### Tools
- Code: grep, glob, edit (hash-anchored)
- LSP: lsp_diagnostics, lsp_rename, lsp_goto_definition
- AST: ast_grep_search, ast_grep_replace
- Delegation: task, call_omo_agent, background_output
- Visual: look_at (PDFs, images)
- Task System: task_create, task_get, task_list, task_update

---

## Part 9: Extensions/Plugins

### KILO
- **MCP Servers:** Via `mcp` in kilo.jsonc
```jsonc
{
  "mcp": {
    "my-server": {
      "type": "local",
      "command": ["docker", "exec", "-i", "container", "command"],
      "environment": { "KEY": "value" },
      "enabled": true
    }
  }
}
```

### OPENCODE/OMO
- **MCP:** Via `mcp` in config
```jsonc
{
  "mcp": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```
- **Skill-embedded MCP:** Skills can bundle their own MCP servers
```yaml
---
name: my-skill
mcp:
  my-mcp:
    command: npx
    args: ["-y", "my-mcp-server"]
---
```

---

## Summary Table

| Feature | Cline | Kilo | OpenCode/OMO |
|---------|-------|------|---------------|
| Skills | ✅ | ✅ | ✅ |
| Rules | ✅ | ✅ | ⚠️ (via AGENTS.md) |
| Commands/Workflows | ✅ | ✅ | ✅ |
| Hooks | ✅ | ❌ | ✅ (30+ built-in) |
| Conditional Rules | ✅ | ❌ | ⚠️ |
| Custom Modes | ❌ | ✅ | ✅ (categories) |
| MCP Servers | ✅ | ✅ | ✅ |
| Subagents | ✅ | ✅ | ✅ (11 agents) |
| Task System | ❌ | ❌ | ✅ |
| Name Matching | Flexible | **STRICT** | **STRICT** |
| Ignore File | `.clineignore` | `.kilocodeignore` | N/A |

---

*Generated: 2026-04-06*
*Sources: https://docs.cline.bot, https://kilo.ai/docs, https://github.com/code-yeongyu/oh-my-openagent*
