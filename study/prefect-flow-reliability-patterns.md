# Prefect Flow Reliability Patterns

## Research Date
2026-04-08

## Context
Current issues in the pipeline:
1. Sequential dlt syncs (should be parallel)
2. No subprocess timeouts (risk of hangs)
3. Need proper retry policies

---

## 1. Parallel Task Execution

### 1.1 The `task.submit()` Pattern

The key to parallel execution in Prefect is using `.submit()` instead of calling tasks directly. Direct calls block sequentially.

```python
from prefect import flow, task
from prefect.futures import wait

@task
def sync_ga4():
    """Sync Google Analytics 4 data"""
    pass

@task
def sync_gads():
    """Sync Google Ads data"""
    pass

@flow
def etl_pipeline():
    # WRONG - Sequential execution (blocks)
    # sync_ga4()
    # sync_gads()
    
    # CORRECT - Parallel execution
    ga4_future = sync_ga4.submit()
    gads_future = sync_gads.submit()
    
    # Wait for both to complete
    wait([ga4_future, gads_future])
```

### 1.2 Parallel Execution for Multiple Sources

```python
from prefect import flow, task
from prefect.futures import wait

@task
def sync_source(source: str):
    """Sync a single data source"""
    pass

@flow
def sync_all_sources(sources: list[str]):
    """Run all source syncs in parallel"""
    futures = [sync_source.submit(source=s) for s in sources]
    wait(futures)
    
    # Collect results
    results = [f.result() for f in futures]
    return results
```

### 1.3 Handling Failures in Parallel Tasks

```python
from prefect import flow, task
from prefect.futures import wait
from prefect.states import State

@task
def sync_source(source: str):
    """Sync a single data source - may fail"""
    if source == "problematic_source":
        raise ConnectionError(f"Failed to sync {source}")
    return f"Sync completed for {source}"

@flow
def robust_sync(sources: list[str]):
    futures = [sync_source.submit(source=s) for s in sources]
    done, not_done = wait(futures)
    
    successful = []
    failed = []
    
    for future in done:
        if future.state.is_completed():
            successful.append(future.result())
        else:
            failed.append({
                "source": future.task_parameters.get("source"),
                "state": future.state
            })
    
    print(f"Successful: {len(successful)}, Failed: {len(failed)}")
    
    if failed:
        # Decide: raise, continue with partial, or notify
        raise Exception(f"Failed sources: {[f['source'] for f in failed]}")
    
    return successful
```

### 1.4 asyncio Approach

For async tasks, use `asyncio.gather()`:

```python
import asyncio
from prefect import flow, task

@task
async def sync_source(source: str):
    """Async sync task"""
    await asyncio.sleep(1)  # Simulate async work
    return f"Sync completed for {source}"

@flow
async def async_etl_pipeline(sources: list[str]):
    results = await asyncio.gather(*[
        sync_source(source=s) for s in sources
    ])
    return results
```

**Recommendation**: Use `.submit()` with `wait()` for sync tasks. This is the most reliable pattern for subprocess-based operations like dlt and dbt.

---

## 2. Subprocess Timeouts

### 2.1 Timeout Values by Task Type

| Task Type | Recommended Timeout | Rationale |
|-----------|---------------------|------------|
| **dlt sync** (small) | 300 seconds (5 min) | Simple API sync with minimal data |
| **dlt sync** (medium) | 600 seconds (10 min) | Standard GA4/Ads sync |
| **dlt sync** (large) | 1800 seconds (30 min) | Large full syncs, complex sources |
| **dbt run** | 900 seconds (15 min) | Medium-sized model runs |
| **dbt run** (large) | 3600 seconds (60 min) | Large models, complex transformations |
| **dbt test** | 300 seconds (5 min) | Tests should be fast |
| **dbt source freshness** | 120 seconds (2 min) | Quick metadata check |

### 2.2 Timeout Configuration

```python
from prefect import task, flow

@task(timeout_seconds=600)  # 10 minute timeout
def sync_ga4():
    """GA4 sync with timeout protection"""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "dlt", "pipeline", "show", "ga4"],
        capture_output=True,
        text=True,
        timeout=600  # Subprocess-level timeout as backup
    )
    return result

@task(timeout_seconds=900)  # 15 minute timeout
def run_dbt_models():
    """dbt run with timeout"""
    import subprocess
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", ".", "--project-dir", "."],
        capture_output=True,
        text=True,
        timeout=900  # Subprocess-level timeout
    )
    return result
```

### 2.3 Important: ThreadPoolTaskRunner Limitation

