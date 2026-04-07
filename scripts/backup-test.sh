#!/bin/bash
# Backup Test CLI - Test backup restore
# Usage: ./backup-test.sh [--keep]
# Example: ./backup-test.sh

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
ok() { echo -e "${GREEN}✅${NC} $1"; }

KEEP=false
if [ "$1" = "--keep" ]; then
    KEEP=true
fi

log "Starting backup restore test..."

cd /var/www/metabase

if [ "$KEEP" = true ]; then
    ./scripts/test-restore.sh --keep
else
    ./scripts/test-restore.sh
fi

ok "Backup test complete"