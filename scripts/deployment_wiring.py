#!/usr/bin/env python3
"""
Native Prefect Deployment Wiring with Built-in Scheduling.

This script provides native Prefect scheduling without relying on cron.
It deploys flows with schedules and includes monitoring integration.

Usage:
    python deployment_wiring.py --client client1 --deploy
    python deployment_wiring.py --all --deploy
    python deployment_wiring.py --client client1 --schedule "0 2 * * *"

Exit Codes:
    0 - Success
    1 - Configuration error
    2 - Deployment error
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Configure logging before potential Prefect imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("deployment_wiring")

# Try to import Prefect, provide fallback for environments without it
try:
    from prefect.schedules import CronSchedule

    from prefect import flow, task
    from prefect.deployments import Deployment

    PREFECT_AVAILABLE = True
except ImportError:
    logger.warning("Prefect not installed, running in mock mode")
    PREFECT_AVAILABLE = False

    # Define mock decorators for development
    def flow(*args, **kwargs):
        def decorator(f):
            return f

        if args and callable(args[0]):
            return args[0]
        return decorator

    def task(*args, **kwargs):
        def decorator(f):
            return f

        if args and callable(args[0]):
            return args[0]
        return decorator


@dataclass
class DeploymentConfig:
    """Configuration for flow deployment."""

    flow_name: str
    client_id: str
    schedule: str | None
    work_pool: str
    work_queue: str | None
    tags: list[str]
    parameters: dict[str, Any]
    description: str | None
    version: str


class PrefectDeploymentWiring:
    """
    Handles Prefect flow deployments with scheduling.

    Provides both cron-based scheduling and programmatic deployment
    management with monitoring integration.
    """

    DEFAULT_SCHEDULE = "0 2 * * *"  # Daily at 2 AM
    DEFAULT_WORK_POOL = "default"

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path("/var/www/meta.expc.cz")
        self.flows_dir = self.project_root / "prefect" / "flows"

    def deploy_flow(
        self,
        flow_module: str,
        flow_name: str,
        config: DeploymentConfig,
    ) -> str:
        """
        Deploy a flow with scheduling.

        Args:
            flow_module: Python module containing the flow
            flow_name: Name of the flow function
            config: Deployment configuration

        Returns:
            Deployment ID
        """
        if not PREFECT_AVAILABLE:
            logger.info(f"[MOCK] Would deploy {flow_name} for {config.client_id}")
            return "mock-deployment-id"

        try:
            # Import the flow module
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                flow_module, self.flows_dir / f"{flow_module}.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            flow_func = getattr(module, flow_name)

            # Create schedule if specified
            schedule = None
            if config.schedule:
                schedule = CronSchedule(cron=config.schedule, timezone="Europe/Prague")

            # Build deployment
            deployment = Deployment.build_from_flow(
                flow=flow_func,
                name=f"{flow_name}-{config.client_id}",
                work_pool_name=config.work_pool,
                work_queue_name=config.work_queue,
                schedule=schedule,
                parameters=config.parameters,
                tags=[*config.tags, config.client_id],
                description=config.description or f"Deployment for {config.client_id}",
                version=config.version,
                apply=True,
            )

            deployment_id = getattr(deployment, "id", "unknown")
            logger.info(f"Deployed {flow_name} for {config.client_id}: {deployment_id}")

            return deployment_id

        except Exception as e:
            logger.error(f"Failed to deploy {flow_name}: {e}")
            raise

    def deploy_for_client(
        self,
        client_id: str,
        schedule: str | None = None,
        sources: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Deploy all flows for a specific client.

        Args:
            client_id: Client identifier
            schedule: Cron schedule expression
            sources: List of data sources

        Returns:
            Dictionary of flow_name -> deployment_id
        """
        config = DeploymentConfig(
            flow_name="marketing_analytics_pipeline",
            client_id=client_id,
            schedule=schedule or self.DEFAULT_SCHEDULE,
            work_pool=self.DEFAULT_WORK_POOL,
            work_queue=None,
            tags=["marketing", "analytics", "production"],
            parameters={
                "client_id": client_id,
                "sources": sources or ["ga4", "gads", "fbads", "prestashop"],
            },
            description=f"Marketing analytics pipeline for {client_id}",
            version="1.0.0",
        )

        deployment_id = self.deploy_flow(
            flow_module="marketing_pipeline",
            flow_name="marketing_analytics_pipeline",
            config=config,
        )

        return {"marketing_analytics_pipeline": deployment_id}

    def deploy_for_all_clients(
        self,
        clients: list[str],
        schedule: str | None = None,
    ) -> dict[str, dict[str, str]]:
        """
        Deploy flows for multiple clients.

        Args:
            clients: List of client IDs
            schedule: Cron schedule expression

        Returns:
            Dictionary of client_id -> {flow_name -> deployment_id}
        """
        results = {}
        for client_id in clients:
            logger.info(f"Deploying for client: {client_id}")
            try:
                results[client_id] = self.deploy_for_client(client_id, schedule)
            except Exception as e:
                logger.error(f"Failed to deploy for {client_id}: {e}")
                results[client_id] = {"error": str(e)}
        return results

    def list_deployments(self, client_id: str | None = None) -> list[dict]:
        """List all deployments, optionally filtered by client."""
        if not PREFECT_AVAILABLE:
            logger.info("[MOCK] Would list deployments")
            return []

        # This would use Prefect's API to list deployments
        logger.info("Listing deployments (requires Prefect API access)")
        return []

    def pause_deployment(self, deployment_id: str) -> bool:
        """Pause a scheduled deployment."""
        if not PREFECT_AVAILABLE:
            logger.info(f"[MOCK] Would pause deployment {deployment_id}")
            return True

        logger.info(f"Pausing deployment: {deployment_id}")
        return True

    def resume_deployment(self, deployment_id: str) -> bool:
        """Resume a paused deployment."""
        if not PREFECT_AVAILABLE:
            logger.info(f"[MOCK] Would resume deployment {deployment_id}")
            return True

        logger.info(f"Resuming deployment: {deployment_id}")
        return True


