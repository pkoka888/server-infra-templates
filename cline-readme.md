# Cline Extension - Complete Customization Reference

**Extension ID**: `saoudrizwan.claude-dev`
**Version**: 3.77.0
**Repository**: https://github.com/cline/cline
**Docs**: https://docs.cline.bot

---

## Part 1: All Directory/File Locations

### Complete File Matrix

| Path | Type | Impact | Auto-detected | What If Missing |
|------|------|--------|---------------|-----------------|
| `.clineignore` | file | ✅ HIGH | Yes | No file exclusion - all files accessible |
| `.clinerules/` | dir | ✅ HIGH | Yes | No rules loaded |
| `.clinerules/*.md` | file | ✅ HIGH | Yes | That rule not applied |
| `.clinerules/workflows/` | dir | ✅ HIGH | Yes | Workflows not available |
| `.clinerules/workflows/*.md` | file | ✅ HIGH | Yes | `/workflow` command not found |
| `.clinerules/hooks/` | dir | ✅ HIGH | Yes | Hooks not registered |
| `.clinerules/hooks/*.sh` | file | ✅ HIGH | Yes | Hook doesn't execute |
| `.cline/skills/` | dir | ✅ HIGH | Yes | Project skills not loaded |
| `.cline/skills/*/SKILL.md` | file | ✅ HIGH | Yes | Skill not available |
| `.cline/skills/*/docs/` | dir | ⚠️ MEDIUM | Yes (lazy) | Docs not accessible from skill |
| `.cline/skills/*/templates/` | dir | ⚠️ MEDIUM | Yes (lazy) | Templates not accessible |
| `.cline/skills/*/scripts/` | dir | ⚠️ MEDIUM | Yes (lazy) | Scripts not executable |
| `.claude/skills/` | dir | ✅ HIGH | Yes | Claude Code compat skills missing |
| `.claude/commands/` | dir | ✅ HIGH | Yes | Slash commands missing |
| `.claude/settings.json` | file | ✅ HIGH | Yes | Hook config not loaded |
| `.claude/hooks/` | dir | ✅ HIGH | Yes | Session hooks missing |
| `.agents/skills/` | dir | ✅ HIGH | Yes | OpenAgent standard skills missing |
| `.cursorrules` | file | ✅ HIGH | Yes | Cursor rules ignored |
| `.cursorrules/` | dir | ✅ HIGH | Yes | Cursor rules directory ignored |
| `.windsurfrules` | file | ✅ HIGH | Yes | Windsurf rules ignored |
| `AGENTS.md` | file | ✅ HIGH | Yes | Standard instructions ignored |
| `~/.cline/skills/` | dir | ✅ HIGH | Yes | Global skills missing |
| `~/Documents/Cline/Rules/` | dir | ✅ HIGH | Yes | Global rules missing |
| `~/Documents/Cline/Workflows/` | dir | ✅ HIGH | Yes | Global workflows missing |
| `~/Documents/Cline/Hooks/` | dir | ✅ HIGH | Yes | Global hooks missing |
| `.github/` | dir | ❌ NONE | No | Not used - ignored |
| `.vscode/` | dir | ⚠️ MEDIUM | No | VSCode settings only |
| `CLAUDE.md` | file | ⚠️ MEDIUM | No | Different purpose (not rules) |

---

## Part 2: Skills System

### Official Docs
https://docs.cline.bot/customization/skills

### SKILL.md Format

