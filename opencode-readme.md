# OpenCode / Oh-My-OpenAgent (OMO) - Complete Reference

**Extension ID**: `sst-dev.opencode` (deprecated - now routes to Kilo)
**Oh-My-OpenAgent**: https://github.com/code-yeongyu/oh-my-openagent (48K stars)
**Docs**: Built into repo + https://github.com/code-yeongyu/oh-my-openagent/blob/dev/docs/

---

## Part 1: All Directory/File Locations

### Complete File Matrix

| Path | Type | Impact | Auto-detected | What If Missing |
|------|------|--------|---------------|-----------------|
| `.opencode/` | dir | ✅ HIGH | Yes | Config directory not found, uses defaults |
| `oh-my-opencode.jsonc` | file | ✅ HIGH | Yes | Main config not loaded (shows warning) |
| `oh-my-openagent.jsonc` | file | ✅ HIGH | Yes | New config not loaded |
| `.opencode/skills/` | dir | ✅ HIGH | Yes | Project skills not loaded |
| `.opencode/skills/*/SKILL.md` | file | ✅ HIGH | Yes | Skill not available |
| `.opencode/commands/` | dir | ✅ HIGH | Yes | Slash commands not available |
| `.opencode/commands/*.md` | file | ✅ HIGH | Yes | Command can't run |
| `.opencode/hooks/` | dir | ✅ HIGH | Yes | Custom hooks not registered |
| `.opencode/hooks/*.ts` | file | ✅ HIGH | Yes | Hook doesn't execute |
| `.claude/skills/` | dir | ✅ HIGH | Yes | Claude Code compat skills missing |
| `.claude/commands/` | dir | ✅ HIGH | Yes | Claude compat commands missing |
| `.claude/settings.json` | file | ✅ HIGH | Yes | Claude hooks config missing |
| `.claude/hooks/` | dir | ✅ HIGH | Yes | Session hooks missing |
| `.agents/skills/` | dir | ✅ HIGH | Yes | OpenAgent standard skills missing |
| `~/.config/opencode/` | dir | ✅ HIGH | Yes | Global config missing |
| `~/.config/opencode/skills/` | dir | ✅ HIGH | Yes | Global skills missing |
| `~/.config/opencode/commands/` | dir | ✅ HIGH | Yes | Global commands missing |
| `~/.agents/skills/` | dir | ✅ HIGH | Yes | User OpenAgent skills missing |
| `AGENTS.md` | file | ✅ HIGH | Yes | Instructions ignored |

---

## Part 2: Skills System

### SKILL.md Format

⚠️ **CRITICAL**: The `name` field **MUST match** the parent directory name!

```yaml
---
name: my-skill-name           # REQUIRED - MUST match directory EXACTLY!
description: Do X. Use when user asks to do X.  # REQUIRED
mcp:                         # OPTIONAL - embed MCP servers
  my-mcp:
    command: npx
    args: ["-y", "my-mcp-server"]
---

# Instructions

Your detailed instructions here...
```

### Required Fields

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | Must match directory name |
| `description` | Yes | Triggers skill |
| `mcp` | No | Skill-embedded MCP servers |

### Skill-Embedded MCP

Skills can bundle their own MCP servers - this is unique to OMO!

```yaml
---
name: playwright-skill
description: Browser automation
mcp:
  playwright:
    command: npx
    args: ["@playwright/mcp@latest"]
---

# Browser Automation

Use Playwright for...
```

### What If Skill Not Found

- If skill directory exists but no SKILL.md → Error
- If skill name doesn't match directory → Error
- If skill MCP server not installed → MCP won't work

### Skill Location Priority (START → END)

```
1. .opencode/skills/                      [PROJECT] ← HIGHEST
2. ~/.config/opencode/skills/             [GLOBAL]
3. .claude/skills/                        [PROJECT] ← Claude Code compat
4. .agents/skills/                        [PROJECT] ← OpenAgent
5. ~/.agents/skills/                       [USER] ← LOWEST
```

---

## Part 3: Commands/Workflows

### Location
```
PROJECT: .opencode/commands/*.md
GLOBAL:  ~/.config/opencode/commands/
```

### Invocation
```bash
/submit-pr      # Just filename without .md
/init-deep
/ralph-loop
```

### Built-in Commands

| Command | Description |
|---------|-------------|
| `/init-deep` | Generate hierarchical AGENTS.md |
| `/ralph-loop` | Self-referential development loop |
| `/ulw-loop` | Ultra-work loop (max performance) |
| `/cancel-ralph` | Cancel Ralph Loop |
| `/refactor` | Intelligent refactoring with LSP |
| `/start-work` | Execute Prometheus plan |
| `/stop-continuation` | Stop all continuation |
| `/handoff` | Create context summary for new session |

### What If Command Not Found

- If command file doesn't exist → Command not available
- If command file empty → Shows empty workflow
- If command has syntax errors → Error shown

---

## Part 4: Hooks System - MOST ADVANCED!

