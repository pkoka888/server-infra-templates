# Metabase Caching & Performance Research

**Date:** 2026-04-06  
**Status:** Research Complete

---

## Key Finding: Redis NOT Used for Metabase Caching

**Metabase stores all cached query results in PostgreSQL (application database), NOT in Redis or Memcached.**

---

## Does LangGraph Use Redis?

**No.** LangGraph is configured with **MemorySaver** by default (in-memory, not persistent):

```python
# langgraph_app/app.py
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
```

### Checkpointer Options Available

| Checkpointer | Storage | Persistence | Redis Needed |
|--------------|---------|-------------|--------------|
| **MemorySaver** | RAM | ❌ Lost on restart | ❌ No |
| **SqliteSaver** | SQLite file | ✅ Yes | ❌ No |
| **PostgresSaver** | PostgreSQL | ✅ Yes | ❌ No (uses DB) |
| **RedisSaver** | Redis | ✅ Yes | ✅ Yes |

### Current Production Setup

- Uses **MemorySaver** (in-memory) - no persistence
- Redis config exists in docker-compose.yml but is **NOT actively used**
- For production persistence, could switch to PostgresSaver (uses existing openproject-db)

---

## What Redis IS Used For in Our Stack

| Service | Redis Purpose | Actually Used? |
|---------|---------------|-----------------|
| LangGraph | Checkpoint storage | ❌ Using MemorySaver |
| LiteLLM | Token caching | ✅ Probably |
| n8n | Workflow state | ✅ Probably |
| Metabase | Query cache | ❌ PostgreSQL |

---

## Summary

| Component | Uses Redis? | Storage |
|-----------|-------------|---------|
| Metabase | ❌ No | PostgreSQL |
| LangGraph | ❌ No | MemorySaver (RAM) |
| LiteLLM | ✅ Yes | Redis |
| n8n | ✅ Yes | Redis |

**Conclusion:** Redis is NOT needed for Metabase or LangGraph in current setup. It's only used by LiteLLM and n8n which are separate services.