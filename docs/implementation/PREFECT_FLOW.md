# Prefect Orchestration Flow

Workflow automation for marketing analytics pipeline.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Prefect Server                           │
│                    (Port 4200)                              │
└─────────────────────────────┬───────────────────────────────┘
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Docker Work Pool                          │
│                  (marketing-pool)                           │
└─────────────────────────────┬───────────────────────────────┘
                              │ Poll
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Prefect Worker                            │
│                 (Docker container)                          │
└─────────────────────────────┬───────────────────────────────┘
                              │ Execute
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Pipeline Tasks                           │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   │
│  │  Sync   │ → │  Sync   │ → │  Sync   │ → │  dbt    │   │
│  │  GA4    │   │ FB Ads  │   │ Presta  │   │  run    │   │
│  └─────────┘   └─────────┘   └─────────┘   └────┬────┘   │
│                                                   │         │
│                     ┌─────────────────────────────┘         │
│                     ▼                                       │
│              ┌───────────┐   ┌─────────────┐               │
│              │   dbt     │ → │   dbt       │               │
│              │   test    │   │   docs      │               │
│              └───────────┘   └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## Flow Definition

```python
"""
Marketing Analytics Pipeline Flow

Orchestrates ETL from GA4, Facebook Ads, and PrestaShop
through to dbt transformations and quality checks.
"""

import logging
from datetime import datetime, timedelta
from typing import Literal

from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from prefect.runtime import flow as flow_runtime

logger = logging.getLogger(__name__)


@task(
    name="sync-ga4",
    retries=2,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
    timeout_seconds=600,
)
def sync_ga4(client_id: str, date_range: str = "last_90_days") -> dict:
    """
    Sync Google Analytics 4 data for client.
    
    Args:
        client_id: Client identifier for environment file
        date_range: Reporting date range preset
        
    Returns:
        Sync result with row counts and timestamps
    """
    import subprocess
    import os
    
    logger = get_run_logger()
    logger.info(f"Starting GA4 sync for {client_id}")
    
    result = subprocess.run(
        [
            "python", "scripts/pipeline.py",
            "--client", client_id,
            "--source", "ga4",
            "--date-range", date_range
        ],
        capture_output=True,
        text=True,
        cwd="/var/www/meta.expc.cz"
    )
    
    if result.returncode != 0:
        logger.error(f"GA4 sync failed: {result.stderr}")
        raise RuntimeError(f"GA4 sync failed: {result.stderr}")
    
    logger.info(f"GA4 sync completed: {result.stdout}")
    return {"source": "ga4", "status": "success", "output": result.stdout}


@task(
    name="sync-facebook-ads",
    retries=2,
    retry_delay_seconds=60,
    timeout_seconds=600,
)
def sync_facebook_ads(client_id: str) -> dict:
    """
    Sync Facebook Ads data for client.
    
    Args:
        client_id: Client identifier
        
    Returns:
        Sync result
    """
    import subprocess
    
    logger = get_run_logger()
    logger.info(f"Starting Facebook Ads sync for {client_id}")
    
    result = subprocess.run(
        [
            "python", "scripts/pipeline.py",
            "--client", client_id,
            "--source", "facebook"
        ],
        capture_output=True,
        text=True,
        cwd="/var/www/meta.expc.cz"
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Facebook sync failed: {result.stderr}")
    
    return {"source": "facebook", "status": "success"}


@task(
    name="sync-prestashop",
    retries=2,
    retry_delay_seconds=60,
    timeout_seconds=900,
)
def sync_prestashop(client_id: str) -> dict:
    """
    Sync PrestaShop orders and customers.
    
    Args:
        client_id: Client identifier
        
    Returns:
        Sync result
    """
    import subprocess
    
    logger = get_run_logger()
    logger.info(f"Starting PrestaShop sync for {client_id}")
    
    result = subprocess.run(
        [
            "python", "scripts/pipeline.py",
            "--client", client_id,
            "--source", "prestashop"
        ],
        capture_output=True,
        text=True,
        cwd="/var/www/meta.expc.cz"
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"PrestaShop sync failed: {result.stderr}")
    
    return {"source": "prestashop", "status": "success"}


@task(
    name="run-dbt-models",
    retries=1,
    retry_delay_seconds=120,
    timeout_seconds=900,
)
def run_dbt_models(client_id: str, full_refresh: bool = False) -> dict:
    """
    Run dbt transformation models.
    
    Args:
        client_id: Client identifier for variable passing
        full_refresh: Force full materialization
        
    Returns:
        dbt run result
    """
    import subprocess
    
    logger = get_run_logger()
    logger.info(f"Running dbt models for {client_id}")
    
    cmd = [
        "dbt", "run",
        "--target", "prod",
        "--vars", f'{{"client_id": "{client_id}"}}'
    ]
    
    if full_refresh:
        cmd.append("--full-refresh")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd="/var/www/meta.expc.cz/dbt"
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"dbt run failed: {result.stderr}")
    
    return {"step": "dbt_run", "status": "success"}


@task(
    name="run-dbt-tests",
    retries=0,  # No retries for tests
    timeout_seconds=300,
)
def run_dbt_tests(client_id: str) -> dict:
    """
    Run dbt data quality tests.
    
    Args:
        client_id: Client identifier
        
    Returns:
        dbt test results
    """
    import subprocess
    
    logger = get_run_logger()
    logger.info(f"Running dbt tests for {client_id}")
    
    result = subprocess.run(
        [
            "dbt", "test",
            "--target", "prod",
            "--vars", f'{{"client_id": "{client_id}"}}'
        ],
        capture_output=True,
        text=True,
        cwd="/var/www/meta.expc.cz/dbt"
    )
    
    # Tests failing should halt pipeline
    if result.returncode != 0:
        logger.error(f"dbt tests failed: {result.stderr}")
        raise RuntimeError(f"dbt tests failed: {result.stderr}")
    
    return {"step": "dbt_test", "status": "success"}


@flow(
    name="marketing-analytics-pipeline",
    description="End-to-end marketing analytics ETL pipeline",
    log_prints=True,
    on_cancellation_hook=None,
)
def marketing_pipeline(
    client_id: str,
    sources: list[str] | None = None,
    run_tests: bool = True,
    full_refresh: bool = False,
) -> dict:
    """
    Main pipeline orchestrator.
    
    Args:
        client_id: Client identifier
        sources: List of sources to sync (default: all)
        run_tests: Whether to run dbt tests
        full_refresh: Force full dbt refresh
        
    Returns:
        Pipeline execution summary
    """
    logger = get_run_logger()
    flow_name = flow_runtime.get_flow_name()
    
    logger.info(f"Starting {flow_name} for client: {client_id}")
    
    if sources is None:
        sources = ["ga4", "facebook", "prestashop"]
    
    results = {"client_id": client_id, "started_at": datetime.utcnow().isoformat()}
    
    # Sync sources in parallel
    sync_results = []
    
    if "ga4" in sources:
        sync_results.append(sync_ga4(client_id))
    
    if "facebook" in sources:
        sync_results.append(sync_facebook_ads(client_id))
    
    if "prestashop" in sources:
        sync_results.append(sync_prestashop(client_id))
    
    results["sync"] = sync_results
    
    # Transform
    results["transform"] = run_dbt_models(client_id, full_refresh)
    
    # Quality checks
    if run_tests:
        results["quality"] = run_dbt_tests(client_id)
    
    results["completed_at"] = datetime.utcnow().isoformat()
    
    logger.info(f"Pipeline completed: {results}")
    
    return results


# Deployment entrypoint
if __name__ == "__main__":
    from prefect.deployments import Deployment
    from prefect.filesystems import LocalFileSystem
    
    deployment = Deployment.build_from_flow(
        flow=marketing_pipeline,
        name="marketing-analytics-prod",
        version="1.0.0",
        work_pool_name="marketing-pool",
        work_queue_name="default",
        infrastructure={"type": "docker-container"},
        storage=LocalFileSystem(basepath="/var/www/meta.expc.cz/prefect"),
        schedule={"rrule": "FREQ=DAILY;BYHOUR=2;BYMINUTE=30"},
        parameters={
            "run_tests": True,
            "full_refresh": False,
        },
        description="Daily marketing analytics ETL pipeline",
    )
    
    deployment.apply()
```

## Retry Policy

| Task | Retries | Delay | Backoff |
|------|---------|-------|---------|
| sync_ga4 | 2 | 60s | Exponential |
| sync_facebook_ads | 2 | 60s | Exponential |
| sync_prestashop | 2 | 60s | Exponential |
| run_dbt_models | 1 | 120s | Fixed |
| run_dbt_tests | 0 | - | - |

## Scheduling

```bash
# Daily at 02:30 UTC (before Metabase backup at 03:00)
FREQ=DAILY;BYHOUR=2;BYMINUTE=30

# Staggered for multiple clients
client1: 02:30
client2: 03:00
client3: 03:30
```

## Deployment Commands

```bash
# Deploy flow
cd /var/www/meta.expc.cz/prefect
python deploy_pipeline.py

# Trigger manually
prefect deployment run marketing-analytics-pipeline/prod -p client_id=client1

# View runs
prefect flow-runs list

# View logs
prefect logs --flow-run-id <run-id>
```
