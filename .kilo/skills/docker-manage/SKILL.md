---
name: docker-manage
description: Manage Docker containers, services, and compose files. Use when restarting services, checking logs, or managing containers.
---

# Docker Management Skill

This skill provides guidance for managing Docker services in this project.

## Project Services

The project uses docker-compose with:
- **metabase** - Metabase analytics platform
- **metabase-db** - PostgreSQL 17 database

## Common Operations

### Service Status

```bash
# Check running services
docker compose ps

# Detailed status
docker compose ps -a
```

### View Logs

```bash
# Metabase logs
docker logs metabase --tail 100
docker logs metabase -f

# Database logs
docker logs metabase-db --tail 50

# Follow all
docker compose logs -f
```

### Restart Services

```bash
# Restart single service
docker compose restart metabase
docker compose restart metabase-db

# Restart all
docker compose restart
```

### Deploy/Update

```bash
# Pull latest images
docker compose pull

# Start services
docker compose up -d

# Full rebuild
docker compose up -d --build
```

### Access Containers

```bash
# Metabase container
docker exec -it metabase sh

# Database container
docker exec -it metabase-db psql -U metabase -d metabase
```

### Health Checks

```bash
# Metabase API health
curl -f http://127.0.0.1:8096/api/health

# PostgreSQL health
docker exec metabase-db pg_isready -U metabase
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose logs

# Remove and recreate
docker compose down
docker compose up -d
```

### Database Connection Issues

```bash
# Check database is running
docker ps | grep metabase-db

# Test connection
docker exec metabase-db pg_isready -U metabase
```

### Clean Up

```bash
# Stop all services
docker compose down

# Remove volumes (WARNING: deletes data)
docker compose down -v

# Remove unused images
docker image prune -f
```

## Project Files

- `docker-compose.yml` - Main compose file
- `.env` - Environment variables (not committed)
