---
name: metabase-api
description: Manage Metabase analytics dashboards, questions, and database queries. Use when working with Metabase, creating dashboards, querying data, or managing analytics.
---

# Metabase API Skill

This skill provides comprehensive guidance for interacting with the Metabase Analytics API.

## Metabase Connection

The Metabase instance is available at:
- URL: https://metabase.expc.cz (port 8096 internally)
- Database: PostgreSQL 17

### Environment Variables Required

Ensure these are set:
- `MB_API_KEY` - Metabase API key for authentication
- `MB_DB_TYPE` - Database type (postgres)
- `MB_DB_HOST` - Database host
- `MB_DB_PORT` - Database port (5432)
- `MB_DB_NAME` - Database name (metabase)

## Common Operations

### 1. Query Metabase API

```bash
# Using docker exec on the container
docker exec metabase-db psql -U metabase -d metabase -c "SELECT * FROM report_dashboard LIMIT 5;"

# Direct API call
curl -H "X-API-Key: $MB_API_KEY" https://metabase.expc.cz/api/dashboard
```

### 2. List Dashboards

```bash
curl -H "X-API-Key: $MB_API_KEY" https://metabase.expc.cz/api/dashboard | jq
```

### 3. Create a New Question

Use the Metabase API to create a saved question:
```bash
curl -X POST \
  -H "X-API-Key: $MB_API_KEY" \
  -H "Content-Type: application/json" \
  https://metabase.expc.cz/api/card \
  -d '{
    "name": "My Question",
    "dataset_query": {
      "type": "query",
      "query": {
        "source_table": <table-id>,
        "aggregation": [["count"]]
      },
      "database": <database-id>
    },
    "display": "bar"
  }'
```

### 4. List Collections

```bash
curl -H "X-API-Key: $MB_API_KEY" https://metabase.expc.cz/api/collection
```

### 5. Check Database Tables

```bash
curl -H "X-API-Key: $MB_API_KEY" https://metabase.expc.cz/api/table | jq
```

## Working with Docker

### Check Metabase Status

```bash
docker compose ps
docker logs metabase --tail 50
curl -f http://127.0.0.1:8096/api/health
```

### Restart Metabase

```bash
docker compose restart metabase
```

### Access PostgreSQL

```bash
docker exec metabase-db psql -U metabase -d metabase
```

## Database Query Examples

### Count Records

```sql
SELECT count(*) FROM report_dashboard;
```

### View Slow Queries

```sql
SELECT query, calls, total_time/calls as avg_time
FROM pg_stat_statements
ORDER BY avg_time DESC
LIMIT 10;
```

### Check Connections

```sql
SELECT count(*) FROM pg_stat_activity;
```

## Best Practices

1. **Always verify API key** is set before making requests
2. **Use collections** to organize dashboards
3. **Cache frequently used questions** in Metabase
4. **Monitor query performance** using pg_stat_statements
5. **Use parameterized queries** to prevent SQL injection

## Error Handling

- 401: Check API key validity
- 403: Insufficient permissions
- 404: Resource not found
- 500: Metabase server error - check logs

## Related Tools

- MCP server: Already configured in `.kilo/kilo.jsonc`
- Docker compose: See `docker-compose.yml`
- Backup script: `scripts/backup-metabase.sh`
