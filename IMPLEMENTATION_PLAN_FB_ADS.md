# Implementation Plan: Facebook Ads → Metabase

## Overview

Connect Facebook/Meta Ads data to Metabase for ad performance analysis.

## Integration Options

### Option A: Airbyte (Recommended - Free, Self-Hosted)

#### Step 1: Deploy Airbyte (if not already)

If Airbyte is already running from Google Ads implementation, skip to Step 2.

```bash
docker run -d \
  --name airbyte \
  -p 8000:8000 \
  -p 8080:8080 \
  airbyte/airbyte
```

#### Step 2: Configure Facebook Ads Source

1. Open http://s60:8000
2. Go to Sources → Add new source
3. Search "Facebook Ads"
4. Configure:
   - Name: `facebook-ads`
   - Account ID: Your Facebook Ad Account ID
   - Access Token: (from Facebook Business)
5. Click "Set up source"

#### Step 3: Get Facebook Access Token

1. Go to Facebook Business Settings
2. → Users → Partners (or create new app)
3. Go to https://developers.facebook.com
4. Create app (type: Business)
5. Add "Marketing API" product
6. Get access token from Marketing API Tools

#### Step 4: Create Connection

1. Go to Connections → New connection
2. Select source: Facebook Ads
3. Select destination: PostgreSQL (metabase-db)
4. Select streams:
   - `campaigns`
   - `ad_sets`
   - `ads`
   - `insights`
   - `ad_insights`
5. Set sync frequency: Every 6 hours
6. Click "Create connection"

### Option B: Stitch (Paid - Easier)

1. Sign up at stitchdata.com
2. Configure Facebook Ads source
3. Configure PostgreSQL destination
4. Select streams and frequency
5. Cost: ~$100/month

### Option C: Graph API + Python (Free, Manual)

```python
import requests
import pandas as pd

def get_facebook_ads(access_token, ad_account_id):
    base_url = f"https://graph.facebook.com/v18.0/act_{ad_account_id}/insights"
    
    params = {
        'access_token': access_token,
        'fields': 'campaign_name,ad_name,impressions,clicks,spend,conversions',
        'time_range': '{"since":"2024-01-01","until":"2024-01-31"}',
        'level': 'campaign'
    }
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    return pd.DataFrame(data['data'])

# Store to PostgreSQL
import psycopg2

def store_to_postgres(df):
    conn = psycopg2.connect(
        host='metabase-db',
        database='metabase',
        user='metabase',
        password='password'
    )
    
    df.to_sql('fb_ads_insights', conn, if_exists='replace', index=False)
```

## Build Dashboards in Metabase

### Questions to Create

1. **Campaign Overview**
   - Total spend
   - Reach and impressions
   - Frequency

2. **Performance Metrics**
   - CTR by campaign
   - CPC (cost per click)
   - CPM (cost per 1k impressions)

3. **Conversions**
   - Conversion rate
   - Cost per conversion
   - ROAS (if revenue tracked)

4. **Creative Performance**
   - Top performing ads
   - A/B test results

### Sample SQL Queries

```sql
-- Daily performance by campaign
SELECT 
  date_start,
  campaign_name,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  SUM(spend) AS spend,
  SUM(conversions_value) AS conversion_value
FROM fb_ads_insights
WHERE date_start >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 1, 2
ORDER BY 1 DESC;

-- ROAS calculation
SELECT 
  campaign_name,
  SUM(spend) AS spend,
  SUM(conversions_value) AS conversion_value,
  SUM(conversions_value) / NULLIF(SUM(spend), 0) AS roas
FROM fb_ads_insights
GROUP BY campaign_name
ORDER BY roas DESC;
```

## Cost Comparison

| Method | Monthly Cost | Setup Time |
|--------|--------------|-------------|
| Airbyte (self-hosted) | $0 (server costs) | 2-3 hours |
| Stitch | $100+ | 30 min |
| Graph API + Python | $0 | 2-3 hours |

## Important Notes

- **Data retention**: Facebook only keeps 2-7 years of data (varies)
- **Attribution windows**: Configure in Metabase (7-day click, 1-day view)
- **Rate limits**: Graph API has rate limits (200 calls/hour per user)
- **Access token**: Long-lived tokens last 60 days, need refresh

## Validation

```bash
# Check data in PostgreSQL
docker exec metabase-db psql -U metabase -d metabase -c \
"SELECT COUNT(*) FROM fb_ads_insights;"
```
