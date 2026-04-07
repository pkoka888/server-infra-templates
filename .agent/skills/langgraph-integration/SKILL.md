---
name: langgraph-integration
description: Integrate LangGraph workflows with Metabase data pipelines.
---

# LangGraph Integration

Call LangGraph workflows from Metabase pipeline scripts.

## Quick Start

```bash
# Test LangGraph connectivity
uv run python scripts/langgraph_client.py
```

## Usage

### Basic Integration

```python
from langgraph_client import get_langgraph_client

# Get client (returns None if unavailable)
client = get_langgraph_client()

if client:
    # Run pre-pipeline validation
    result = client.validate_dataset("ga4_client1", checks=["nulls", "schema"])
    print(result)
```

### Full Client Usage

```python
from langgraph_client import LangGraphClient

client = LangGraphClient()

# Check health
if client.health_check():
    # Run audit
    result = client.run_audit("s60", "security")
    print(result)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/workflow/audit` | POST | Run server audit |
| `/workflow/validate` | POST | Validate dataset |

## Configuration

Environment variables:
- `LANGGRAPH_HOST` - Default: `100.111.141.111`
- `LANGGRAPH_PORT` - Default: `8093`

## Related Skills

- `.agent/skills/metabase-pipeline/` - Pipeline operations
- `.agent/constitution/rules.md` - Hard guards