### Official Docs
https://github.com/code-yeongyu/oh-my-openagent/blob/dev/docs/reference/features.md#hooks

### Hook Events

| Event | When | Can |
|-------|------|-----|
| `PreToolUse` | Before tool execution | Block, modify input, inject context |
| `PostToolUse` | After tool execution | Add warnings, modify output |
| `Message` | During message processing | Transform content |
| `Event` | Session lifecycle | Recovery, fallback |
| `Transform` | Context transformation | Inject context |
| `Params` | API parameters | Adjust model settings |

### Built-in Hooks (30+)

#### Context & Injection
| Hook | Event | Description |
|------|-------|-------------|
| `directory-agents-injector` | PreToolUse + PostToolUse | Auto-inject AGENTS.md |
| `directory-readme-injector` | PreToolUse + PostToolUse | Auto-inject README.md |
| `rules-injector` | PreToolUse + PostToolUse | Inject rules on conditions |
| `compaction-context-injector` | Event | Preserve context during compaction |
| `context-window-monitor` | Event | Monitor token consumption |

#### Productivity & Control
| Hook | Event | Description |
|------|-------|-------------|
| `keyword-detector` | Message + Transform | Detect ultrawork/search/analyze |
| `think-mode` | Params | Auto-detect thinking needs |
| `ralph-loop` | Event + Message | Self-referential loop |
| `auto-slash-command` | Message | Auto-execute slash commands |

#### Quality & Safety
| Hook | Event | Description |
|------|-------|-------------|
| `comment-checker` | PostToolUse | Reduce excessive comments |
| `thinking-block-validator` | Transform | Prevent API errors |
| `edit-error-recovery` | PostToolUse + Event | Recover from edit failures |
| `write-existing-file-guard` | PreToolUse | Prevent overwrites |

#### Recovery & Stability
| Hook | Event | Description |
|------|-------|-------------|
| `session-recovery` | Event | Recover from errors |
| `runtime-fallback` | Event + Message | Auto-switch models on errors |
| `model-fallback` | Event + Message | Fallback chain |
| `json-error-recovery` | PostToolUse | Recover from JSON errors |

#### Truncation
| Hook | Event | Description |
|------|-------|-------------|
| `tool-output-truncator` | PostToolUse | Truncate large outputs |

### Hook Configuration

In `oh-my-openagent.jsonc`:
```jsonc
{
  "disabled_hooks": ["comment-checker", "keyword-detector"]
}
```

Or via Claude Code settings:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{ "type": "command", "command": "eslint --fix $FILE" }]
    }]
  }
}
```

### What If Hook Not Found

- If hook script doesn't exist → Configuration error
- If hook has syntax errors → Hook fails silently
- If hook in disabled list → Completely disabled

---

## Part 5: Configuration

### Config Files (both recognized during transition)
```jsonc
// oh-my-opencode.jsonc OR oh-my-openagent.jsonc
{
  "agents": {
    "sisyphus": {
      "model": "claude-opus-4-6",
      "fallback_models": [...]
    }
  },
  "categories": {
    "deep": {
      "model": "gpt-5.4",
      "thinking": { "type": "enabled", "budgetTokens": 32000 }
    }
  },
  "disabled_skills": ["playwright"],
  "ralph_loop": { "enabled": true, "default_max_iterations": 100 },
  "browser_automation_engine": { "provider": "agent-browser" },
  "tmux": { "enabled": true, "layout": "main-vertical" }
}
```

### What If Config Not Found

- If neither config file exists → Uses all defaults
- If config has invalid JSON → Error shown, uses defaults

---

## Part 6: Agents System - UNIQUE TO OMO!

### 11 Specialized Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| **Sisyphus** | claude-opus-4-6 | Default orchestrator |
| **Hephaestus** | gpt-5.4 | Autonomous deep worker |
| **Oracle** | gpt-5.4 | Architecture decisions, code review |
| **Librarian** | minimax-m2.7 | Multi-repo analysis |
| **Explore** | grok-code-fast-1 | Fast codebase exploration |
| **Multimodal-Looker** | gpt-5.4 | Visual content (PDFs, images) |
| **Prometheus** | claude-opus-4-6 | Strategic planner |
| **Metis** | claude-opus-4-6 | Plan consultant |
| **Momus** | gpt-5.4 | Plan reviewer |
| **Atlas** | claude-sonnet-4-6 | Todo-list orchestrator |
| **Sisyphus-Junior** | varies | Category-spawned executor |

### Invoke Agents
```
Ask @oracle to review this design
Ask @librarian how this is implemented
Ask @explore for the policy on this feature
```

### Tool Restrictions Per Agent

| Agent | Restrictions |
|-------|--------------|
| oracle | Read-only (no write, edit, task) |
| librarian | Cannot write, edit, or delegate |
| explore | Cannot write, edit, or delegate |
| multimodal-looker | read only |
| atlas | Cannot delegate |
| momus | Cannot write, edit, or delegate |

---

## Part 7: Categories System - UNIQUE TO OMO!

### Built-in Categories

| Category | Model | Use Case |
|----------|-------|----------|
| `visual-engineering` | gemini-3.1-pro | Frontend, UI/UX |
| `ultrabrain` | gpt-5.4 (xhigh) | Deep reasoning |
| `deep` | gpt-5.4 (medium) | Autonomous problem-solving |
| `artistry` | gemini-3.1-pro (high) | Creative tasks |
| `quick` | gpt-5.4-mini | Simple modifications |
| `unspecified-low` | claude-sonnet-4-6 | Low effort |
| `unspecified-high` | claude-opus-4-6 (max) | High effort |
| `writing` | gemini-3-flash | Documentation |

### Usage
```
task({ category: "visual-engineering", prompt: "Add a chart..." })
```

---

## Part 8: Built-in Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| `git-master` | commit, rebase, squash | Git expert |
| `playwright` | Browser tasks | Playwright MCP |
| `playwright-cli` | Browser tasks | CLI integration |
| `agent-browser` | Browser tasks | Vercel agent-browser |
| `dev-browser` | Browser tasks | Stateful scripting |
| `frontend-ui-ux` | UI/UX tasks | Design persona |

---

## Part 9: Task System - UNIQUE TO OMO!

### Task Tools

| Tool | Description |
|------|-------------|
| `task_create` | Create task with auto-ID |
| `task_get` | Retrieve task by ID |
| `task_list` | List all active tasks |
| `task_update` | Update task status |

### Example
```javascript
task_create({ subject: "Build frontend" }); // T-001
task_create({ subject: "Build backend" }); // T-002
task_create({ subject: "Run tests", blockedBy: ["T-001", "T-002"] }); // T-003

