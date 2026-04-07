#!/bin/bash

# Script to monitor Docker resource usage on the host (s60)
# Usage: monitor-s60-docker-stats.sh
# Logs output to standard output with a timestamp header.

set -euo pipefail

echo "--- $(date) - Docker Stats Monitoring ---"
echo "Displaying CPU and Memory usage for all running containers:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo "--- End of Stats ---"