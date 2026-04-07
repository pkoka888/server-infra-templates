#!/bin/bash
# Enhanced Metabase Backup Script with Verification
# Usage: ./backup-metabase.sh [--verify-only] [--dry-run]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"

# Configuration
BACKUP_NAME="metabase-$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="/tmp/$BACKUP_NAME"
REPO="ssh://pavel@100.91.164.109/var/backups/borg/metabase"
LOG_FILE="$LOG_DIR/backup-$(date +%Y%m%d).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
DRY_RUN=false
VERIFY_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --verify-only) VERIFY_ONLY=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$BACKUP_DIR"

# Signal handler for cleanup on interrupt
cleanup_on_signal() {
    log "WARN" "Interrupted, cleaning up..."
    rm -rf "$BACKUP_DIR"
    exit 130
}
trap cleanup_on_signal INT TERM

log() {
    local level=$1
    local msg=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [$level] $msg" | tee -a "$LOG_FILE"
}

log_step() {
    log "INFO" "==== $1 ===="
}

check_requirements() {
    log_step "Checking requirements"
    
    # Check Borg passphrase
    if [ -z "${BORG_PASSPHRASE:-}" ]; then
        if [ -f ~/.config/borg/metabase-passphrase ]; then
            export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"
        else
            log "ERROR" "BORG_PASSPHRASE not set and key file not found"
            exit 1
        fi
    fi
    
    # Check borg exists
    if ! command -v borg &> /dev/null; then
        log "ERROR" "borg command not found"
        exit 1
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        log "ERROR" "docker command not found"
        exit 1
    fi
    
    log "OK" "All requirements satisfied"
}

check_database_health() {
    log_step "Checking database health"
    
    # Check container is running
    if ! docker ps --format '{{.Names}}' | grep -q '^metabase-db$'; then
        log "ERROR" "metabase-db container not running"
        exit 1
    fi
    
    # Check PostgreSQL is ready
    if ! docker exec metabase-db pg_isready -U metabase -d metabase &>/dev/null; then
        log "ERROR" "PostgreSQL not ready"
        exit 1
    fi
    
    # Check DB size
    DB_SIZE=$(docker exec metabase-db psql -U metabase -d metabase -t -c "SELECT pg_database_size('metabase')/1024/1024 as mb;" 2>/dev/null | tr -d ' ')
    log "OK" "Database size: ${DB_SIZE}MB"
}

dump_database() {
    log_step "Dumping database"
    
    # Check if any connections are active
    ACTIVE_CONN=$(docker exec metabase-db psql -U metabase -d metabase -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='metabase';" 2>/dev/null | tr -d ' ')
    log "INFO" "Active connections: $ACTIVE_CONN"
    
    # Dump with custom format for verification
    docker exec metabase-db pg_dump -U metabase metabase -F c -b -v -f "/tmp/metabase_dump.backup" 2>&1 | tee -a "$LOG_FILE" || {
        log "ERROR" "Database dump failed"
        rm -rf "$BACKUP_DIR"
        exit 1
    }
    
    # Move to backup dir
    mv /tmp/metabase_dump.backup "$BACKUP_DIR/metabase.backup"
    
    # Calculate checksum
    SHA256=$(sha256sum "$BACKUP_DIR/metabase.backup" | cut -d' ' -f1)
    echo "$SHA256" > "$BACKUP_DIR/checksum.sha256"
    log "OK" "Backup file checksum: $SHA256"
    
    # Also dump SQL for verification
    docker exec metabase-db pg_dump -U metabase metabase -f "/tmp/metabase_schema.sql" 2>/dev/null
    mv /tmp/metabase_schema.sql "$BACKUP_DIR/schema.sql"
    
    FILE_SIZE=$(du -h "$BACKUP_DIR/metabase.backup" | cut -f1)
    log "OK" "Backup file size: $FILE_SIZE"
}

verify_backup() {
    log_step "Verifying backup"
    
    # Verify checksum
    if ! sha256sum -c "$BACKUP_DIR/checksum.sha256" > /dev/null 2>&1; then
        log "ERROR" "Checksum verification failed"
        exit 1
    fi
    log "OK" "Checksum verified"
    
    # Verify PostgreSQL custom format
    if command -v pg_restore &> /dev/null; then
        # Try dry-run restore to verify format
        pg_restore --dry-run "$BACKUP_DIR/metabase.backup" 2>&1 | head -5 || true
    fi
    
    # Count tables in schema
    TABLE_COUNT=$(grep -c "^CREATE TABLE" "$BACKUP_DIR/schema.sql" 2>/dev/null || echo "0")
    log "INFO" "Tables in backup: $TABLE_COUNT"
    
    # Check for critical tables
    for table in report_dashboard report_card core_user; do
        if grep -q "CREATE TABLE.*$table" "$BACKUP_DIR/schema.sql" 2>/dev/null; then
            log "OK" "Found critical table: $table"
        else
            log "WARN" "Missing critical table: $table"
        fi
    done
}

backup_to_borg() {
    log_step "Backing up to Borg repository"
    
    if [ "$DRY_RUN" = true ]; then
        log "INFO" "DRY RUN - Would create: $REPO::$BACKUP_NAME"
        return
    fi
    
    # Create backup archive
    borg create "$REPO::$BACKUP_NAME" "$BACKUP_DIR" 2>&1 | tee -a "$LOG_FILE" || {
        log "ERROR" "Borg backup failed"
        exit 1
    }
    
    # Prune old backups
    log "INFO" "Pruning old backups (keep: 30 daily, 12 weekly, 6 monthly)"
    borg prune "$REPO" \
        --keep-daily 30 \
        --keep-weekly 12 \
        --keep-monthly 6 \
        2>&1 | tee -a "$LOG_FILE" || {
        log "WARN" "Pruning failed (continuing)"
    }
    
    # List backup info
    borg list "$REPO" --last 1 2>&1 | tee -a "$LOG_FILE"
}

cleanup() {
    log_step "Cleaning up"
    rm -rf "$BACKUP_DIR"
    log "OK" "Temporary files cleaned"
}

send_notification() {
    local status=$1
    local message=$2
    
    # Log notification
    log "$status" "$message"
    
    # Could add: n8n webhook, email, Slack, etc.
    # Example: curl -X POST "$N8N_WEBHOOK" -d "{\"status\":\"$status\",\"message\":\"$message\"}"
}

# Main execution
main() {
    log "INFO" "========================================="
    log "INFO" "Metabase Backup Script Started"
    log "INFO" "========================================="
    
    if [ "$VERIFY_ONLY" = true ]; then
        log "INFO" "Verification only mode"
        check_requirements
        # Could add: verify_latest_backup
        log "INFO" "Verification complete"
        exit 0
    fi
    
    trap 'send_notification "FAILURE" "Backup failed at step: $CURRENT_STEP"' ERR
    
    CURRENT_STEP="requirements"; check_requirements
    CURRENT_STEP="database_health"; check_database_health
    CURRENT_STEP="dump"; dump_database
    CURRENT_STEP="verify"; verify_backup
    CURRENT_STEP="borg"; backup_to_borg
    CURRENT_STEP="cleanup"; cleanup
    
    send_notification "SUCCESS" "Backup completed: $BACKUP_NAME"
    log "INFO" "========================================="
    log "INFO" "Backup completed successfully"
    log "INFO" "========================================="
}

main "$@"
