# Top GitHub Repositories for Agentic Extensions - Extended Research

Comprehensive research of top repositories for Cline, Kilo, OpenCode/Oh-My-OpenAgent, Claude Code CLI, and Metabase. Includes 2026 updates, new features, and recommendations for our Metabase project.

---

## Part 1: CLINE (saoudrizwan.claude-dev) - Extended Research

### Current Status (April 2026)

| Property | Value |
|----------|-------|
| **Stars** | 60K+ |
| **Version** | 3.77.0 |
| **Language** | TypeScript |

### 2026 New Features

| Feature | Status | PR/Issue |
|---------|--------|----------|
| **Prompts Library** | ✅ NEW | #9170 - Community and team prompt support |
| **Cline Canary** | ✅ In Progress | #10061 - Separate Canary/Stable releases |
| **GPT-5.3-Codex** | ✅ Released | New GA model in v3.67.1 |
| **Streaming Improvements** | ⚠️ Issues | #576 - Performance concerns |

### Top Repositories for Cline

| # | Repository | Stars | Purpose |
|---|------------|-------|---------|
| 1 | cline/cline | 60K | Main extension |
| 2 | aktsmm/vscode-agent-skill-ninja | 14 | Skill management UI |
| 3 | bartwisch/MCPRules | 22 | MCP for programming guidelines |
| 4 | Abderraouf-yt/skills-mcp-server | 1 | 634+ AI development skills |
| 5 | xllinbupt/MCP2skill | 0 | MCP to skills converter |
| 6 | Hisma/cline-rules-workflows | 4 | Rules and workflows collection |
| 7 | travisvn/awesome-claude-skills | 10.6K | Cross-agent skills (works with Cline) |
| 8 | alirezarezvani/claude-skills | 9.6K | Cross-agent skills |
| 9 | jeremylongshore/claude-code-plugins-plus-skills | 1.8K | 1367 skills + CCPI |
| 10 | MCPRules/mcp-registry | N/A | MCP server registry |

### Cline Directory Structure (Complete)

```
Project/
├── .cline/                    # Skills (project-level)
│   ├── skills/
│   │   └── */SKILL.md
│   └── config.json
├── .clinerules/              # Rules (project-level)
│   ├── *.md                  # Rule files
│   ├── workflows/
│   │   └── *.md              # Workflows
│   └── hooks/
│       └── *.sh              # Hooks
├── .claude/                   # Claude Code compat
│   ├── skills/
│   ├── commands/
│   │   ├── *.md
│   │   └── release.md
│   │   └── hotfix-release.md
│   ├── hooks/
│   │   └── *.sh
│   └── settings.json
├── .agents/                   # OpenAgent standard
│   └── skills/
├── .cursorrules              # Cursor detection
├── .windsurfrules            # Windsurf detection
├── AGENTS.md                 # Standard format
└── .clineignore              # File exclusions
```

### Recent Issues (2026)

| Issue | Status | Impact |
|-------|--------|--------|
| Extension host slow to stop | Open #10051 | Performance |
| Freezes on question | Open #9094 | Usability |
| High CPU load | Open #9454 | Performance |
| CLI not detected (Windows) | Open #9136 | Integration |
| Extension restart loops (SSH) | Open #9248 | Stability |

---

## Part 2: KILO (kilocode.kilo-code) - Extended Research

### Current Status (April 2026)

| Property | Value |
|----------|-------|
| **Stars** | 17.6K → 18K |
| **Version** | 7.1.21 (GA) |
| **Language** | TypeScript |

### 2026 Major Updates

| Feature | Release | Description |
|---------|---------|-------------|
| **New VSCode Extension** | Apr 2026 | Completely rebuilt on portable core |
| **Faster Execution** | v7.1+ | Parallel tool calls |
| **Subagents** | v7.1+ | Better orchestration |
| **Shared Core** | v7.1+ | Across VS Code, CLI, Cloud |

### Kilo New Features (April 2026)

From official docs: https://kilo.ai/docs/code-with-ai/platforms/vscode/whats-new

