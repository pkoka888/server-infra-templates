# Implementation Plan: Google Analytics 4 → Metabase

## Overview

Connect GA4 to Metabase using BigQuery as intermediate layer.

## Prerequisites

- GA4 property configured
- Google Cloud Platform project with billing enabled
- BigQuery API enabled
- Service account with BigQuery Job User + BigQuery Data Editor roles

## Step 1: Enable GA4 BigQuery Export

1. **Create GCP Project** (if not exists):
   - Go to https://console.cloud.google.com
   - Create new project: `metabase-analytics`
   - Enable billing

2. **Create Service Account**:
   - IAM → Service Accounts → Create
   - Name: `ga4-export`
   - Role: BigQuery Job User, BigQuery Data Editor
   - Create JSON key, download securely

3. **Link GA4 to BigQuery**:
   - Go to GA4 Admin → Property → BigQuery links
   - Click "Create BigQuery link"
   - Select GCP project and dataset
   - Choose:
     - Daily export: ✓ (free)
     - Streaming export: ✗ (costs apply, skip for now)
   - Click Create

## Step 2: Create BigQuery Dataset

```bash
# Via bq CLI
bq mk --location=EU ga4_data

# Or via GCP Console
# BigQuery → + → Dataset → Name: ga4_data, Location: EU
```

## Step 3: Connect BigQuery to Metabase

1. Go to Metabase Admin → Databases → Add database
2. Select "BigQuery"
3. Fill in:
   - Display name: `GA4`
   - Project ID: `metabase-analytics-xxxxx`
   - Dataset ID: `ga4_data`
   - Service account JSON: (paste from step 1)
4. Click "Save"

## Step 4: Create Summary Views

Create views for common dashboard queries:

```sql
-- Daily sessions summary
CREATE OR REPLACE VIEW ga_daily_sessions AS
SELECT 
  _PARTITIONTIME AS date,
  SUM(totals.visits) AS sessions,
  SUM(totals.users) AS users,
  SUM(totals.newVisits) AS new_visits,
  SUM(totals.pageviews) AS pageviews,
  AVG(totals.avgSessionDuration) AS avg_session_duration_sec
FROM `metabase-analytics-xxxxx.ga4_data.events_*`
WHERE _PARTITIONTIME >= '2024-01-01'
GROUP BY 1;

-- Traffic sources
CREATE OR REPLACE VIEW ga_traffic_sources AS
SELECT 
  PARSE_DATE('%Y%m%d', _TABLE_SUFFIX) AS date,
  trafficSource.medium AS medium,
  trafficSource.source AS source,
  trafficSource.campaign AS campaign,
  SUM(totals.visits) AS visits,
  SUM(totals.transactions) AS transactions,
  SUM(totals.totalRevenue) AS revenue
FROM `metabase-analytics-xxxxx.ga4_data.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20240101' AND '20241231'
GROUP BY 1, 2, 3, 4;

-- Top pages
CREATE OR REPLACE VIEW ga_top_pages AS
SELECT 
  pagePath,
  pageTitle,
  COUNT(*) AS pageviews,
  SUM(hits.time) AS total_time
FROM `metabase-analytics-xxxxx.ga4_data.events_*`,
UNNEST(hits) AS hit
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 100;
```

## Step 5: Build Metabase Dashboards

Create questions in Metabase:

1. **Traffic Overview** (from `ga_daily_sessions`)
   - Line chart: Sessions over time
   - Big number: Total sessions this month

2. **Traffic Sources** (from `ga_traffic_sources`)
   - Pie chart: Visits by medium
   - Table: Top campaigns by revenue

3. **Conversions**
   - Goal completions by date
   - Conversion rate trend

4. **E-commerce** (if e-commerce tracking enabled)
   - Revenue by product
   - Purchase funnel

## Cost Estimate

| Item | Free Tier | Additional Cost |
|------|-----------|-----------------|
| GA4 → BigQuery Export | Daily export | - |
| BigQuery Storage | 10GB/month | $0.02/GB |
| BigQuery Queries | 1TB/month | $5/TB |
| Metabase Query | - | - |

**Monthly cost**: ~$0-5/month (likely $0 for small/medium site)

## Timeline

| Task | Time |
|------|------|
| GCP setup | 30 min |
| GA4 export enable | 15 min |
| Metabase BigQuery connection | 15 min |
| Views creation | 30 min |
| Dashboard building | 1-2 hours |

**Total**: ~3 hours

## Validation

```bash
# Test BigQuery data exists
bq query --use_legacy_sql=false \
"SELECT COUNT(*) FROM \`project.ga4_data.events_*\`"
```

## Rollback

1. Disconnect BigQuery in Metabase Admin
2. Disable GA4 export in GA4 Admin
3. Delete BigQuery dataset (optional):
   ```bash
   bq rm -r ga4_data
   ```
