"""
Prefect 3.x flow for orchestrating marketing analytics pipeline.
Orchestrates dlt syncs → dbt models → dbt tests.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

from prefect import flow, get_run_logger, task


def exponential_backoff(backoff_factor: float = 2):
    """Calculate exponential backoff delay for retries."""

    def backoff_func(retries: int) -> float:
        return backoff_factor**retries

    return backoff_func


logging.basicConfig(level=logging.INFO)

# Constants - auto-detect environment
import os

if os.path.exists("/var/www/meta.expc.cz"):
    PROJECT_ROOT = Path("/var/www/meta.expc.cz")
elif os.path.exists("/workspace"):
    PROJECT_ROOT = Path("/workspace")
else:
    PROJECT_ROOT = Path(__file__).parent.parent.parent

DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"
PIPELINE_SCRIPT = PROJECT_ROOT / "scripts" / "pipeline.py"


@task(
    retries=3,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
    retry_jitter_factor=0.3,
    timeout_seconds=600,  # 10 min for dlt sync
)
def run_dlt_sync(source_name: str, client_id: str) -> dict[str, Any]:
    """
    Run dlt sync for a specific source and client.

    Args:
        source_name: One of 'ga4', 'gads', 'fbads', 'prestashop'
        client_id: Client identifier (e.g., 'client1')

    Returns:
        Dict with execution results
    """
    logger = get_run_logger()
    logger.info(f"Starting dlt sync: {source_name} for client {client_id}")

    cmd = [
        "python",
        str(PIPELINE_SCRIPT),
        "--source",
        source_name,
        "--client",
        client_id,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT,
        )
        logger.info(f"dlt sync {source_name} completed successfully")
        return {
            "source": source_name,
            "client_id": client_id,
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"dlt sync {source_name} failed: {e}")
        raise RuntimeError(f"dlt sync failed for {source_name}: {e.stderr}") from e


@task(
    retries=2,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
    retry_jitter_factor=0.3,
    timeout_seconds=900,  # 15 min for dbt run
)
def run_dbt_models(project_dir: Path, models: str | None = None) -> dict[str, Any]:
    """
    Run dbt models.

    Args:
        project_dir: Path to dbt project directory
        models: Optional model selector (e.g., '+my_model')

    Returns:
        Dict with execution results
    """
    logger = get_run_logger()
    logger.info(f"Running dbt models in {project_dir}")

    # Build dbt run command
    cmd = ["dbt", "run", "--project-dir", str(project_dir)]
    if models:
        cmd.extend(["--select", models])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_dir,
        )
        logger.info("dbt run completed successfully")
        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"dbt run failed: {e}")
        raise RuntimeError(f"dbt run failed: {e.stderr}") from e


@task(
    retries=1,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
    retry_jitter_factor=0.3,
    timeout_seconds=300,  # 5 min for dbt test
)
def run_dbt_tests(project_dir: Path) -> dict[str, Any]:
    """
    Run dbt tests for all models.

    Args:
        project_dir: Path to dbt project directory

    Returns:
        Dict with execution results
    """
    logger = get_run_logger()
    logger.info(f"Running dbt tests in {project_dir}")

    cmd = ["dbt", "test", "--project-dir", str(project_dir)]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_dir,
        )
        logger.info("dbt test completed successfully")
        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"dbt test failed: {e}")
        raise RuntimeError(f"dbt test failed: {e.stderr}") from e


@flow(
    name="marketing_analytics_pipeline",
    description="Orchestrates dlt syncs → dbt models → dbt tests",
    log_prints=True,
)
def marketing_analytics_pipeline(
    client_id: str,
    sources: list[str] | None = None,
    dbt_models: str | None = None,
) -> dict[str, Any]:
    """
    Main marketing analytics pipeline flow.

    Orchestration:
    1. Run all dlt syncs (GA4, GAds, FB Ads, PrestaShop)
    2. Run dbt models (sequential - depends on all syncs)
    3. Run dbt tests (sequential - depends on dbt models)

    Args:
        client_id: Client identifier (e.g., 'client1')
        sources: List of sources to sync (default: all)
        dbt_models: Optional dbt model selector

    Returns:
        Dict with all execution results
    """
    logger = get_run_logger()
    logger.info(f"Starting marketing analytics pipeline for client: {client_id}")

    # Default to all sources if not specified
    if sources is None:
        sources = ["ga4", "gads", "fbads", "prestashop"]

    # Phase 1: Run dlt syncs in parallel
    logger.info(f"Phase 1: Running dlt syncs for sources: {sources}")
    futures = [run_dlt_sync.submit(s, client_id) for s in sources]
    sync_results = [f.result() for f in futures]
    logger.info(f"All dlt syncs completed: {len(sync_results)} sources")

    # Phase 2: Run dbt models (depends on all syncs)
    logger.info("Phase 2: Running dbt models")
    dbt_run_result = run_dbt_models(DBT_PROJECT_DIR, dbt_models)

    # Phase 3: Run dbt tests (depends on dbt models)
    logger.info("Phase 3: Running dbt tests")
    dbt_test_result = run_dbt_tests(DBT_PROJECT_DIR)

    # Compile results
    results = {
        "client_id": client_id,
        "sources": sources,
        "sync_results": sync_results,
        "dbt_run": dbt_run_result,
        "dbt_test": dbt_test_result,
    }

    logger.info("Marketing analytics pipeline completed successfully")
    return results


if __name__ == "__main__":
    # Example local execution
    result = marketing_analytics_pipeline(
        client_id="client1",
        sources=["ga4", "gads"],
    )
    print(f"Pipeline result: {result}")
