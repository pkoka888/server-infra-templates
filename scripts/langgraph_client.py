"""
LangGraph client for Metabase pipeline integration.
Provides utilities to call LangGraph workflows from pipeline scripts.
"""

import os
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

# LangGraph API configuration
LANGGRAPH_HOST = os.environ.get("LANGGRAPH_HOST", "100.111.141.111")
LANGGRAPH_PORT = os.environ.get("LANGGRAPH_PORT", "8093")
LANGGRAPH_URL = f"http://{LANGGRAPH_HOST}:{LANGGRAPH_PORT}"


class LangGraphClient:
    """Client for LangGraph API integration."""

    def __init__(self, base_url: str = LANGGRAPH_URL):
        self.base_url = base_url
        self.timeout = 30

    def health_check(self) -> bool:
        """Check if LangGraph API is available."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def run_audit(self, target_server: str, audit_type: str = "security") -> dict:
        """Run server audit workflow."""
        try:
            response = requests.post(
                f"{self.base_url}/workflow/audit",
                json={"target_server": target_server, "audit_type": audit_type},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.warning(f"LangGraph audit failed: {e}")
            return {"status": "error", "message": str(e)}

    def validate_dataset(self, dataset: str, checks: list = None) -> dict:
        """Validate dataset before loading."""
        if checks is None:
            checks = ["nulls", "duplicates", "schema"]

        try:
            response = requests.post(
                f"{self.base_url}/workflow/validate",
                json={"dataset": dataset, "checks": checks},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return {"status": "skipped", "reason": "LangGraph unavailable"}

    def log_event(self, client_id: str, event_type: str, data: dict) -> dict:
        """Log pipeline event to LangGraph for audit trail."""
        try:
            response = requests.post(
                f"{self.base_url}/workflow/log",
                json={"event_type": event_type, "client_id": client_id, "data": data},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return {"status": "skipped", "reason": "LangGraph unavailable"}

    def run_etl(self, client_id: str, sources: list) -> dict:
        """Run full ETL workflow via LangGraph."""
        try:
            response = requests.post(
                f"{self.base_url}/workflow/etl",
                json={"client_id": client_id, "sources": sources},
                timeout=self.timeout * 10,  # ETL takes longer
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.warning(f"LangGraph ETL failed: {e}")
            return {"status": "error", "message": str(e)}


def get_langgraph_client() -> Optional[LangGraphClient]:
    """Get LangGraph client if available."""
    client = LangGraphClient()
    if client.health_check():
        return client
    logger.info("LangGraph not available, skipping integration")
    return None


if __name__ == "__main__":
    # Test the client
    client = LangGraphClient()
    print(f"LangGraph available: {client.health_check()}")

    if client.health_check():
        print("Running test audit...")
        result = client.run_audit("s60", "security")
        print(result)
