# Prefect Configuration

This directory contains Prefect 3.x orchestration for the marketing analytics pipeline.

## Structure

```
prefect/
├── flows/                    # Flow definitions
│   └── marketing_pipeline.py # Main pipeline flow
├── deployments/              # Deployment configurations
│   └── marketing_analytics.py
├── blocks/                   # Prefect blocks for credentials
│   └── __init__.py
├── setup_work_pool.py        # Work pool setup script
└── docker-pool.yaml          # Docker work pool config (generated)
```

## Quick Start

### 1. Install Prefect

```bash
pip install prefect prefect-dbt
```

### 2. Set up Work Pool

```bash
python prefect/setup_work_pool.py
```

Or manually:
```bash
prefect work-pool create docker-pool --type docker
```

### 3. Start Prefect Server

```bash
prefect server start
```

### 4. Start Worker

```bash
prefect worker start --pool docker-pool
```

### 5. Deploy Flow

**Option A: Using Python API (Recommended for Prefect 3.x)**

```bash
cd /var/www/meta.expc.cz
python prefect/deployments/marketing_analytics.py --client client1

# Or deploy all clients
python prefect/deployments/marketing_analytics.py --all
```

**Option B: Using prefect.yaml (Declarative)**

```bash
cd /var/www/meta.expc.cz
prefect deploy --all --prefect-file prefect/prefect.yaml
```

> **Note**: `prefect deployment apply` is deprecated in Prefect 3.x. Use `flow.deploy()` or `prefect deploy` instead.

## Running Flows

### Via CLI

```bash
# Run with default parameters
prefect deployment run marketing-analytics-pipeline/marketing-analytics-daily

# Run with custom parameters
prefect deployment run marketing-analytics-pipeline/marketing-analytics-daily \
  --params '{"client_id": "client1", "sources": ["ga4", "gads"]}'
```

### Via Python

```python
from flows.marketing_pipeline import marketing_analytics_pipeline

result = marketing_analytics_pipeline(
    client_id="client1",
    sources=["ga4", "gads", "fbads", "prestashop"],
)
```

## Schedule

- **Default**: Daily at 2:00 AM Europe/Prague
- **Cron**: `0 2 * * *`

## Multi-Client Support

The pipeline supports multiple clients via the `client_id` parameter:

```python
# Client 1 - all sources
marketing_analytics_pipeline(client_id="client1")

# Client 2 - subset of sources
marketing_analytics_pipeline(
    client_id="client2",
    sources=["ga4", "gads", "fbads"]
)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Prefect Orchestration                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   run_dlt    │  │   run_dlt    │  │   run_dlt    │       │
│  │    ga4       │  │    gads      │  │    fbads     │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            ▼                                 │
│                   ┌──────────────────┐                       │
│                   │  run_dbt_models  │                       │
│                   └────────┬─────────┘                       │
│                            ▼                                 │
│                   ┌──────────────────┐                       │
│                   │   run_dbt_tests  │                       │
│                   └──────────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling

- **dlt syncs**: 3 retries with 60s delay
- **dbt run**: 2 retries with 30s delay
- **dbt test**: 1 retry with 30s delay
- **Fail fast**: Any task failure stops the pipeline

## Environment Variables

Required in execution environment:

```bash
PREFECT_API_URL=http://localhost:4200/api
PREFECT_LOGGING_LEVEL=INFO
DBT_PROFILES_DIR=/var/www/meta.expc.cz/dbt
```
