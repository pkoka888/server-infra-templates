---
name: metabase-ai-assistant
description: Use Metabase AI Assistant MCP for AI-powered SQL generation, dashboard automation, and enterprise BI. Use when needing AI help with queries, creating visualizations, or automating Metabase tasks.
---

# Metabase AI Assistant Skill

This skill provides guidance for using the Metabase AI Assistant MCP Server (https://github.com/enessari/metabase-ai-assistant).

## Features

- **111+ tools** for AI-powered operations
- **SQL generation** from natural language
- **Dashboard automation**
- **Enterprise BI features**
- Works with Claude, Cursor, ChatGPT

## Installation

```bash
# Install via npx
npx -y metabase-ai-assistant
```

## Configuration

Add to your `.kilo/kilo.jsonc`:

```jsonc
{
  "mcp": {
    "metabase-ai": {
      "command": "npx",
      "args": ["-y", "metabase-ai-assistant"],
      "env": {
        "METABASE_URL": "https://metabase.expc.cz",
        "METABASE_API_KEY": "$MB_API_KEY"
      }
    }
  }
}
```

## Available Tools

### Dashboard Tools
- `create_dashboard` - Create new dashboard
- `update_dashboard` - Update dashboard properties
- `delete_dashboard` - Remove dashboard
- `get_dashboard` - Get dashboard details
- `list_dashboards` - List all dashboards

### Question/Card Tools
- `create_question` - Create new question
- `execute_question` - Run question
- `create_card_from_text` - Generate card from description

### Database Tools
- `list_databases` - List databases
- `list_tables` - List tables in database
- `get_table_fields` - Get table schema
- `get_field_values` - Get field sample values

### SQL Tools
- `generate_sql` - Generate SQL from natural language
- `optimize_sql` - Optimize existing SQL
- `explain_sql` - Explain SQL query
- `validate_sql` - Validate SQL syntax

### User Management
- `list_users` - List users
- `create_user` - Create new user
- `update_user` - Update user

### Collection Tools
- `list_collections` - List collections
- `create_collection` - Create collection
- `move_to_collection` - Move items

## Usage Examples

### Generate SQL from Natural Language

Ask: "Create a SQL query to count users by signup date"

The MCP will use AI to generate appropriate SQL based on your database schema.

### Create Dashboard

Ask: "Create a dashboard with sales metrics"

The MCP will:
1. Analyze available data
2. Generate relevant questions
3. Create dashboard with visualizations

### Automate Reporting

Ask: "Set up daily sales report"

The MCP will create scheduled questions and notifications.

## Best Practices

1. **Start with natural language** - Describe what you want
2. **Iterate on results** - Refine SQL/visualizations
3. **Use templates** - Save common queries
4. **Monitor usage** - Track API calls

## Connection Details

- **URL**: https://metabase.expc.cz (port 8096 internally)
- **API Key**: Set via `MB_API_KEY` environment variable
- **Database**: PostgreSQL 17

## Troubleshooting

- 401: Check METABASE_API_KEY
- Connection refused: Check Metabase is running
- Timeout: Increase timeout in config
