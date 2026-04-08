#!/usr/bin/env python3
"""
Deploy marketing analytics pipeline to Prefect.

Uses Prefect 3.x deployment patterns with Python API.
"""

import argparse
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent


def create_deployment_yaml(client_id: str, sources: list[str]):
    """Create deployment.yaml for Prefect deployment."""
    deployment = {
        "name": f"marketing-analytics-{client_id}",
        "version": "1.0.0",
        "work_pool": {
            "name": "docker-pool",
            "work_queue_name": f"queue-{client_id}",
        },
        "flow_name": "marketing_analytics_pipeline",
        "parameters": {
            "client_id": client_id,
            "sources": sources,
        },
        "tags": ["marketing", client_id],
        "description": f"Marketing analytics pipeline for {client_id}",
        "schedule": None,  # Can add cron schedule here
    }
    return deployment


def deploy_via_api(client_id: str, sources: list[str], api_url: str):
    """Deploy using Prefect REST API."""

    deployment = create_deployment_yaml(client_id, sources)
    deployment["path"] = str(PROJECT_ROOT / "prefect" / "flows")

    print(f"Deployment configuration for {client_id}:")
    print(yaml.dump(deployment, default_flow_style=False))

    print("\nTo deploy, use one of these methods:")
    print("\n1. Using Prefect YAML (recommended for production):")
    print("   Create prefect.yaml with deployment definition")
    print("   Run: prefect deploy --prefect-file prefect.yaml")
    print("\n2. Using Python API:")
    print("   from prefect import flow")
    print("   from prefect.flows import Flow")
    print("   flow.from_source(...)")
    print("\n3. Manual deployment via API:")
    print(f"   POST {api_url}/deployments")


def deploy_with_prefect_yaml():
    """Generate prefect.yaml for this project."""
    prefect_yaml = {
        " prefect-version": "3.0.0",
        "build": [
            {
                "prefect-docker/docker": {
                    "image": "prefecthq/prefect:3-latest",
                    "context": ".",
                }
            }
        ],
        "push": [
            {
                "prefect-docker/docker": {
                    "image": "prefecthq/prefect:3-meta-expccz:latest",
                    "context": ".",
                }
            }
        ],
        "pull": [{"prefect-gcp/gcr": {"repository": "prefecthq", "tag": "3-latest"}}],
        "deployments": [
            {
                "name": "marketing-analytics-{client_id}",
                "work_pool": {"name": "docker-pool"},
                "flow_location": "./prefect/flows/marketing_pipeline.py",
                "entrypoint": "marketing_pipeline:marketing_analytics_pipeline",
                "parameters": {
                    "client_id": "{client_id}",
                    "sources": ["ga4", "gads", "fbads", "prestashop"],
                },
                "schedule": {
                    "cron": "0 1 * * *",
                    "timezone": "Europe/Prague",
                },
                "tags": ["marketing", "etl"],
            }
        ],
    }

    yaml_content = yaml.dump(prefect_yaml, default_flow_style=False, sort_keys=False)
    yaml_content = yaml_content.replace("' prefect", "prefect")  # Fix key formatting

    output_path = PROJECT_ROOT / "prefect" / "prefect.yaml"
    output_path.write_text(yaml_content)
    print(f"Created {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Deploy marketing analytics pipeline")
    parser.add_argument("--client", default="client1", help="Client ID")
    parser.add_argument("--all", action="store_true", help="Deploy for all clients")
    parser.add_argument("--sources", nargs="+", help="Sources to sync")
    parser.add_argument("--generate-yaml", action="store_true", help="Generate prefect.yaml")
    parser.add_argument("--api-url", default="http://localhost:4200/api", help="Prefect API URL")
    args = parser.parse_args()

    if args.sources is None:
        sources = ["ga4", "gads", "fbads", "prestashop"]
    else:
        sources = args.sources

    if args.generate_yaml:
        deploy_with_prefect_yaml()
        print("\nTo deploy, run:")
        print("  cd /var/www/meta.expc.cz")
        print("  prefect deploy --prefect-file prefect/prefect.yaml")
        return

    if args.all:
        clients = ["client1", "client2"]
        for client in clients:
            deploy_via_api(client, sources, args.api_url)
    else:
        deploy_via_api(args.client, sources, args.api_url)

    print("\n" + "=" * 60)
    print("DEPLOYMENT OPTIONS")
    print("=" * 60)
    print("\nOption 1: Use prefect.yaml (recommended)")
    print("  python prefect/deployments/marketing_analytics.py --client client1 --generate-yaml")
    print("  prefect deploy --prefect-file prefect/prefect.yaml")
    print("\nOption 2: Schedule via crontab (alternative)")
    print("  cat crontab/crontab_entry.txt | crontab -")
    print("\nOption 3: Run manually")
    print("  python prefect/flows/marketing_pipeline.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
