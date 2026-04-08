"""
LangGraph Observability Pipeline

AI-powered log analysis and alerting pipeline using Loki, Grafana, and Prometheus.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import TypedDict, Annotated
from dataclasses import dataclass, field
import httpx
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    timestamp: str
    stream: dict
    values: list
    message: str = ""

    def __post_init__(self):
        if self.values:
            self.message = self.values[0][1] if len(self.values) > 1 else ""

    @property
    def labels(self) -> dict:
        return self.stream

    @property
    def timestamp_unix(self) -> int:
        return int(self.values[0][0]) if self.values else 0


class LokiClient:
    """Client for Loki HTTP API."""

    def __init__(self, url: str = "http://100.91.164.109:3100"):
        self.url = url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)

    async def query(self, query: str, limit: int = 100) -> list[LogEntry]:
        """Execute instant query."""
        response = await self.client.get(
            f"{self.url}/loki/api/v1/query", params={"query": query, "limit": limit}
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            raise ValueError(f"Query failed: {data}")

        entries = []
        for stream in data["data"]["result"]:
            for timestamp, message in stream.get("values", []):
                entries.append(
                    LogEntry(
                        timestamp=timestamp, stream=stream["stream"], values=[[timestamp, message]]
                    )
                )
        return entries

    async def query_range(
        self, query: str, start: int, end: int, limit: int = 1000
    ) -> list[LogEntry]:
        """Execute range query."""
        response = await self.client.get(
            f"{self.url}/loki/api/v1/query_range",
            params={"query": query, "start": start, "end": end, "limit": limit},
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            raise ValueError(f"Query failed: {data}")

        entries = []
        for stream in data["data"]["result"]:
            for timestamp, message in stream.get("values", []):
                entries.append(
                    LogEntry(
                        timestamp=timestamp, stream=stream["stream"], values=[[timestamp, message]]
                    )
                )
        return entries

    async def get_labels(self) -> list[str]:
        """Get all label names."""
        response = await self.client.get(f"{self.url}/loki/api/v1/label")
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    async def get_label_values(self, label: str) -> list[str]:
        """Get values for a specific label."""
        response = await self.client.get(f"{self.url}/loki/api/v1/label/{label}")
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    async def health_check(self) -> bool:
        """Check Loki health."""
        try:
            response = await self.client.get(f"{self.url}/ready")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()


class GrafanaClient:
    """Client for Grafana HTTP API."""

    def __init__(self, url: str = "http://100.91.164.109:3000", api_key: str | None = None):
        self.url = url.rstrip("/")
        self.api_key = api_key or os.getenv("GRAFANA_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=60.0)

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def create_alert_rule(self, alert: dict) -> str:
        """Create a Grafana alert rule. Returns UID."""
        response = await self.client.post(
            f"{self.url}/api/v1/provisioning/alert-rules", headers=self._headers(), json=alert
        )
        response.raise_for_status()
        return response.json().get("uid", "")

    async def list_alert_rules(self) -> list[dict]:
        """List all alert rules."""
        response = await self.client.get(
            f"{self.url}/api/v1/provisioning/alert-rules", headers=self._headers()
        )
        response.raise_for_status()
        return response.json().get("provisionedAlertRules", [])

    async def delete_alert_rule(self, uid: str):
        """Delete an alert rule."""
        response = await self.client.delete(
            f"{self.url}/api/v1/provisioning/alert-rules/{uid}", headers=self._headers()
        )
        response.raise_for_status()

    async def get_datasources(self) -> list[dict]:
        """List all datasources."""
        response = await self.client.get(f"{self.url}/api/datasources", headers=self._headers())
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> bool:
        """Check Grafana health."""
        try:
            response = await self.client.get(f"{self.url}/api/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()


@dataclass
class Finding:
    """Represents a detected issue."""

    type: str  # "error", "anomaly", "pattern"
    severity: str  # "critical", "warning", "info"
    message: str
    count: int
    affected_services: list[str]
    sample_logs: list[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "count": self.count,
            "affected_services": self.affected_services,
            "sample_logs": self.sample_logs,
            "timestamp": self.timestamp,
        }


class ObservabilityState(TypedDict):
    """State for the observability pipeline."""

    # Configuration
    time_range: str
    services: list[str] | None
    loki_url: str
    grafana_url: str

    # Processing state
    raw_logs: list[dict]
    parsed_logs: list[dict]
    errors: list[dict]
    anomalies: list[dict]
    patterns: list[dict]
    findings: list[dict]

    # Results
    alerts_created: list[dict]
    summary: str

    # Metadata
    run_id: str
    started_at: str
    completed_at: str | None


class ObservabilityPipeline:
    """
    LangGraph pipeline for AI-powered observability.

    Orchestrates:
    1. Log fetching from Loki
    2. Error detection
    3. Anomaly detection
    4. Pattern analysis
    5. Alert creation in Grafana
    """

    def __init__(
        self,
        loki_url: str = "http://100.91.164.109:3100",
        grafana_url: str = "http://100.91.164.109:3000",
        grafana_api_key: str | None = None,
    ):
        self.loki_url = loki_url
        self.grafana_url = grafana_url
        self.grafana_api_key = grafana_api_key

        self.loki = LokiClient(loki_url)
        self.grafana = GrafanaClient(grafana_url, grafana_api_key)

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""

        workflow = StateGraph(ObservabilityState)

        # Add nodes
        workflow.add_node("fetch_logs", self.fetch_logs)
        workflow.add_node("detect_errors", self.detect_errors)
        workflow.add_node("detect_anomalies", self.detect_anomalies)
        workflow.add_node("analyze_patterns", self.analyze_patterns)
        workflow.add_node("aggregate_findings", self.aggregate_findings)
        workflow.add_node("create_alerts", self.create_alerts)
        workflow.add_node("generate_summary", self.generate_summary)

        # Define edges
        workflow.set_entry_point("fetch_logs")

        workflow.add_edge("fetch_logs", "detect_errors")
        workflow.add_edge("detect_errors", "detect_anomalies")
        workflow.add_edge("detect_anomalies", "analyze_patterns")
        workflow.add_edge("analyze_patterns", "aggregate_findings")
        workflow.add_edge("aggregate_findings", "create_alerts")
        workflow.add_edge("create_alerts", "generate_summary")
        workflow.add_edge("generate_summary", END)

        return workflow.compile()

    async def fetch_logs(self, state: ObservabilityState) -> dict:
        """Fetch logs from Loki based on time range and services."""
        logger.info(f"Fetching logs for range: {state['time_range']}")

        # Parse time range
        time_map = {"last 5m": 5, "last 15m": 15, "last 1h": 60, "last 6h": 360, "last 24h": 1440}

        minutes = time_map.get(state["time_range"], 15)
        end = datetime.utcnow()
        start = end - timedelta(minutes=minutes)

        start_ns = int(start.timestamp() * 1e9)
        end_ns = int(end.timestamp() * 1e9)

        # Build query
        query = '{job=~".+"}'
        if state.get("services"):
            service_filter = " | ".join([f'job="{s}"' for s in state["services"]])
            query = f"{{{service_filter}}}"

        try:
            logs = await self.loki.query_range(query=query, start=start_ns, end=end_ns, limit=1000)

            raw_logs = [
                {"timestamp": log.timestamp, "labels": log.labels, "message": log.message}
                for log in logs
            ]

            logger.info(f"Fetched {len(raw_logs)} log entries")

            return {"raw_logs": raw_logs, "parsed_logs": raw_logs}
        except Exception as e:
            logger.error(f"Failed to fetch logs: {e}")
            return {"raw_logs": [], "parsed_logs": []}

    async def detect_errors(self, state: ObservabilityState) -> dict:
        """Detect error patterns in logs."""
        logger.info("Detecting errors...")

        errors = []
        error_keywords = ["error", "exception", "failed", "fatal", "critical"]

        for log in state.get("parsed_logs", []):
            message = log.get("message", "").lower()
            if any(keyword in message for keyword in error_keywords):
                errors.append(
                    {
                        "log": log,
                        "matched_keyword": next(k for k in error_keywords if k in message),
                        "timestamp": log.get("timestamp"),
                    }
                )

        # Group errors by service
        error_counts: dict = {}
        for error in errors:
            job = error["log"].get("labels", {}).get("job", "unknown")
            error_counts[job] = error_counts.get(job, 0) + 1

        logger.info(f"Found {len(errors)} errors across {len(error_counts)} services")

        return {"errors": errors}

    async def detect_anomalies(self, state: ObservabilityState) -> dict:
        """Detect statistical anomalies in log volume."""
        logger.info("Detecting anomalies...")

        anomalies = []
        raw_logs = state.get("raw_logs", [])

        if not raw_logs:
            return {"anomalies": []}

        # Group by minute
        volume_by_minute: dict = {}
        for log in raw_logs:
            ts = int(log.get("timestamp", 0))
            minute = ts // 60_000_000_000  # Convert ns to minutes
            volume_by_minute[minute] = volume_by_minute.get(minute, 0) + 1

        if len(volume_by_minute) >= 2:
            volumes = list(volume_by_minute.values())
            avg = sum(volumes) / len(volumes)
            max_vol = max(volumes)

            # Detect spikes (> 3x average)
            if max_vol > avg * 3:
                anomalies.append(
                    {
                        "type": "volume_spike",
                        "severity": "warning",
                        "message": f"Log volume spike detected: {max_vol}x average",
                        "details": {
                            "average": avg,
                            "max": max_vol,
                            "ratio": max_vol / avg if avg > 0 else 0,
                        },
                    }
                )

        return {"anomalies": anomalies}

    async def analyze_patterns(self, state: ObservabilityState) -> dict:
        """Analyze recurring patterns in logs."""
        logger.info("Analyzing patterns...")

        patterns = []
        errors = state.get("errors", [])

        # Group by error type
        error_types: dict = {}
        for error in errors:
            msg = error.get("log", {}).get("message", "")[:100]
            error_types[msg] = error_types.get(msg, 0) + 1

        # Find recurring patterns
        for msg, count in error_types.items():
            if count > 1:
                patterns.append(
                    {
                        "type": "recurring_error",
                        "message": msg,
                        "count": count,
                        "severity": "warning" if count > 5 else "info",
                    }
                )

        logger.info(f"Found {len(patterns)} patterns")

        return {"patterns": patterns}

    async def aggregate_findings(self, state: ObservabilityState) -> dict:
        """Aggregate all findings."""
        logger.info("Aggregating findings...")

        findings = []

        # Convert errors to findings
        errors = state.get("errors", [])
        if errors:
            service_counts: dict = {}
            for error in errors:
                job = error.get("log", {}).get("labels", {}).get("job", "unknown")
                service_counts[job] = service_counts.get(job, 0) + 1

            for service, count in service_counts.items():
                if count >= 5:
                    findings.append(
                        Finding(
                            type="high_error_rate",
                            severity="critical" if count > 20 else "warning",
                            message=f"High error rate in {service}: {count} errors",
                            count=count,
                            affected_services=[service],
                            sample_logs=[
                                e.get("log", {}).get("message", "")[:200] for e in errors[:3]
                            ],
                        ).to_dict()
                    )

        # Add anomalies as findings
        for anomaly in state.get("anomalies", []):
            findings.append(anomaly)

        # Add patterns as findings
        for pattern in state.get("patterns", []):
            findings.append(pattern)

        return {"findings": findings}

    async def create_alerts(self, state: ObservabilityState) -> dict:
        """Create alerts in Grafana based on findings."""
        logger.info("Creating alerts...")

        alerts_created = []
        findings = state.get("findings", [])

        for finding in findings:
            if finding.get("severity") in ["critical", "warning"]:
                try:
                    alert_rule = {
                        "title": f"Auto: {finding.get('message', 'Unknown issue')[:50]}",
                        "condition": "B",
                        "data": [
                            {
                                "refId": "A",
                                "relativeTimeRange": {"from": 300, "to": 0},
                                "datasourceUid": "loki",  # Update with actual UID
                                "model": {
                                    "expr": f'sum(rate{{level=~"error|fatal"}}[5m])) > 0',
                                    "instant": True,
                                },
                            },
                            {
                                "refId": "B",
                                "relativeTimeRange": {"from": 0, "to": 0},
                                "datasourceUid": "__expr__",
                                "model": {
                                    "conditions": [
                                        {
                                            "evaluator": {"params": [0], "type": "gt"},
                                            "query": {"params": ["A"]},
                                            "type": "query",
                                        }
                                    ],
                                    "type": "classic_conditions",
                                },
                            },
                        ],
                        "noDataState": "OK",
                        "execErrState": "Error",
                        "for": "5m",
                        "labels": {
                            "severity": finding.get("severity", "warning"),
                            "auto_created": "true",
                        },
                        "annotations": {
                            "summary": finding.get("message", ""),
                            "finding_type": finding.get("type", ""),
                        },
                    }

                    uid = await self.grafana.create_alert_rule(alert_rule)
                    alerts_created.append(
                        {"finding": finding, "alert_uid": uid, "status": "created"}
                    )
                    logger.info(f"Created alert: {uid}")

                except Exception as e:
                    logger.error(f"Failed to create alert: {e}")
                    alerts_created.append({"finding": finding, "status": "failed", "error": str(e)})

        return {"alerts_created": alerts_created}

    async def generate_summary(self, state: ObservabilityState) -> dict:
        """Generate a human-readable summary."""
        logger.info("Generating summary...")

        total_logs = len(state.get("raw_logs", []))
        total_errors = len(state.get("errors", []))
        total_anomalies = len(state.get("anomalies", []))
        alerts_created = len(state.get("alerts_created", []))

        summary = f"""
