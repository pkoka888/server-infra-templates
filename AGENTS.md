# Metabase Deployment — Agent Guidelines

## Purpose

BI/analytics dashboard for PrestaShop e-commerce. Connects to OpenProject (PostgreSQL), research data (SQLite), and Prometheus metrics. Provides dashboards for infrastructure health, project metrics, research pipeline, and client delivery.

## Build / Lint / Test Commands

### Python (Primary)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all linters (ruff + mypy)
uv run ruff check .
uv run mypy .

# Run single test file
uv run pytest tests/test_pipeline.py -v

# Run single test function
uv run pytest tests/test_pipeline.py::TestPipeline::test_get_client_env -v

# Run tests matching pattern
uv run pytest -k "test_api" -v

# Run with coverage
uv run pytest --cov=scripts --cov-report=term-missing

# Auto-fix ruff issues
uv run ruff check --fix .
```

### dbt

```bash
cd dbt

# Install dependencies
dbt deps

# Run all models
dbt run

# Run specific model
dbt run --select stg_ga4__traffic

# Run tests
dbt test

# Run specific test
dbt test --select stg_ga4__traffic

# Generate docs
dbt docs generate && dbt docs serve
```

### Docker

```bash
# Deploy/update
docker compose up -d
docker compose pull

# Health checks
docker inspect --format='{{.State.Health.Status}}' metabase
docker exec metabase curl -sf http://localhost:3000/api/health

# Logs
docker logs metabase --tail 100
```

---

## Code Style Guidelines

### General Principles

- **Line length**: 100 characters max
- **Python version**: 3.10+
- **Formatter**: ruff (line-length 100, target py310)
- **Type checker**: mypy

### Imports

**Organize imports in this order (ruff `I` rule will enforce):**

1. Standard library (`import os`, `import logging`)
2. Third-party (`import requests`, `import httpx`)
3. Local application (`from scripts import pipeline`)

**Use absolute imports from project root:**

```python
from scripts.agent_logger import AgentLogger  # Good
from ..agent_logger import AgentLogger        # Avoid
```

**Conditional imports for optional dependencies:**

```python
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
```

### Type Annotations

- Use `str | None` syntax (Python 3.10+ union syntax, not `Optional[str]`)
- Use `list[str]` syntax (not `List[str]`)
- Type all function parameters and return values when ambiguous
- Use `TypedDict` for structured state dictionaries

```python
# Good
def process_data(user_id: str) -> dict[str, Any] | None:
    ...

class ETLState(TypedDict):
    client_id: str
    sources: list[str]
    status: str
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Variables | snake_case | `client_id`, `total_revenue` |
| Functions | snake_case | `get_client_env()`, `extract_data()` |
| Classes | PascalCase | `AgentLogger`, `ETLState` |
| Constants | UPPER_SNAKE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private vars | _leading_underscore | `_client`, `_config` |
| Type aliases | PascalCase | `ClientConfig`, `MetricsDict` |

### Error Handling

**Use specific exceptions:**

```python
# Good
raise ValueError(f"Invalid client_id: {client_id}")
raise FileNotFoundError(f"Config not found: {env_file}")

# Avoid
raise Exception("Something went wrong")
```

**Catch and re-raise with context:**

```python
try:
    result = client.get(url)
except requests.RequestException as e:
    raise RuntimeError(f"Failed to fetch {url}") from e
```

**Use logging for errors, not print:**

```python
logger = logging.getLogger(__name__)

logger.error(f"Failed to process {source}: {e}")
logger.warning(f"Config missing, using defaults: {e}")
```

### Async / Sync Patterns

- Use `httpx.AsyncClient` for async operations
- Use `requests` for sync operations (ETL scripts, simple API calls)
- Never mix sync/async in the same function

```python
# Async (httpx)
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# Sync (requests)
response = requests.get(url)
```

### Docstrings

Use docstrings for modules and public classes/functions:

