# Metabase Tech Stack Integration Research

**Date:** 2026-04-06  
**Status:** Research Complete

---

## 1. LiteLLM Integration (AI Gateway)

### Current State in op.expc.cz

LiteLLM runs on s62 at `100.111.141.111:4000` (Tailscale-only).

### Integration Options for Metabase

| Option | Description | Effort | Use Case |
|--------|-------------|--------|----------|
| SQL generation | Use LiteLLM to convert natural language to SQL | Medium | AI-powered queries |
| Data summarization | Summarize query results with LLM | Medium | Dashboard insights |
| Recommendation engine | ML-based recommendations | High | Product suggestions |

### Implementation Path

```python
# scripts/ai_query.py
import requests

LITELLM_URL = "http://100.111.141.111:4000"

def generate_sql(prompt: str, schema: str) -> str:
    response = requests.post(f"{LITELLM_URL}/v1/chat/completions", json={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": f"Generate SQL for: {schema}"},
            {"role": "user", "content": prompt}
        ]
    })
    return response.json()["choices"][0]["message"]["content"]
```

---

## 2. Redis Integration (Caching)

### Current State in op.expc.cz

Redis (`expc-redis`) available at `expc-redis:6379` on `expccz_expc_internal` network.

### Integration Options

| Option | Description | Effort | Use Case |
|--------|-------------|--------|----------|
| Query result cache | Cache Metabase query results | High | Faster dashboard loads |
| Rate limiting | Rate limit API calls | Medium | Prevent abuse |
| Session store | Store user sessions | Medium | Multi-node Metabase |

### Limitation

Metabase runs on its own Docker network (`metabase-net`), not connected to `expccz_expc_internal`. Need to add to network or run separate Redis.

### Recommended Approach

Create a dedicated cache layer in pipeline scripts:

```python
# scripts/cache.py
import redis
import json
import hashlib

class QueryCache:
    def __init__(self):
        self.redis = redis.Redis(
            host='expc-redis',
            port=6379,
            password='<from-env>',
            decode_responses=True
        )
    
    def get(self, query: str) -> dict | None:
        key = hashlib.md5(query.encode()).hexdigest()
        cached = self.redis.get(f"metabase:query:{key}")
        return json.loads(cached) if cached else None
    
    def set(self, query: str, result: dict, ttl: int = 3600):
        key = hashlib.md5(query.encode()).hexdigest()
        self.redis.setex(f"metabase:query:{key}", ttl, json.dumps(result))
```

---

## 3. LangGraph Integration (Workflows)

### Current State in op.expc.cz

LangGraph runs on s60 at `100.111.141.111:8093` via `langgraph_app` container.

### Integration Options

| Option | Description | Effort | Use Case |
|--------|-------------|--------|----------|
| ETL orchestration | Run pipeline via LangGraph | Medium | Complex data transforms |
| Automated reporting | Generate reports on schedule | Medium | Scheduled reports |
| Data validation | Validate data before load | Low | Quality checks |

### Recommended Approach

Use LangGraph for complex ETL workflows:

```python
# langgraph_app/graph/pipeline.py
from langgraph.graph import StateGraph

class PipelineState(TypedDict):
    client_id: str
    source: str
    records: list
    errors: list

def build_pipeline_graph():
    builder = StateGraph(PipelineState)
    builder.add_node("extract", extract_data)
    builder.add_node("transform", transform_data)
    builder.add_node("load", load_to_metabase)
    builder.add_edge("extract", "transform")
    builder.add_edge("transform", "load")
    return builder.compile()
```

---

## 4. Secrets Management (SOPS)

### Current State in op.expc.cz

SOPS with Age encryption used for secrets in `server-infra-gem/.sops/`.

### Integration Options

| Option | Description | Effort | Use Case |
|--------|-------------|--------|----------|
| Shared API keys | Store GA4/G-Ads keys in SOPS | Low | Centralized secrets |
| DB credentials | Store DB passwords in SOPS | Low | Rotate credentials |

### Recommended Approach

For now, use local `.env.client_name` files. SOPS integration can be added later if needed for multi-server deployments.

---

## Summary: What's Worth Integrating

| Technology | Status for Metabase | Recommendation |
|------------|---------------------|----------------|
| LiteLLM | Available on s62 | Add as optional AI query layer |
| Redis | Available in expc network | Use in pipeline scripts, not Metabase |
| LangGraph | Available on s60 | Use for complex ETL only |
| SOPS | Used in op.expc.cz | Keep local .env for simplicity |

---

## Action Items

- [ ] Add LiteLLM client to `pyproject.toml` for AI queries
- [ ] Add Redis client to `pyproject.toml` for caching
- [ ] Create `scripts/cache.py` for query caching
- [ ] Create `scripts/ai_query.py` for natural language queries
- [ ] Document how to connect LangGraph workflows