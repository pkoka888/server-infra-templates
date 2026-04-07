---
name: postgres-backup
description: Backup and restore PostgreSQL databases. Use when backing up Metabase data, restoring from backup, or managing database snapshots.
---

# PostgreSQL Backup/Restore Skill

This skill provides guidance for PostgreSQL backup and restore operations.

## Database Connection

- Host: metabase-db (Docker service)
- User: metabase
- Database: metabase
- Port: 5432

## Backup Operations

### Full Database Dump

```bash
# Using docker exec
docker exec metabase-db pg_dump -U metabase -d metabase -F c -b -v -f /tmp/metabase_backup.dump

# Copy to host
docker cp metabase-db:/tmp/metabase_backup.dump ./metabase_backup_$(date +%Y%m%d).dump
```

### Table-Specific Backup

```bash
# Backup specific table
docker exec metabase-db pg_dump -U metabase -d metabase -t report_dashboard -F c -b -v -f /tmp/dashboard.dump
```

### SQL Dump (human-readable)

```bash
# Plain SQL format
docker exec metabase-db pg_dump -U metabase -d metabase -F p -f /tmp/metabase.sql

# Copy to host
docker cp metabase-db:/tmp/metabase.sql ./metabase_backup_$(date +%Y%m%d).sql
```

## Restore Operations

### Full Database Restore

```bash
# From custom format dump
docker exec -i metabase-db psql -U metabase -d metabase < ./metabase_backup.dump

# From plain SQL
docker exec -i metabase-db psql -U metabase -d metabase < ./metabase_backup.sql
```

### Restore to Different Database

```bash
# Create new database first
docker exec metabase-db psql -U metabase -c "CREATE DATABASE metabase_test;"

# Restore
docker exec -i metabase-db pg_restore -U metabase -d metabase_test ./metabase_backup.dump
```

## Scheduled Backups

### Manual Backup Script

```bash
#!/bin/bash
set -euo pipefail

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/metabase"

mkdir -p "$BACKUP_DIR"

docker exec metabase-db pg_dump -U metabase -d metabase -F c -b -v -f "/tmp/metabase_$DATE.dump"

docker cp "metabase-db:/tmp/metabase_$DATE.dump" "$BACKUP_DIR/metabase_$DATE.dump"

docker exec metabase-db rm "/tmp/metabase_$DATE.dump"

echo "Backup complete: $BACKUP_DIR/metabase_$DATE.dump"
```

### Borg Backup Integration

This project uses Borg for backups:

```bash
# Manual backup
/var/www/metabase/scripts/backup-metabase.sh

# List backups
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"
borg list ssh://pavel@100.91.164.109/var/backups/borg/metabase
```

## Verification

### Verify Backup File

```bash
# Check dump file integrity
docker exec metabase-db pg_restore --verify-only -d metabase /tmp/metabase_backup.dump

# List tables in dump
docker exec metabase-db pg_restore -l /tmp/metabase_backup.dump
```

### Test Restore (non-destructive)

```bash
# Create test database
docker exec metabase-db psql -U metabase -c "CREATE DATABASE metabase_test;"

# Restore to test
docker exec -i metabase-db pg_restore -U metabase -d metabase_test ./metabase_backup.dump

# Verify
docker exec metabase-db psql -U metabase -d metabase_test -c "SELECT count(*) FROM report_dashboard;"
```

## Important Tables

| Table | Description |
|-------|-------------|
| report_dashboard | Metabase dashboards |
| report_card | Saved questions/cards |
| core_user | Users |
| setting | Metabase settings |
| collection | Collections/folders |

## Best Practices

1. **Test backups regularly** - Always verify backups can be restored
2. **Automate backups** - Use cron or systemd timers
3. **Store offsite** - Use Borg for remote backups
4. **Version backups** - Keep multiple backup versions
5. **Monitor backups** - Set up alerts for failed backups

## Troubleshooting

### "Connection refused"

```bash
# Check PostgreSQL is running
docker ps | grep metabase-db

# Check port
docker exec metabase-db pg_isready -p 5432
```

### "Database does not exist"

```bash
# List databases
docker exec metabase-db psql -U metabase -l
```

### Permission denied

```bash
# Check user permissions
docker exec metabase-db psql -U metabase -c "\du"
```
