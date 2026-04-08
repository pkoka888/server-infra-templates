"""
Prefect blocks configuration for storing credentials and settings.
Uses Prefect 3.x block system for secure credential management.
"""

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("/var/www/meta.expc.cz")


def create_postgres_credentials_block():
    """Create PostgreSQL credentials block for dbt."""
    # Read from .env file
    env_file = PROJECT_ROOT / ".env"
    db_url = None

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("PIPELINE_DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip()
                    break

    if db_url:
        # Store as secret block using CLI
        subprocess.run(
            ["prefect", "secret", "create", "postgres-metabase-db", "--value", db_url],
            check=False,  # May already exist
        )
        print("Created secret block: postgres-metabase-db")
    else:
        print("Warning: PIPELINE_DATABASE_URL not found in .env")


def create_client_config_block(client_id: str):
    """Create configuration block for a client."""
    env_file = PROJECT_ROOT / f".env.{client_id}"
    if not env_file.exists():
        print(f"Warning: No .env.{client_id} file found")
        return

    # Parse env file
    config = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

    # Store as JSON block using CLI
    config_json = json.dumps(config)
    subprocess.run(
        [
            "prefect",
            "block",
            "create",
            "json",
            f"client-config-{client_id}",
            "--value",
            config_json,
        ],
        check=False,
    )
    print(f"Created JSON block: client-config-{client_id}")


def setup_all_blocks():
    """Set up all required Prefect blocks."""
    print("Setting up Prefect blocks...")

    # PostgreSQL credentials
    create_postgres_credentials_block()

    # Client configurations
    for client_id in ["client1", "client2"]:
        create_client_config_block(client_id)

    print("Blocks setup complete")


if __name__ == "__main__":
    setup_all_blocks()
