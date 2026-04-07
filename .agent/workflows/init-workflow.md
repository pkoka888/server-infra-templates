# Init Workflow — Metabase

**Purpose:** Initialize a new Metabase project or client

---

## Quick Start

```bash
cd /var/www/metabase

# 1. Verify Python environment
uv run python --version

# 2. Setup new client
./scripts/setup-pipeline.sh client_name

# 3. Verify pipeline
uv run python scripts/pipeline.py --list-clients --client test
```

---

## First-Time Setup

### 1. Environment

```bash
# Ensure uv is available
which uv  # Should return /home/pavel/.local/bin/uv

# Create venv
uv venv .venv --python python3
uv sync
```

### 2. Docker Services

```bash
# Start Metabase stack
docker compose up -d

# Verify health
docker inspect --format='{{.State.Health.Status}}' metabase
curl -sf http://127.0.0.1:8096/api/health
```

### 3. First Client

```bash
# Copy example config
cp scripts/.env.example scripts/.env.client1

# Edit with real credentials
# (GA4, G-Ads, FB-Ads, PrestaShop API keys)

# Test pipeline
uv run python scripts/pipeline.py --source ga4 --client client1
```

---

## Verification Checklist

- [ ] Python venv created with uv
- [ ] Dependencies installed (`uv sync`)
- [ ] Docker containers running
- [ ] Metabase API accessible
- [ ] Client config created
- [ ] Pipeline runs without errors

---

## Common Issues

| Issue | Fix |
|-------|-----|
| `uv: command not found` | Install: `curl -LsSf https://astral.sh/uv/install.sh | sh` |
| `ImportError: dlt` | Run: `uv sync` |
| `No such client` | Create `.env.client_name` file |
| DB connection failed | Check `.env` has correct PostgreSQL settings |