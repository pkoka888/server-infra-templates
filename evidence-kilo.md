# Kilo Extension (kilocode.kilo-code) Evidence

## Server s60 - Installation Directories

### VSCode (code-server)
- **Extension Directory**: `/home/pavel/.vscode-server/extensions/kilocode.kilo-code-7.1.21-linux-x64`
- **Extension Version**: 7.1.21
- **GlobalStorage**: `/home/pavel/.vscode-server/data/User/globalStorage/kilocode.kilo-code`
- **File Count**: 220 files

### Antigravity
- **Extension Directory**: `/home/pavel/.antigravity-server/extensions/kilocode.kilo-code-7.1.21-linux-x64`
- **Extension Version**: 7.1.21
- **GlobalStorage**: Same as VSCode (shared)
- **File Count**: 220 files

### Older Versions Present
- VSCode: `kilocode.kilo-code-7.1.20-linux-x64` (also installed)
- Antigravity: `kilocode.kilo-code-7.1.19-linux-x64`

## Files Comparison (VSCode vs Antigravity on s60)

### Identical Files
All 220 files are identical between VSCode and Antigravity except for `package.json`.

### Difference in package.json
Only difference is in `installedTimestamp` field.

## GlobalStorage Comparison

### VSCode GlobalStorage
```
/home/pavel/.vscode-server/data/User/globalStorage/kilocode.kilo-code/
├── cache/
├── roo-index-cache-*.json (2 files)
├── sessions/        (10 subdirs)
├── settings/
└── tasks/         (96 items)
```

## Key Extension Directories

```
kilocode.kilo-code-7.1.21-linux-x64/
├── assets/icons/
├── bin/kilo              (CLI executable)
├── dist/                (JS/CSS + KaTeX fonts)
├── docs/                (Feature documentation)
│   ├── agent-behaviour/
│   ├── chat-ui-features/
│   ├── cli-side/
│   ├── error-handling/
│   ├── features/
│   ├── infrastructure/
│   ├── non-agent-features/
│   └── ui-polish/
├── tests/               (Visual regression snapshots)
├── .storybook/
└── package.json
```

## Local `.kilo/` Directory

Located at: `/var/www/metabase/.kilo/`

```
.kilo/
├── bun.lock
├── .gitignore
├── kilo.json           (Kilo configuration)
├── node_modules/
└── package.json
```

**kilo.json contents:**
```json
{
  "mcpServers": {},
  "agent": {
    "skills": [],
    "subagentTypes": []
  }
}
```

## No `.kilocode/` Directory

Note: There is no `.kilocode/` directory in `/var/www/metabase/`. The extension uses `.kilo/` for configuration.

## Comparison: VSCode vs Antigravity vs Local

| Aspect | VSCode Extension | Antigravity Extension | Local .kilo/ |
|--------|---------------|------------------|---------------|
| Location | ~/.vscode-server/ | ~/.antigravity-server/ | /var/www/metabase/.kilo |
| Version | 7.1.21 | 7.1.21 | N/A |
| Files | 220 | 220 | 5 |
| CLI | Yes (bin/kilo) | Yes | No |

## Summary

The Kilo extension is installed identically on both VSCode and Antigravity (s60).
- Both have identical file sets (220 files)
- GlobalStorage is shared
- The local `.kilo/` directory in var/www/metabase contains:
  - kilo.json (config)
  - node_modules (dependencies)
  - bun.lock (lockfile)
  - package.json

This is the workspace-specific configuration, separate from the VSCode extension installation.

## Public Repository

- **GitHub**: https://github.com/Kilo-Org/kilocode
- **Stars**: 17,481
- **Primary language**: TypeScript
- **Extension ID**: kilocode.kilo-code

Generated: 2026-04-06