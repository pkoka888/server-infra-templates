# MCP Server Configuration Templates

This directory contains template configurations for Model Context Protocol (MCP) servers.

## Common MCP Servers

### SQLite Research Database
```json
{
  "type": "local",
  "command": [
    "npx", "-y", "@modelcontextprotocol/server-sqlite",
    "PATH_TO_DB"
  ],
  "enabled": true,
  "timeout": 10000
}
```

### GitHub Integration
```json
{
  "type": "local",
  "command": [
    "docker", "run", "-i", "--rm",
    "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ghcr.io/github/github-mcp-server"
  ],
  "enabled": true,
  "timeout": 15000
}
```

### OpenProject
```json
{
  "type": "local",
  "command": ["PATH_TO_OPENPROJECT_MCP"],
  "environment": {
    "OPENPROJECT_URL": "${OPENPROJECT_URL}",
    "OPENPROJECT_API_KEY": "${OPENPROJECT_API_KEY}"
  },
  "enabled": true,
  "timeout": 10000
}
```

### Filesystem
```json
{
  "type": "local",
  "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/allowed/directory"],
  "enabled": true,
  "timeout": 10000
}
```

### Git
```json
{
  "type": "local",
  "command": ["npx", "-y", "@modelcontextprotocol/server-git"],
  "enabled": true,
  "timeout": 10000
}
```

## Usage

1. Copy `kilo.json` template to project `.kilo/` directory
2. Update placeholder paths with actual values
3. Set environment variables in `.env` file
4. Never commit `.env` — add to `.gitignore`

## Best Practices

- Use environment variables for secrets
- Set appropriate timeouts (10000-30000ms)
- Enable/disable servers per project need
- Document required env vars in `.env.example`
