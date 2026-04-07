# Metabase Project - Skills Summary

Created: 2026-04-06

## Skills Overview

| Category | Count | Location |
|----------|-------|----------|
| **Custom (Project-Specific)** | 8 | `.kilo/skills/` |
| **Marketplace** | 41 | `.kilo/skills/marketplace/` |
| **Total Skills** | 56 | Combined |

## Custom Skills Created

| Skill | Purpose | Trigger Phrases |
|-------|---------|-----------------|
| `metabase-api` | Dashboard/question management | "query metabase", "dashboard" |
| `docker-manage` | Docker container management | "restart", "logs", "docker" |
| `postgres-backup` | PostgreSQL backup/restore | "backup", "restore", "dump" |
| `borg-backup` | Borg backup repository | "borg", "remote backup" |
| `metabase-ai-assistant` | AI-powered SQL/automation | "AI help", "generate SQL" |
| `metabase-embedding` | Embedded analytics | "embed", "white-label" |
| `metabase-permissions` | RBAC & access control | "permissions", "groups" |

## Marketplace Skills Available

Located in `.kilo/skills/marketplace/`:

- `agent-md-refactor`
- `angular-*` (various Angular skills)
- `artifacts-builder`
- `canvas-design`
- `changelog-generator`
- `competitive-ads-extractor`
- `content-research-writer`
- `create-pull-request`
- `dbt`, `dbt-migration`
- `domain-name-brainstormer`
- (and 28 more...)

## Directory Structure

```
var/www/metabase/.kilo/
├── kilo.jsonc                    # Config with Metabase MCP
└── skills/
    ├── metabase-api/          ✅ Custom
    ├── metabase-ai-assistant/ ✅ Custom
    ├── metabase-embedding/     ✅ Custom
    ├── metabase-permissions/  ✅ Custom
    ├── docker-manage/         ✅ Custom
    ├── postgres-backup/        ✅ Custom
    ├── borg-backup/           ✅ Custom
    └── marketplace/            ✅ 41 skills
```

## MCP Servers Configured

```jsonc
{
  "mcp": {
    "metabase": {
      "type": "local",
      "command": ["docker", "exec", "-i", "metabase", "metabase", "api"],
      "environment": { "MB_API_KEY": "$MB_API_KEY" }
    }
  }
}
```

## Usage

To use a skill, simply describe what you need:

- "Backup the database" → Uses `postgres-backup`
- "Create an embedded dashboard" → Uses `metabase-embedding`
- "Set up user permissions" → Uses `metabase-permissions`
- "Restart the Metabase service" → Uses `docker-manage`

All skills are automatically loaded when Kilo starts a new session.
