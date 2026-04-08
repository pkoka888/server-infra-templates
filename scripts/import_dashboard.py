#!/usr/bin/env python3
"""
Metabase Dashboard Import Script

Import dashboard from JSON export to Metabase.
Supports creating new dashboards and updating existing ones.

Usage:
    python scripts/import_dashboard.py --file metabase/marketing_dashboard.json
    python scripts/import_dashboard.py --file metabase/marketing_dashboard.json --update
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import requests


@dataclass
class MetabaseConfig:
    url: str
    api_key: str
    database_id: int

    @classmethod
    def from_env(cls) -> "MetabaseConfig":
        return cls(
            url=os.getenv("METABASE_URL", "http://localhost:8096"),
            api_key=os.getenv("METABASE_API_KEY", ""),
            database_id=int(os.getenv("METABASE_DATABASE_ID", "1")),
        )


class MetabaseClient:
    def __init__(self, config: MetabaseConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "x-api-key": config.api_key,
            }
        )

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.config.url}{path}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def get_dashboard_by_name(self, name: str) -> dict | None:
        try:
            response = self._request("GET", "/api/dashboard")
            dashboards = response.json()
            for dashboard in dashboards:
                if dashboard.get("name") == name:
                    return dashboard
            return None
        except requests.HTTPError:
            return None

    def create_dashboard(self, dashboard_data: dict) -> dict:
        payload = {
            "name": dashboard_data["name"],
            "description": dashboard_data.get("description", ""),
            "creator_id": dashboard_data.get("creator_id", 1),
            "enable_embedding": dashboard_data.get("enable_embedding", True),
        }
        response = self._request("POST", "/api/dashboard", json=payload)
        return response.json()

    def update_dashboard(self, dashboard_id: int, dashboard_data: dict) -> dict:
        payload = {
            "name": dashboard_data["name"],
            "description": dashboard_data.get("description", ""),
            "enable_embedding": dashboard_data.get("enable_embedding", True),
        }
        response = self._request("PUT", f"/api/dashboard/{dashboard_id}", json=payload)
        return response.json()

    def add_card_to_dashboard(self, dashboard_id: int, card_data: dict, row: int, col: int) -> dict:
        card_query = card_data["dataset_query"]
        card_query["database"] = self.config.database_id

        card_payload = {
            "name": card_data.get("name", "Untitled Card"),
            "display": card_data.get("display", "table"),
            "dataset_query": card_query,
            "visualization_settings": card_data.get("visualization_settings", {}),
        }

        response = self._request("POST", "/api/card", json=card_payload)
        card = response.json()

        dashcard_payload = {
            "cardId": card["id"],
            "dashboardId": dashboard_id,
            "row": row,
            "col": col,
            "sizeX": card_data.get("size_x", 4),
            "sizeY": card_data.get("size_y", 3),
            "series": [],
            "parameter_mappings": [],
        }

        response = self._request(
            "POST", f"/api/dashboard/{dashboard_id}/cards", json=dashcard_payload
        )
        return response.json()

    def import_dashboard(self, dashboard_data: dict, update: bool = False) -> dict:
        name = dashboard_data["name"]
        existing = self.get_dashboard_by_name(name)

        if existing and update:
            print(f"Updating existing dashboard: {name} (ID: {existing['id']})")
            dashboard = self.update_dashboard(existing["id"], dashboard_data)
        elif existing:
            print(f"Dashboard already exists: {name} (ID: {existing['id']})")
            return existing
        else:
            print(f"Creating new dashboard: {name}")
            dashboard = self.create_dashboard(dashboard_data)
            print(f"Created dashboard with ID: {dashboard['id']}")

        print(f"Adding {len(dashboard_data.get('cards', []))} cards...")
        for i, card in enumerate(dashboard_data.get("cards", [])):
            row = card.get("row", 0)
            col = card.get("col", 0)
            try:
                self.add_card_to_dashboard(dashboard["id"], card, row, col)
                print(
                    f"  [{i + 1}/{len(dashboard_data['cards'])}] Added: {card.get('name', 'Untitled')}"
                )
            except Exception as e:
                print(
                    f"  [{i + 1}/{len(dashboard_data['cards'])}] Failed: {card.get('name', 'Untitled')} - {e}"
                )

        return dashboard


def main():
    parser = argparse.ArgumentParser(description="Import Metabase dashboard")
    parser.add_argument("--file", type=Path, required=True, help="Dashboard JSON file")
    parser.add_argument("--update", action="store_true", help="Update existing dashboard")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    config = MetabaseConfig.from_env()
    if not config.api_key:
        print("Error: METABASE_API_KEY environment variable not set")
        sys.exit(1)

    with open(args.file) as f:
        dashboard_data = json.load(f)

    if args.dry_run:
        print("Dry run - would create dashboard:")
        print(f"  Name: {dashboard_data['name']}")
        print(f"  Description: {dashboard_data.get('description', '')}")
        print(f"  Cards: {len(dashboard_data.get('cards', []))}")
        for card in dashboard_data.get("cards", []):
            print(f"    - {card.get('name', 'Untitled')} ({card.get('display', 'unknown')})")
        return

    client = MetabaseClient(config)
    result = client.import_dashboard(dashboard_data, update=args.update)

    print(f"\nDashboard URL: {config.url}/dashboard/{result['id']}")


if __name__ == "__main__":
    main()
