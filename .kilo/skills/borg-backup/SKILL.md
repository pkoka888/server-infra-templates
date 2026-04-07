---
name: borg-backup
description: Manage Borg backup repository for Metabase data. Use when backing up, restoring, or checking backup status.
---

# Borg Backup Skill

This skill provides guidance for using Borg backup with the Metabase project.

## Backup Repository

- Server: ssh://pavel@100.91.164.109/var/backups/borg/metabase
- Passphrase: Stored in `~/.config/borg/metabase-passphrase`

## Prerequisites

```bash
# Set passphrase
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"

# Verify connection
borg list ssh://pavel@100.91.164.109/var/backups/borg/metabase
```

## Backup Operations

### Manual Backup

```bash
# Run the backup script
/var/www/metabase/scripts/backup-metabase.sh

# Or manual borg create
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"
borg create \
    ssh://pavel@100.91.164.109/var/backups/borg/metabase::metabase-$(date +%Y%m%d-%H%M%S) \
    /var/www/metabase \
    --exclude '*.log' \
    --exclude 'node_modules/' \
    --exclude '.git/'
```

### List Backups

```bash
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"
borg list ssh://pavel@100.91.164.109/var/backups/borg/metabase
```

### Backup Info

```bash
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"
borg info ssh://pavel@100.91.164.109/var/backups/borg/metabase::metabase-latest
```

## Restore Operations

### List Archive Contents

```bash
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"
borg list ssh://pavel@100.91.164.109/var/backups/borg/metabase::<archive-name>
```

### Extract Specific Archive

```bash
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"

# Extract to temp directory
mkdir -p /tmp/metabase-restore
cd /tmp/metabase-restore
borg extract ssh://pavel@100.91.164.109/var/backups/borg/metabase::<archive-name>
```

### Extract Specific Files

```bash
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"
borg extract \
    ssh://pavel@100.91.164.109/var/backups/borg/metabase::<archive-name> \
    --paths /var/www/metabase/docker-compose.yml \
    --paths /var/www/metabase/.env
```

## Verify Backups

### Check Archive Integrity

```bash
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"
borg check ssh://pavel@100.91.164.109/var/backups/borg/metabase
```

### Extract and Verify

```bash
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"

# Test extract to verify
borg extract --dry-run ssh://pavel@100.91.164.109/var/backups/borg/metabase::<archive-name>
```

## Pruning (Delete Old Backups)

```bash
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"

# Keep daily backups for 7 days
# Keep weekly backups for 4 weeks
# Keep monthly backups for 6 months
borg prune \
    ssh://pavel@100.91.164.109/var/backups/borg/metabase \
    --keep-daily=7 \
    --keep-weekly=4 \
    --keep-monthly=6
```

## Compression

Borg uses default lz4 compression. For better compression:

```bash
borg create --compression zstd ...
```

## Troubleshooting

### "Connection refused"

```bash
# Check SSH connection
ssh pavel@100.91.164.109 "echo connected"

# Check backup directory exists
ssh pavel@100.91.164.109 "ls /var/backups/borg/metabase"
```

### "Passphrase incorrect"

```bash
# Verify passphrase
cat ~/.config/borg/metabase-passphrase
```

### "Repository not found"

```bash
# Check if repo exists
ssh pavel@100.91.164.109 "ls -la /var/backups/borg/"
```

## Best Practices

1. **Test restores** - Regularly test extracting backups
2. **Monitor failures** - Set up alerts for failed backups
3. **Prune old backups** - Use borg prune to manage storage
4. **Encrypt** - All backups are encrypted with passphrase
5. **Offsite** - Backups are on remote server

## Scripts

- `/var/www/metabase/scripts/backup-metabase.sh` - Main backup script
- `/var/www/metabase/scripts/query-metabase.py` - Query utilities
