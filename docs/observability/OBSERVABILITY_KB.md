# Observability Stack: Loki + Grafana + LangGraph Pipeline

## Overview

This document describes the comprehensive observability stack integrating **Loki** (log aggregation), **Grafana** (visualization & alerting), **Prometheus** (metrics), and **LangGraph** (AI-powered log analysis and alerting pipeline).

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OBSERVABILITY STACK                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌────────────┐ │
│  │   Docker    │    │   Apps      │    │  Prometheus │    │   Kilo     │ │
│  │   Logs      │    │   Logs      │    │   Metrics   │    │   Agent    │ │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └─────┬──────┘ │
│         │                   │                   │                   │        │
│         ▼                   ▼                   ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        Promtail                                      │  │
│  │            (Log scraping + Label enrichment)                         │  │
│  └──────────────────────────┬──────────────────────────────────────────┘  │
│                             │                                              │
│                             ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         Loki (Port 3100)                             │  │
│  │                   (Log aggregation & storage)                        │  │
│  └──────────────────────────┬──────────────────────────────────────────┘  │
│                             │                                              │
│         ┌───────────────────┴───────────────────┐                       │
│         ▼                                       ▼                        │
│  ┌─────────────────┐                    ┌─────────────────┐              │
│  │    Grafana      │                    │   LangGraph     │              │
│  │  (Dashboards)   │                    │   Pipeline      │              │
│  │  (Alerting)     │                    │   (AI Analysis) │              │
│  └────────┬────────┘                    └────────┬────────┘              │
│           │                                      │                       │
│           ▼                                      ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    Alertmanager / Notifications                      │  │
│  │                 (Email, Slack, PagerDuty, Webhooks)                 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Loki - Log Aggregation

**Endpoint:** `http://100.91.164.109:3100`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/loki/api/v1/push` | POST | Send log entries |
| `/loki/api/v1/query` | GET | Query logs (instant) |
| `/loki/api/v1/query_range` | GET | Query logs (range) |
| `/loki/api/v1/label` | GET | List all labels |
| `/loki/api/v1/series` | GET | List series |
| `/ready` | GET | Health check |

### 2. Grafana - Visualization & Alerting

**Current Instance:** `http://100.91.164.109:3000`

| API Endpoint | Purpose |
|--------------|---------|
| `/api/datasources` | List datasources |
| `/api/alertmanager/config` | Alertmanager config |
| `/api/v1/provisioning/alert-rules` | Manage alert rules |
| `/api/health` | Health check |

### 3. Prometheus - Metrics

| Endpoint | Purpose |
|----------|---------|
| `/metrics` | Prometheus metrics |
| `/api/v1/query` | Query metrics |
| `/api/v1/query_range` | Query range |

## LogQL Reference

### Basic Queries

```logql
# All logs
{job="myapp"}

# Filter by label
{namespace="production", app="web"}

# Text search
{job="myapp"} |= "error"
{job="myapp"} |= "timeout" != "connection timeout"

# Regex
{job="myapp"} |~ "HTTP [4-5]\\d{2}"

# JSON parsing
{job="api"} | json | level="error"
{job="api"} | json | duration > 1000
```

### Rate Queries

```logql
# Error rate per second
sum(rate({job="api"} |= "error" [1m]))

# Requests per second
sum(rate({job="api"}[5m]))

# Top 10 error-producing services
topk(10, sum by (service) (rate({level="error"}[5m])))
```

### Aggregation

```logql
# Count logs by level
sum by (level) (count_over_time({job="myapp"}[5m]))

# Sum bytes by service
sum by (service) (sum_over_time({job="myapp"} | unwrap bytes [1m]))

# Average duration
avg by (service) (rate({job="api"} | unwrap duration_ms [1m]))
```

## Loki Alerting Rules

