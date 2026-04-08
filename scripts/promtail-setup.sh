#!/bin/bash
# promtail-setup.sh - Setup Promtail for Loki log scraping

set -e

CONFIG_FILE="/var/www/meta.expc.cz/config/promtail-config.yaml"
CONTAINER_NAME="promtail-loki"

echo "=== Promtail Setup for Loki ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Warning: Not running as root. Docker commands may fail."
fi

# Create positions file
mkdir -p /tmp
touch /tmp/promtail-positions.yaml
chmod 666 /tmp/promtail-positions.yaml

# Stop existing container
echo "Stopping existing Promtail container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Pull latest image
echo "Pulling Grafana Promtail image..."
docker pull grafana/promtail:3.4.0

# Run Promtail
echo "Starting Promtail container..."
docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    -p 9080:9080 \
    -v /var/www/meta.expc.cz/config/promtail-config.yaml:/etc/promtail/promtail.yaml:ro \
    -v /tmp/promtail-positions.yaml:/tmp/promtail-positions.yaml \
    -v /var/log:/var/log:ro \
    -v /etc/localtime:/etc/localtime:ro \
    --network host \
    grafana/promtail:3.4.0 \
    -config.file=/etc/promtail/promtail.yaml

echo "=== Promtail started ==="
echo "Container: $CONTAINER_NAME"
echo "Logs: docker logs -f $CONTAINER_NAME"
echo "Config validation: docker exec $CONTAINER_NAME promtail --dry-run"

# Wait for health check
sleep 5
docker ps | grep $CONTAINER_NAME || echo "Container not running"

echo ""
echo "Verify Loki connection:"
curl -s http://100.91.164.109:3100/ready