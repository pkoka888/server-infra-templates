# Kilo Extension - Complete Customization Reference

**Extension ID**: `kilocode.kilo-code`
**Version**: 7.1.21
**Repository**: https://github.com/Kilo-Org/kilocode
**Docs**: https://kilo.ai/docs

---

## Part 1: All Directory/File Locations

### Complete File Matrix

| Path | Type | Impact | Auto-detected | What If Missing |
|------|------|--------|---------------|-----------------|
| `.kilo/` | dir | ✅ HIGH | Yes | Config directory not found, uses defaults |
| `.kilo/kilo.jsonc` | file | ✅ HIGH | Yes | Main config not loaded |
| `.kilo/kilo.json` | file | ✅ HIGH | Yes | Legacy config ignored |
| `.kilo/skills/` | dir | ✅ HIGH | Yes | Project skills not loaded |
| `.kilo/skills/*/SKILL.md` | file | ✅ HIGH | Yes | Skill not available |
| `.kilo/skills/*/docs/` | dir | ⚠️ MEDIUM | Yes (lazy) | Docs not accessible from skill |
| `.kilo/skills/*/templates/` | dir | ⚠️ MEDIUM | Yes (lazy) | Templates not accessible |
| `.kilo/skills/*/scripts/` | dir | ⚠️ MEDIUM | Yes (lazy) | Scripts not executable |
| `.kilo/commands/` | dir | ✅ HIGH | Yes | Slash commands not available |
| `.kilo/commands/*.md` | file | ✅ HIGH | Yes | Command can't run |
| `.kilo/rules/` | dir | ✅ HIGH | Yes | Custom rules missing |
| `.kilocode/` | dir | ⚠️ MEDIUM | Yes (migration) | Legacy config auto-migrated |
| `.kilocode/kilo.json` | file | ⚠️ MEDIUM | Yes | Legacy config ignored |
| `.kilocode/skills/` | dir | ⚠️ MEDIUM | Yes | Legacy skills still loaded during transition |
| `.kilocodeignore` | file | ✅ HIGH | Yes | No file exclusion |
| `.claude/skills/` | dir | ✅ HIGH | Yes | Claude Code compat skills missing |
| `.claude/commands/` | dir | ✅ HIGH | Yes | Claude compat commands missing |
| `.claude/settings.json` | file | ✅ HIGH | Yes | Hook config missing |
| `.agents/skills/` | dir | ✅ HIGH | Yes | OpenAgent standard skills missing |
| `AGENTS.md` | file | ✅ HIGH | Yes | Standard instructions ignored |
| `CLAUDE.md` | file | ✅ HIGH | Yes | Claude compat instructions |
| `CONTEXT.md` | file | ⚠️ MEDIUM | Yes | Additional context ignored |
| `~/.config/kilo/` | dir | ✅ HIGH | Yes | Global config missing |
| `~/.kilo/` | dir | ✅ HIGH | Yes | Global data directory missing |
| `~/.kilo/skills/` | dir | ✅ HIGH | Yes | Global skills missing |
| `~/.kilo/commands/` | dir | ✅ HIGH | Yes | Global commands missing |
| `kilo.json` | file | ⚠️ MEDIUM | No | Alternative config name (root) |
| `.vscode/` | dir | ⚠️ MEDIUM | No | VSCode settings only |
| `node_modules/` | dir | ❌ NONE | No | Should be in .kilocodeignore |

---

## Part 2: Skills System

### Official Docs
https://kilo.ai/docs/customize/skills

### SKILL.md Format

⚠️ **CRITICAL**: The `name` field **MUST match** the parent directory name!

```yaml
---
name: my-skill-name           # REQUIRED - MUST match directory EXACTLY!
description: Do X. Use when user asks to do X.  # REQUIRED - max 1024 chars
license: Apache-2.0          # OPTIONAL
metadata:                   # OPTIONAL - arbitrary key-value
  author: example
  version: 1.0.0
---

# Instructions

Your detailed instructions here...
```

### Required Fields

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | Max 64 chars, lowercase letters, numbers, hyphens only |
| `name` | Yes | **MUST match directory name exactly!** |
| `description` | Yes | Max 1024 chars, triggers skill |
| `license` | No | String or filename |
| `metadata` | No | Key-value object |

### What If Skill Not Found

- If skill directory exists but no SKILL.md → Error: "missing required 'name' field"
- If skill name doesn't match directory → Error: "name doesn't match directory"
- If skill in config paths but directory empty → Silent skip
- If skill in config URLs but unreachable → Silent skip (5s timeout)

### Skill Location Priority (START → END)

