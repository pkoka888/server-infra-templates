---
name: metabase-pipeline
description: Manage dlt data pipelines for Metabase analytics — sync GA4, Google Ads, Facebook Ads, PrestaShop data.
---

# metabase-pipeline

## Purpose

Manage data pipelines that sync marketing data (GA4, Google Ads, Facebook Ads, PrestaShop) to PostgreSQL for Metabase visualization.

## Project Context

- **Project path:** `/var/www/metabase/`
- **Environment:** Python with uv package manager
- **Database:** PostgreSQL (metabase-db) via Docker

## Pipeline Scripts

| File | Purpose |
|------|---------|
| `scripts/pipeline.py` | Main multi-client data pipeline |
| `scripts/setup-pipeline.sh` | Initialize new client environment |
| `scripts/langgraph_etl.py` | LangGraph ETL workflow orchestration |
| `scripts/langgraph_client.py` | LangGraph API client |
| `scripts/.env.example` | Template for client credentials |

## Usage

```bash
# Setup new client
./scripts/setup-pipeline.sh client_name

# Run specific source
uv run python scripts/pipeline.py --source ga4 --client client_name

# Run all sources
uv run python scripts/pipeline.py --all --client client_name

# Run with LangGraph ETL workflow
uv run python scripts/langgraph_etl.py client1 ga4,gads,fbads

# Test LangGraph API connection
uv run python scripts/langgraph_client.py

# List available clients
uv run python scripts/pipeline.py --list-clients --client test
```

## Dependencies

All dependencies defined in `pyproject.toml`:
- `dlt[postgres]` — Data loading
- `google-analytics-data` — GA4 API
- `facebook-business` — Meta Ads API
- `langgraph` — ETL workflow orchestration
- `litellm` — AI/LLM integration
- `requests` — HTTP client

## Best Practices

1. **Use uv for all package operations** — no pip
2. **Isolate client data** — separate datasets per client
3. **Verify before sync** — check credentials exist
4. **Log pipeline runs** — capture output for debugging
5. **Schedule during off-peak** — 2am recommended

## Safety Rules

- Never commit credentials (`.env.*` files)
- Verify container health before running pipelines
- Test with `--list-clients` before full sync
- Check dataset isolation after new client setup

## Constitution References

- `.agent/constitution/rules.md` — Hard guards
- `.agent/constitution/business.md` — Business scope
- `.agent/agents.md` — Agent behavior