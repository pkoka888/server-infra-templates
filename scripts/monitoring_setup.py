#!/usr/bin/env python3
"""
Prefect Flow Health Monitoring and Alerting.

Monitors Prefect flow runs, collects metrics, and sends notifications
on failures. Integrates with Slack and email for alerting.

Usage:
    python monitoring_setup.py --check
    python monitoring_setup.py --watch --interval 60
    python monitoring_setup.py --alert-on-failure --channels slack,email

Environment Variables:
    SLACK_WEBHOOK_URL - Slack webhook for notifications
    EMAIL_SMTP_HOST - SMTP server for email alerts
    EMAIL_RECIPIENTS - Comma-separated list of recipients
    PREFECT_API_URL - Prefect API endpoint
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("prefect_monitoring")


class ExitCode(IntEnum):
    """Exit codes for monitoring script."""

    SUCCESS = 0
    CONFIG_ERROR = 1
    CHECK_ERROR = 2
    ALERT_ERROR = 3


@dataclass
class MonitoringConfig:
    """Configuration for monitoring."""

    prefect_api_url: str
    prefect_api_key: str | None
    slack_webhook: str | None
    smtp_host: str | None
    smtp_port: int
    email_recipients: list[str]
    check_interval_seconds: int
    alert_cooldown_minutes: int

    @classmethod
    def from_environment(cls) -> MonitoringConfig:
        """Load configuration from environment variables."""
        email_recipients = os.getenv("EMAIL_RECIPIENTS", "")
        return cls(
            prefect_api_url=os.getenv("PREFECT_API_URL", "http://localhost:4200/api"),
            prefect_api_key=os.getenv("PREFECT_API_KEY"),
            slack_webhook=os.getenv("SLACK_WEBHOOK_URL"),
            smtp_host=os.getenv("EMAIL_SMTP_HOST"),
            smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
            email_recipients=[e.strip() for e in email_recipients.split(",") if e.strip()],
            check_interval_seconds=int(os.getenv("CHECK_INTERVAL_SECONDS", "300")),
            alert_cooldown_minutes=int(os.getenv("ALERT_COOLDOWN_MINUTES", "60")),
        )


@dataclass
class FlowRunStatus:
    """Status of a flow run."""

    id: str
    name: str
    state: str
    start_time: datetime | None
    end_time: datetime | None
    duration_seconds: float | None
    parameters: dict[str, Any]
    error_message: str | None = None


class NotificationChannel:
    """Base class for notification channels."""

    def send(self, title: str, message: str, details: dict | None = None) -> bool:
        """Send notification."""
        raise NotImplementedError


class SlackNotifier(NotificationChannel):
    """Slack webhook notifier."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = requests.Session()

    def send(self, title: str, message: str, details: dict | None = None) -> bool:
        """Send notification to Slack."""
        color = "danger" if "fail" in message.lower() else "good"

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in (details or {}).items()
                    ],
                    "footer": "Prefect Monitoring",
                    "ts": int(datetime.now(timezone.utc).timestamp()),
                }
            ]
        }

        try:
            response = self.session.post(
                self.webhook_url,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            logger.info("Slack notification sent")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class EmailNotifier(NotificationChannel):
    """Email notifier (placeholder implementation)."""

    def __init__(self, smtp_host: str, smtp_port: int, recipients: list[str]):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.recipients = recipients

    def send(self, title: str, message: str, details: dict | None = None) -> bool:
        """Send email notification."""
        # Placeholder - would use smtplib in production
        logger.info(f"[EMAIL] Would send to {self.recipients}: {title}")
        return True


class PrefectMonitor:
    """
    Monitors Prefect flow runs and handles alerting.

    Tracks flow run states, collects metrics, and sends notifications
    on failures or anomalies.
    """

    FAILED_STATES = {"FAILED", "CRASHED", "CANCELLED"}
    WARNING_STATES = {"LATE", "PAUSED"}

    def __init__(self, config: MonitoringConfig | None = None):
        self.config = config or MonitoringConfig.from_environment()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        if self.config.prefect_api_key:
            self.session.headers["Authorization"] = f"Bearer {self.config.prefect_api_key}"

        self.notifiers: list[NotificationChannel] = []
        if self.config.slack_webhook:
            self.notifiers.append(SlackNotifier(self.config.slack_webhook))
        if self.config.smtp_host and self.config.email_recipients:
            self.notifiers.append(
                EmailNotifier(
                    self.config.smtp_host,
                    self.config.smtp_port,
                    self.config.email_recipients,
                )
            )

        self._last_alert_time: dict[str, datetime] = {}

    def get_recent_flow_runs(
        self,
        hours: int = 24,
        flow_name: str | None = None,
    ) -> list[FlowRunStatus]:
        """
        Get recent flow runs.

        Args:
            hours: Lookback period in hours
            flow_name: Optional flow name filter

        Returns:
            List of flow run statuses
        """
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        url = urljoin(self.config.prefect_api_url, "/flow_runs/filter")
        payload = {
            "sort": "START_TIME_DESC",
            "limit": 100,
            "flow_runs": {
                "start_time": {"after_": since},
            },
        }

        if flow_name:
            payload["flows"] = {"name": {"any_": [flow_name]}}

        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            runs = response.json()

            return [self._parse_flow_run(run) for run in runs]

        except requests.RequestException as e:
            logger.error(f"Failed to get flow runs: {e}")
            return []

    def _parse_flow_run(self, run: dict) -> FlowRunStatus:
        """Parse flow run response into FlowRunStatus."""
        state = run.get("state", {})
        start_time = run.get("start_time")
        end_time = run.get("end_time")

        duration = None
        if start_time and end_time:
            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            duration = (end - start).total_seconds()

        return FlowRunStatus(
            id=run["id"],
            name=run.get("name", "Unknown"),
            state=state.get("name", "UNKNOWN"),
            start_time=datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            if start_time
            else None,
            end_time=datetime.fromisoformat(end_time.replace("Z", "+00:00")) if end_time else None,
            duration_seconds=duration,
            parameters=run.get("parameters", {}),
            error_message=state.get("message"),
        )

    def check_flow_health(self, flow_name: str | None = None) -> dict[str, Any]:
        """
        Check health of recent flow runs.

        Returns:
            Health status summary
        """
        runs = self.get_recent_flow_runs(hours=24, flow_name=flow_name)

        failed = [r for r in runs if r.state in self.FAILED_STATES]
        warning = [r for r in runs if r.state in self.WARNING_STATES]
        completed = [r for r in runs if r.state == "COMPLETED"]

        health = {
            "total": len(runs),
            "completed": len(completed),
            "failed": len(failed),
            "warning": len(warning),
            "failed_runs": failed,
            "warning_runs": warning,
        }

        # Alert on failures
        for run in failed:
            self._alert_on_failure(run)

        return health

    def _alert_on_failure(self, run: FlowRunStatus) -> None:
        """Send alert for failed flow run."""
        # Check cooldown
        last_alert = self._last_alert_time.get(run.id)
        if last_alert:
            cooldown = timedelta(minutes=self.config.alert_cooldown_minutes)
            if datetime.now(timezone.utc) - last_alert < cooldown:
                logger.debug(f"Skipping alert for {run.id} (cooldown)")
                return

        title = f"❌ Flow Run Failed: {run.name}"
        message = f"Flow run failed with state: {run.state}"
        if run.error_message:
            message += f"\nError: {run.error_message}"

        details = {
            "Run ID": run.id,
            "State": run.state,
            "Client": run.parameters.get("client_id", "unknown"),
            "Duration": f"{run.duration_seconds:.0f}s" if run.duration_seconds else "N/A",
        }

        for notifier in self.notifiers:
            notifier.send(title, message, details)

        self._last_alert_time[run.id] = datetime.now(timezone.utc)

    def collect_metrics(self) -> dict[str, Any]:
        """
        Collect metrics about flow runs.

        Returns:
            Metrics dictionary
        """
        runs = self.get_recent_flow_runs(hours=24)

        total_duration = sum(r.duration_seconds for r in runs if r.duration_seconds)
        avg_duration = total_duration / len(runs) if runs else 0

        by_state: dict[str, int] = {}
        for run in runs:
            by_state[run.state] = by_state.get(run.state, 0) + 1

        by_client: dict[str, dict] = {}
        for run in runs:
            client = run.parameters.get("client_id", "unknown")
            if client not in by_client:
                by_client[client] = {"total": 0, "failed": 0}
            by_client[client]["total"] += 1
            if run.state in self.FAILED_STATES:
                by_client[client]["failed"] += 1

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_runs_24h": len(runs),
            "average_duration_seconds": avg_duration,
            "by_state": by_state,
            "by_client": by_client,
        }

    def watch_continuously(
        self,
        flow_name: str | None = None,
        on_health_check: callable | None = None,
    ) -> None:
        """
        Watch flow runs continuously.

        Args:
            flow_name: Optional flow name to watch
            on_health_check: Optional callback for health check results
        """
        logger.info(
            f"Starting continuous monitoring (interval: {self.config.check_interval_seconds}s)"
        )

        while True:
            try:
                health = self.check_flow_health(flow_name)
                metrics = self.collect_metrics()

                if on_health_check:
                    on_health_check(health, metrics)

                logger.info(
                    f"Health check: {health['completed']} completed, "
                    f"{health['failed']} failed, {health['warning']} warning"
                )

                time.sleep(self.config.check_interval_seconds)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
                time.sleep(self.config.check_interval_seconds)