```python
"""
Agent Logger for Observability Stack.

Standardized logging for AI agents with Loki integration.
"""

class AgentLogger:
    """Structured logger for AI agents."""
    
    def task_start(self, task_id: str, task_type: str):
        """Log task start event."""
        ...
```

---

## Project Structure

```
.
├── scripts/          # Main ETL pipeline scripts
│   ├── pipeline.py    # dlt pipeline orchestration
│   ├── langgraph_etl.py
│   └── agent_logger.py
├── tests/             # pytest test suite
│   ├── test_*.py
│   └── e2e/
├── dbt/               # dbt transformation models
│   └── models/
├── prefect/           # Prefect workflow definitions
└── config/            # Configuration files
```

---

## Essential Commands

### Health Checks

```bash
docker inspect --format='{{.State.Health.Status}}' metabase
docker exec metabase curl -sf http://localhost:3000/api/health
docker exec metabase-db psql -U metabase -d metabase -c "SELECT count(*) FROM report_dashboard;"
```

### Database Access

```bash
docker exec metabase-db psql -U metabase -d metabase
```

### Slow Query Analysis

```bash
docker exec metabase-db psql -U metabase -d metabase -c "
SELECT query, calls, total_time/calls as avg_time
FROM pg_stat_statements ORDER BY avg_time DESC LIMIT 10;"
```

---

## Credentials & Secrets

- **Never commit** `.env` or `.env.*` files
- Store credentials in per-client `.env.client_name`
- Use `~/.config/borg/` for backup passphrases
- Borg passphrase: `~/.config/borg/metabase-passphrase`

---

## Non-Obvious Points

- **Timezone**: Europe/Prague (JAVA_TIMEZONE and TZ)
- **DB health wait**: `depends_on` with `service_healthy` condition
- **ETL timing**: Runs 01:00-02:30 (before 03:00 backup)
- **httpx vs requests**: Use `httpx` for async, `requests` for sync

---

## Implementation Reference

Implementation guidance is organized in `docs/implementation/`:

| Document | Purpose |
|----------|---------|
| `docs/connectors/CONNECTOR_RESEARCH.md` | GA4, FB Ads, PrestaShop failure modes |
| `docs/implementation/DOCKER_BLUEPRINT.md` | Production Docker Compose stack |
| `docs/implementation/DBT_CONVENTIONS.md` | dbt project standards and templates |
| `docs/implementation/PREFECT_FLOW.md` | Prefect orchestration flow definition |
| `docs/implementation/QUALITY_POLICY.md` | Data quality validation strategy |

## Phase 1 Checklist

### Foundation
- [ ] Docker Compose with health checks deployed
- [ ] PostgreSQL 17 with Metabase connected
- [ ] Secrets in `.env` (never committed)

### Ingestion
- [ ] GA4 connector validated (sampling, quota, schema drift)
- [ ] Facebook Ads connector validated (rate limits, attribution)
- [ ] PrestaShop connector validated (rate limits, order states)
- [ ] First successful sync for each source

### Transformation
- [ ] dbt project structure following conventions
- [ ] Staging models: `stg_ga4__traffic`, `stg_facebook__ads`, `stg_prestashop__orders`
- [ ] One mart model: `fct_marketing_performance`
- [ ] Tests on primary keys and business logic

### Orchestration
- [ ] Prefect server and Docker worker running
- [ ] Flow deployed: `marketing-analytics-pipeline`
- [ ] Schedule: daily at 02:30 UTC
- [ ] Alerting on failure

### Quality
- [ ] Row count validation after sync
- [ ] dbt tests passing
- [ ] Revenue reconciliation (< 0.1% tolerance)
- [ ] Slack alerts configured

## Phase 2 (Deferred)

- Google Ads connector
- Google Search Console integration
- OpenLineage for lineage tracking
- Attribution modeling
- Cohort analysis
- Superset as alternative BI

---

## Policy References

- `.agent/agents.md` — Agent behavior
- `.agent/constitution/rules.md` — Hard guards
- `.agent/constitution/embedding-policy.md` — Dashboard embedding
- `.agent/constitution/database-policy.md` — PostgreSQL config
