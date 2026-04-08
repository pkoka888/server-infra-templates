# Marketing Analytics Platform - User Onboarding Manual

## Overview

This manual guides new team members through setting up and using the marketing analytics platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                                │
│  GA4  │  Facebook Ads  │  Google Ads  │  PrestaShop  │  SEO     │
└───────┴───────────────┴──────────────┴──────────────┴─────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      dlt PIPELINE                                │
│              scripts/pipeline.py (multi-client)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL WAREHOUSE                         │
│     ga4_client1  │  fbads_client1  │  prestashop_client1        │
└─────────────────┴────────────────┴───────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                               │
              ▼                               ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│         dbt            │       │       Metabase         │
│  (Transformation)       │       │    (Visualization)      │
│  - Staging models      │       │    - Dashboards         │
│  - Mart models         │       │    - Questions          │
│  - Data quality        │       │                        │
└─────────────────────────┘       └─────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PREFECT                                    │
│  (Orchestration)                                                │
│  - Schedule dlt syncs                                           │
│  - Run dbt models                                               │
│  - Data quality checks                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Access Required**
   - Git repository access
   - Server access (s60)
   - API credentials for data sources

2. **Software**
   - Docker & Docker Compose
   - Python 3.11+
   - uv (package manager)
   - Git

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/pkoka888/server-infra-templates.git
cd server-infra-templates
```

### 2. Setup Python Environment

```bash
# Using uv (recommended)
uv sync

# Or using virtualenv
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Configure Credentials

#### Option A: SOPS (Recommended for Development)

```bash
# Copy template
cp .sops/secrets/metabase-clients.template.yaml \
   .sops/secrets/metabase-client1.yaml

# Edit encrypted secrets
sops .sops/secrets/metabase-client1.yaml

# Unlock secrets when needed
source .sops/scripts/unlock.sh
```

#### Option B: Ansible Vault (Recommended for Production)

```bash
# Create vault password file (KEEP SECURE!)
echo "your-secure-vault-password" > ~/.vault_pass
chmod 600 ~/.vault_pass

# Create encrypted secrets file
ansible-vault create ansible/group_vars/all/vault.yml
```

**Required Variables:**
```bash
# PostgreSQL (for Metabase)
POSTGRES_PASSWORD=your_secure_password

# GA4
GA4_PROPERTY_ID=123456789
GA4_CLIENT_ID=xxx.apps.googleusercontent.com
GA4_CLIENT_SECRET=xxx
GA4_REFRESH_TOKEN=xxx

# Facebook Ads
FB_AD_ACCOUNT_ID=act_123456
FB_ACCESS_TOKEN=xxx

# Google Ads
GADS_CUSTOMER_ID=1234567890
GADS_DEVELOPER_TOKEN=xxx
GADS_CLIENT_ID=xxx
GADS_CLIENT_SECRET=xxx
```

### 4. Start Services

```bash
# Start all services
docker compose up -d

# Or with specific services
docker compose up -d metabase metabase-db

# Verify services
docker compose ps
```

### 5. Verify Services

```bash
# Check Metabase health
curl http://localhost:8096/api/health

# Check PostgreSQL
docker exec metabase-db pg_isready -U metabase

# Check Prefect (if running)
docker exec prefect-server prefect server status
```

### 6. Access Services

| Service | URL | Default Login |
|---------|-----|--------------|
| Metabase | http://localhost:8096 | Email in setup |
| Prefect (local) | http://localhost:4200 | N/A (local) |

## First-Time Setup Checklist

