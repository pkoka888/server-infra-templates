# Metabase Deployment — Agent Guidelines

## Purpose

BI/analytics dashboard for PrestaShop e-commerce. Connects to OpenProject (PostgreSQL), research data (SQLite), and Prometheus metrics. Provides dashboards for infrastructure health, project metrics, research pipeline, and client delivery.

## Instance

| Property | Value |
|----------|-------|
| URL | https://metabase.expc.cz |
| Port | 8096 (internal) |
| DB | PostgreSQL 17 |
| Version | v0.59.5 |
| Server | s60 (Docker) |

## Essential Commands

```bash
# Deploy/update
docker compose up -d
docker compose pull

# Health checks
docker inspect --format='{{.State.Health.Status}}' metabase
docker inspect --format='{{.State.Health.Status}}' metabase-db
docker exec metabase curl -sf http://localhost:3000/api/health

# Logs
docker logs metabase --tail 100

# Database access
docker exec metabase-db psql -U metabase -d metabase
```

## Backup

```bash
/var/www/metabase/scripts/backup-metabase.sh

# List backups
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"
borg list ssh://pavel@100.91.164.109/var/backups/borg/metabase
```

## Query Utilities

```bash
# Dashboard count
docker exec metabase-db psql -U metabase -d metabase -c "SELECT count(*) FROM report_dashboard;"

# Slow queries (requires pg_stat_statements extension)
docker exec metabase-db psql -U metabase -d metabase -c "
SELECT query, calls, total_time/calls as avg_time
FROM pg_stat_statements ORDER BY avg_time DESC LIMIT 10;"
```

## Non-Obvious Points

- **Credentials**: Stored in `.env` (never committed)
- **Timezone**: Europe/Prague (JAVA_TIMEZONE and TZ)
- **DB waits for health**: `depends_on` with `service_healthy` condition
- **Borg passphrase**: Located at `~/.config/borg/metabase-passphrase`

## Policy References

- `.agent/agents.md` — Agent behavior for Metabase
- `.agent/constitution/rules.md` — Hard guards and pipeline rules
- `.agent/constitution/embedding-policy.md` — Dashboard embedding rules
- `.agent/constitution/database-policy.md` — PostgreSQL config
- `.agent/skills/metabase-pipeline/SKILL.md` — Pipeline operations
- `.agent/workflows/init-workflow.md` — Initialization steps

## Data Sources Integration

Multi-client ETL pipeline using **dlt** (Apache-2.0) - no Docker required, Python-only.

### Architecture

```
Client APIs (GA4, G-Ads, FB-Ads, PrestaShop, SEO)
           │
           ▼
    ┌──────────────┐
    │ dlt pipeline │  scripts/pipeline.py
    └──────┬───────┘
           │
           ▼
    PostgreSQL (isolated datasets per client)
           │
           ▼
       Metabase
```

### Quick Start

```bash
# 1. Setup new client
./scripts/setup-pipeline.sh client_name

# 2. Edit .env.client_name with credentials
#    - GA4: property_id, client_id, client_secret, refresh_token
#    - G-Ads: developer_token, customer_id, OAuth credentials
#    - FB-Ads: ad_account_id, access_token
#    - PrestaShop: shop_url, api_key
#    - SEO: GSC, Ahrefs, SEMrush API keys

# 3. Run pipeline
python scripts/pipeline.py --all --client client_name
```

### Per-Client Variables

Create `.env.client_name` for each client:

```
CLIENT_ID=client1
GA4_PROPERTY_ID=123456789
GA4_CLIENT_ID=xxx.apps.googleusercontent.com
GA4_CLIENT_SECRET=
GA4_REFRESH_TOKEN=
GADS_CUSTOMER_ID=1234567890
GADS_DEVELOPER_TOKEN=
FB_AD_ACCOUNT_ID=act_123456789
FB_ACCESS_TOKEN=
PS_SHOP_URL=https://shop.com
PS_API_KEY=
```

### Dataset Isolation

Each client gets separate datasets:
- `ga4_client1`, `gads_client1`, `fbads_client1`, `prestashop_client1`
- All clients share same PostgreSQL (metabase-db)

### Scheduling

```bash
# crontab -e
# Daily at 2am for each client
0 2 * * * cd /var/www/metabase && source .venv/bin/activate && python scripts/pipeline.py --all --client client1 >> logs/pipeline_client1.log 2>&1
```

### LangGraph ETL Integration

For advanced ETL orchestration with checkpointing:

```bash
# Run ETL workflow with LangGraph
uv run python scripts/langgraph_etl.py client1 ga4,gads,fbads

# Test LangGraph client
uv run python scripts/langgraph_client.py
```

**Files:**
- `scripts/langgraph_etl.py` - In-process LangGraph ETL graph
- `scripts/langgraph_client.py` - API client for LangGraph server

### Using uv (Recommended)

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

```bash
# Create venv and install dependencies
uv venv .venv --python python3
uv sync

# Run pipeline (activates venv automatically)
uv run python scripts/pipeline.py --all --client client1

# Add new dependency
uv add requests
uv add --dev pytest

# Update all packages
uv sync --upgrade
```

### Credentials

- Never commit `.env.*` files (add to `.gitignore`)
- Shared config in `.env` (PostgreSQL connection)
- API keys go in per-client `.env.client_name`

### Available Sources

| Source | Method | Verified Source |
|--------|--------|-----------------|
| Google Analytics 4 | dlt | `google-analytics` |
| Google Ads | dlt | `google-ads` |
| Facebook Ads | dlt | `facebook-ads` |
| PrestaShop | Custom API | `requests` |
| Google Search Console | dlt | Ready |
| Ahrefs/SEMrush | Python | API keys |

See `METABASE_DATA_SOURCES_INTEGRATION.md` for full documentation.

## Python

```bash
uv run ruff check .
uv run mypy .
uv run pytest
```