## Observability Report

**Time Range:** {state.get("time_range", "unknown")}
**Run ID:** {state.get("run_id", "unknown")}

### Summary
- Total logs processed: {total_logs}
- Errors detected: {total_errors}
- Anomalies detected: {total_anomalies}
- Alerts created: {alerts_created}

### Findings
"""

        findings = state.get("findings", [])
        if findings:
            for i, finding in enumerate(findings[:5], 1):
                summary += f"\n{i}. **{finding.get('severity', 'info').upper()}**: {finding.get('message', 'No message')}"
        else:
            summary += "\nNo significant findings."

        return {"summary": summary}

    async def run(self, time_range: str = "last 15m", services: list[str] | None = None) -> dict:
        """Run the complete observability pipeline."""

        initial_state: ObservabilityState = {
            "time_range": time_range,
            "services": services,
            "loki_url": self.loki_url,
            "grafana_url": self.grafana_url,
            "raw_logs": [],
            "parsed_logs": [],
            "errors": [],
            "anomalies": [],
            "patterns": [],
            "findings": [],
            "alerts_created": [],
            "summary": "",
            "run_id": datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        }

        try:
            result = await self.graph.ainvoke(initial_state)
            result["completed_at"] = datetime.utcnow().isoformat()
            return result
        finally:
            await self.loki.close()
            await self.grafana.close()


async def main():
    """Run the pipeline as a standalone script."""
    pipeline = ObservabilityPipeline()

    result = await pipeline.run(
        time_range="last 1h",
        services=None,  # Monitor all services
    )

    print(result["summary"])

    if result.get("alerts_created"):
        print(f"\nCreated {len(result['alerts_created'])} alerts")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