```
1. .kilo/skills/                   [PROJECT] ← HIGHEST
2. .claude/skills/                 [PROJECT] ← Claude Code compat
3. .agents/skills/                 [PROJECT] ← OpenAgent standard
4. ~/.kilo/skills/                 [GLOBAL]
5. skills.paths in kilo.jsonc      [CONFIG]
6. skills.urls in kilo.jsonc        [REMOTE - LOWEST]
```

### Remote Skills
```jsonc
{
  "skills": {
    "paths": ["/path/to/shared/skills", "~/my-skills"],
    "urls": ["https://example.com/skills/my-skill/SKILL.md"]
  }
}
```

---

## Part 3: Commands/Workflows

### Official Docs
https://kilo.ai/docs/customize/workflows

### Location
```
PROJECT: .kilo/commands/*.md
GLOBAL:  ~/.config/kilo/commands/
```

### Invocation
```bash
/submit-pr      # Just filename without .md
```

### Format (with YAML Frontmatter)
```yaml
---
description: Submit a pull request with checks
agent: code
model: claude-sonnet-4-20250514
subtask: false
---

# Submit PR Workflow

You are helping submit a pull request. Follow these steps:

1. Check for TODO comments
2. Run tests
3. Commit and push
4. Create PR
```

### What If Command Not Found

- If command file doesn't exist → `/command` returns "command not found"
- If command file is empty → Shows empty workflow
- If command has invalid frontmatter → Parsing error, command may not work properly

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `description` | No | Shown in command picker |
| `agent` | No | Which agent to use (code, architect, chat) |
| `model` | No | Model override for this command |
| `subtask` | No | If true, runs as sub-agent session |

---

## Part 4: Custom Rules

### Official Docs
https://kilo.ai/docs/customize/custom-rules

### Location
```
PROJECT: .kilo/rules/*.md
GLOBAL:  ~/.kilo/rules/*.md
LEGACY: .kilocoderules/*.md (deprecated, auto-migrated)
```

### What If Rules Not Found

- If rules directory doesn't exist → No custom rules loaded
- If rule file is empty → No impact (empty rule)
- If rule file invalid → Parsed as plain text

### Format
```markdown
# Project Guidelines

## Code Style
- Use TypeScript for all new files
- Prefer composition over inheritance

## Testing
- Unit tests required for business logic
```

---

## Part 5: Custom Instructions

### Official Docs
https://kilo.ai/docs/customize/custom-instructions

### Auto-Discovered Files

| File | Location | Priority |
|------|----------|----------|
| `AGENTS.md` | Project root | HIGH |
| `CLAUDE.md` | Project root | HIGH |
| `CONTEXT.md` | Project root | MEDIUM |
| `AGENTS.md` | Global `~/.config/kilo/` | MEDIUM |
| `AGENTS.md` | Subdirectories | DYNAMIC |

### Per-Directory Instructions

Place `AGENTS.md` in any subdirectory. It's loaded when the agent accesses files in that directory.

### What If Instructions Not Found

- If AGENTS.md doesn't exist → No project-wide instructions loaded
- If subdirectory AGENTS.md doesn't exist → No directory-specific instructions
- If config instructions path invalid → Silent skip

### Configuration Option
```jsonc
{
  "instructions": [
    "./docs/coding-standards.md",
    "./teams/frontend-rules.md",
    "https://example.com/team-instructions.md"
  ]
}
```

---

## Part 6: Custom Modes

### Official Docs
https://kilo.ai/docs/customize/custom-modes

### Location
```jsonc
// In kilo.jsonc
{
  "modes": {
    "debug": {
      "description": "Debugging mode",
      "skills": ["debug-helper"],
      "prompt": "You are in debug mode...",
      "model": "claude-sonnet-4-20250514"
    }
  }
}
```

### Built-in Modes

| Mode | Purpose |
|------|---------|
| `code` | General coding |
| `architect` | Planning and design |
| `chat` | Conversation |

### What If Mode Not Found

- If mode defined but skills missing → Mode works but skills unavailable
- If mode model invalid → Falls back to default model

---

## Part 7: .kilocodeignore

### Location
```
.kilocodeignore              [PROJECT]
~/.kilocodeignore            [HOME]
```

### What If Missing

- If `.kilocodeignore` doesn't exist → No exclusion, all files accessible
- Files normally ignored (node_modules) still counted in context

### Format
```
# Dependencies
node_modules/

# Build output
dist/
build/

# Logs
*.log

# Large files
*.mp4
*.zip
```

---

## Part 8: Configuration (kilo.jsonc)

### Official Schema
```jsonc
{
  "$schema": "https://app.kilo.ai/config.json",
  ...
}
```

