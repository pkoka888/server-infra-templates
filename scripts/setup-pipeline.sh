#!/bin/bash
# Quick Setup: dlt Multi-Client Pipeline for Metabase
# Uses uv for fast Python package management

set -euo pipefail

CLIENT="${1:-default}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== dlt Pipeline Setup for Client: $CLIENT ==="

# Step 1: Create client-specific env file
if [ ! -f "$SCRIPT_DIR/.env.$CLIENT" ]; then
    echo "Creating .env.$CLIENT from example..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env.$CLIENT"
    echo "Edit .env.$CLIENT with your credentials!"
else
    echo "Using existing .env.$CLIENT"
fi

# Step 2: Install dependencies with uv
echo "Installing Python dependencies with uv..."
cd "$PROJECT_DIR"

# Create .venv if not exists
if [ ! -d ".venv" ]; then
    uv venv .venv --python python3
fi

# Sync dependencies from pyproject.toml
uv sync

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To activate environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To run pipeline for client '$CLIENT':"
echo "  uv run python scripts/pipeline.py --source ga4 --client $CLIENT"
echo "  uv run python scripts/pipeline.py --source gads --client $CLIENT"
echo "  uv run python scripts/pipeline.py --source fbads --client $CLIENT"
echo "  uv run python scripts/pipeline.py --source prestashop --client $CLIENT"
echo "  uv run python scripts/pipeline.py --all --client $CLIENT"
echo ""
echo "To schedule with cron (daily at 2am):"
echo "  0 2 * * * cd $PROJECT_DIR && source .venv/bin/activate && python scripts/pipeline.py --all --client $CLIENT >> logs/pipeline.log 2>&1"
