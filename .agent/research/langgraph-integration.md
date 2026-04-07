# LangGraph Integration with Metabase

**Date:** 2026-04-06  
**Status:** Research Complete

---

## Overview

LangGraph provides workflow orchestration for infrastructure automation. It can enhance Metabase by:
- Automating data pipeline runs
- Validating data before loading
- Generating AI-powered insights from query results

---

## Current LangGraph Setup (in op.expc.cz)

### Service Location
- **Host:** s60 (Tailscale: `100.111.141.111:8093`)
- **Port:** 8080 inside container, exposed via Traefik
- **API:** REST endpoints via FastAPI/LangServe

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/workflow/audit` | POST | Run server audit |
| `/workflow/audit/async` | POST | Start async audit |
| `/workflow/rollback` | POST | Run rollback workflow |

### Checkpoint Storage
- **Currently:** MemorySaver (in-memory, lost on restart)
- **Available:** SQLite, PostgreSQL (for persistence)

---

## Integration Options for Metabase

### Option 1: Call LangGraph API from Pipeline (Recommended)

Simple integration - pipeline calls LangGraph API:

```python
# scripts/pipeline.py
import requests

def run_langgraph_validation(client_id: str, source: str) -> dict:
    """Validate data before loading via LangGraph."""
    response = requests.post(
        "http://100.111.141.111:8093/workflow/validate",
        json={"dataset": f"{source}_{client_id}", "checks": ["nulls", "duplicates"]}
    )
    return response.json()
```

### Option 2: Run LangGraph Workflow for ETL Orchestration

Use LangGraph to orchestrate complex ETL:

```python
# Example: orchestrate multi-source sync
from langgraph.graph import StateGraph

class ETLState(TypedDict):
    client_id: str
    sources: list
    results: dict
    errors: list

def build_etl_graph():
    builder = StateGraph(ETLState)
    builder.add_node("extract_ga4", extract_ga4)
    builder.add_node("extract_gads", extract_gads) 
    builder.add_node("validate", validate_data)
    builder.add_node("load", load_to_metabase)
    
    builder.add_edge("__start__", "extract_ga4")
    builder.add_edge("extract_ga4", "extract_gads")
    builder.add_edge("extract_gads", "validate")
    builder.add_edge("validate", "load")
    
    return builder.compile()
```

### Option 3: AI Insights from Query Results

Use LiteLLM via LangGraph to generate insights:

```python
def generate_insight(query_result: dict, question: str) -> str:
    """Use LiteLLM to generate insight from query result."""
    import litellm
    
    response = litellm.completion(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a data analyst. Analyze query results and provide insights."},
            {"role": "user", "content": f"Question: {question}\nResult: {query_result}"}
        ]
    )
    return response.choices[0].message.content
```

---

## How to Call LangGraph from Metabase Project

### 1. Direct API Call

```bash
# Test LangGraph API
curl -X POST http://100.111.141.111:8093/workflow/audit \
  -H "Content-Type: application/json" \
  -d '{"target_server": "s60", "audit_type": "security"}'
```

### 2. Add to Pipeline

```python
# In scripts/pipeline.py
def pre_pipeline_validation(client_id: str):
    """Validate client config before running pipelines."""
    # Call LangGraph validation workflow
    try:
        response = requests.post(
            "http://100.111.141.111:8093/workflow/validate",
            json={"client_id": client_id},
            timeout=30
        )
        return response.json()
    except requests.RequestException:
        return {"status": "skipped", "reason": "LangGraph unavailable"}
```

---

## Current Gaps & Inconsistencies

### 1. No LangGraph Skills in Metabase Project

**Gap:** Metabase project lacks LangGraph integration skills.

**Solution:** Add skill reference to `.agent/skills/`

### 2. Redis Still Configured But Not Used

**Inconsistency:** LangGraph docker-compose has Redis config but uses MemorySaver.

**Solution:** Document in research or remove unused config.

### 3. No Test Coverage

**Gap:** No tests for pipeline scripts.

**Solution:** Create `tests/` directory with basic tests.

### 4. Environment Variable Inconsistency

**Inconsistency:** Some vars use `MB_` prefix, others don't.

**Solution:** Standardize in documentation.

---

## Action Items

- [ ] Add LangGraph API client to pipeline
- [ ] Create tests directory with basic tests
- [ ] Document environment variable standards
- [ ] Add skill reference for LangGraph execution