**Critical**: When using the default `ThreadPoolTaskRunner`, timeouts **cannot interrupt blocking operations** like `time.sleep()`, `subprocess.run()`, or network requests.

```python
from prefect import flow, task
from prefect.task_runners import ProcessPoolTaskRunner

# For reliable timeout on blocking operations, use ProcessPoolTaskRunner
@flow(task_runner=ProcessPoolTaskRunner())
def etl_with_reliable_timeouts():
    slow_task.submit()  # Timeout WILL work with ProcessPoolTaskRunner
```

Alternative: Use subprocess-level timeouts as a backup:

```python
import subprocess
from prefect import task

@task(timeout_seconds=600)
def sync_with_backup_timeout():
    try:
        result = subprocess.run(
            ["python", "-m", "dlt", "pipeline", "run", "ga4"],
            capture_output=True,
            text=True,
            timeout=540  # Slightly less than task timeout
        )
        if result.returncode != 0:
            raise RuntimeError(f"dlt failed: {result.stderr}")
        return result
    except subprocess.TimeoutExpired:
        raise TimeoutError("dlt sync exceeded timeout limit")
```

---

## 3. Retry Policies

### 3.1 Exponential Backoff Configuration

```python
from prefect import task
from prefect.tasks import exponential_backoff

@task(
    retries=3,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),  # 2, 4, 8, 16...
    retry_jitter_factor=0.5  # Add randomness to avoid thundering herd
)
def api_sync_task():
    """Task with exponential backoff retry"""
    pass
```

### 3.2 Custom Retry Conditions

```python
import httpx
from prefect import task

def retry_handler(task, task_run, state) -> bool:
    """
    Decide whether to retry based on exception type.
    Returns True = retry, False = fail immediately
    """
    try:
        state.result()
    except httpx.HTTPStatusError as exc:
        # Don't retry on client errors (4xx)
        if 400 <= exc.response.status_code < 500:
            return False
        # Retry on server errors (5xx)
        return True
    except httpx.ConnectError:
        # Retry on connection errors
        return True
    except TimeoutError:
        # Retry on timeouts
        return True
    except:
        # Retry on everything else
        return True

@task(
    retries=3,
    retry_delay_seconds=exponential_backoff(backoff_factor=3),
    retry_condition_fn=retry_handler
)
def fetch_api_data():
    """API call with smart retry conditions"""
    response = httpx.get("https://api.example.com/data", timeout=30)
    response.raise_for_status()
    return response.json()
```

### 3.3 Retry Policy Summary

| Scenario | Retries | Delay Strategy | Jitter |
|----------|---------|---------------|--------|
| External API calls | 3-5 | Exponential (2x-3x) | 0.3-0.5 |
| Database operations | 2-3 | Exponential (2x) | 0.2 |
| dlt sync | 3 | Exponential (2x) | 0.3 |
| dbt run | 2 | Linear (30-60s) | 0 |
| Non-critical tasks | 1-2 | Fixed (10-30s) | 0.1 |

---

## 4. Flow-Level Error Handling

### 4.1 on_failure Callback Pattern

```python
from prefect import flow, task
from prefect.blocks.notifications import SlackWebhook

@task
def sync_data():
    """May fail"""
    raise ConnectionError("API unavailable")

@flow(on_failure=[handle_flow_failure])
def etl_pipeline():
    sync_data()

async def handle_flow_failure(flow, flow_run, state):
    """Callback when flow fails"""
    # Get failure details
    failure_message = str(state.result(raise_exception=False))
    
    # Log for debugging
    logger = get_run_logger()
    logger.error(f"Flow failed: {failure_message}")
    
    # Send notification (Slack, email, etc.)
    await SlackWebhook.notify(
        f":x: Flow *{flow.name}* failed\n"
        f"Run ID: {flow_run.id}\n"
        f"Error: {failure_message}"
    )
```

### 4.2 State-Based Error Handling

```python
from prefect import flow, task
from prefect.states import State

@flow
def robust_etl():
    try:
        # Run sync tasks
        sync_task.submit()
        
        # Run transformation
        transform_task.submit()
        
        # Run validation
        validate_task.submit()
        
    except Exception as e:
        # Handle cleanup
        cleanup_partial_data()
        # Re-raise or handle differently
        raise
```

### 4.3 Notification Patterns