```yaml
groups:
  - name: application_alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate({app="myapp", level="error"}[5m])) by (app)
            / sum(rate({app="myapp"}[5m])) by (app)
            > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "{{ $labels.app }} error rate is {{ $value | humanizePercentage }}"

      # Service down
      - alert: ServiceDown
        expr: |
          sum(rate({job="myapp"}[5m])) by (job) == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service not receiving logs"
          description: "{{ $labels.job }} has not sent logs for 2 minutes"

      # Credential leak detection
      - alert: CredentialsLeaked
        expr: |
          sum by (cluster, job) (count_over_time(
            {namespace="prod"} |~ "http(s?)://(\\w+):(\\w+)@" [5m]
          ) > 0)
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Credentials found in logs"
          description: "{{ $labels.job }} is leaking HTTP credentials"
```

## Grafana Alerting API

### Create Alert Rule

```bash
curl -X POST "http://100.91.164.109:3000/api/v1/provisioning/alert-rules" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d '{
    "title": "High Error Rate",
    "condition": "B",
    "data": [
      {
        "refId": "A",
        "relativeTimeRange": {"from": 300, "to": 0},
        "datasourceUid": "<LOKI_UID>",
        "model": {
          "expr": "sum(rate({app=\"myapp\", level=\"error\"}[5m]))",
          "instant": true,
          "intervalMs": 1000,
          "maxDataPoints": 43200,
          "refId": "A"
        }
      },
      {
        "refId": "B",
        "relativeTimeRange": {"from": 0, "to": 0},
        "datasourceUid": "__expr__",
        "model": {
          "conditions": [
            {
              "evaluator": {"params": [0], "type": "gt"},
              "operator": {"type": "and"},
              "query": {"params": ["A"]},
              "reducer": {"type": "last"},
              "type": "query"
            }
          ],
          "type": "classic_conditions"
        }
      }
    ],
    "noDataState": "OK",
    "execErrState": "Error",
    "for": "5m",
    "labels": {"severity": "warning"},
    "annotations": {
      "summary": "High error rate detected"
    }
  }'
```

### List Alert Rules

```bash
curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
  "http://100.91.164.109:3000/api/v1/provisioning/alert-rules"
```

### Delete Alert Rule

```bash
curl -X DELETE "http://100.91.164.109:3000/api/v1/provisioning/alert-rules/{uid}" \
  -H "Authorization: Bearer $GRAFANA_API_KEY"
```

## LangGraph Pipeline Architecture

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH OBSERVABILITY PIPELINE                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐                                                      │
│   │   Schedule   │                                                      │
│   │   Trigger    │                                                      │
│   └──────┬───────┘                                                      │
│          │                                                               │
│          ▼                                                               │
│   ┌──────────────┐     ┌──────────────┐                                 │
│   │  Fetch Logs  │────▶│  Parse Logs  │                                 │
│   │  (Loki API)  │     │  (Structured)│                                 │
│   └──────────────┘     └──────┬───────┘                                 │
│                               │                                          │
│          ┌────────────────────┼────────────────────┐                     │
│          ▼                    ▼                    ▼                     │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │
│   │  Error       │     │  Anomaly     │     │  Pattern     │          │
│   │  Detection   │     │  Detection   │     │  Analysis    │          │
│   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘          │
│          │                    │                    │                   │
│          └────────────────────┼────────────────────┘                   │
│                               ▼                                          │
│                        ┌──────────────┐                                 │
│                        │  Aggregate   │                                 │
│                        │  Findings    │                                 │
│                        └──────┬───────┘                                 │
│                               │                                          │
│          ┌────────────────────┼────────────────────┐                   │
│          ▼                    ▼                    ▼                     │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │
│   │  Create      │     │  Create      │     │  Generate    │          │
│   │  Grafana     │     │  Prometheus  │     │  Summary     │          │
│   │  Alert       │     │  Alert       │     │  Report      │          │
│   └──────────────┘     └──────────────┘     └──────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### State Schema

```python
@dataclass
class ObservabilityState(TypedDict):
    # Input
    time_range: str  # e.g., "last 15m", "last 1h"
    services: list[str] | None  # Filter by services
    
    # Processing
    raw_logs: list[dict]  # Raw log entries from Loki
    parsed_logs: list[dict]  # Parsed structured logs
    errors: list[dict]  # Detected errors
    anomalies: list[dict]  # Detected anomalies
    patterns: list[dict]  # Identified patterns
    
    # Output
    alerts_created: list[dict]  # Alerts created in Grafana
    metrics_written: list[dict]  # Custom metrics to Prometheus
    summary: str  # Human-readable summary
    
    # Metadata
    run_id: str
    started_at: datetime
    completed_at: datetime | None
```