- **Parallel Tool Calls** - Multiple tools execute simultaneously
- **Subagents** - Delegated agent tasks
- **Shared Core** - Same engine across all platforms
- **Improved MCP** - Better server integration
- **Modes** - Custom mode configurations

### Top Repositories for Kilo

| # | Repository | Stars | Purpose |
|---|------------|-------|---------|
| 1 | Kilo-Org/kilocode | 18K | Main extension |
| 2 | Kilo-Org/kilo-marketplace | 73 | Skills, MCPs, Modes |
| 3 | Kilo-Org/kilo-dev-mcp-server | 26 | Local dev tools |
| 4 | klaudworks/universal-skills | 175 | Universal skills |
| 5 | kilocode-agent/kilocode-2.0 | 1 | Enhanced fork |
| 6 | snussik/kiloconfig | 0 | Custom configs |
| 7 | Kilo-Org/kilocode-legacy | 15 | Legacy version |
| 8 | alirezarezvani/claude-skills | 9.6K | Cross-agent |
| 9 | travisvn/awesome-claude-skills | 10.6K | Skills collection |
| 10 | jeremylongshore/claude-code-plugins-plus-skills | 1.8K | 1367 skills |

### Kilo Directory Structure (Complete)

```
Project/
├── .kilo/                     # Main config
│   ├── kilo.jsonc             # Config file
│   ├── kilo.json              # Alt config name
│   ├── skills/                # Project skills
│   │   └── */SKILL.md
│   ├── rules/                 # Custom rules
│   │   └── *.md
│   ├── commands/              # Slash commands
│   │   └── *.md
│   ├── mcps/                  # Local MCP servers
│   └── node_modules/
├── .kilocode/                 # Legacy (auto-migrated)
│   ├── kilo.json
│   └── skills/
├── .claude/                   # Claude Code compat
│   └── skills/
├── .agents/                   # OpenAgent standard
│   └── skills/
├── AGENTS.md                  # Standard format
├── CLAUDE.md                  # Claude compat
├── CONTEXT.md                 # Additional context
└── .kilocodeignore            # File exclusions
```

### Kilo Configuration Schema

```jsonc
{
  "$schema": "https://app.kilo.ai/config.json",
  "mcp": { ... },           // MCP servers
  "skills": {              // Skills config
    "paths": [],
    "urls": []
  },
  "modes": { ... },         // Custom modes
  "instructions": [],       // Additional instructions
  "agent": { ... }         // Agent config
}
```

---

## Part 3: OPENCODE / OH-MY-OPENAGENT - Extended Research

### Current Status (April 2026)

| Property | Value |
|----------|-------|
| **Stars** | 48.6K |
| **Version** | 3.15.3 |
| **Language** | TypeScript |

### 2026 New Features

| Feature | Status | Description |
|---------|--------|-------------|
| **11 Specialized Agents** | ✅ | Sisyphus, Hephaestus, Oracle, etc. |
| **30+ Built-in Hooks** | ✅ | Automation hooks |
| **Categories System** | ✅ | visual-engineering, deep, quick |
| **Task System** | ✅ | With dependencies |
| **Background Agents** | ✅ | Parallel execution |
| **Ralph Loop** | ✅ | Continuous development |
| **Skill-Embedded MCP** | ✅ | MCP in SKILL.md |
| **tmux Integration** | ✅ | Visual multi-agent |

### OpenCode/OMO Directory Structure (Complete)

```
Project/
├── .opencode/                 # Main config
│   ├── skills/              # Project skills
│   │   └── */SKILL.md
│   ├── commands/            # Slash commands
│   │   └── *.md
│   └── hooks/               # Custom hooks
│       └── *.ts
├── oh-my-openagent.jsonc     # Config (new name)
├── oh-my-opencode.jsonc      # Config (legacy)
├── .claude/                  # Claude Code compat
│   ├── skills/
│   ├── commands/
│   ├── hooks/
│   └── settings.json
├── .agents/                  # OpenAgent standard
│   └── skills/
├── ~/.config/opencode/      # Global config
│   ├── skills/
│   ├── commands/
│   └── hooks/
├── AGENTS.md                 # Standard format
└── ~/.agents/skills/         # User-level skills
```

