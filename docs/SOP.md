# Standard Operating Procedures (SOP)

## Marketing Analytics Platform Operations

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-08 | System | Initial SOP |

---

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Pipeline Execution](#pipeline-execution)
3. [Data Quality Monitoring](#data-quality-monitoring)
4. [Incident Response](#incident-response)
5. [Backup Procedures](#backup-procedures)
6. [Deployment Procedures](#deployment-procedures)
7. [Secret Rotation](#secret-rotation)
8. [Escalation Matrix](#escalation-matrix)

---

## Daily Operations

### Morning Health Check

```bash
# 1. Check service health
curl http://localhost:8096/api/health
docker compose ps

# 2. Check container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 3. Verify Prefect flows
docker exec prefect-server prefect flow ls

# 4. Check recent pipeline runs
docker logs prefect-worker --tail 50
```

### Daily ETL Pipeline

| Time | Task | Command |
|------|------|---------|
| 02:00 | GA4 sync | `python scripts/pipeline.py --source ga4 --client client1` |
| 02:30 | Facebook sync | `python scripts/pipeline.py --source fbads --client client1` |
| 03:00 | PrestaShop sync | `python scripts/pipeline.py --source prestashop --client client1` |
| 03:30 | dbt transform | `cd dbt && dbt run` |
| 04:00 | dbt test | `cd dbt && dbt test` |

---

## Pipeline Execution

### Manual Pipeline Run

```bash
# Navigate to project
cd /var/www/meta.expc.cz

# Activate environment
source .venv/bin/activate

# Run full pipeline for client
python scripts/pipeline.py --all --client client1

# Run specific source
python scripts/pipeline.py --source ga4 --client client1

# Dry run to preview
python scripts/pipeline.py --source ga4 --client client1 --dry-run
```

### Monitoring Pipeline Execution

```bash
# View pipeline logs
tail -f logs/pipeline_client1.log

# Check Prefect UI
open http://localhost:4200

# Check container resource usage
docker stats

# Monitor PostgreSQL connections
docker exec metabase-db psql -U metabase -d metabase -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='metabase';"
```

---

## Data Quality Monitoring

### Running Data Quality Tests

```bash
# Run all dbt tests
cd dbt
dbt test

# Run specific model tests
dbt test --select stg_ga4__traffic

# Generate test report
dbt test --store-failures
cat target/run_results.json
```

### Data Quality Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Row count variance | ±5% | ±10% | Investigate source |
| Null percentage | >1% | >5% | Check ETL |
| Revenue negative | 0 | >0 | Immediate alert |
| Freshness | >24h | >48h | Check scheduler |
| Duplicate rows | >0.1% | >1% | Check dedup logic |

### Quality Dashboard Checks

1. Navigate to Metabase → Marketing Performance
2. Verify data freshness indicator
3. Check for null values in key metrics
4. Compare daily counts with baseline

---

## Incident Response

### Service Down

```bash
# Level 1: Single container restart
docker compose restart metabase

# Level 2: Full stack restart
docker compose down && docker compose up -d

# Level 3: Check logs and escalate
docker compose logs --tail=100 metabase
docker inspect --format='{{.State.Health.Status}}' metabase
```

### Pipeline Failure

```bash
# 1. Identify failure point
docker logs prefect-worker --tail 200 | grep ERROR

# 2. Check source API status
curl -I https://analytics.google.com
curl -I https://graph.facebook.com

# 3. Retry failed task
docker exec prefect-worker prefect task-run create \
  --flow marketing-analytics-pipeline \
  --task run_dlt_sync

# 4. Manual data reload if needed
python scripts/pipeline.py --source ga4 --client client1 --full-refresh
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
docker exec metabase-db pg_isready -U metabase

# Check connection pool
docker exec metabase-db psql -U metabase -d metabase -c \
  "SELECT * FROM pg_stat_activity WHERE datname='metabase';"

# Restart database if needed
docker compose restart metabase-db
```

### Escalation Matrix

| Severity | Response Time | Contact | Actions |
|----------|---------------|---------|---------|
| P1 - Complete outage | 15 min | On-call engineer | Restart services, escalate |
| P2 - Partial failure | 1 hour | Team lead | Investigate, fix or workaround |
| P3 - Degraded | 4 hours | Assigned engineer | Schedule maintenance |
| P4 - Minor issue | 24 hours | Any available | Log for next sprint |

---

## Backup Procedures

### Automated Backup (Daily)

```bash
# Backup is run via cron at 03:00
/var/www/metabase/scripts/backup-metabase.sh

# Verify backup
export BORG_PASSPHRASE="$(cat ~/.config/borg/metabase-passphrase)"
borg list ssh://pavel@100.91.164.109/var/backups/borg/metabase
```

### Manual Backup

```bash
# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker exec metabase-db pg_dump -U metabase metabase > \
  backups/metabase_${TIMESTAMP}.sql

# Compress backup
gzip backups/metabase_${TIMESTAMP}.sql

# Upload to remote
borg create \
  ssh://pavel@100.91.164.109/var/backups/borg/metabase::${TIMESTAMP} \
  backups/metabase_${TIMESTAMP}.sql.gz
```

### Restore from Backup

```bash
# List available backups
borg list ssh://pavel@100.91.164.109/var/backups/borg/metabase

# Extract specific backup
borg extract \
  ssh://pavel@100.91.164.109/var/backups/borg/metabase::2026-04-08

# Restore to database
docker exec -i metabase-db psql -U metabase metabase < backups/latest.sql
```

---

## Deployment Procedures

### Application Update

```bash
# 1. Pull latest changes
git pull origin master

# 2. Update dependencies
uv sync

# 3. Update Docker images
docker compose pull

# 4. Restart services
docker compose up -d

# 5. Verify deployment
curl http://localhost:8096/api/health
```

### Metabase Update

```bash
# 1. Backup current database
docker exec metabase-db pg_dump -U metabase metabase > backups/pre-upgrade.sql

# 2. Update image version in docker-compose.yml
# image: metabase/metabase:v0.XX.X

# 3. Pull and restart
docker compose pull metabase
docker compose up -d metabase

# 4. Monitor startup
docker logs -f metabase
```

### dbt Model Update

```bash
# 1. Pull latest dbt changes
git pull

# 2. Update dbt dependencies
cd dbt && dbt deps

# 3. Run modified models
dbt run --select my_new_model+

# 4. Test changes
dbt test --select my_new_model+

# 5. If all tests pass, run full pipeline
dbt run && dbt test
```

---

## Secret Rotation

### When to Rotate

| Secret Type | Rotation Frequency | Triggers |
|------------|---------------------|----------|
| API Keys | Quarterly | Suspicious activity |
| OAuth Tokens | 6 months | Expiry warning |
| Database Password | 6 months | Compliance |
| Borg Passphrase | Annual | Team member departure |

### Rotation Procedure

```bash
# 1. Generate new secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Update vault (Ansible)
ansible-vault edit ansible/group_vars/all/vault.yml

# 3. Or update SOPS
sops .sops/secrets/metabase-client1.yaml

# 4. Deploy new secrets
ansible-playbook ansible/playbooks/deploy.yml --ask-vault-pass

# 5. Verify functionality
python scripts/pipeline.py --source ga4 --client client1 --dry-run
```

---

## Escalation Matrix

### Contact Hierarchy

| Level | Role | Contact Method |
|-------|------|----------------|
| 1 | Automated monitoring | PagerDuty |
| 2 | On-call engineer | Slack #incidents |
| 3 | Team lead | Direct message |
| 4 | Engineering manager | Phone |

### Communication Templates

#### P1 Incident
```
🚨 [P1] Marketing Analytics Platform Down
Time: {timestamp}
Impact: {affected users/revenue}
Status: Investigating
Action: Restarting services, escalate if not resolved in 15 min
```

#### P2 Incident
```
⚠️ [P2] Pipeline Failure Detected
Time: {timestamp}
Source: {ga4/fbads/prestashop}
Error: {brief description}
Status: Investigating
ETA: {resolution estimate}
```

---

## Quick Reference

### Essential Commands

```bash
# Health check
curl http://localhost:8096/api/health

# Restart services
docker compose restart

# View logs
docker compose logs -f

# Run pipeline
python scripts/pipeline.py --all --client client1

# dbt operations
cd dbt && dbt run && dbt test

# Backup
/var/www/metabase/scripts/backup-metabase.sh
```

### Important URLs

| Service | URL |
|---------|-----|
| Metabase | http://localhost:8096 |
| Prefect | http://localhost:4200 |
| Grafana | (if configured) |

### Emergency Contacts

- On-call: Check PagerDuty schedule
- Slack: #analytics-platform
- Documentation: /docs/SOP.md
