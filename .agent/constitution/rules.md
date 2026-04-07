# Infrastructure Rules — Metabase

**Version:** 1.0.0  
**Date:** 2026-04-06  
**Purpose:** Deployment safety and data pipeline rules for Metabase

---

## Hard Guards (NEVER DO)

1. **Never** modify PostgreSQL schema in same deploy as dashboard changes
2. **Never** expose metabase-db port externally
3. **Never** commit `.env.*` files with real credentials
4. **Never** deploy without running health checks

---

## Network Exposure Rules

| Service | Exposure | Verification |
|---------|-----------|--------------|
| Metabase UI | Traefik (metabase.expc.cz) | `curl -sf https://metabase.expc.cz/api/health` |
| PostgreSQL (metabase-db) | Docker network only | `docker exec metabase-db psql -c "SELECT 1"` |
| Pipeline scripts | Tailscale-only | SSH to s60, run via `uv run` |

---

## Data Pipeline Rules

### Client Isolation

- Each client gets **separate PostgreSQL dataset**: `ga4_client1`, `gads_client1`, etc.
- Never mix client data in same tables
- Use `.env.client_name` files for per-client credentials

### Credential Management

| Type | Storage | Access |
|------|---------|--------|
| Shared (DB connection) | `.env` | All clients |
| Per-client (API keys) | `.env.client_name` | Specific client only |
| Pipeline logs | `logs/` | All clients |

### Package Management

- **Use uv exclusively** — no pip for dependencies
- Define dependencies in `pyproject.toml`
- Run `uv sync` after any change

---

## Post-Deploy Verification

```bash
# 1. Check containers
docker ps --filter "name=metabase"

# 2. Check health
docker inspect --format='{{.State.Health.Status}}' metabase

# 3. Test API
curl -sf http://127.0.0.1:8096/api/health

# 4. Test pipeline (dry run)
uv run python scripts/pipeline.py --list-clients --client test
```

---

## Evidence Labels

| Label | Meaning |
|-------|---------|
| `✅ Verified` | Command ran successfully |
| `⚠️ Partial` | Some checks passed, some failed |
| `❌ Failed` | Check failed - investigate before proceeding |
| `🔒 Secure` | Credentials verified as not committed |