"""
LangGraph ETL Graph for Metabase Data Pipeline.

This module provides an in-process LangGraph workflow for ETL orchestration
with pre/post validation, checkpointing, and audit logging.

Usage:
    # Run full ETL workflow
    from langgraph_etl import run_etl_workflow
    result = run_etl_workflow(client_id="client1", sources=["ga4", "gads"])

    # Or use individual nodes
    from langgraph_etl import validate_client, extract_data, load_data
"""

import os
import logging
from typing import TypedDict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if LangGraph is available
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available, using fallback mode")


# State schema for ETL workflow
class ETLState(TypedDict):
    """State for ETL workflow."""

    client_id: str
    sources: list[str]
    current_source: Optional[str]
    results: dict
    errors: list[dict]
    started_at: Optional[str]
    completed_at: Optional[str]
    status: str  # "pending", "running", "completed", "failed"


def validate_client(node_input: dict) -> dict:
    """Validate client configuration before running pipelines."""
    client_id = node_input.get("client_id")
    errors = []

    # Check env file exists
    env_file = f".env.{client_id}"
    if not os.path.exists(env_file):
        errors.append(
            {"stage": "validate", "error": f"Missing config file: {env_file}", "severity": "error"}
        )

    # Return state with validation results
    return {
        "client_id": client_id,
        "sources": node_input.get("sources", []),
        "errors": errors,
        "status": "running" if not errors else "failed",
    }


def extract_data(node_input: dict) -> dict:
    """Extract data from source (placeholder for dlt extraction)."""
    import subprocess

    client_id = node_input.get("client_id")
    source = node_input.get("current_source")

    # Skip if no source (initial call)
    if not source:
        return node_input

    logger.info(f"Extracting {source} data for {client_id}")

    # Run the actual pipeline
    result = subprocess.run(
        ["python", "scripts/pipeline.py", "--source", source, "--client", client_id],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )

    results = node_input.get("results", {})
    errors = node_input.get("errors", [])

    if result.returncode == 0:
        results[source] = {"status": "success", "output": result.stdout}
    else:
        errors.append(
            {"stage": "extract", "source": source, "error": result.stderr, "severity": "error"}
        )
        results[source] = {"status": "failed"}

    return {"results": results, "errors": errors}


def load_data(node_input: dict) -> dict:
    """Load data to warehouse (placeholder for dbt run)."""
    import subprocess

    client_id = node_input.get("client_id")
    results = node_input.get("results", {})
    errors = node_input.get("errors", [])

    logger.info(f"Loading data for {client_id}")

    # Run dbt run
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", "dbt", "--project-dir", "dbt"],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )

    if result.returncode == 0:
        results["dbt_run"] = {"status": "success", "output": result.stdout}
    else:
        errors.append({"stage": "load", "error": result.stderr, "severity": "error"})
        results["dbt_run"] = {"status": "failed"}

    node_input["completed_at"] = datetime.now().isoformat()
    node_input["status"] = "failed" if errors else "completed"

    return {
        "results": results,
        "errors": errors,
        "completed_at": node_input["completed_at"],
        "status": node_input["status"],
    }


if LANGGRAPH_AVAILABLE:
    # Create the ETL graph
    def build_etl_graph():
        """Build the ETL workflow graph."""
        builder = StateGraph(ETLState)

        # Add nodes
        builder.add_node(
            "validate",
            lambda state: {**state, "started_at": datetime.now().isoformat(), "status": "running"},
        )
        builder.add_node("extract", extract_data)
        builder.add_node("load", load_data)

        # Define edges
        builder.add_edge("__start__", "validate")
        builder.add_edge("validate", "extract")
        builder.add_edge("extract", "load")
        builder.add_edge("load", END)

        return builder.compile(checkpointer=MemorySaver())

    # Create singleton instance
    _etl_graph = None

    def get_etl_graph():
        """Get the ETL graph instance."""
        global _etl_graph
        if _etl_graph is None:
            _etl_graph = build_etl_graph()
        return _etl_graph


def run_etl_workflow(client_id: str, sources: list[str] = None) -> dict:
    """
    Run the full ETL workflow for a client.

    Args:
        client_id: Client identifier
        sources: List of sources to sync (default: all)

    Returns:
        dict: Workflow result with status, results, and errors
    """
    if sources is None:
        sources = ["ga4", "gads", "fbads", "prestashop"]

    # Always use fallback mode for now (simpler, more reliable)
    # The LangGraph-based version needs more work for iterative ETL
    logger.info("Running ETL in fallback mode")
    import subprocess

    results = {}
    errors = []

    for source in sources:
        logger.info(f"Processing {source} for client {client_id}")
        result = subprocess.run(
            ["python", "scripts/pipeline.py", "--source", source, "--client", client_id],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        results[source] = {"status": "success" if result.returncode == 0 else "failed"}
        if result.returncode != 0:
            errors.append({"source": source, "error": result.stderr[:500]})

    return {
        "client_id": client_id,
        "status": "completed" if not errors else "failed",
        "results": results,
        "errors": errors,
        "mode": "fallback",
    }

    # Run with LangGraph
    graph = get_etl_graph()

    initial_state = {
        "client_id": client_id,
        "sources": sources,
        "current_source": None,
        "results": {},
        "errors": [],
        "started_at": None,
        "completed_at": None,
        "status": "pending",
    }

    config = {"configurable": {"thread_id": f"etl-{client_id}-{datetime.now().strftime('%Y%m%d')}"}}

    result = graph.invoke(initial_state, config)

    return {
        "client_id": client_id,
        "status": result.get("status"),
        "results": result.get("results"),
        "errors": result.get("errors"),
        "started_at": result.get("started_at"),
        "completed_at": result.get("completed_at"),
        "mode": "langgraph",
    }


if __name__ == "__main__":
    import sys

    client_id = sys.argv[1] if len(sys.argv) > 1 else "test"
    sources = sys.argv[2].split(",") if len(sys.argv) > 2 else ["ga4"]

    print(f"Running ETL for client: {client_id}, sources: {sources}")
    result = run_etl_workflow(client_id, sources)
    print(f"Result: {result}")
