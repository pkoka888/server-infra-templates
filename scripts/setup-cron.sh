#!/bin/bash
# Cron setup for Metabase automation
# Usage: ./setup-cron.sh [--remove] [--list]

CRON_MARKER="# === METABASE_AUTOMATION ==="

setup_cron() {
    echo "Installing Metabase cron jobs..."
    
    # Get current crontab, filter out old entries
    local current=""
    if crontab -l 2>/dev/null | grep -q "^[^#]"; then
        current=$(crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | grep -v "metabase/scripts/" | grep -v "metabase.*pipeline.py")
    fi
    
    # New entries
    local new_entries="
$CRON_MARKER
# Pipeline client1: Daily at 2:00 AM
0 2 * * * cd /var/www/metabase && /usr/local/bin/uv run python scripts/pipeline.py --all --client client1 >> /var/www/metabase/logs/pipeline-client1-\$(date +\%Y\%m\%d).log 2>&1
# Backup: Daily at 4:00 AM
0 4 * * * cd /var/www/metabase && /bin/bash /var/www/metabase/scripts/backup-metabase.sh >> /var/www/metabase/logs/backup-\$(date +\%Y\%m\%d).log 2>&1
# Restore test: Weekly Sunday at 5:00 AM
0 5 * * 0 cd /var/www/metabase && /bin/bash /var/www/metabase/scripts/test-restore.sh >> /var/www/metabase/logs/restore-test-\$(date +\%Y\%m\%d).log 2>&1
# Audit s60: Daily at 6:30 AM
0 6 * * * cd /var/www/metabase && /bin/bash /var/www/metabase/scripts/audit.sh s60 security >> /var/www/metabase/logs/audit-s60-\$(date +\%Y\%m\%d).log 2>&1
# LangGraph health: Weekly Sunday at 6:00 AM
0 6 * * 0 cd /var/www/metabase && /bin/bash /var/www/metabase/scripts/langgraph-diagnostics.sh --test >> /var/www/metabase/logs/langgraph-health-\$(date +\%Y\%m\%d).log 2>&1
"
    
    # Install
    echo "$current$new_entries" | crontab -
    
    echo "✅ Cron jobs installed:"
    list_cron
}

remove_cron() {
    local current=$(crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | grep -v "metabase/scripts/")
    echo "$current" | crontab -
    echo "✅ Metabase cron jobs removed"
}

list_cron() {
    echo ""
    crontab -l 2>/dev/null | grep -E "metabase|pipeline|audit|backup|restore|langgraph" || echo "No Metabase cron jobs found"
}

case "${1:-}" in
    --remove) remove_cron ;;
    --list) list_cron ;;
    *) setup_cron ;;
esac