```yaml
---
name: my-skill-name           # REQUIRED - recommended to match directory
description: Do X. Use when user asks to do X.  # REQUIRED - max 1024 chars
license: Apache-2.0          # OPTIONAL
compatibility:               # OPTIONAL - env requirements
  - product: vscode
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
| `name` | Yes | Lowercase, hyphens, max 64 chars |
| `description` | Yes | Max 1024 chars, triggers skill |

### Skill Location Priority (START → END)

```
1. .cline/skills/                   [PROJECT] ← HIGHEST
2. .clinerules/skills/             [PROJECT]
3. .claude/skills/                 [PROJECT] ← Claude Code compat
4. .agents/skills/                 [PROJECT] ← OpenAgent standard
5. ~/.cline/skills/                [GLOBAL] ← LOWEST
```

### What If Skill Not Found

- If skill directory exists but no SKILL.md → Skill silently skipped
- If skill in wrong format → Parsing error, skill not loaded
- If skill name doesn't match directory → Still works (flexible)

---

## Part 3: Rules System

### Official Docs
https://docs.cline.bot/customization/cline-rules

### Supported Locations

```
PROJECT: .clinerules/*.md
GLOBAL:  ~/Documents/Cline/Rules/*.md  (macOS/Linux)
         ~/Cline/Rules/*.md            (Linux/WSL alt)
         Documents\Cline\Rules\*.md    (Windows)
```

### Auto-Detected Formats

| Format | Source | Detection |
|--------|--------|-----------|
| `.clinerules/` | Cline | Automatic |
| `.cursorrules` | Cursor | Root file |
| `.cursorrules/` | Cursor | Directory |
| `.windsurfrules` | Windsurf | Root file |
| `AGENTS.md` | Standard | Root file |

### What If Rules Not Found

- If `.clinerules/` doesn't exist → No custom rules loaded
- If rule file is empty → No impact (empty rule)
- If rule file has invalid markdown → Parsed as plain text

### Conditional Rules (YAML Frontmatter)

```yaml
---
paths:
  - "src/components/**"
  - "src/hooks/**"
---

# React Guidelines

- Use functional components with hooks
```

### Glob Patterns

| Pattern | Matches |
|---------|---------|
| `src/**/*.ts` | All TS under src/ |
| `*.md` | Root markdown only |
| `**/*.test.ts` | Tests anywhere |
| `packages/{web,api}/**` | Web OR API |

---

## Part 4: Workflows System

### Official Docs
https://docs.cline.bot/customization/workflows

### Location
```
PROJECT: .clinerules/workflows/*.md
GLOBAL:  ~/Documents/Cline/Workflows/*.md
```

### Invocation
```bash
/workflow.md    # Run workflow
/release.md     # Run specific workflow
```

### What If Workflow Not Found

- If workflow file doesn't exist → `/workflow` command not available
- If workflow file is empty → Shows empty workflow
- If workflow has syntax errors → Shows error to user

### Format
```yaml
---
name: release-workflow
description: Standard release process
---

# Release Workflow

## Steps

### 1. Bump Version
Run: npm version patch

### 2. Update Changelog
Edit CHANGELOG.md
```

---

## Part 5: Hooks System

### Official Docs
https://docs.cline.bot/customization/hooks

### Location
```
PROJECT: .clinerules/hooks/*.sh
GLOBAL:  ~/Documents/Cline/Hooks/*.sh
```

### Configuration (`.claude/settings.json`)
```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "./.clinerules/hooks/my-hook.sh"
      }]
    }],
    "PreTask": [...],
    "PostTask": [...]
  }
}
```

### Hook Events

| Event | When | Can Modify |
|-------|------|------------|
| `SessionStart` | Session begins | ✅ |
| `PreTask` | Before each task | ✅ Input |
| `PostTask` | After each task | ✅ Output |
| `PreReadFile` | Before reading file | ✅ |
| `PostReadFile` | After reading file | ✅ |
| `PreEditFile` | Before editing | ✅ Input |
| `PostEditFile` | After editing | ✅ Output |

### What If Hook Not Found

- If hook script doesn't exist → Configuration error shown
- If hook has syntax errors → Hook fails silently
- If hook is not executable → May not run properly

---

## Part 6: .clineignore

### Location
```
PROJECT: .clineignore (root)
```

### What If Missing

- If `.clineignore` doesn't exist → No exclusion, all files accessible
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
```

---

## Part 7: CLI vs Extension

| Feature | Extension | CLI |
|---------|-----------|-----|
| Skills | ✅ | ✅ |
| Rules | ✅ | ✅ |
| Workflows | ✅ | ✅ |
| Hooks | ✅ | ✅ |
| .clineignore | ✅ | ❌ |
| Browser (Puppeteer) | ✅ | ❌ |
| UI | ✅ | ❌ |

---

## Part 8: Compatibility Matrix

| Tool | Skills | Rules | Hooks | Workflows |
|------|--------|-------|-------|------------|
| Cline | ✅ | ✅ | ✅ | ✅ |
| Claude Code | ✅ | ✅ | ✅ | ✅ |
| Cursor | ❌ | ✅ | ❌ | ❌ |
| Windsurf | ❌ | ✅ | ❌ | ❌ |
| OpenAgent | ✅ | ❌ | ❌ | ❌ |

---

## Part 9: Priority Order Summary

### Skills (Highest → Lowest)
```
.cline/skills/ → .clinerules/skills/ → .claude/skills/ → .agents/skills/ → ~/.cline/skills/
```

### Rules (Combined)
```
Project .clinerules/*.md + Global ~/Documents/Cline/Rules/*.md
(Project rules combined with global, workspace takes precedence on conflict)
```

### Hooks
```
.claude/settings.json (project) + ~/.claude/settings.json (global)
```

---

## Part 10: Decision Matrix - What If Missing

| File/Dir | Cline Behavior |
|----------|----------------|
| `.cline/skills/` | Silent skip, no project skills loaded |
| `.clinerules/` | Silent skip, no rules applied |
| `.clinerules/workflows/` | `/workflow` commands return "not found" |
| `.clinerules/hooks/` | Hooks in settings.json show error but continue |
| `.claude/settings.json` | Silent skip, no hooks configured |
| `.clineignore` | No exclusion, all files accessible |
| `AGENTS.md` | No standard instructions loaded |

---

## Best Practices

### Do ✅
- Commit `.cline/` and `.clinerules/` to version control
- Use specific skill descriptions (vague = won't trigger)
- Test conditional rules with specific paths
- Keep SKILL.md under 5k tokens

### Don't ❌
- Don't put secrets in rule/skill files
- Don't modify extension directory
- Don't use vague skill descriptions

---

*Generated: 2026-04-06*
*Source: https://docs.cline.bot*