def main() -> int:
    """Main entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Monitor Prefect flows and send alerts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check
  %(prog)s --watch --interval 60
  %(prog)s --metrics --output metrics.json
        """,
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Run single health check",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch continuously",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300)",
    )
    parser.add_argument(
        "--flow",
        type=str,
        help="Flow name to monitor (default: all)",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Collect and output metrics",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for metrics (JSON)",
    )

    args = parser.parse_args()

    config = MonitoringConfig.from_environment()
    config.check_interval_seconds = args.interval

    monitor = PrefectMonitor(config)

    try:
        if args.check:
            health = monitor.check_flow_health(args.flow)
            print("Health Status:")
            print(f"  Total: {health['total']}")
            print(f"  Completed: {health['completed']}")
            print(f"  Failed: {health['failed']}")
            print(f"  Warning: {health['warning']}")

            if health["failed_runs"]:
                print("\nFailed Runs:")
                for run in health["failed_runs"]:
                    print(f"  - {run.name} ({run.id}): {run.state}")

            return 0 if health["failed"] == 0 else 2

        elif args.watch:

            def on_check(health: dict, metrics: dict) -> None:
                if args.output:
                    with open(args.output, "w") as f:
                        json.dump({"health": health, "metrics": metrics}, f, indent=2, default=str)

            monitor.watch_continuously(args.flow, on_check)

        elif args.metrics:
            metrics = monitor.collect_metrics()
            output = json.dumps(metrics, indent=2, default=str)

            if args.output:
                with open(args.output, "w") as f:
                    f.write(output)
                logger.info(f"Metrics written to {args.output}")
            else:
                print(output)

        else:
            logger.error("No action specified. Use --check, --watch, or --metrics")
            return 1

        return 0

    except Exception as e:
        logger.exception(f"Monitoring failed: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