### OpenCode/OMO MCP Support

```yaml
# Skill-embedded MCP (UNIQUE!)
---
name: playwright-skill
mcp:
  playwright:
    command: npx
    args: ["@playwright/mcp@latest"]
---
```

---

## Part 4: METABASE - Top Repositories

### Main Repository

| Property | Value |
|----------|-------|
| **Stars** | 46.7K |
| **Forks** | 6.3K |
| **Language** | Clojure (52%), TypeScript (39%) |
| **URL** | https://github.com/metabase/metabase |

### Latest Releases (2026)

| Version | Date | Notes |
|---------|------|-------|
| v0.58.9 | 2026-03-12 | Current stable |
| v0.57.15 | 2026-03-04 | Previous |
| v0.55.4 | 2025-06-17 | LTS candidate |

### Top Metabase Repositories

| # | Repository | Stars | Purpose |
|---|------------|-------|---------|
| 1 | metabase/metabase | 46.7K | Main application |
| 2 | metabase/awesome-metabase | 11 | Community examples |
| 3 | vvaezian/metabase_api_python | 161 | Python API wrapper |
| 4 | metabase/metabase-nodejs-react-sdk-embedding-sample | 10 | Embedding sample |
| 5 | metabase/metabase-cursor-plugin | 2 | Cursor AI integration |
| 6 | metabase/data-stack-survey-2025 | 5 | Community survey |
| 7 | enessari/metabase-ai-assistant | 35 | MCP Server for AI (111+ tools) |
| 8 | metabase/embedding-sandbox | N/A | Embedding examples |

### Metabase Libraries & Tools

#### Python

| Library | Stars | Purpose |
|---------|-------|---------|
| metabase-api (vvaezian) | 161 | Full API wrapper |
| metabase-api (pypi) | 28K+ mo | Official-like wrapper |
| metabase_api_python (qianthinking) | 0 | Fork |

#### Node.js

| Library | Purpose |
|---------|---------|
| metabase-node | Node.js client |
| @metabase/embedding-sdk | Official SDK |

#### AI/MCP Integration

| Repository | Stars | Purpose |
|------------|-------|---------|
| enessari/metabase-ai-assistant | 35 | MCP Server (111+ tools) for AI |
| metabase/metabase-cursor-plugin | 2 | Cursor integration |

### Metabase API Endpoints (Key)

| Endpoint | Purpose |
|----------|---------|
| `/api/dashboard` | Manage dashboards |
| `/api/card` | Manage questions |
| `/api/collection` | Organize content |
| `/api/table` | Database tables |
| `/api/database` | Database management |
| `/api/user` | User management |
| `/api/session` | Authentication |

---

## Part 5: CROSS-AGENT COMPATIBLE REPOSITORIES

These work across multiple agents:

| Repository | Stars | Works With |
|-----------|-------|------------|
| alirezarezvani/claude-skills | 9.6K | Claude Code, Cline, Kilo, OpenCode, Cursor |
| travisvn/awesome-claude-skills | 10.6K | All agents |
| jeremylongshore/claude-code-plugins-plus-skills | 1.8K | Claude Code, Kilo, OpenCode |
| first-fluke/oh-my-agent | 556 | Antigravity, Claude Code, Codex, OpenCode |
| klaudworks/universal-skills | 175 | Multiple agents |
| metabase/awesome-metabase | 11 | Metabase ecosystem |
| enessari/metabase-ai-assistant | 35 | Metabase + AI agents |

---

## Part 6: RECOMMENDATIONS FOR OUR METABASE PROJECT

### Current Setup