### Nodes

| Node | Purpose | Tools Used |
|------|---------|------------|
| `fetch_logs` | Query Loki for logs | Loki HTTP API |
| `parse_logs` | Parse and structure logs | json, logfmt parsers |
| `detect_errors` | Identify error patterns | Pattern matching |
| `detect_anomalies` | Find statistical anomalies | Statistics |
| `analyze_patterns` | Identify recurring patterns | NLP, clustering |
| `aggregate_findings` | Consolidate all findings | Aggregation |
| `create_alerts` | Create Grafana alerts | Grafana API |
| `write_metrics` | Write custom metrics | Prometheus API |
| `generate_summary` | Create summary report | LLM |

### Conditional Edges

```python
def should_alert(state: ObservabilityState) -> str:
    """Determine if we should create alerts."""
    if len(state["errors"]) > 10:
        return "critical_alert"
    elif len(state["errors"]) > 0:
        return "warning_alert"
    elif len(state["anomalies"]) > 0:
        return "anomaly_alert"
    return "no_alert"
```

## Integration with Kilo/OpenCode

### Agent Logging Standard

```python
import logging
import json
from datetime import datetime

class AgentLogger:
    """Standard logging for AI agents."""
    
    def __init__(self, agent_name: str, loki_url: str):
        self.agent_name = agent_name
        self.loki_url = loki_url
        
    def log(self, level: str, message: str, **kwargs):
        """Log with structured metadata."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.agent_name,
            "level": level,
            "message": message,
            "metadata": kwargs
        }
        self._push_to_loki(entry)
        
    def log_task_start(self, task_id: str, task_type: str):
        self.log("info", f"Task started: {task_type}", 
                 event="task_start", task_id=task_id, task_type=task_type)
        
    def log_task_complete(self, task_id: str, duration_ms: int):
        self.log("info", "Task completed",
                 event="task_complete", task_id=task_id, duration_ms=duration_ms)
        
    def log_error(self, error: Exception, context: dict):
        self.log("error", str(error),
                 event="error", error_type=type(error).__name__,
                 stack_trace=traceback.format_exc(), **context)
```

### Recommended Labels

```yaml
# For all agent logs
labels:
  job: "ai-agent"
  agent: "kilo" | "opencode" | "custom"
  task_type: "code_generation" | "debugging" | "analysis"
  environment: "production" | "staging" | "development"
```

## Prometheus Integration

### Custom Metrics from Logs

```logql
# Convert log counts to metrics (recording rules)
- record: agent:tasks_total:rate5m
  expr: sum by (agent, task_type) (rate({job="ai-agent"}[5m]))

- record: agent:errors_total:rate5m  
  expr: sum by (agent, error_type) (rate({job="ai-agent", level="error"}[5m]))

- record: agent:task_duration_seconds:avg
  expr: avg by (agent) (rate({job="ai-agent"} | unwrap duration_ms [5m])) / 1000
```

### Alert Rules

```yaml
groups:
  - name: agent_alerts
    rules:
      - alert: AgentHighErrorRate
        expr: |
          sum by (agent) (rate({job="ai-agent", level="error"}[5m]))
            / sum by (agent) (rate({job="ai-agent"}[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Agent {{ $labels.agent }} has high error rate"
          
      - alert: AgentUnresponsive
        expr: |
          sum(rate({job="ai-agent"}[5m])) by (agent) == 0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Agent {{ $labels.agent }} not logging"
```

## Next Steps

1. **Set up Promtail** - Configure log scraping from Docker containers
2. **Deploy LangGraph pipeline** - Implement the monitoring pipeline
3. **Configure alerts** - Set up Grafana alert rules
4. **Agent integration** - Add structured logging to Kilo/OpenCode

## References

- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/)
- [LogQL Reference](https://grafana.com/docs/loki/latest/query/)
- [Grafana MCP Server](https://github.com/grafana/mcp-grafana)
- [Loki MCP Server](https://github.com/grafana/loki-mcp)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
