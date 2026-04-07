# Implementation Plan: Google Ads → Metabase

## Overview

Connect Google Ads data to Metabase for campaign performance analysis.

## Integration Options

### Option A: Airbyte (Recommended - Free, Self-Hosted)

#### Step 1: Deploy Airbyte on s60

```bash
# Create docker network
docker network create airbyte-network

# Run Airbyte
docker run -d \
  --name airbyte \
  --network airbyte-network \
  -p 8000:8000 \
  -p 8080:8080 \
  airbyte/airbyte
```

#### Step 2: Configure Google Ads Source

1. Open http://s60:8000
2. Go to Sources → Add new source
3. Search "Google Ads"
4. Configure:
   - Name: `google-ads`
   - Developer Token (from Google Ads API Center)
   - OAuth:
     - Client ID
     - Client Secret
     - Refresh Token
5. Click "Set up source"

#### Step 3: Configure PostgreSQL Destination

1. Go to Destinations → Add new destination
2. Select "PostgreSQL"
3. Configure:
   - Host: `metabase-db`
   - Port: `5432`
   - Database: `metabase`
   - User: `metabase`
   - Password: (from .env)
4. Click "Set up destination"

#### Step 4: Create Connection

1. Go to Connections → New connection
2. Select source: Google Ads
3. Select destination: PostgreSQL
4. Select streams:
   - `accounts`
   - `campaigns`
   - `ad_groups`
   - `ads`
   - `keyword_stats`
   - `search_terms`
5. Set sync frequency: Every 6 hours
6. Click "Create connection"

### Option B: Stitch (Paid - Easier)

1. Sign up at stitchdata.com
2. Configure Google Ads source
3. Configure PostgreSQL destination
4. Select streams and frequency
5. Cost: ~$100/month

### Option C: Google Ads Script + PostgreSQL (Free, Manual)

For simple exports without ETL tool:

```javascript
// Google Ads Script (run in Google Ads UI)
function main() {
  var report = AdsApp.report(
    'SELECT campaign_name, date, impressions, clicks, cost, conversions ' +
    'FROM CAMPAIGN_PERFORMANCE_REPORT ' +
    'DURING LAST_30_DAYS'
  );
  
  var rows = report.rows();
  var data = [];
  
  while (rows.hasNext()) {
    var row = rows.next();
    data.push([
      row['campaign_name'],
      row['date'],
      row['impressions'],
      row['clicks'],
      row['cost'],
      row['conversions']
    ]);
  }
  
  // Post to webhook or PostgreSQL
  // (requires additional setup)
}
```

## Build Dashboards in Metabase

### Questions to Create

1. **Campaign Performance**
   - Total spend by campaign
   - ROAS: revenue / cost
   - CTR by campaign

2. **Ad Group Performance**
   - Best performing ad groups
   - Quality score trends

3. **Keyword Analysis**
   - Top keywords by clicks
   - Cost per click trends

4. **Conversion Tracking**
   - Conversions by campaign
   - Cost per conversion

### Sample SQL Queries

```sql
-- Daily spend by campaign
SELECT 
  campaign_name,
  SUM(cost) AS total_spend,
  SUM(clicks) AS total_clicks,
  SUM(impressions) AS total_impressions,
  SUM(conversions) AS total_conversions
FROM google_ads.campaigns
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY campaign_name
ORDER BY total_spend DESC;

-- ROAS calculation
SELECT 
  campaign_name,
  SUM(conversions) AS conversions,
  SUM(cost) AS cost,
  SUM(conversions) / NULLIF(SUM(cost), 0) AS roas
FROM google_ads.campaigns
GROUP BY campaign_name;
```

## Cost Comparison

| Method | Monthly Cost | Setup Time |
|--------|--------------|-------------|
| Airbyte (self-hosted) | $0 (server costs) | 2-3 hours |
| Stitch | $100+ | 30 min |
| Google Ads Script | $0 | 1-2 hours |

## Validation

```bash
# Check data in PostgreSQL
docker exec metabase-db psql -U metabase -d metabase -c \
"SELECT COUNT(*) FROM google_ads_campaigns;"
```

## Troubleshooting

- **OAuth token expiry**: Refresh tokens expire, need re-authentication
- **API limits**: Google Ads has query limits (10k rows/day for scripts)
- **MCC access**: If managing multiple accounts, need sub-account access