```
var/www/metabase/
├── .kilo/
│   ├── kilo.jsonc            # Config (Metabase MCP configured)
│   └── skills/
│       ├── metabase-api/     ✅ Created
│       ├── docker-manage/    ✅ Created
│       ├── postgres-backup/  ✅ Created
│       ├── borg-backup/      ✅ Created
│       └── marketplace/      ✅ 41 skills
```

### Recommended Additions

#### 1. Install Metabase AI MCP (enessari/metabase-ai-assistant)
```jsonc
// Add to kilo.jsonc
{
  "mcp": {
    "metabase-ai": {
      "command": "npx",
      "args": ["-y", "metabase-ai-assistant"]
    }
  }
}
```

#### 2. Add Python Metabase API
```bash
pip install metabase-api
```

#### 3. Clone Cross-Agent Skills
```bash
git clone https://github.com/alirezarezvani/claude-skills.git .claude/skills/community
```

#### 4. Create Additional Metabase Skills

| Skill | Purpose | Files |
|-------|---------|-------|
| metabase-embedding | Embed dashboards | `.kilo/skills/metabase-embedding/` |
| metabase-permissions | RBAC management | `.kilo/skills/metabase-permissions/` |
| metabase-sql | Native queries | `.kilo/skills/metabase-sql/` |

### Skills Trigger Phrases

Our custom skills respond to:

| Skill | Trigger Phrases |
|-------|----------------|
| metabase-api | "query metabase", "dashboard", "card", "question" |
| docker-manage | "restart", "logs", "docker", "container" |
| postgres-backup | "backup", "restore", "dump", "pg" |
| borg-backup | "borg", "remote backup", "archive" |

---

## Part 7: COMPLETE FEATURE MATRIX (2026)

| Feature | Cline | Kilo | OpenCode/OMO | Claude Code |
|---------|-------|------|--------------|-------------|
| **Skills** | ✅ | ✅ | ✅ | ✅ |
| **Rules** | ✅ | ✅ | ✅ (AGENTS.md) | ✅ |
| **Commands/Workflows** | ✅ | ✅ | ✅ | ✅ |
| **Hooks** | 7 events | ❌ | 30+ built-in | ✅ |
| **MCP Servers** | ✅ | ✅ | ✅ | ✅ |
| **Skill-Embedded MCP** | ❌ | ❌ | ✅ | ❌ |
| **Task System** | ❌ | ❌ | ✅ | ✅ |
| **Multiple Agents** | ❌ | ❌ | 11 | ❌ |
| **Categories** | ❌ | ✅ | ✅ (8) | ❌ |
| **Background Tasks** | ❌ | ❌ | ✅ | ✅ |
| **Conditional Rules** | ✅ | ❌ | ⚠️ | ❌ |
| **Custom Modes** | ❌ | ✅ | ✅ | ❌ |
| **Prompts Library** | ✅ NEW | ❌ | ❌ | ❌ |
| **Parallel Tool Calls** | ⚠️ | ✅ NEW | ✅ | ⚠️ |
| **Browser Automation** | ✅ (Puppeteer) | ❌ | ✅ (Playwright) | ✅ |

---

## Part 8: COMMUNITY RESOURCES

### Cline
- **GitHub**: https://github.com/cline/cline
- **Reddit**: https://www.reddit.com/r/CLine/
- **Docs**: https://docs.cline.bot

### Kilo
- **GitHub**: https://github.com/Kilo-Org/kilocode
- **Reddit**: https://www.reddit.com/r/kilocode/
- **Docs**: https://kilo.ai/docs
- **Blog**: https://blog.kilo.ai

### OpenCode/OMO
- **GitHub**: https://github.com/code-yeongyu/oh-my-openagent
- **Reddit**: https://www.reddit.com/r/opencodeCLI/
- **Docs**: https://mintlify.com/code-yeongyu/oh-my-opencode

### Metabase
- **GitHub**: https://github.com/metabase/metabase
- **Discourse**: https://discourse.metabase.com
- **Awesome List**: https://github.com/metabase/awesome-metabase

---

*Generated: 2026-04-06*
*Research Sources: GitHub, Official Docs, Reddit, NPM, PyPI*
