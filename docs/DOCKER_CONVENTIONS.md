# Docker Naming Conventions & Best Practices

## Container Naming

### Golden Rules

1. **Use kebab-case**: `metabase-db`, `prefect-server`
2. **Include service type**: `{service}-{component}`
3. **Be descriptive**: `metabase-db` not `db`
4. **Be consistent**: Same pattern across all services

### Naming Patterns

| Pattern | Example | Use Case |
|---------|--------|----------|
| `{service}-{component}` | `metabase-db` | Primary databases |
| `{service}-{role}` | `metabase-app` | Primary application |
| `{service}-{feature}` | `analytics-dbt` | Feature-specific |
| `{service}-{worker}` | `prefect-worker` | Worker processes |

### Container Names by Service

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           METABASE STACK                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  metabase              # Main application                                    │
│  metabase-db          # PostgreSQL database                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         PREFECT STACK                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  prefect-server       # API server                                          │
│  prefect-worker       # Worker process                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         ANALYTICS STACK                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  analytics-dbt        # dbt transformation (job-based)                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Image Naming

### Image Registry Patterns

```
# Format
{registry}/{namespace}/{image}:{tag}

# Examples
docker.io/library/postgres:17-alpine
docker.io/metabase/metabase:v0.59.5
docker.io/prefecthq/prefect:3-latest
ghcr.io/dbt-labs/dbt-postgres:1.9.latest
```

### Image Tagging Strategy

| Tag | Description | Example |
|-----|-------------|---------|
| `latest` | Most recent stable | `metabase:latest` |
| `v{version}` | Specific version | `metabase:v0.59.5` |
| `{major}` | Major version only | `postgres:17` |
| `{sha}` | Git commit hash | `app:a1b2c3d` |

### Recommended Tags for This Project

```yaml
# docker-compose.yml

services:
  metabase:
    image: metabase/metabase:v0.59.5  # Pin exact version

  metabase-db:
    image: postgres:17-alpine  # Pin major version

  prefect-server:
    image: prefecthq/prefect:3-latest  # Pin major version

  prefect-worker:
    image: prefecthq/prefect:3-latest

  dbt:
    image: ghcr.io/dbt-labs/dbt-postgres:1.9.latest
```

## Volume Naming

### Volume Naming Convention

```
# Format
{project}_{service}_{purpose}

# Examples
metabase_metabase-db-data       # Metabase database data
metabase_prefect-data           # Prefect state data
```

### Volume Map

| Volume | Service | Purpose |
|--------|---------|---------|
| `metabase-db-data` | metabase-db | PostgreSQL data directory |
| `prefect-data` | prefect-server | Prefect server state |

### Volume Best Practices

```yaml
volumes:
  # Descriptive names with project prefix
  metabase-db-data:           # Good
  data:                        # Bad - too generic

  # Use driver-specific options
  metabase-db-data:
    driver: local

  # For production with backup
  postgres-backups:
    driver: local
```

## Network Naming

### Network Naming Convention

```
# Format
{project}_{network}

# Examples
metabase_metabase-net          # Internal network
metabase_public-net            # External access
```

### Network Map

| Network | Driver | Purpose |
|---------|--------|---------|
| `metabase-net` | bridge | Internal service communication |

### Network Configuration

```yaml
networks:
  metabase-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

## Environment Variables

### Naming Convention

```
# Format
{SERVICE}_{VARIABLE_NAME}

# Examples
MB_DB_HOST=metabase-db
MB_DB_PASS=secret
PREFECT_API_URL=http://prefect-server:4200/api
```

### Variable Prefix Map

| Service | Prefix | Example |
|---------|--------|---------|
| Metabase | `MB_` | `MB_DB_HOST`, `MB_DB_PASS` |
| PostgreSQL | `POSTGRES_` | `POSTGRES_USER` |
| Prefect | `PREFECT_` | `PREFECT_API_URL` |
| dbt | `DBT_` | `DBT_PROFILES_DIR` |

### Variable Categories

#### Database (Required)
```bash
POSTGRES_USER=metabase
POSTGRES_PASSWORD=<vault>
POSTGRES_DB=metabase
```

#### Metabase (Required)
```bash
MB_DB_TYPE=postgres
MB_DB_HOST=metabase-db
MB_DB_PORT=5432
MB_DB_USER=metabase
MB_DB_PASS=<vault>
MB_DB_DBNAME=metabase
```

#### Google Analytics (Required for ETL)
```bash
GA4_PROPERTY_ID=123456789
GA4_CLIENT_ID=<vault>
GA4_CLIENT_SECRET=<vault>
GA4_REFRESH_TOKEN=<vault>
```

#### Facebook Ads (Required for ETL)
```bash
FB_AD_ACCOUNT_ID=act_123456
FB_ACCESS_TOKEN=<vault>
```

#### PrestaShop (Required for ETL)
```bash
PS_SHOP_URL=https://shop.example.com
PS_API_KEY=<vault>
```

#### Prefect (Optional)
```bash
PREFECT_API_URL=http://prefect-server:4200/api
PREFECT_API_KEY=<vault>  # For cloud
```

## Resource Limits

### Memory & CPU Naming

```
# Format
{limit|reservation}_{resource}

