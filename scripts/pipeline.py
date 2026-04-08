#!/usr/bin/env python3
"""
dlt Multi-Client Data Pipeline for Metabase Analytics
Supports: Google Analytics 4, Google Ads, Facebook Ads, PrestaShop

Usage:
    python pipeline.py --source ga4 --client CLIENT_ID
    python pipeline.py --source gads --client CLIENT_ID
    python pipeline.py --source fbads --client CLIENT_ID
    python pipeline.py --source prestashop --client CLIENT_ID
    python pipeline.py --all --client CLIENT_ID
"""

import argparse
import logging
import os
from datetime import datetime
from pathlib import Path

import dlt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pipeline configuration
PIPELINE_NAME = "metabase_analytics"

# Try to import LangGraph client (optional)
try:
    from langgraph_client import get_langgraph_client

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.info("LangGraph client not available, skipping integration")


def get_client_env(client_id: str) -> dict:
    """Load client-specific environment variables."""
    env_file = f".env.{client_id}"

    env = {}
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env[key.strip()] = value.strip()

    # Also check .env
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() not in env:
                            env[key.strip()] = value.strip()

    return env


def run_ga4_pipeline(client_id: str, credentials: dict) -> dlt.Pipeline:
    """Run Google Analytics 4 pipeline using dlt verified source."""
    from google_analytics import google_analytics

    dataset_name = f"ga4_{client_id}"

    pipeline = dlt.pipeline(
        pipeline_name=f"{PIPELINE_NAME}_ga4_{client_id}",
        destination="postgres",
        dataset_name=dataset_name,
    )

    # Configure queries for this client
    queries = [
        {
            "name": "traffic",
            "dimensions": ["date", "country", "city", "deviceCategory", "channelGroup"],
            "metrics": [
                "sessions",
                "totalUsers",
                "newUsers",
                "bounceRate",
                "averageSessionDuration",
            ],
            "date_range": {"start_date": "2024-01-01", "end_date": None},
        },
        {
            "name": "events",
            "dimensions": ["date", "eventName", "deviceCategory"],
            "metrics": ["eventCount", "users", "newUsers"],
            "date_range": {"start_date": "2024-01-01", "end_date": None},
        },
    ]

    # Get GA4 property ID from credentials
    property_id = credentials.get("GA4_PROPERTY_ID")
    if not property_id:
        logger.warning(f"No GA4_PROPERTY_ID for client {client_id}, skipping GA4")
        return None

    source = google_analytics(
        property_id=int(property_id),
        queries=queries,
        credentials={
            "client_id": credentials.get("GA4_CLIENT_ID"),
            "client_secret": credentials.get("GA4_CLIENT_SECRET"),
            "refresh_token": credentials.get("GA4_REFRESH_TOKEN"),
            "project_id": credentials.get("GA4_PROJECT_ID"),
        },
    )

    info = pipeline.run(source)
    logger.info(f"GA4 pipeline loaded {info}")
    return pipeline


def run_gads_pipeline(client_id: str, credentials: dict) -> dlt.Pipeline:
    """Run Google Ads pipeline using dlt verified source."""
    from google_ads import google_ads_source

    dataset_name = f"gads_{client_id}"

    pipeline = dlt.pipeline(
        pipeline_name=f"{PIPELINE_NAME}_gads_{client_id}",
        destination="postgres",
        dataset_name=dataset_name,
    )

    source = google_ads_source(
        credentials={
            "developer_token": credentials.get("GADS_DEVELOPER_TOKEN"),
            "client_id": credentials.get("GADS_CLIENT_ID"),
            "client_secret": credentials.get("GADS_CLIENT_SECRET"),
            "refresh_token": credentials.get("GADS_REFRESH_TOKEN"),
            "customer_id": credentials.get("GADS_CUSTOMER_ID"),
        }
    )

    info = pipeline.run(source)
    logger.info(f"Google Ads pipeline loaded {info}")
    return pipeline


def run_fbads_pipeline(client_id: str, credentials: dict) -> dlt.Pipeline:
    """Run Facebook Ads pipeline using dlt verified source."""
    from facebook_ads import facebook_ads_source

    dataset_name = f"fbads_{client_id}"

    pipeline = dlt.pipeline(
        pipeline_name=f"{PIPELINE_NAME}_fbads_{client_id}",
        destination="postgres",
        dataset_name=dataset_name,
    )

    # Get access token
    access_token = credentials.get("FB_ACCESS_TOKEN")
    if not access_token:
        logger.warning(f"No FB_ACCESS_TOKEN for client {client_id}, skipping FB Ads")
        return None

    ad_account_id = credentials.get("FB_AD_ACCOUNT_ID")
    if not ad_account_id:
        logger.warning(f"No FB_AD_ACCOUNT_ID for client {client_id}, skipping FB Ads")
        return None

    source = facebook_ads_source(
        access_token=access_token,
        ad_account_id=ad_account_id,
    )

    info = pipeline.run(source)
    logger.info(f"Facebook Ads pipeline loaded {info}")
    return pipeline


