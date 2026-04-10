# Docker Compose Blueprint

Minimal production-ready stack for the analytics platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                          │
│                   (analytics_internal)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Metabase   │  │ metabase-db │  │    dbt       │       │
│  │   :3000      │  │   :5432     │  │  (runner)    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ prefect-     │  │ prefect-     │                         │
│  │  server      │  │  worker      │                         │
│  │   :4200      │  │  (docker)    │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## docker-compose.yml

```yaml
name: meta-analytics
version: "3.8"

networks:
  analytics_internal:
    driver: bridge

volumes:
  metabase_db:
  prefect_data:

services:
  metabase:
    image: metabase/metabase:v0.59.5
    container_name: metabase
    hostname: metabase
    ports:
      - "8096:3000"
    environment:
      JAVA_TIMEZONE: Europe/Prague
      TZ: Europe/Prague
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabase
      MB_DB_PORT: 5432
      MB_DB_HOST: metabase-db
      MB_DB_USER: ${POSTGRES_USER:-metabase}
      MB_DB_PASS: ${POSTGRES_PASSWORD}
      MB_SITE_URL: https://metabase.expc.cz
      MB_EMOJI_IN_LOGS: "false"
    depends_on:
      metabase-db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s
    networks:
      - analytics_internal

  metabase-db:
    image: postgres:17-alpine
    container_name: metabase-db
    hostname: metabase-db
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-metabase}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: metabase
      TZ: Europe/Prague
      PGTZ: Europe/Prague
    volumes:
      - metabase_db:/var/lib/postgresql/data
      - ./crontab:/etc/cron.d/backup-crontab
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-metabase}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - analytics_internal

  prefect-server:
    image: prefecthq/prefect:3-latest
    container_name: prefect-server
    hostname: prefect-server
    command: prefect server start
    environment:
      PREFECT_API_URL: http://prefect-server:4200/api
      PREFECT_UI_URL: http://localhost:4200
    ports:
      - "4200:4200"
      - "4201:4201"
    volumes:
      - prefect_data:/root/.prefect
    networks:
      - analytics_internal

  prefect-worker:
    image: prefecthq/prefect:3-latest
    container_name: prefect-worker
    hostname: prefect-worker
    command: prefect worker start --pool marketing-pool --type docker
    environment:
      PREFECT_API_URL: http://prefect-server:4200/api
      PREFECT_API_KEY: ${PREFECT_API_KEY}
      DOCKER_HOST: unix:///var/run/docker.sock
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - prefect_data:/root/.prefect
      - .:/app
    depends_on:
      prefect-server:
        condition: service_healthy
    networks:
      - analytics_internal

  dbt-runner:
    image: ghcr.io/dbt-labs/dbt-postgres:1.8
    container_name: dbt-runner
    hostname: dbt-runner
    command: ["sleep", "infinity"]
    environment:
      DBT_PROFILES_DIR: /app/dbt
      DBT_TARGET: prod
      PREFECT_API_URL: http://prefect-server:4200/api
    volumes:
      - .:/app
      - dbt_packages:/root/.dbt
    working_dir: /app/dbt
    networks:
      - analytics_internal
    profiles:
      - source: ../docker.sock
        target: /var/run/docker.sock

volumes:
  metabase_db:
  prefect_data:
  dbt_packages:
```

## Health Check Priority

| Service | Health Check | Timeout | Retries |
|---------|-------------|---------|---------|
| metabase-db | `pg_isready` | 5s | 5 |
| metabase | `curl /api/health` | 10s | 5 |
| prefect-server | TCP port 4200 | 5s | 3 |
| prefect-worker | Worker poll | N/A | N/A |

## Deployment Commands

```bash
# Deploy stack
docker compose up -d

# Verify health
docker compose ps

# View logs
docker compose logs -f metabase

# Restart with pull
docker compose pull && docker compose up -d
```

## Secrets Management

Store in `.env` (never commit):

```
POSTGRES_PASSWORD=<strong-password>
PREFECT_API_KEY=<generated-key>
METABASE_SESSION_SECRET=<generated-secret>
```

Rotate via Ansible playbook: `ansible/playbooks/rotate-secrets.yml`