task_list();
// T-001 [pending] Build frontend
// T-002 [pending] Build backend  
// T-003 [pending] Tests blocked by [T-001, T-002]
```

---

## Part 10: CLI vs Extension

| Feature | Extension | CLI |
|---------|-----------|-----|
| Skills | ✅ | ✅ |
| Rules | ✅ (AGENTS.md) | ✅ |
| Commands | ✅ | ✅ |
| Hooks | ✅ (30+ built-in) | ✅ |
| Agents | ✅ (11 agents) | ✅ |
| Categories | ✅ | ✅ |
| MCP Servers | ✅ | ✅ |
| Task System | ✅ | ✅ |
| Background Agents | ✅ | ✅ |
| UI | ✅ | ❌ Terminal |

---

## Part 11: Compatibility Matrix

| Tool | Skills | Commands | Hooks | Agents |
|------|--------|----------|-------|--------|
| OpenCode/OMO | ✅ | ✅ | ✅ | ✅ |
| Claude Code | ✅ | ✅ | ✅ | ❌ |
| Kilo | ✅ | ✅ | ❌ | ❌ |
| Cline | ✅ | ✅ | ✅ | ❌ |

---

## Part 12: Priority Order Summary

### Skills (Highest → Lowest)
```
.opencode/skills/ → ~/.config/opencode/skills/ → .claude/skills/ → .agents/skills/ → ~/.agents/skills/
```

### Commands
```
.opencode/commands/ → ~/.config/opencode/commands/ → .claude/commands/
```

### Config
```
oh-my-openagent.jsonc → oh-my-opencode.jsonc → defaults
```

---

## Part 13: Decision Matrix - What If Missing

| File/Dir | OpenCode/OMO Behavior |
|----------|----------------------|
| `.opencode/` | Uses default empty config |
| Config file | Shows warning, uses defaults |
| `.opencode/skills/` | No project skills |
| `.opencode/commands/` | Only built-in commands |
| `.opencode/hooks/` | Only built-in hooks |
| `AGENTS.md` | No directory-specific context |
| skill MCP server | MCP won't initialize |

---

## Best Practices

### Do ✅
- Match skill name to directory name EXACTLY
- Use skill-embedded MCP for specialized tools
- Leverage built-in hooks for automation
- Use categories + skills combo for specialized agents
- Test with "What skills do you have available?"
- Use ralph-loop for continuous development
- Enable tmux for visual multi-agent

### Don't ❌
- Don't put secrets in config files
- Don't use wrong config filename (use both during transition)
- Don't skip disabling unused hooks (performance)

---

## Migration to Kilo

### Old → New Mapping

| OpenCode | Kilo | Status |
|----------|------|--------|
| `.opencode/` | `.kilo/` | ✅ Supported |
| `.opencode/skills/` | `.kilo/skills/` | ✅ Supported |
| `opencode.json` | `kilo.jsonc` | ✅ Supported |
| `sst-dev.opencode` | `kilocode.kilo-code` | ✅ Use new |

Kilo still loads `.opencode/` during transition period.

---

*Generated: 2026-04-06*
*Sources: https://github.com/code-yeongyu/oh-my-openagent, https://kilo.ai/docs*
