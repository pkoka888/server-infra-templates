# Agent Behavior for Metabase

**Version:** 1.0.0  
**Date:** 2026-04-06  
**Purpose:** Define agent behavior for Metabase deployment and data pipeline operations

---

## Context

You are working on the **Metabase** project in `/var/www/metabase/`. This is a BI/analytics platform providing dashboards for PrestaShop e-commerce, connecting to:
- PostgreSQL (metabase-db, OpenProject)
- External marketing APIs (GA4, Google Ads, Facebook Ads, SEO)

---

## Key Constraints

### Network Exposure

| Service | Exposure | Access |
|---------|-----------|--------|
| Metabase UI | Traefik | Via metabase.expc.cz with auth |
| PostgreSQL | Internal | Docker network only |
| Pipeline scripts | Tailscale | Via SSH to s60 |

### Deployment Rules

1. **Never** modify database schema in same deploy as dashboard changes
2. **Never** expose PostgreSQL port externally
3. **Always** verify health after container restarts
4. **Never** commit `.env.*` files with real credentials

### Data Pipeline Rules

1. **Isolate** each client's data in separate PostgreSQL datasets
2. **Use** uv for all Python package management
3. **Verify** API credentials before running pipelines
4. **Log** all pipeline runs to `logs/` directory

---

## Verification Methods

| Action | Command |
|--------|---------|
| Container health | `docker inspect --format='{{.State.Health.Status}}' metabase` |
| API health | `docker exec metabase curl -sf http://localhost:3000/api/health` |
| Database connectivity | `docker exec metabase-db psql -U metabase -d metabase -c "SELECT 1;"` |
| Pipeline test | `uv run python scripts/pipeline.py --list-clients --client test` |

---

## Evidence Search Order

1. `AGENTS.md` — Project-specific guidance
2. `.env` files — Configuration (never commit)
3. `docker-compose.yml` — Service definitions
4. `scripts/pipeline.py` — Pipeline logic

---

## What NOT to Assume

| ❌ Don't Assume | Why |
|----------------|-----|
| Container running = accessible | Port may not be exposed |
| .env file exists = valid | Credentials may be missing |
| Pipeline runs = data loads | API limits may block |
| Dataset exists = has data | Client may not have source configured |