# Prefect 3.x Deployment Best Practices

**Date**: 2026-04-08  
**Purpose**: Fix deployment configuration and document best practices for Prefect 3.x

---

## Executive Summary

**Current Issue**: The README instructs `prefect deployment apply deployments/marketing_analytics.py`, but `prefect deployment apply` expects YAML files, not Python files. This command will fail in Prefect 3.x.

**Root Cause**: The `Deployment` class and `prefect deployment build/apply` commands were **deprecated in Prefect 3.x** (PR #12283) and removed.

**Recommended Solution**: Use `flow.deploy()` Python API method for programmatic deployments.

---

## Prefect 3.x Deployment Methods Comparison

### Method 1: `prefect.yaml` + `prefect deploy` CLI

**Best for**: Declarative, version-controlled deployments

```yaml
# prefect.yaml
prefect-version: 3.x

deployments:
  - name: marketing-analytics-daily
    entrypoint: prefect/flows/marketing_pipeline.py:marketing_analytics_pipeline
    schedule:
      cron: "0 2 * * *"
      timezone: Europe/Prague
    work_pool:
      name: docker-pool
    parameters:
      client_id: client1
      sources: [ga4, gads, fbads, prestashop]
```

```bash
# Deploy
prefect deploy --all
# Or specific deployment
prefect deploy --name marketing-analytics-daily
```

### Method 2: `flow.deploy()` Python API (RECOMMENDED)

**Best for**: Programmatic deployments, CI/CD pipelines, multi-client setups

```python
# prefect/deployments/marketing_analytics.py
from prefect import flow

@flow(log_prints=True)
def marketing_analytics_pipeline(client_id: str, sources: list[str] | None = None):
    # ... flow implementation
    pass

if __name__ == "__main__":
    marketing_analytics_pipeline.deploy(
        name="marketing-analytics-daily",
        work_pool_name="docker-pool",
        cron="0 2 * * *",
        timezone="Europe/Prague",
        parameters={
            "client_id": "client1",
            "sources": ["ga4", "gads", "fbads", "prestashop"],
        },
        job_variables={
            "image": "prefecthq/prefect:3-latest",
            "env": {
                "PREFECT_LOGGING_LEVEL": "INFO",
                "DBT_PROFILES_DIR": "/var/www/meta.expc.cz/dbt",
            },
            "volumes": ["/var/www/meta.expc.cz:/var/www/meta.expc.cz:ro"],
            "working_dir": "/var/www/meta.expc.cz",
        },
    )
```

```bash
python prefect/deployments/marketing_analytics.py
```

---

## Deprecation Timeline

| Version | Status | Commands |
|---------|--------|----------|
| Prefect 2.x | Deprecated | `prefect deployment build`, `prefect deployment apply` |
| Prefect 3.0+ | **Removed** | These commands no longer exist |

### Error You'll See

If you try `prefect deployment apply` in Prefect 3.x:
```
Error: 'Deployment' class and deployment build/apply commands have been removed.
Use 'prefect deploy' or 'flow.deploy()' instead.
```

---

## Path Handling Best Practices

### Entrypoint Format

Prefect 3.x supports two formats for referencing flows:

#### File Path (relative to project root)
```yaml
entrypoint: prefect/flows/marketing_pipeline.py:marketing_analytics_pipeline
```

#### Module Path (for installed packages)
```yaml
entrypoint: my_package.flows.marketing_pipeline:marketing_analytics_pipeline
```

### Project Root Configuration

**Critical**: When using `prefect deploy`, the project root is determined by:
1. The directory containing `prefect.yaml`
2. The directory where you run the command
3. Can be overridden with `--prefect-file` flag

```bash
# Use custom prefect.yaml location
cd /var/www/meta.expc.cz
prefect deploy --prefect-file prefect/prefect.yaml --name marketing-analytics-daily
```

### Docker Pool Job Variables

For `docker-pool`, the `entrypoint` path must be accessible within the container:

```python
job_variables={
    "working_dir": "/var/www/meta.expc.cz",
    "volumes": ["/var/www/meta.expc.cz:/var/www/meta.expc.cz:ro"],
    # The entrypoint should be relative to working_dir
}
```

**Recommended**: Mount project directory and set `working_dir`:

```python
job_variables={
    "working_dir": "/var/www/meta.expc.cz",
    "volumes": [
        "/var/www/meta.expc.cz:/var/www/meta.expc.cz:ro",
    ],
    "env": {
        "PYTHONPATH": "/var/www/meta.expc.cz",
    },
}
```

---

## Work Pool Configuration

### Docker Pool Setup

```bash
# Create docker pool
prefect work-pool create docker-pool --type docker
```

### Recommended Job Variables

```python
DOCKER_POOL_CONFIG = {
    "image": "prefecthq/prefect:3-latest",
    "env": {
        "PREFECT_LOGGING_LEVEL": "INFO",
        "PREFECT_API_URL": "http://host.docker.internal:4200/api",
        "DBT_PROFILES_DIR": "/var/www/meta.expc.cz/dbt",
        "PYTHONPATH": "/var/www/meta.expc.cz",
    },
    "volumes": [
        "/var/www/meta.expc.cz:/var/www/meta.expc.cz:ro",
        "/var/www/meta.expc.cz/.env:/var/www/meta.expc.cz/.env:ro",
    ],
    "working_dir": "/var/www/meta.expc.cz",
    "memory": "4g",
    "cpu": "2.0",
    "auto_remove": True,
    "network_mode": "host",  # For localhost access
}
```

### Key Configuration Points

| Variable | Purpose | Notes |
|----------|---------|-------|
| `image` | Docker image for execution | Use `prefecthq/prefect:3-latest` or custom image |
| `working_dir` | Working directory in container | Must contain flow code |
| `volumes` | Mount local files | Mount project dir and .env |
| `network_mode` | Network configuration | `host` for localhost access |
| `env` | Environment variables | Set API URL, paths, credentials |

---

## Recommended Approach for This Project

### 1. Migrate to `flow.deploy()` Pattern

**File: `prefect/deployments/marketing_analytics.py`** (updated):

```python
"""
Prefect 3.x deployment configuration for marketing analytics pipeline.
Uses flow.deploy() API (Prefect 3.x recommended approach).
"""

from prefect import flow, get_client
from prefect.schedules import CronSchedule

# Import the flow from flows module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from prefect.flows.marketing_pipeline import marketing_analytics_pipeline


def deploy_marketing_pipeline(
    client_id: str = "client1",
    schedule: str = "0 2 * * *",
    timezone: str = "Europe/Prague",
):
    """
    Deploy the marketing analytics pipeline.
    
    Args:
        client_id: Client identifier
        schedule: Cron schedule string
        timezone: Timezone for schedule
    """
    marketing_analytics_pipeline.deploy(
        name=f"marketing-analytics-{client_id}",
        work_pool_name="docker-pool",
        cron=schedule,
        timezone=timezone,
        parameters={
            "client_id": client_id,
            "sources": ["ga4", "gads", "fbads", "prestashop"],
        },
        tags=["marketing", "analytics", "daily"],
        description="Daily marketing analytics pipeline: dlt syncs → dbt models → dbt tests",
        job_variables={
            "image": "prefecthq/prefect:3-latest",
            "env": {
                "PREFECT_LOGGING_LEVEL": "INFO",
                "DBT_PROFILES_DIR": "/var/www/meta.expc.cz/dbt",
                "PYTHONPATH": "/var/www/meta.expc.cz",
            },
            "volumes": [
                "/var/www/meta.expc.cz:/var/www/meta.expc.cz:ro",
            ],
            "working_dir": "/var/www/meta.expc.cz",
            "memory": "4g",
            "cpu": "2.0",
            "network_mode": "host",
        },
    )


def deploy_all_clients():
    """Deploy pipelines for all clients."""
    clients = [
        {"client_id": "client1", "sources": ["ga4", "gads", "fbads", "prestashop"]},
        {"client_id": "client2", "sources": ["ga4", "gads", "fbads"]},
    ]
    
    for client in clients:
        print(f"Deploying pipeline for {client['client_id']}...")
        marketing_analytics_pipeline.with_options(
            parameters={"client_id": client["client_id"], "sources": client["sources"]}
        ).deploy(
            name=f"marketing-analytics-{client['client_id']}",
            work_pool_name="docker-pool",
            cron="0 2 * * *",
            timezone="Europe/Prague",
            tags=["marketing", "analytics", "daily"],
            job_variables={
                "image": "prefecthq/prefect:3-latest",
                "env": {
                    "PREFECT_LOGGING_LEVEL": "INFO",
                    "DBT_PROFILES_DIR": "/var/www/meta.expc.cz/dbt",
                },
                "volumes": ["/var/www/meta.expc.cz:/var/www/meta.expc.cz:ro"],
                "working_dir": "/var/www/meta.expc.cz",
            },
        )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy marketing analytics pipeline")
    parser.add_argument("--client", default="client1", help="Client ID")
    parser.add_argument("--all", action="store_true", help="Deploy all clients")
    args = parser.parse_args()
    
    if args.all:
        deploy_all_clients()
    else:
        deploy_marketing_pipeline(client_id=args.client)
```

### 2. Alternative: Use `prefect.yaml` (Declarative)

**File: `prefect/prefect.yaml`**:

```yaml
prefect-version: "3.x"
name: marketing-analytics

deployments:
  - name: marketing-analytics-client1
    entrypoint: prefect/flows/marketing_pipeline.py:marketing_analytics_pipeline
    schedule:
      cron: "0 2 * * *"
      timezone: Europe/Prague
    work_pool:
      name: docker-pool
      job_variables:
        image: prefecthq/prefect:3-latest
        working_dir: /var/www/meta.expc.cz
        volumes:
          - /var/www/meta.expc.cz:/var/www/meta.expc.cz:ro
        env:
          PREFECT_LOGGING_LEVEL: INFO
          DBT_PROFILES_DIR: /var/www/meta.expc.cz/dbt
          PYTHONPATH: /var/www/meta.expc.cz
        memory: 4g
        cpu: "2.0"
        network_mode: host
    parameters:
      client_id: client1
      sources:
        - ga4
        - gads
        - fbads
        - prestashop
    tags:
      - marketing
      - analytics
      - daily
    description: Daily marketing analytics pipeline for client1

  - name: marketing-analytics-client2
    entrypoint: prefect/flows/marketing_pipeline.py:marketing_analytics_pipeline
    schedule:
      cron: "0 3 * * *"
      timezone: Europe/Prague
    work_pool:
      name: docker-pool
      job_variables:
        image: prefecthq/prefect:3-latest
        working_dir: /var/www/meta.expc.cz
        volumes:
          - /var/www/meta.expc.cz:/var/www/meta.expc.cz:ro
        env:
          PREFECT_LOGGING_LEVEL: INFO
          DBT_PROFILES_DIR: /var/www/meta.expc.cz/dbt
          PYTHONPATH: /var/www/meta.expc.cz
        memory: 4g
        cpu: "2.0"
        network_mode: host
    parameters:
      client_id: client2
      sources:
        - ga4
        - gads
        - fbads
    tags:
      - marketing
      - analytics
      - daily
    description: Daily marketing analytics pipeline for client2
```

**Deploy command**:
```bash
cd /var/www/meta.expc.cz
prefect deploy --all
# Or specific deployment
prefect deploy --name marketing-analytics-client1
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/prefect-deploy.yml
name: Deploy Prefect Flows

on:
  push:
    branches: [main]
    paths:
      - 'prefect/**'
      - 'flows/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install Prefect
        run: pip install prefect prefect-docker
        
      - name: Configure Prefect API
        run: |
          prefect config set PREFECT_API_URL=${{ secrets.PREFECT_API_URL }}
          prefect config set PREFECT_API_KEY=${{ secrets.PREFECT_API_KEY }}
          
      - name: Deploy flows
        run: |
          cd prefect
          python deployments/marketing_analytics.py --all
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `Deployment class not found` | Using old API | Migrate to `flow.deploy()` |
| `Flow not found` | Wrong entrypoint path | Check path relative to project root |
| `Module import error` | Missing PYTHONPATH | Set in job_variables or mount |
| `File not found` | Volume not mounted | Add volume in job_variables |

### Debug Commands

```bash
# Check Prefect version
prefect version

# List deployments
prefect deployment ls

# Inspect deployment
prefect deployment inspect marketing-analytics-client1

# Run flow locally
python prefect/flows/marketing_pipeline.py

# Test work pool
prefect work-pool inspect docker-pool
```

---

## Summary of Changes Needed

### Files to Update

1. **`prefect/README.md`**: Replace deployment instructions
2. **`prefect/deployments/marketing_analytics.py`**: Migrate to `flow.deploy()` pattern
3. **`prefect/setup_work_pool.py`**: Update instructions

### Quick Fix Commands

```bash
# Install prerequisites
pip install prefect prefect-docker

# Set up work pool (if not exists)
prefect work-pool create docker-pool --type docker

# Deploy using Python API (recommended)
cd /var/www/meta.expc.cz
python prefect/deployments/marketing_analytics.py --client client1

# Or deploy all clients
python prefect/deployments/marketing_analytics.py --all

# Alternative: Use prefect.yaml
cd /var/www/meta.expc.cz
prefect deploy --all --prefect-file prefect/prefect.yaml
```

---

## References

- [Prefect 3.x Deploy via Python](https://docs.prefect.io/v3/how-to-guides/deployments/deploy-via-python)
- [Prefect YAML Deployments](https://docs.prefect.io/v3/how-to-guides/deployments/prefect-yaml)
- [Deprecation PR #12283](https://github.com/PrefectHQ/prefect/pull/12283)
- [Prefect Work Pools](https://docs.prefect.io/v3/concepts/work-pools/)