def run_prestashop_pipeline(client_id: str, credentials: dict) -> dlt.Pipeline:
    """Run PrestaShop pipeline - direct database connection."""
    import requests

    dataset_name = f"prestashop_{client_id}"

    pipeline = dlt.pipeline(
        pipeline_name=f"{PIPELINE_NAME}_prestashop_{client_id}",
        destination="postgres",
        dataset_name=dataset_name,
    )

    # Get PrestaShop API credentials
    shop_url = credentials.get("PS_SHOP_URL")
    api_key = credentials.get("PS_API_KEY")

    if not shop_url or not api_key:
        logger.warning(f"No PrestaShop credentials for client {client_id}")
        return None

    # PrestaShop API base - use ws_key query param (most reliable)
    api_url = f"{shop_url}/api/"
    auth_params = {"ws_key": api_key}

    def get_orders():
        """Fetch orders from PrestaShop."""
        response = requests.get(f"{api_url}orders", params={**auth_params, "limit": 1000})
        if response.status_code == 200:
            return response.json().get("orders", [])
        return []

    def get_customers():
        """Fetch customers from PrestaShop."""
        response = requests.get(f"{api_url}customers", params={**auth_params, "limit": 1000})
        if response.status_code == 200:
            return response.json().get("customers", [])
        return []

    def get_products():
        """Fetch products from PrestaShop."""
        response = requests.get(f"{api_url}products", params={**auth_params, "limit": 1000})
        if response.status_code == 200:
            return response.json().get("products", [])
        return []

    # Extract data
    data = []

    orders = get_orders()
    for order in orders:
        data.append({"type": "order", "data": order})

    customers = get_customers()
    for customer in customers:
        data.append({"type": "customer", "data": customer})

    products = get_products()
    for product in products:
        data.append({"type": "product", "data": product})

    info = pipeline.run(data, table_name="prestashop_data")
    logger.info(f"PrestaShop pipeline loaded {info}")
    return pipeline


def run_all_pipelines(client_id: str):
    """Run all pipelines for a client."""
    credentials = get_client_env(client_id)

    # Initialize LangGraph client for logging
    langgraph_client = None
    if LANGGRAPH_AVAILABLE:
        langgraph_client = get_langgraph_client()
        if langgraph_client:
            logger.info("LangGraph client connected, logging pipeline start")
        else:
            logger.info("LangGraph not available, continuing without integration")

    results = {}

    # Pre-run: Validate client configuration
    if langgraph_client:
        try:
            langgraph_client.log_event(
                client_id,
                "pipeline_start",
                {
                    "sources": ["ga4", "gads", "fbads", "prestashop"],
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to log to LangGraph: {e}")

    try:
        results["ga4"] = run_ga4_pipeline(client_id, credentials)
    except Exception as e:
        logger.error(f"GA4 pipeline failed: {e}")

    try:
        results["gads"] = run_gads_pipeline(client_id, credentials)
    except Exception as e:
        logger.error(f"Google Ads pipeline failed: {e}")

    try:
        results["fbads"] = run_fbads_pipeline(client_id, credentials)
    except Exception as e:
        logger.error(f"Facebook Ads pipeline failed: {e}")

    try:
        results["prestashop"] = run_prestashop_pipeline(client_id, credentials)
    except Exception as e:
        logger.error(f"PrestaShop pipeline failed: {e}")

    # Post-run: Log completion status
    if langgraph_client:
        try:
            success_count = sum(1 for r in results.values() if r is not None)
            langgraph_client.log_event(
                client_id,
                "pipeline_complete",
                {
                    "sources_attempted": 4,
                    "sources_succeeded": success_count,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to log completion to LangGraph: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(description="dlt Multi-Client Data Pipeline")
    parser.add_argument(
        "--source",
        choices=["ga4", "gads", "fbads", "prestashop", "all"],
        default="all",
        help="Data source to sync",
    )
    parser.add_argument("--client", required=True, help="Client ID for environment")
    parser.add_argument("--list-clients", action="store_true", help="List available clients")

    args = parser.parse_args()

    if args.list_clients:
        print("Available clients:")
        for f in Path(".").glob(".env.*"):
            print(f"  - {f.name[5:]}")  # Remove .env. prefix
        return

    run_all_pipelines(args.client)


if __name__ == "__main__":
    main()
