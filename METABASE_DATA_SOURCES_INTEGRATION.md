# Metabase Data Sources Integration Manual

## Overview

This manual covers integrating external marketing data sources (Google Analytics, Google Ads, Facebook Ads, SEO tools, PrestaShop) into Metabase for visualization.

**Key finding**: Metabase has no native drivers for marketing APIs. Data must be loaded into PostgreSQL before Metabase can query it.

## Architecture

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────┐
│ Google GA4  │   │ Google Ads  │   │  FB Ads    │   │ PrestaShop│
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └────┬─────┘
       │                 │                 │                │
       ▼                 ▼                 ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    dlt Python Pipeline                      │
│              (MIT/Apache-2.0, verified sources)            │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │ PostgreSQL (Multi- │
                  │ Client datasets)  │
                  └────────┬───────────┘
                           ▼
                  ┌────────────────────┐
                  │ Metabase           │
                  │ (visualization)    │
                  └────────────────────┘
```

---

## Solution: dlt (data load tool)

**License**: Apache-2.0 (MIT-compatible)  
**Stars**: 5.2k on GitHub  
**Setup**: `pip install dlt[postgres]`

### Why dlt?

| Feature | dlt | Airbyte | Singer |
|---------|-----|---------|--------|
| Docker required | No | Yes | No |
| License | Apache-2.0 | Apache-2.0 | AGPL-3.0 |
| Multi-client | Yes | Yes | No |
| Verified sources | 100+ | 600+ | 50+ |
| Maintenance | Active | Very active | Abandoned |

### Available Verified Sources

From `dlt-hub/verified-sources` (Apache-2.0):
- Google Analytics 4 ✓
- Google Ads ✓
- Facebook Ads ✓
- Google Search Console ✓
- HubSpot, Salesforce, Stripe, etc.

---

## Multi-Client Setup

### Directory Structure

```
/var/www/metabase/
├── scripts/
│   ├── pipeline.py          # Main dlt pipeline (multi-client)
│   ├── setup-pipeline.sh    # Quick setup script
│   ├── .env.example          # Template for client config
│   └── .env.client1          # Client 1 credentials
│   └── .env.client2          # Client 2 credentials
└── ...
```

### Variable System

**Per-client variables** (in `.env.client_name`):
```
CLIENT_ID=client1
GA4_PROPERTY_ID=123456789
GA4_CLIENT_ID=xxxxx
GA4_CLIENT_SECRET=xxxxx
GA4_REFRESH_TOKEN=xxxxx
GADS_CUSTOMER_ID=1234567890
GADS_DEVELOPER_TOKEN=xxxxx
FB_AD_ACCOUNT_ID=act_xxxxx
FB_ACCESS_TOKEN=xxxxx
PS_SHOP_URL=https://client-store.com
PS_API_KEY=xxxxx
```

**Shared variables** (in `.env`):
```
POSTGRES_HOST=metabase-db
POSTGRES_PORT=5432
POSTGRES_USER=metabase
POSTGRES_PASSWORD=xxxxx
POSTGRES_DATABASE=metabase
```

### Running for Specific Client

```bash
# Activate virtual environment
source .venv/bin/activate

# Run GA4 for client1
python scripts/pipeline.py --source ga4 --client client1

# Or use uv run (no activation needed)
uv run python scripts/pipeline.py --source ga4 --client client1

# Run all sources for client2
python scripts/pipeline.py --all --client client2

# List available clients
python scripts/pipeline.py --list-clients
```

### Schedule with Cron

```bash
# crontab -e
# Run daily at 2am for all clients
0 2 * * * cd /var/www/metabase && source .venv/bin/activate && python scripts/pipeline.py --all --client client1 >> logs/pipeline_client1.log 2>&1
0 2 * * * cd /var/www/metabase && source .venv/bin/activate && python scripts/pipeline.py --all --client client2 >> logs/pipeline_client2.log 2>&1
```

### Dataset Naming

Each client gets isolated dataset in PostgreSQL:
- `ga4_client1` - Client 1 GA4 data
- `gads_client1` - Client 1 Google Ads
- `fbads_client1` - Client 1 Facebook Ads
- `prestashop_client1` - Client 1 PrestaShop

Metabase connects to PostgreSQL and can see all client datasets.

---

## Quick Start

```bash
# 1. Run setup
./scripts/setup-pipeline.sh client1

# 2. Edit .env.client1 with credentials

# 3. Test single source
python scripts/pipeline.py --source ga4 --client client1

# 4. Run all sources
python scripts/pipeline.py --all --client client1
```

---

## Data Sources by Platform

### Google Analytics 4

| Method | Complexity | Cost | Refresh |
|--------|------------|------|---------|
| BigQuery Export | Medium | Free + BQ costs | Daily (hourly with stream) |
| Stitch | Low | $100+/mo | Hourly |
| Airbyte | High | Free (self-hosted) | Hourly |
| Python script | Medium | API costs | Custom |

### Google Ads

| Method | Complexity | Cost | Refresh |
|--------|------------|------|---------|
| BigQuery Export (with GA4) | Medium | Free + BQ costs | Daily |
| Stitch | Low | $100+/mo | Hourly |
| Airbyte | High | Free | Hourly |
| Google Ads Script | Medium | Free | Custom |

### Facebook/Meta Ads

| Method | Complexity | Cost | Refresh |
|--------|------------|------|---------|
| Stitch | Low | $100+/mo | Hourly |
| Airbyte | High | Free | Hourly |
| Graph API + Python | Medium | Free (rate limited) | Custom |

### SEO Tools

| Tool | Export Method | Integration |
|------|---------------|-------------|
| Google Search Console | BigQuery or API | BigQuery/API |
| Ahrefs | API + Python | Python transform |
| SEMrush | API + Python | Python transform |
| Screaming Frog | CSV export | Manual upload |
| Screaming Frog | API (paid) | Python transform |

---

## Recommended Architecture for This Project

Given the PrestaShop e-commerce context:

### Phase 1: Google Analytics 4
- Enable GA4 → BigQuery export (free)
- Connect BigQuery to Metabase
- Build: traffic, conversion, product performance dashboards

### Phase 2: Google Ads + Facebook Ads
- Use Airbyte (self-hosted, free) on s60
- Connect to PostgreSQL (metabase-db)
- Build: ROAS, ad spend, campaign performance dashboards

### Phase 3: SEO
- Google Search Console → BigQuery
- Ahrefs/SEMrush → Python transform → PostgreSQL
- Build: keyword rankings, organic traffic dashboards

### Phase 4: Unified Dashboard
- Join marketing data with PrestaShop sales data
- Calculate true ROI (ad spend vs revenue)

---

## Implementation Priority

1. **GA4** (highest impact, lowest cost) - BigQuery export
2. **Google Search Console** (free, high value)
3. **Google Ads** (via Airbyte)
4. **Facebook Ads** (via Airbyte)
5. **SEO tools** (Ahrefs, SEMrush - requires paid API access)

---

## Next Steps

See implementation plans in:
- `IMPLEMENTATION_PLAN_GA4.md`
- `IMPLEMENTATION_PLAN_GOOGLE_ADS.md`
- `IMPLEMENTATION_PLAN_FB_ADS.md`
- `IMPLEMENTATION_PLAN_SEO.md`
