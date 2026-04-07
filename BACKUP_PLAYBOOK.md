# Metabase Backup & Restore Playbook

## Overview

This playbook covers backup, restore testing, and LangGraph diagnostics for the Metabase deployment.

## Quick Reference

| Command | Description |
|---------|-------------|
| `./scripts/backup-metabase.sh` | Run daily backup |
| `./scripts/backup-metabase.sh --verify-only` | Verify backup without creating new |
| `./scripts/test-restore.sh` | Test restore (weekly) |
| `./scripts/langgraph-diagnostics.sh --test` | Diagnose LangGraph issues |

---

## 1. Backup Operations

### Daily Backup

```bash
cd /var/www/metabase
./scripts/backup-metabase.sh
```

**What it does:**
1. Checks database health (pg_isready)
2. Dumps PostgreSQL to custom format (.backup)
3. Calculates SHA256 checksum
4. Verifies critical tables exist
5. Archives to Borg (s62)
6. Prunes old backups (30 daily, 12 weekly, 6 monthly)

**Schedule (crontab):**
```bash
# Daily at 4:00 AM
0 4 * * * cd /var/www/metabase && ./scripts/backup-metabase.sh >> logs/backup-$(date +\%Y\%m\%d).log 2>&1
```

### Verify Latest Backup

```bash
./scripts/backup-metabase.sh --verify-only
```

---

## 2. Restore Testing

### Weekly Restore Test

```bash
cd /var/www/metabase
./scripts/test-restore.sh
```

**What it does:**
1. Finds latest backup from Borg
2. Extracts to temp directory
3. Verifies checksum
4. Creates test database (`metabase_restore_test`)
5. Restores backup to test DB
6. Verifies table count and data
7. Cleans up (or keeps with `--keep`)

**Schedule:**
```bash
# Weekly on Sunday at 5:00 AM
0 5 * * 0 cd /var/www/metabase && ./scripts/test-restore.sh >> logs/restore-test-$(date +\%Y\%m\%d).log 2>&1
```

### Manual Restore (Emergency)

```bash
# 1. Find backup
borg list ssh://pavel@100.91.164.109/var/backups/borg/metabase

# 2. Extract specific backup
borg extract ssh://pavel@100.91.164.109/var/backups/borg/metabase::20260406-040000 /tmp/restore

# 3. Restore (CAREFUL - this overwrites!)
docker exec -i metabase-db pg_restore -U metabase -d metabase < /tmp/restore/metabase.backup
```

---

## 3. LangGraph Diagnostics

### Run Diagnostics

```bash
cd /var/www/metabase
./scripts/langgraph-diagnostics.sh --test
```

**Checks:**
- Container status
- Health endpoint
- Audit endpoint (5 attempts)
- Recent error logs

### Fix LangGraph Issues

```bash
# Auto-fix (restart container + retest)
./scripts/langgraph-diagnostics.sh --fix

# Just restart
./scripts/langgraph-diagnostics.sh --restart
```

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| 500 on /workflow/audit | Checkpointer race condition | Restart container |
| Container not responding | OOM or deadlock | `docker restart` |
| Slow responses | PostgresSaver busy | Check DB connections |

---

## 4. Restore Procedures

### Emergency Restore from Backup

**Prerequisites:**
- Metabase container running
- Access to Borg repo (s62)

**Steps:**

```bash
# 1. Stop Metabase to prevent new data
docker compose stop metabase

# 2. Extract backup
cd /var/www/metabase
export BORG_PASSPHRASE=$(cat ~/.config/borg/metabase-passphrase)
borg extract ssh://pavel@100.91.164.109/var/backups/borg/metabase::20260406-040000 /tmp/metabase-restore

# 3. Drop existing database (DANGER!)
docker exec metabase-db psql -U metabase -c "DROP DATABASE metabase;"
docker exec metabase-db psql -U metabase -c "CREATE DATABASE metabase;"

# 4. Restore
docker exec -i metabase-db pg_restore -U metabase -d metabase < /tmp/metabase-restore/metabase.backup

# 5. Start Metabase
docker compose start metabase

# 6. Verify
docker exec metabase curl -sf http://localhost:3000/api/health
```

---

## 5. Verification Checklist

After any restore:

- [ ] `docker exec metabase curl -sf http://localhost:3000/api/health` returns `{"status":"ok"}`
- [ ] Can log into Metabase admin
- [ ] Dashboards are accessible
- [ ] Questions execute correctly
- [ ] Scheduled queries work
- [ ] Embeds still function (if used)

---

## 6. Backup Files Location

| Type | Location |
|------|----------|
| Borg repo | `ssh://pavel@100.91.164.109/var/backups/borg/metabase` |
| Local logs | `/var/www/metabase/logs/backup-YYYYMMDD.log` |
| Temp files | `/tmp/metabase-backup-YYYYMMDD-HHMMSS/` |

---

## 7. Troubleshooting

### Backup Failed

```bash
# Check logs
tail -f logs/backup-$(date +%Y%m%d).log

# Common issues:
# - Borg passphrase wrong: export BORG_PASSPHRASE=$(cat ~/.config/borg/metabase-passphrase)
# - Database locked: wait for active queries or use --force
```

### Restore Failed

```bash
# Check backup exists
borg list ssh://pavel@100.91.164.109/var/backups/borg/metabase

# Verify backup integrity
./scripts/backup-metabase.sh --verify-only

# Check disk space on s62
ssh pavel@100.91.164.109 df -h
```

### LangGraph Issues

```bash
# Full diagnostics
./scripts/langgraph-diagnostics.sh --test

# View container logs
docker logs langgraph_app-langgraph-app-1 --tail 100

# Check database connections
docker exec metabase-db psql -U metabase -c "SELECT * FROM pg_stat_activity WHERE datname='langgraph';"
```

---

## 8. Recovery Time Objectives

| Scenario | Max Recovery Time |
|----------|-------------------|
| Minor corruption | 1 hour |
| Complete database loss | 4 hours |
| Full disaster recovery | 8 hours |

---

## 9. Contact Info

| Role | Contact |
|------|---------|
| Backup Admin | pavel |
| Database Admin | pavel |
| On-call | pavel |