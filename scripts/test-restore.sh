#!/bin/bash
# Metabase Restore Test Script
# Verifies backup integrity by performing a test restore
# Usage: ./test-restore.sh [--keep] [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"

# Configuration
REPO="ssh://pavel@100.91.164.109/var/backups/borg/metabase"
TEST_DB_NAME="metabase_restore_test"
LOG_FILE="$LOG_DIR/restore-test-$(date +%Y%m%d).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Arguments
DRY_RUN=false
KEEP_TEST_DB=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --keep) KEEP_TEST_DB=true; shift ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_step() {
    log "==== $1 ===="
}

get_latest_backup() {
    log_step "Finding latest backup"
    
    if [ "$DRY_RUN" = true ]; then
        log "INFO" "DRY RUN - Would find latest backup from $REPO"
        return
    fi
    
    export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase 2>/dev/null || echo '')"
    
    LATEST=$(borg list "$REPO" --last 1 --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('archives'):
    print(data['archives'][0]['name'])
" 2>/dev/null)
    
    if [ -z "$LATEST" ]; then
        log "ERROR" "No backups found in repository"
        exit 1
    fi
    
    log "INFO" "Latest backup: $LATEST"
    echo "$LATEST"
}

extract_backup() {
    local backup_name=$1
    local extract_dir="/tmp/metabase-restore-test"
    
    log_step "Extracting backup"
    
    rm -rf "$extract_dir"
    mkdir -p "$extract_dir"
    
    if [ "$DRY_RUN" = true ]; then
        log "INFO" "DRY RUN - Would extract $backup_name"
        echo "$extract_dir"
        return
    fi
    
    export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase 2>/dev/null || echo '')"
    
    borg extract "$REPO::$backup_name" "$extract_dir" 2>&1 | tee -a "$LOG_FILE" || {
        log "ERROR" "Extraction failed"
        exit 1
    }
    
    # Find the backup file
    BACKUP_FILE=$(find "$extract_dir" -name "*.backup" -o -name "*.dump" 2>/dev/null | head -1)
    
    if [ -z "$BACKUP_FILE" ]; then
        # Try SQL format
        BACKUP_FILE=$(find "$extract_dir" -name "*.sql" 2>/dev/null | head -1)
    fi
    
    if [ -z "$BACKUP_FILE" ]; then
        log "ERROR" "No backup file found in extracted archive"
        exit 1
    fi
    
    log "INFO" "Found backup file: $BACKUP_FILE"
    echo "$BACKUP_FILE"
}

verify_backup_file() {
    local backup_file=$1
    
    log_step "Verifying backup file"
    
    if [ ! -f "$backup_file" ]; then
        log "ERROR" "Backup file not found: $backup_file"
        exit 1
    fi
    
    # Check file size
    SIZE=$(du -h "$backup_file" | cut -f1)
    log "INFO" "Backup file size: $SIZE"
    
    # Check checksum if exists
    if [ -f "$(dirname "$backup_file")/checksum.sha256" ]; then
        if sha256sum -c "$(dirname "$backup_file")/checksum.sha256" > /dev/null 2>&1; then
            log "OK" "Checksum verified"
        else
            log "WARN" "Checksum mismatch - backup may be corrupted"
        fi
    fi
    
    # Check file format
    if file "$backup_file" | grep -q "SQL"; then
        log "INFO" "Format: SQL text"
        # Check table count
        TABLES=$(grep -c "^CREATE TABLE" "$backup_file" 2>/dev/null || echo "0")
        log "INFO" "Tables found: $TABLES"
    elif file "$backup_file" | grep -q "gzip"; then
        log "INFO" "Format: gzip compressed"
    elif file "$backup_file" | grep -q "custom"; then
        log "INFO" "Format: PostgreSQL custom format"
    else
        log "WARN" "Unknown format"
    fi
}

test_restore() {
    local backup_file=$1
    
    log_step "Testing restore to test database"
    
    # Check if test DB exists
    if docker exec metabase-db psql -U metabase -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$TEST_DB_NAME"; then
        log "INFO" "Test database exists, dropping..."
        docker exec metabase-db psql -U metabase -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;" 2>/dev/null || true
    fi
    
    # Create test database
    log "INFO" "Creating test database: $TEST_DB_NAME"
    docker exec metabase-db psql -U metabase -c "CREATE DATABASE $TEST_DB_NAME;" 2>&1 | tee -a "$LOG_FILE" || {
        log "ERROR" "Failed to create test database"
        exit 1
    }
    
    # Try to restore based on file format
    if file "$backup_file" | grep -q "SQL"; then
        log "INFO" "Restoring from SQL format..."
        docker exec -i metabase-db psql -U metabase -d "$TEST_DB_NAME" < "$backup_file" 2>&1 | tee -a "$LOG_FILE" || {
            log "ERROR" "SQL restore failed"
            return 1
        }
    else
        log "INFO" "Restoring from custom format..."
        docker exec -i metabase-db pg_restore -U metabase -d "$TEST_DB_NAME" "$backup_file" 2>&1 | tee -a "$LOG_FILE" || {
            log "ERROR" "Custom format restore failed"
            return 1
        }
    fi
    
    # Verify restore
    log "INFO" "Verifying restored database..."
    
    # Check table count
    TABLE_COUNT=$(docker exec metabase-db psql -U metabase -d "$TEST_DB_NAME" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
    log "INFO" "Tables in test DB: $TABLE_COUNT"
    
    # Check critical tables
    CRITICAL_TABLES=("report_dashboard" "report_card" "core_user" "metabase_database")
    for table in "${CRITICAL_TABLES[@]}"; do
        COUNT=$(docker exec metabase-db psql -U metabase -d "$TEST_DB_NAME" -t -c "SELECT count(*) FROM \"$table\";" 2>/dev/null | tr -d ' ' || echo "0")
        if [ "$COUNT" -gt 0 ]; then
            log "OK" "Table '$table': $COUNT rows"
        else
            log "WARN" "Table '$table': empty or missing"
        fi
    done
    
    log "OK" "Restore test completed successfully"
}

cleanup_test_db() {
    if [ "$KEEP_TEST_DB" = true ]; then
        log "INFO" "Keeping test database for inspection"
        log "INFO" "Connect with: docker exec metabase-db psql -U metabase -d $TEST_DB_NAME"
        return
    fi
    
    log_step "Cleaning up test database"
    docker exec metabase-db psql -U metabase -c "DROP DATABASE IF EXISTS $TEST_DB_NAME;" 2>/dev/null || true
    log "OK" "Test database removed"
}

cleanup_extract() {
    log_step "Cleaning up extracted files"
    rm -rf /tmp/metabase-restore-test
    log "OK" "Extracted files removed"
}

send_notification() {
    local status=$1
    local message=$2
    log "$status" "$message"
}

# Main
main() {
    log "========================================="
    log "Metabase Restore Test Started"
    log "========================================="
    
    trap 'send_notification "FAILURE" "Restore test failed"' ERR
    
    LATEST_BACKUP=$(get_latest_backup)
    BACKUP_FILE=$(extract_backup "$LATEST_BACKUP")
    verify_backup_file "$BACKUP_FILE"
    test_restore "$BACKUP_FILE"
    cleanup_test_db
    cleanup_extract
    
    send_notification "SUCCESS" "Restore test completed: $LATEST_BACKUP"
    log "========================================="
    log "Restore test completed successfully"
    log "========================================="
}

main "$@"