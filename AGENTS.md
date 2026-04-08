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

> **IMPORTANT**: ETL runs at 01:00-02:30 to avoid conflict with 03:00 backup window.

```bash
# crontab -e
# Daily at 1am for each client (BEFORE backup at 3am)
0 1 * * * cd /var/www/metabase && source .venv/bin/activate && python scripts/pipeline.py --all --client client1 >> logs/pipeline_client1.log 2>&1

# Client 2 - staggered 30 min later
30 1 * * * cd /var/www/metabase && source .venv/bin/activate && python scripts/pipeline.py --all --client client2 >> logs/pipeline_client2.log 2>&1

# dbt run - after ETL completes
30 2 * * * cd /var/www/metabase/dbt && source ../.venv/bin/activate && dbt run --target prod >> ../logs/dbt_run.log 2>&1

# dbt test - after dbt run
45 2 * * * cd /var/www/metabase/dbt && source ../.venv/bin/activate && dbt test --target prod >> ../logs/dbt_test.log 2>&1
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

## dbt Transformations

The platform uses **dbt** (data build tool) for SQL transformations with a staging → marts architecture.

### Project Structure

```
dbt/
├── dbt_project.yml           # Project configuration
├── profiles.yml             # Database connections
├── packages.yml             # Package dependencies
├── macros/                  # Custom macros
│   └── data_quality/
│       └── _validations.sql # Shared validation macros
└── models/
    ├── staging/            # Source-conformed models
    │   ├── ga4/            # stg_ga4__traffic
    │   ├── facebook/        # stg_facebook__ads, campaigns
    │   └── prestashop/     # stg_prestashop__orders
    └── marts/
        └── marketing/       # fct_marketing_performance
```

### Running dbt

```bash
# Navigate to dbt directory
cd dbt

# Install dependencies
dbt deps

# Run all models
dbt run

# Run specific client
dbt run --vars '{"client_id": "client1"}'

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

### dbt Docker Service

```bash
# Run dbt in Docker container
docker compose run --rm dbt dbt run

# Or with specific vars
docker compose run --rm dbt dbt run --vars '{"client_id": "client1"}'
```

## Prefect Orchestration

**Prefect** handles workflow orchestration with scheduled pipelines and retry policies.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Prefect Server                          │
│                     (Port 4200)                            │
└─────────────────────────────┬───────────────────────────────┘
                              │ PREFECT_API_URL
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Prefect Worker                         │
│                 (Docker work pool)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Marketing Pipeline                      │
│  dlt sync (GA4/FB Ads/PrestaShop) → dbt run → dbt test   │
└─────────────────────────────────────────────────────────────┘
```

### Commands

```bash
# Start Prefect server and worker
docker compose up -d prefect-server prefect-worker

# Access Prefect UI
open http://localhost:4200

# Deploy pipeline for client
python prefect/deployments/marketing_analytics.py --client client1

# Deploy for all clients
python prefect/deployments/marketing_analytics.py --all

# Check flow status
docker exec prefect-server prefect flow ls
```

### Flow Features

- **Parallel execution**: dlt syncs run concurrently
- **Timeouts**: dlt (10min), dbt run (15min), dbt test (5min)
- **Retries**: Exponential backoff with jitter
- **Schedule**: Daily at 2 AM

## Documentation

| Document | Purpose |
|----------|---------|
| `docs/ONBOARDING.md` | User onboarding manual |
| `docs/DEPENDENCIES.md` | Architecture diagram |
| `docs/DOCKER_CONVENTIONS.md` | Container/volume naming standards |
| `docs/SOP.md` | Standard operating procedures |
| `docs/SOPS_VAULT.md` | Secrets management (SOPS + Ansible) |

## Ansible Infrastructure

```bash
# Deploy platform with Ansible
ansible-playbook ansible/playbooks/deploy.yml --ask-vault-pass

# Backup database
ansible-playbook ansible/playbooks/backup.yml --ask-vault-pass

# Rotate secrets
ansible-playbook ansible/playbooks/rotate-secrets.yml --ask-vault-pass
```

### Ansible Vault Setup

```bash
# Create vault password
echo "your-password" > ~/.vault_pass
chmod 600 ~/.vault_pass

# Edit encrypted secrets
ansible-vault edit ansible/group_vars/all/vault.yml.example
```