# Examples
memory: 2G
cpus: "2.0"
```

### Resource Limit Map

| Service | Memory | CPU | Notes |
|---------|--------|-----|-------|
| metabase | 3G | 2.0 | Java heap 2G |
| metabase-db | 2G | 1.0 | PostgreSQL |
| prefect-server | 1G | 1.0 | API server |
| prefect-worker | 2G | 2.0 | Work execution |
| dbt | 2G | 1.0 | Job-based |

### Resource Configuration

```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: "1.0"
    reservations:
      memory: 1G
      cpus: "0.5"
```

## Health Check Naming

### Health Check Convention

```
# Format
test: ["CMD", "{command}"]
interval: {duration}
timeout: {duration}
retries: {count}
```

### Health Check Map

| Service | Test Command | Interval | Timeout | Retries |
|---------|-------------|----------|---------|---------|
| metabase | `curl -f http://localhost:3000/api/health` | 30s | 10s | 5 |
| metabase-db | `pg_isready -U ${MB_DB_USER}` | 10s | 5s | 5 |
| prefect-server | `prefect server status` | 30s | 10s | 5 |
| prefect-worker | N/A | - | - | - |
| dbt | N/A | - | - | - |

## Logging Naming

### Log Driver Configuration

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
    labels: "{{.Name}}"
    env: "{{.ImageName}}"
```

### Log Options Map

| Option | Value | Description |
|--------|-------|-------------|
| `max-size` | `10m` | Max log file size |
| `max-file` | `3` | Number of rotated files |
| `labels` | `{{.Name}}` | Add container name label |
| `env` | `{{.ImageName}}` | Add image name label |

## Service Dependencies

### Depends-On Convention

```yaml
depends_on:
  {service}:
    condition: service_healthy  # Wait for health check
```

### Dependency Map

```
metabase
  └── depends_on: metabase-db (healthy)

prefect-server
  └── depends_on: [optional] metabase-db (healthy)

prefect-worker
  └── depends_on: prefect-server (healthy)

dbt
  └── depends_on: metabase-db (healthy)
```

## Port Mapping

### Port Convention

```
# Internal ports are well-known
# External ports use localhost binding

{PROTOCOL}://127.0.0.1:{external}:{internal}
```

### Port Map

| Service | Internal | External | Protocol | Purpose |
|---------|----------|----------|----------|---------|
| metabase | 3000 | 8096 | HTTP | Web UI |
| prefect-server | 4200 | 4200 | HTTP | API & UI |
| metabase-db | 5432 | - | TCP | Internal only |

## Docker Compose File Structure

```yaml
# docker-compose.yml

version: "3.8"  # Deprecated but kept for compatibility

services:
  # === Core Services ===
  {service-name}:
    image: {registry}/{image}:{tag}
    container_name: {project}-{service}  # kebab-case
    restart: unless-stopped
    ports:
      - "127.0.0.1:{port}:{internal}"
    environment:
      - {SERVICE}_{VAR}={value}
    volumes:
      - {volume-name}:/path
    healthcheck:
      test: ["CMD", "{command}"]
      interval: 30s
      timeout: 10s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - metabase-net
    depends_on:
      {dependency}:
        condition: service_healthy

volumes:
  {volume-name}:

networks:
  {network-name}:
    driver: bridge
```

## Quick Reference

```bash
# Generate container name
echo "{project}-{service}"  # e.g., metabase-metabase-db

# List volumes with naming
docker volume ls --filter "name=metabase"

# Network inspection
docker network inspect metabase_metabase-net

# Resource usage
docker stats --no-stream $(docker ps --filter "name=metabase" --format "{{.Names}}")
```