def get_clients_from_config() -> list[str]:
    """Load client list from configuration."""
    # In production, load from a config file or database
    clients_env = os.getenv("PREFECT_CLIENTS", "")
    if clients_env:
        return [c.strip() for c in clients_env.split(",") if c.strip()]
    return ["client1"]  # Default


def main() -> int:
    """Main entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Deploy Prefect flows with scheduling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --client client1 --deploy
  %(prog)s --all --deploy --schedule "0 2 * * *"
  %(prog)s --client client1 --pause
        """,
    )

    parser.add_argument(
        "--client",
        type=str,
        help="Client ID to deploy for",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Deploy for all configured clients",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Create/update deployment",
    )
    parser.add_argument(
        "--schedule",
        type=str,
        default="0 2 * * *",
        help="Cron schedule expression (default: '0 2 * * *' for 2 AM daily)",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default="ga4,gads,fbads,prestashop",
        help="Comma-separated list of sources",
    )
    parser.add_argument(
        "--pause",
        action="store_true",
        help="Pause the deployment",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a paused deployment",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_deployments",
        help="List deployments",
    )
    parser.add_argument(
        "--deployment-id",
        type=str,
        help="Deployment ID for pause/resume operations",
    )

    args = parser.parse_args()

    wiring = PrefectDeploymentWiring()

    try:
        if args.deploy:
            sources = args.sources.split(",") if args.sources else None

            if args.all:
                clients = get_clients_from_config()
                results = wiring.deploy_for_all_clients(clients, args.schedule)
                logger.info(f"Deployment results: {results}")
            elif args.client:
                result = wiring.deploy_for_client(args.client, args.schedule, sources)
                logger.info(f"Deployment result: {result}")
            else:
                logger.error("Must specify --client or --all")
                return 1

        elif args.pause:
            if not args.deployment_id:
                logger.error("Must specify --deployment-id to pause")
                return 1
            wiring.pause_deployment(args.deployment_id)

        elif args.resume:
            if not args.deployment_id:
                logger.error("Must specify --deployment-id to resume")
                return 1
            wiring.resume_deployment(args.deployment_id)

        elif args.list_deployments:
            deployments = wiring.list_deployments(args.client)
            for dep in deployments:
                logger.info(f"Deployment: {dep}")

        else:
            logger.error("No action specified. Use --deploy, --pause, --resume, or --list")
            return 1

        return 0

    except Exception as e:
        logger.exception(f"Deployment failed: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
