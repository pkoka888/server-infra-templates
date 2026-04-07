# Metabase User Manual

## Table of Contents

1. [Quick Start](#quick-start)
2. [Data Pipeline](#data-pipeline)
3. [LangGraph Integration](#langgraph-integration)
4. [Backup & Restore](#backup--restore)
5. [Troubleshooting](#troubleshooting)
6. [Reference](#reference)

---

## Quick Start

### Access Metabase

| Service | URL | Auth |
|---------|-----|------|
| Metabase | https://metabase.expc.cz | Admin account |
| API Health | http://127.0.0.1:8096/api/health | - |

### Basic Commands

```bash
# Check Metabase status
docker exec metabase curl -sf http://localhost:3000/api/health

# Check database
docker exec metabase-db psql -U metabase -d metabase -c "SELECT count(*) FROM report_dashboard;"

# Restart Metabase
docker compose restart metabase
```

---

## Data Pipeline

### Setup New Client

```bash
cd /var/www/metabase

# 1. Setup environment
./scripts/setup-pipeline.sh client_name

# 2. Edit credentials
nano scripts/.env.client_name

# 3. Test connection
uv run python scripts/pipeline.py --list-clients --client client_name
```

### Run Pipeline

```bash
# Run specific source
uv run python scripts/pipeline.py --source ga4 --client client1
uv run python scripts/pipeline.py --source gads --client client1
uv run python scripts/pipeline.py --source fbads --client client1
uv run python scripts/pipeline.py --source prestashop --client client1

# Run all sources
uv run python scripts/pipeline.py --all --client client1
```

### Using SOPS (Optional)

```bash
# Unlock vault (from op.expc.cz)
cd /var/www/metabase
source .sops/scripts/unlock.sh

# Import secrets to .env format
./scripts/import-sops.sh client1

# Lock vault when done
source .sops/scripts/lock.sh
```

---

## LangGraph Integration

### Run Server Audit

```bash
# Via CLI script
cd /var/www/metabase
uv run python scripts/langgraph_client.py

# Via direct API
curl -X POST http://100.111.141.111:8093/workflow/audit \
  -H "Content-Type: application/json" \
  -d '{"target_server": "s60", "audit_type": "security"}'
```

### Diagnostics

```bash
# Run diagnostics
./scripts/langgraph-diagnostics.sh --test

# Auto-fix issues
./scripts/langgraph-diagnostics.sh --fix

# Just restart
./scripts/langgraph-diagnostics.sh --restart
```

### Available Workflows

| Workflow | Description | Usage |
|----------|-------------|-------|
| `/workflow/audit` | Security/performance/compliance audit | POST with target_server |
| `/workflow/rollback` | Rollback deployment | POST with backup_id |
| `/health` | Health check | GET |

---

## Backup & Restore

### Run Backup

```bash
cd /var/www/metabase

# Standard backup
./scripts/backup-metabase.sh

# Verify only (no new backup)
./scripts/backup-metabase.sh --verify-only

# Dry run
./scripts/backup-metabase.sh --dry-run
```

### Test Restore

```bash
# Weekly restore test
./scripts/test-restore.sh

# Keep test database for inspection
./scripts/test-restore.sh --keep
```

### Manual Restore (Emergency)

```bash
# 1. Stop Metabase
docker compose stop metabase

# 2. Extract backup
export BORG_PASSPHRASE=$(cat ~/.config/borg/metabase-passphrase)
borg extract ssh://pavel@100.91.164.109/var/backups/borg/metabase::20260406-040000 /tmp/restore

# 3. Restore
docker exec -i metabase-db pg_restore -U metabase -d metabase < /tmp/restore/metabase.backup

# 4. Start Metabase
docker compose start metabase
```

---

## Troubleshooting

### Metabase Issues

| Issue | Solution |
|-------|----------|
| Slow queries | Check PostgreSQL: `docker exec metabase-db psql -U metabase -c "SELECT * FROM pg_stat_activity;"` |
| 504 timeout | Increase Jetty threads: `MB_JETTY_MAX_THREADS=50` |
| Memory issues | Check container: `docker stats metabase` |
| Embeds broken | Check embedding policy: `.agent/constitution/embedding-policy.md` |

### Pipeline Issues

| Issue | Solution |
|-------|----------|
| No data loaded | Check credentials in `.env.client_name` |
| API rate limits | Wait and retry, check API quotas |
| Dataset not found | Run: `docker exec metabase-db psql -U metabase -d metabase -c "\\dn"` |

### LangGraph Issues

| Issue | Solution |
|-------|----------|
| 500 errors | Run: `./scripts/langgraph-diagnostics.sh --fix` |
| Slow responses | Check DB: `docker exec metabase-db psql -U metabase -c "SELECT * FROM pg_stat_activity WHERE datname='langgraph';"` |
| Container stuck | Restart: `docker restart langgraph_app-langgraph-app-1` |

---

## Reference

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/pipeline.py` | Main data pipeline |
| `scripts/backup-metabase.sh` | Database backup |
| `scripts/test-restore.sh` | Restore testing |
| `scripts/langgraph_diagnostics.sh` | LangGraph diagnostics |
| `scripts/langgraph_etl.py` | ETL workflow |
| `scripts/audit.sh` | Run server audit |
| `scripts/rollback.sh` | Rollback deployment |
| `scripts/backup-test.sh` | Quick backup test |

### CLI Commands

```bash
# Run audit on server
./scripts/audit.sh s60 security
./scripts/audit.sh s61 performance
./scripts/audit.sh s62 compliance

# Rollback (requires backup ID)
./scripts/rollback.sh metabase 20260406-040000

# Quick backup test
./scripts/backup-test.sh
./scripts/backup-test.sh --keep  # Keep test DB

# LangGraph diagnostics
./scripts/langgraph-diagnostics.sh --test
./scripts/langgraph-diagnostics.sh --fix
```

### Environment Variables

**Shared (.env):**
```
POSTGRES_HOST=metabase-db
POSTGRES_PORT=5432
POSTGRES_USER=metabase
POSTGRES_PASSWORD=<from docker-compose.env>
POSTGRES_DATABASE=metabase
```

**Per Client (.env.client_name):**
```
# PrestaShop
PS_SHOP_URL=https://mystore.com
PS_API_KEY=<key>

# GA4
GA4_PROPERTY_ID=123456789
GA4_CLIENT_ID=xxx.apps.googleusercontent.com
GA4_CLIENT_SECRET=
GA4_REFRESH_TOKEN=

# Google Ads
GADS_CUSTOMER_ID=1234567890
GADS_DEVELOPER_TOKEN=
GADS_CLIENT_ID=
GADS_CLIENT_SECRET=
GADS_REFRESH_TOKEN=

# Facebook Ads
FB_AD_ACCOUNT_ID=act_123456789
FB_ACCESS_TOKEN=
```

### Scheduled Tasks

| Task | Schedule | Command |
|------|----------|---------|
| Backup | Daily 4:00 | `./scripts/backup-metabase.sh` |
| Restore Test | Weekly Sun 5:00 | `./scripts/test-restore.sh` |
| Pipeline (client1) | Daily 2:00 | `uv run python scripts/pipeline.py --all --client client1` |
| LangGraph Health | Daily 6:00 | `./scripts/langgraph-diagnostics.sh --test` |

**To setup automated tasks:**
```bash
./scripts/setup-cron.sh        # Install cron jobs
./scripts/setup-cron.sh --list # Show current jobs
./scripts/setup-cron.sh --remove # Remove jobs
```

### Ports

| Service | Port | Interface |
|---------|------|-----------|
| Metabase UI | 8096 | 192.168.1.60 |
| Metabase internal | 3000 | localhost |
| PostgreSQL | 5432 | docker network |
| LangGraph | 8093 | Tailscale |

### Key Files

- `AGENTS.md` - Agent guidelines
- `BACKUP_PLAYBOOK.md` - Backup documentation
- `users-tasks.md` - Setup instructions
- `.agent/` - Agent governance structure

### Support

| Issue | Contact |
|-------|---------|
| Backup problems | pavel |
| Pipeline issues | pavel |
| LangGraph issues | pavel |
| Metabase access | pavel |