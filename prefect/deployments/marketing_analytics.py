#!/usr/bin/env python3
"""Deploy marketing analytics pipeline to Prefect."""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prefect import flow
from prefect.logging import get_logger

logger = get_logger()


def deploy_pipeline(client_id: str = "client1", sources: list | None = None):
    """Deploy the marketing analytics pipeline."""
    if sources is None:
        sources = ["ga4", "gads", "fbads", "prestashop"]

    from flows.marketing_pipeline import marketing_analytics_pipeline

    logger.info(f"Deploying pipeline for client: {client_id}")

    deployment = marketing_analytics_pipeline.deploy(
        name=f"marketing-analytics-{client_id}",
        work_pool_name="docker-pool",
        image="prefecthq/prefect:3-latest",
        build=False,  # Don't rebuild image
        parameters={
            "client_id": client_id,
            "sources": sources,
        },
        tags=["marketing", client_id],
    )

    logger.info(f"Deployment created: {deployment}")
    return deployment


def main():
    parser = argparse.ArgumentParser(description="Deploy marketing analytics pipeline")
    parser.add_argument("--client", default="client1", help="Client ID")
    parser.add_argument("--all", action="store_true", help="Deploy for all clients")
    parser.add_argument("--sources", nargs="+", help="Sources to sync")
    args = parser.parse_args()

    if args.all:
        clients = ["client1", "client2"]  # Add more clients as needed
        for client in clients:
            deploy_pipeline(client, args.sources)
    else:
        deploy_pipeline(args.client, args.sources)


if __name__ == "__main__":
    main()