- [ ] Clone repository
- [ ] Install `uv` package manager
- [ ] Run `uv sync` to install Python dependencies
- [ ] Configure credentials (SOPS or Ansible Vault)
- [ ] Start Docker services
- [ ] Complete Metabase setup wizard (http://localhost:8096)
- [ ] Add database connection in Metabase
- [ ] Configure Prefect deployments
- [ ] Run initial dlt pipeline test
- [ ] Run dbt models test

## Multi-Client Setup

### Adding a New Client

```bash
# 1. Create SOPS secrets file
cp .sops/secrets/metabase-clients.template.yaml \
   .sops/secrets/metabase-client_name.yaml

# 2. Edit with client credentials
sops .sops/secrets/metabase-client_name.yaml

# 3. Run pipeline for client
python scripts/pipeline.py --all --client client_name

# 4. Build dbt models
cd dbt && dbt run --vars '{"client_id": "client_name"}'

# 5. Deploy to Prefect
python prefect/deployments/marketing_analytics.py --client client_name
```

### Client Dataset Naming

| Client | GA4 Schema | Facebook Schema | PrestaShop Schema |
|--------|------------|-----------------|-------------------|
| client1 | ga4_client1 | fbads_client1 | prestashop_client1 |
| client2 | ga4_client2 | fbads_client2 | prestashop_client2 |

### Client-Specific Workflow

```
┌──────────────────────────────────────────────────────────────┐
│                  CLIENT ONBOARDING FLOW                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Create secrets (.sops or ansible-vault)                  │
│     └── .sops/secrets/metabase-{client}.yaml                 │
│                                                               │
│  2. Configure data sources                                   │
│     ├── GA4 credentials                                      │
│     ├── Facebook Ads credentials                             │
│     └── PrestaShop API key                                   │
│                                                               │
│  3. Run initial sync                                          │
│     └── python scripts/pipeline.py --all --client {id}       │
│                                                               │
│  4. Transform data                                           │
│     └── cd dbt && dbt run --vars '{"client_id": "{id}"}'     │
│                                                               │
│  5. Verify in Metabase                                        │
│     └── Add database → Create dashboard                      │
│                                                               │
│  6. Schedule automation                                      │
│     └── python prefect/deployments/marketing_analytics.py    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## dbt Usage

### Install Dependencies

```bash
cd dbt
dbt deps
```

### Run Models

```bash
# All models for default client
dbt run

# Specific client
dbt run --vars '{"client_id": "client2"}'

# Specific model
dbt run --select stg_facebook__ads

# Mart models only
dbt run --select marts+
```

### Test Models

```bash
# All tests
dbt test

# Specific model tests
dbt test --select stg_facebook__ads

# Generate docs
dbt docs generate
dbt docs serve
```

### dbt Project Structure

```
dbt/
├── models/
│   ├── staging/          # Source-conformed models
│   │   ├── ga4/
│   │   ├── facebook/
│   │   └── prestashop/
│   └── marts/            # Business-conformed models
│       └── marketing/
├── macros/               # Custom macros
└── tests/               # Custom tests
```

## Prefect Usage

### Start Prefect Server

```bash
# Start server
docker compose up -d prefect-server prefect-worker

# Access UI
open http://localhost:4200
```

### Deploy Pipeline

```bash
# Deploy for specific client
python prefect/deployments/marketing_analytics.py --client client1

# Deploy for all clients
python prefect/deployments/marketing_analytics.py --all
```

### Manual Trigger

```bash
# Via Prefect UI or CLI
prefect flow-run create -f marketing_analytics_pipeline -p client_id=client1
```

## Metabase Dashboards

### Pre-built Dashboards

1. **Marketing Performance**
   - Channel comparison
   - ROAS by campaign
   - Spend vs Revenue

2. **E-commerce**
   - Orders trend
   - Customer metrics
   - Product performance

### Building Custom Questions

1. Navigate to Metabase
2. Click **+ New** → **Question**
3. Select **Native Query** for SQL
4. Write your query
5. Click **Save**

### Sample Queries

**Daily Revenue by Channel:**
```sql
SELECT 
    date,
    channel,
    SUM(revenue) as revenue
FROM marts.fct_marketing_performance
GROUP BY 1, 2
ORDER BY 1 DESC
```

**Top Campaigns by ROAS:**
```sql
SELECT 
    channel,
    campaign_name,
    SUM(revenue) / NULLIF(SUM(spend), 0) as roas,
    SUM(spend) as spend,
    SUM(revenue) as revenue
FROM marts.fct_marketing_performance
WHERE date >= CURRENT_DATE - 30
GROUP BY 1, 2
ORDER BY roas DESC
LIMIT 20
```

## Data Quality

### Running Quality Checks

```bash
# Via dbt
dbt test

# Via Great Expectations (if configured)
great_expectations checkpoint run marketing_checkpoint
```

### Quality Metrics

| Metric | Target | Alert Threshold |
|--------|--------|------------------|
| Row count variance | ±5% | ±10% |
| Null percentage | <1% | >5% |
| Freshness | <24h | >48h |
| Revenue negative | 0 | >0 |

## Troubleshooting

### Pipeline Failures

```bash
# Check logs
docker logs metabase
docker logs metabase-db

# Check pipeline logs
cat logs/pipeline_client1.log

# Manual sync
python scripts/pipeline.py --source ga4 --client client1 --dry-run
```

### dbt Issues

```bash
# Debug connection
dbt debug

# Clean and rebuild
dbt clean
dbt deps
dbt run

# Check logs
cat target/run_results.json
```

### Metabase Issues

```bash
# Check health
curl http://localhost:8096/api/health

# View logs
docker logs metabase
```

## Security

### Credential Management

- **Never commit** `.env` files
- Use **SOPS/ansible-vault** for production secrets
- Rotate API keys quarterly
- Use read-only API keys where possible

### Access Control

| Role | Access |
|------|--------|
| Viewer | Metabase dashboards (read-only) |
| Analyst | Metabase + SQL queries |
| Engineer | All services + deployments |

## Support

- **Documentation**: `/docs` directory
- **Runbooks**: `/docs/runbooks` directory
- **Issues**: GitHub Issues

## Quick Reference

```bash
# Daily operations
python scripts/pipeline.py --all --client client1    # Run ETL
cd dbt && dbt run && dbt test                       # Transform & test
docker compose logs -f                              # View logs

# Maintenance
docker compose down && docker compose up -d         # Restart
dbt clean && dbt deps && dbt run                    # Reset dbt
docker system prune                                # Clean up

# Monitoring
curl http://localhost:8096/api/health              # Metabase health
docker stats                                       # Container stats
```
