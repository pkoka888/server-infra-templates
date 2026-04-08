"""
Prefect work pool setup script.
Creates docker-pool and configures default job variables.
"""

import os
import subprocess
from pathlib import Path

# Configuration
WORK_POOL_NAME = "docker-pool"
WORK_POOL_TYPE = "docker"  # Use docker work pool for containerized execution
PROJECT_ROOT = Path("/var/www/meta.expc.cz")

# Default job variables for docker-pool
DEFAULT_JOB_VARIABLES = {
    "image": "prefecthq/prefect:3-latest",
    "env": {
        "PREFECT_LOGGING_LEVEL": "INFO",
        "PREFECT_API_URL": os.getenv("PREFECT_API_URL", "http://localhost:4200/api"),
        "DBT_PROFILES_DIR": "/var/www/meta.expc.cz/dbt",
        "PYTHONPATH": "/var/www/meta.expc.cz",
    },
    "volumes": [
        "/var/www/meta.expc.cz:/var/www/meta.expc.cz:ro",
        "/var/www/meta.expc.cz/.env:/var/www/meta.expc.cz/.env:ro",
    ],
    "working_dir": "/var/www/meta.expc.cz",
    "memory": "4g",
    "cpu": "2.0",
    "auto_remove": True,
    "network_mode": "host",
}


def create_work_pool():
    """Create docker-pool work pool if it doesn't exist."""
    # Check if work pool exists
    try:
        result = subprocess.run(
            ["prefect", "work-pool", "ls", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        if WORK_POOL_NAME in result.stdout:
            print(f"Work pool '{WORK_POOL_NAME}' already exists")
            return
    except subprocess.CalledProcessError:
        pass  # Will try to create anyway

    # Create work pool
    try:
        subprocess.run(
            ["prefect", "work-pool", "create", WORK_POOL_NAME, "--type", WORK_POOL_TYPE],
            check=True,
        )
        print(f"Created work pool: {WORK_POOL_NAME} (type: {WORK_POOL_TYPE})")
    except subprocess.CalledProcessError as e:
        print(f"Error creating work pool: {e}")
        raise


def create_docker_pool_config():
    """Create a docker-pool.yaml configuration file for reference."""
    config_path = PROJECT_ROOT / "prefect" / "docker-pool.yaml"

    config_content = f"""\
# Prefect Docker Work Pool Configuration
# Apply with: prefect work-pool create --config docker-pool.yaml

name: {WORK_POOL_NAME}
type: docker

# Base job template
base_job_template:
  job_configuration:
    image: prefecthq/prefect:3-latest
    auto_remove: true
    network_mode: host
    working_dir: /var/www/meta.expc.cz
    memory: 4g
    cpu: 2.0
    volumes:
      - /var/www/meta.expc.cz:/var/www/meta.expc.cz:ro
      - /var/www/meta.expc.cz/.env:/var/www/meta.expc.cz/.env:ro
    env:
      PREFECT_LOGGING_LEVEL: INFO
      DBT_PROFILES_DIR: /var/www/meta.expc.cz/dbt
      PYTHONPATH: /var/www/meta.expc.cz

  variables:
    properties:
      image:
        type: string
        title: Docker Image
        default: prefecthq/prefect:3-latest
      memory:
        type: string
        title: Memory Limit
        default: 4g
      cpu:
        type: string
        title: CPU Limit
        default: "2.0"
      volumes:
        type: array
        title: Volume Mounts
      env:
        type: object
        title: Environment Variables
"""

    config_path.write_text(config_content)
    print(f"Created docker-pool config: {config_path}")


def print_next_steps():
    """Print instructions for next steps."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                   Prefect Setup Complete                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Next steps:                                                     ║
║                                                                  ║
║  1. Start Prefect server:                                        ║
║     prefect server start                                         ║
║                                                                  ║
║  2. In another terminal, start a worker:                         ║
║     prefect worker start --pool docker-pool                      ║
║                                                                  ║
║  3. Deploy the flow (Python API - Prefect 3.x):                  ║
║     python prefect/deployments/marketing_analytics.py --client client1
║                                                                  ║
║  4. Or deploy all clients:                                       ║
║     python prefect/deployments/marketing_analytics.py --all      ║
║                                                                  ║
║  5. Alternative: Use prefect.yaml                               ║
║     prefect deploy --all --prefect-file prefect/prefect.yaml     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


def main():
    """Main setup function."""
    print("Setting up Prefect work pool...")

    # Create work pool
    create_work_pool()

    # Create YAML config for reference
    create_docker_pool_config()

    print_next_steps()


if __name__ == "__main__":
    main()