### Complete Structure

```jsonc
{
  "$schema": "https://app.kilo.ai/config.json",
  
  // MCP Servers
  "mcp": {
    "server-name": {
      "type": "local" | "remote",
      "command": ["docker", "exec", "-i", "container", "command"],
      "url": "https://remote-server.com/mcp",
      "environment": { "VAR": "value" },
      "enabled": true,
      "timeout": 15000
    }
  },
  
  // Skills
  "skills": {
    "paths": ["/path", "~/path"],
    "urls": ["https://url/SKILL.md"]
  },
  
  // Custom modes
  "modes": {
    "debug": {
      "description": "Debug mode",
      "skills": ["debug-helper"],
      "model": "claude-sonnet-4-20250514"
    }
  },
  
  // Instructions
  "instructions": [
    "./docs/rules.md"
  ],
  
  // Agent config
  "agent": {
    "skills": [],
    "subagentTypes": []
  }
}
```

### What If Config Not Found

- If `.kilo/kilo.jsonc` missing → Uses defaults
- If `.kilo/kilo.json` exists → Loaded as legacy
- If config has invalid JSON → Error shown, uses defaults
- If `$schema` invalid → Ignored, continues loading

### Example: Our Current Config
```jsonc
{
  "$schema": "https://app.kilo.ai/config.json",
  "mcp": {
    "metabase": {
      "type": "local",
      "command": ["docker", "exec", "-i", "metabase", "metabase", "api"],
      "environment": {
        "MB_API_KEY": "$MB_API_KEY"
      },
      "enabled": true,
      "timeout": 15000
    }
  }
}
```

---

## Part 9: CLI vs Extension

| Feature | Extension | CLI |
|---------|-----------|-----|
| Skills | ✅ | ✅ |
| Custom Rules | ✅ | ✅ |
| Custom Instructions | ✅ | ✅ |
| Custom Modes | ✅ | ✅ |
| Commands/Workflows | ✅ | ✅ |
| MCP Servers | ✅ | ✅ |
| UI Integration | ✅ Full | ❌ Terminal |
| Diff Viewer | ✅ | ❌ |
| Agent Manager | ✅ | ❌ |
| .kilocodeignore | ✅ | ✅ |
| 500+ Models | ✅ | ✅ |

---

## Part 10: Compatibility Matrix

| Tool | Skills | Rules | Commands | Modes | Instructions |
|------|--------|-------|----------|-------|--------------|
| Kilo | ✅ | ✅ | ✅ | ✅ | ✅ |
| Claude Code | ✅ | ✅ | ✅ | ❌ | ✅ |
| OpenAgent | ✅ | ❌ | ❌ | ❌ | ❌ |
| OpenCode (legacy) | ✅ | ✅ | ✅ | ❌ | ✅ |

---

## Part 11: Priority Order Summary

### Skills (Highest → Lowest)
```
.kilo/skills/ → .claude/skills/ → .agents/skills/ → ~/.kilo/skills/ → config paths → config URLs
```

### Config Loading
```
Project kilo.jsonc → Global ~/.kilo/kilo.jsonc → Environment variables
```

### Instructions
```
Project AGENTS.md → Global AGENTS.md → Config instructions → Default
```

---

## Part 12: Decision Matrix - What If Missing

| File/Dir | Kilo Behavior |
|----------|---------------|
| `.kilo/` | Uses default empty config |
| `.kilo/kilo.jsonc` | Uses defaults, no MCP loaded |
| `.kilo/skills/` | No project skills loaded |
| `.kilo/commands/` | No custom slash commands |
| `.kilocodeignore` | No exclusion, all files accessible |
| `skills.urls` URL unreachable | Silent skip (5s timeout) |
| `AGENTS.md` | No project instructions |
| Subdirectory AGENTS.md | No directory-specific instructions |

---

## Part 13: Hooks - Note

**Kilo does NOT currently support hooks** (as of v7.1)

Feature request: https://github.com/Kilo-Org/kilocode/issues/5827

Alternative: Use Custom Instructions via `instructions` key in config

---

## Best Practices

### Do ✅
- Match skill name to directory name EXACTLY
- Commit `.kilo/` to version control
- Use specific skill descriptions
- Keep SKILL.md under 5k tokens
- Use environment variables for secrets in config
- Test skills by asking "What skills do you have available?"

### Don't ❌
- Don't put secrets in config files (use env vars)
- Don't modify extension directory
- Don't use mismatched skill names (strict!)
- Don't skip testing skills after adding

---

*Generated: 2026-04-06*
*Source: https://kilo.ai/docs*
