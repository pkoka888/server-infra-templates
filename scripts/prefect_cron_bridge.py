#!/usr/bin/env python3
"""
Prefect Cron Bridge - Trigger Prefect flows via API from cron.

This script provides a bridge between traditional cron scheduling and
Prefect's flow orchestration, enabling cron-based triggers with proper
authentication, logging, and error handling.

Usage:
    python prefect_cron_bridge.py --client client1 --env production
    python prefect_cron_bridge.py --flow marketing_analytics_pipeline --client client2

Exit Codes:
    0 - Success
    1 - Configuration error
    2 - Authentication error
    3 - Flow trigger error
    4 - Flow run monitoring error
    5 - Flow run failed
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("prefect_cron_bridge")


class ExitCode(IntEnum):
    """Exit codes for cron integration."""

    SUCCESS = 0
    CONFIG_ERROR = 1
    AUTH_ERROR = 2
    TRIGGER_ERROR = 3
    MONITOR_ERROR = 4
    FLOW_FAILED = 5


@dataclass
class PrefectConfig:
    """Configuration for Prefect API connection."""

    api_url: str
    api_key: str | None
    timeout_seconds: int = 300
    poll_interval_seconds: int = 10
    max_wait_seconds: int = 3600

    @classmethod
    def from_environment(cls) -> PrefectConfig:
        """Load configuration from environment variables."""
        api_url = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")
        api_key = os.getenv("PREFECT_API_KEY")
        timeout = int(os.getenv("PREFECT_TIMEOUT", "300"))
        poll_interval = int(os.getenv("PREFECT_POLL_INTERVAL", "10"))
        max_wait = int(os.getenv("PREFECT_MAX_WAIT", "3600"))

        if not api_url:
            raise ValueError("PREFECT_API_URL environment variable not set")

        return cls(
            api_url=api_url,
            api_key=api_key,
            timeout_seconds=timeout,
            poll_interval_seconds=poll_interval,
            max_wait_seconds=max_wait,
        )


class PrefectCronBridge:
    """
    Bridge between cron and Prefect flow runs.

    Handles flow triggering, status monitoring, and result reporting
    suitable for cron-based scheduling.
    """

    # Flow run states that indicate completion
    TERMINAL_STATES = {"COMPLETED", "FAILED", "CRASHED", "CANCELLED"}
    SUCCESS_STATES = {"COMPLETED"}

    def __init__(self, config: PrefectConfig | None = None):
        self.config = config or PrefectConfig.from_environment()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        if self.config.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.config.api_key}"

    def trigger_flow(
        self,
        flow_name: str,
        parameters: dict[str, Any],
        deployment_name: str | None = None,
    ) -> str:
        """
        Trigger a Prefect flow run.

        Args:
            flow_name: Name of the flow to trigger
            parameters: Flow parameters
            deployment_name: Optional specific deployment name

        Returns:
            Flow run ID

        Raises:
            requests.RequestException: If API call fails
        """
        # First, find the deployment
        deployment_id = self._get_deployment_id(flow_name, deployment_name)

        if not deployment_id:
            raise RuntimeError(f"No deployment found for flow: {flow_name}")

        logger.info(f"Found deployment {deployment_id} for flow {flow_name}")

        # Create flow run
        url = urljoin(self.config.api_url, f"/deployments/{deployment_id}/create_flow_run")

        payload = {
            "parameters": parameters,
            "state": {"type": "SCHEDULED", "message": "Triggered by cron"},
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
            flow_run = response.json()
            flow_run_id = flow_run["id"]
            logger.info(f"Created flow run: {flow_run_id}")
            return flow_run_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger flow: {e}")
            raise

    def _get_deployment_id(self, flow_name: str, deployment_name: str | None = None) -> str | None:
        """Get deployment ID for a flow."""
        url = urljoin(self.config.api_url, "/deployments/filter")

        payload = {"flows": {"name": {"any_": [flow_name]}}}

        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            deployments = response.json()

            if deployments:
                return deployments[0]["id"]
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get deployment: {e}")
            return None

    def wait_for_completion(self, flow_run_id: str) -> dict[str, Any]:
        """
        Poll flow run until completion.

        Args:
            flow_run_id: ID of the flow run to monitor

        Returns:
            Final flow run state

        Raises:
            TimeoutError: If flow doesn't complete within max_wait_seconds
        """
        url = urljoin(self.config.api_url, f"/flow_runs/{flow_run_id}")
        start_time = time.time()

        while time.time() - start_time < self.config.max_wait_seconds:
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                flow_run = response.json()

                state = flow_run.get("state", {})
                state_type = state.get("type", "UNKNOWN")
                state_name = state.get("name", "Unknown")

                logger.info(f"Flow run status: {state_name}")

                if state_type in self.TERMINAL_STATES:
                    logger.info(f"Flow run reached terminal state: {state_type}")
                    return flow_run

                time.sleep(self.config.poll_interval_seconds)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error polling flow run: {e}")
                time.sleep(self.config.poll_interval_seconds)

        raise TimeoutError(
            f"Flow run {flow_run_id} did not complete within {self.config.max_wait_seconds}s"
        )

    def run_flow(
        self,
        flow_name: str,
        parameters: dict[str, Any],
        wait: bool = True,
        deployment_name: str | None = None,
    ) -> tuple[str, dict[str, Any] | None]:
        """
        Trigger and optionally wait for a flow run.

        Args:
            flow_name: Name of the flow
            parameters: Flow parameters
            wait: Whether to wait for completion
            deployment_name: Optional deployment name

        Returns:
            Tuple of (flow_run_id, final_state or None)
        """
        flow_run_id = self.trigger_flow(flow_name, parameters, deployment_name)

        if not wait:
            return flow_run_id, None

        final_state = self.wait_for_completion(flow_run_id)
        return flow_run_id, final_state


def main() -> int:
    """Main entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Trigger Prefect flows from cron",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --client client1
  %(prog)s --flow marketing_analytics_pipeline --client client2 --env production
  %(prog)s --client client1 --no-wait
        """,
    )

    parser.add_argument(
        "--client",
        type=str,
        required=True,
        help="Client ID to run the pipeline for",
    )
    parser.add_argument(
        "--flow",
        type=str,
        default="marketing_analytics_pipeline",
        help="Flow name to trigger (default: marketing_analytics_pipeline)",
    )
    parser.add_argument(
        "--env",
        type=str,
        default="staging",
        choices=["staging", "production"],
        help="Environment to run in",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default="ga4,gads,fbads,prestashop",
        help="Comma-separated list of sources (default: all)",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for flow completion (fire-and-forget)",
    )
    parser.add_argument(
        "--deployment",
        type=str,
        help="Specific deployment name (optional)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Log file path (default: stdout only)",
    )

    args = parser.parse_args()

    # Add file handler if requested
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)

    logger.info(f"Starting cron bridge for client: {args.client}")
    logger.info(f"Environment: {args.env}")
    logger.info(f"Flow: {args.flow}")

    try:
        # Load configuration
        config = PrefectConfig.from_environment()
        bridge = PrefectCronBridge(config)

        # Build flow parameters
        sources = args.sources.split(",") if args.sources else None
        parameters = {
            "client_id": args.client,
            "sources": sources,
        }

        # Trigger flow
        flow_run_id, final_state = bridge.run_flow(
            flow_name=args.flow,
            parameters=parameters,
            wait=not args.no_wait,
            deployment_name=args.deployment,
        )

        if args.no_wait:
            logger.info(f"Flow triggered: {flow_run_id} (not waiting)")
            return ExitCode.SUCCESS

        # Check result
        if final_state:
            state_type = final_state.get("state", {}).get("type", "UNKNOWN")
            if state_type in bridge.SUCCESS_STATES:
                logger.info(f"Flow completed successfully: {flow_run_id}")
                return ExitCode.SUCCESS
            else:
                logger.error(f"Flow failed with state: {state_type}")
                return ExitCode.FLOW_FAILED

        return ExitCode.SUCCESS

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return ExitCode.CONFIG_ERROR
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in (401, 403):
            logger.error(f"Authentication error: {e}")
            return ExitCode.AUTH_ERROR
        logger.error(f"API error: {e}")
        return ExitCode.TRIGGER_ERROR
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return ExitCode.TRIGGER_ERROR
    except TimeoutError as e:
        logger.error(f"Monitoring timeout: {e}")
        return ExitCode.MONITOR_ERROR
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return ExitCode.TRIGGER_ERROR


if __name__ == "__main__":
    sys.exit(main())