```python
from prefect import flow
from prefect.blocks.notifications import SlackWebhook, EmailWebhook

@flow(
    on_failure=[notify_failure],
    on_cancellation=[notify_cancellation]
)
def production_pipeline():
    """Production ETL with notifications"""
    pass

async def notify_failure(flow, flow_run, state):
    """Send failure notification"""
    error = state.result(raise_exception=False)
    
    await SlackWebhook.notify(
        block_name="slack-alerts",
        msg=f"""
:rotating_light: Flow Failed: {flow.name}

Run: {flow_run.name}
Error: {str(error)[:500]}
Link: {get_run_url(flow_run)}
"""
    )

async def notify_cancellation(flow, flow_run, state):
    """Send cancellation notification"""
    await SlackWebhook.notify(
        block_name="slack-alerts",
        msg=f"""
:warning: Flow Cancelled: {flow.name}
Run: {flow_run.name}
"""
    )
```

---

## 5. Recommended Implementation Pattern

```python
from prefect import flow, task
from prefect.futures import wait
from prefect.tasks import exponential_backoff
from prefect.blocks.notifications import SlackWebhook

# Timeout constants
DLT_SYNC_TIMEOUT = 600      # 10 minutes
DBT_RUN_TIMEOUT = 900       # 15 minutes
DBT_TEST_TIMEOUT = 300      # 5 minutes

# Retry configuration
API_RETRY_CONFIG = {
    "retries": 3,
    "retry_delay_seconds": exponential_backoff(backoff_factor=2),
    "retry_jitter_factor": 0.3,
}

@task(timeout_seconds=DLT_SYNC_TIMEOUT, **API_RETRY_CONFIG)
def sync_dlt_source(source: str, credentials: dict):
    """Sync a dlt source with timeout and retry"""
    import subprocess
    
    result = subprocess.run(
        ["python", "-m", "dlt", "pipeline", "run", source],
        env={**os.environ, **credentials},
        capture_output=True,
        text=True,
        timeout=DLT_SYNC_TIMEOUT - 60  # Backup subprocess timeout
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"dlt sync failed: {result.stderr}")
    
    return result

@task(timeout_seconds=DBT_RUN_TIMEOUT, retries=2)
def run_dbt_models():
    """Run dbt models with timeout"""
    import subprocess
    
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", ".", "--project-dir", "."],
        capture_output=True,
        text=True,
        timeout=DBT_RUN_TIMEOUT - 60
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"dbt run failed: {result.stderr}")
    
    return result

@flow(
    name="client-etl-pipeline",
    on_failure=[notify_failure],
    timeout_seconds=3600  # 1 hour max for entire flow
)
def etl_pipeline(client_id: str, sources: list[str]):
    """
    Reliable ETL pipeline with:
    - Parallel source syncs
    - Proper timeouts
    - Exponential backoff retries
    - Failure notifications
    """
    # Sync all sources in parallel
    sync_futures = [
        sync_dlt_source.submit(source=source, credentials={...})
        for source in sources
    ]
    
    # Wait for all syncs to complete
    wait(sync_futures)
    
    # Check for failures
    done, not_done = wait(sync_futures)
    
    failed_sources = []
    for future in done:
        if not future.state.is_completed():
            failed_sources.append(future.task_parameters.get("source"))
    
    if failed_sources:
        raise RuntimeError(f"Failed sources: {failed_sources}")
    
    # Run dbt after all syncs complete
    run_dbt_models()
```

---

## 6. Summary: Recommended Values

| Component | Setting | Value |
|-----------|---------|-------|
| **dlt sync** | `timeout_seconds` | 600 (10 min) |
| **dlt sync** | `retries` | 3 |
| **dlt sync** | `retry_delay_seconds` | exponential_backoff(2) |
| **dlt sync** | `retry_jitter_factor` | 0.3 |
| **dbt run** | `timeout_seconds` | 900 (15 min) |
| **dbt run** | `retries` | 2 |
| **dbt run** | `retry_delay_seconds` | [30, 60] |
| **dbt test** | `timeout_seconds` | 300 (5 min) |
| **Flow level** | `timeout_seconds` | 3600 (1 hour) |
| **Flow level** | `on_failure` | notify callback |

---

## References

- [Prefect Concurrent Execution](https://docs.prefect.io/v3/how-to-guides/workflows/run-work-concurrently)
- [Prefect Retries](https://docs.prefect.io/v3/how-to-guides/workflows/retries)
- [Prefect Tasks](https://docs.prefect.io/v3/concepts/tasks)
- [Prefect Timeouts](https://docs.prefect.io/v3/how-to-guides/workflows/write-and-run#cancel-a-workflow-if-it-runs-for-too-long)
