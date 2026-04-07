#!/bin/bash
# Rollback CLI - Rollback deployments
# Usage: ./rollback.sh <service> <backup_id>
# Example: ./rollback.sh metabase 20260406-040000

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
ok() { echo -e "${GREEN}✅${NC} $1"; }
warn() { echo -e "${YELLOW}⚠️${NC} $1"; }
err() { echo -e "${RED}❌${NC} $1"; }

if [ $# -lt 2 ]; then
    echo "Usage: $0 <service> <backup_id>"
    echo ""
    echo "Arguments:"
    echo "  service    - Service to rollback (metabase, openproject, etc.)"
    echo "  backup_id   - Backup timestamp (e.g., 20260406-040000)"
    echo ""
    echo "Examples:"
    echo "  $0 metabase 20260406-040000"
    echo "  $0 openproject 20260405-030000"
    exit 1
fi

SERVICE=$1
BACKUP_ID=$2

log "Starting rollback for $SERVICE to backup $BACKUP_ID"

# Check if backup exists
REPO="ssh://pavel@100.91.164.109/var/backups/borg/metabase"
export BORG_PASSPHRASE=$(cat ~/.config/borg/metabase-passphrase 2>/dev/null || echo '')

if ! borg list "$REPO" 2>/dev/null | grep -q "$BACKUP_ID"; then
    err "Backup not found: $BACKUP_ID"
    borg list "$REPO" | tail -5
    exit 1
fi
ok "Backup found"

# Warning
warn "This will replace current data with backup!"
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log "Cancelled"
    exit 0
fi

# For Metabase
if [ "$SERVICE" = "metabase" ]; then
    log "Stopping Metabase..."
    docker compose stop metabase
    
    log "Extracting backup..."
    EXTRACT_DIR="/tmp/rollback-$BACKUP_ID"
    rm -rf "$EXTRACT_DIR"
    borg extract "$REPO::$BACKUP_ID" "$EXTRACT_DIR"
    
    log "Restoring database..."
    docker exec -i metabase-db pg_restore -U metabase -d metabase < "$EXTRACT_DIR"/*.backup 2>/dev/null || \
    docker exec -i metabase-db psql -U metabase -d metabase < "$EXTRACT_DIR"/*.sql
    
    log "Starting Metabase..."
    docker compose start metabase
    
    # Verify
    sleep 5
    if docker exec metabase curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
        ok "Rollback complete - Metabase healthy"
    else
        warn "Metabase may need attention - check manually"
    fi
    
    rm -rf "$EXTRACT_DIR"
else
    err "Service not supported: $SERVICE"
    echo "Supported: metabase"
fi

ok "Rollback finished"