# Implementation Plan: SEO Data → Metabase

## Overview

Integrate SEO data from various tools into Metabase for organic search performance tracking.

## Supported Data Sources

| Source | API Available | Best Method |
|--------|---------------|--------------|
| Google Search Console | ✓ | BigQuery/API |
| Ahrefs | ✓ (paid) | Python |
| SEMrush | ✓ (paid) | Python |
| Screaming Frog | ✓ (paid) | CSV/API |
| Moz | ✓ (paid) | Python |
| Google PageSpeed | ✓ | Python |
| Screaming Frog (free) | ✗ | Manual export |

---

## Google Search Console (GSC)

### Option 1: BigQuery Export (Recommended)

1. **Enable GSC → BigQuery**:
   - Search Console → Settings → BigQuery exports
   - Select GCP project and dataset
   - Enable daily export

2. **Connect BigQuery to Metabase**:
   - Already done for GA4 implementation
   - Just add new views

3. **Create Views**:
```sql
-- Search impressions by query
CREATE OR REPLACE VIEW gsc_search_queries AS
SELECT 
  query,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  AVG(position) AS avg_position,
  SUM(impressions * ctr) AS estimated_impressions
FROM `project.ga4_data.searchconsole_*`
GROUP BY query;

-- Pages performance
CREATE OR REPLACE VIEW gsc_pages AS
SELECT 
  page,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  AVG(position) AS avg_position
FROM `project.ga4_data.searchconsole_*`
GROUP BY page
ORDER BY clicks DESC;
```

### Option 2: API + Python

```python
from google.search.console import SearchConsole
import pandas as pd

def get_gsc_data():
    client = SearchConsole.from_service_account_json('credentials.json')
    
    response = client.search(
        siteUrl='https://example.com',
        startDate='2024-01-01',
        endDate='2024-12-31',
        dimensions=['query', 'page']
    )
    
    return pd.DataFrame(response['rows'])
```

---

## Ahrefs

### Prerequisites
- Ahrefs account with API access (paid plans)
- API key from https://ahrefs.com/api

### Python Integration

```python
import requests
import pandas as pd

AHREFS_API_KEY = "your-api-key"

def get_ahrefs_organic_keywords(domain):
    url = "https://api.ahrefs.com/v3/ahrefs_site_explorer"
    
    payload = {
        "target": domain,
        "output": "organic_keywords",
        "limit": 1000
    }
    
    headers = {
        "Authorization": f"Basic {AHREFS_API_KEY}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    
    return pd.DataFrame(data['organic_keywords'])

def get_ahrefs_backlinks(domain):
    url = "https://api.ahrefs.com/v3/ahrefs_site_explorer"
    
    payload = {
        "target": domain,
        "output": "backlinks",
        "limit": 1000
    }
    
    headers = {
        "Authorization": f"Basic {AHREFS_API_KEY}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return pd.DataFrame(response.json()['backlinks'])

def store_to_postgres(df, table_name):
    import psycopg2
    
    conn = psycopg2.connect(
        host='metabase-db',
        database='metabase',
        user='metabase',
        password='password'
    )
    
    df.to_sql(table_name, conn, if_exists='replace', index=False)

# Run weekly
domains = ['prestashop-project.com', 'example.com']
for domain in domains:
    keywords = get_ahrefs_organic_keywords(domain)
    store_to_postgres(keywords, f'seo_ahrefs_keywords_{domain}')
```

### Metabase Dashboard Questions

```sql
-- Top organic keywords
SELECT 
  keyword,
  traffic,
  volume,
  difficulty,
  position
FROM seo_ahrefs_keywords
ORDER BY traffic DESC
LIMIT 50;

-- Keywords by difficulty
SELECT 
  difficulty_bucket,
  COUNT(*) AS count,
  AVG(volume) AS avg_volume
FROM (
  SELECT 
    CASE 
      WHEN difficulty < 30 THEN 'Easy'
      WHEN difficulty < 60 THEN 'Medium'
      ELSE 'Hard'
    END AS difficulty_bucket,
    *
  FROM seo_ahrefs_keywords
) t
GROUP BY 1;
```

---

## SEMrush

### Prerequisites
- SEMrush account with API access
- API key from https://www.semrush.com/api/

### Python Integration

```python
import requests
import pandas as pd

SEMRUSH_API_KEY = "your-api-key"

def get_semrush_organic(domain):
    url = "https://api.semrush.com/?type=domain_organic"
    
    params = {
        "key": SEMRUSH_API_KEY,
        "domain": domain,
        "database": "google",
        "export_columns": "Ph,Nq,Co,Nr,Td",
        "display_limit": 1000
    }
    
    response = requests.get(url, params=params)
    lines = response.text.strip().split('\n')[1:]  # Skip header
    
    data = []
    for line in lines:
        parts = line.split(';')
        data.append({
            'keyword': parts[0],
            'volume': int(parts[1]) if parts[1] else 0,
            'cpc': float(parts[2]) if parts[2] else 0,
            'results': int(parts[3]) if parts[3] else 0,
            'trend': parts[4]
        })
    
    return pd.DataFrame(data)
```

---

## Screaming Frog (SEO Spider)

### Option 1: Export to CSV (Free)

1. Run Screaming Frog on your site
2. Export → Internal → All
3. Upload CSV to Metabase

### Option 2: API (Paid - SEO Spider)

```python
import requests
import xml.etree.ElementTree as ET

def get_screaming_frog_data(api_key, url):
    # Requires Screaming Frog SEO Spider (paid)
    # Run in API mode: screaming-frog.exe --api
    
    base_url = f"http://localhost:8080/api/{api_key}"
    
    response = requests.get(f"{base_url}/ crawl/{url}/export?type=internal_html")
    
    # Parse and store
    # ...
```

---

## Google PageSpeed Insights

### Python Integration

```python
import requests
import pandas as pd

def get_pagespeed(url):
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    
    params = {
        "url": url,
        "key": "YOUR_API_KEY",
        "strategy": "mobile"
    }
    
    response = requests.get(api_url, params=params)
    data = response.json()
    
    return {
        "url": url,
        "lcp": data['lighthouseResult']['audits']['largest-contentful-paint']['numericValue'],
        "cls": data['lighthouseResult']['audits']['cumulative-layout-shift']['numericValue'],
        "fid": data['lighthouseResult']['audits']['first-input-delay']['numericValue'],
        "performance_score": data['lighthouseResult']['categories']['performance']['score']
    }

# Batch check multiple URLs
urls = [
    "https://prestashop-project.com",
    "https://prestashop-project.com/products",
    # ...
]

results = [get_pagespeed(url) for url in urls]
df = pd.DataFrame(results)
df.to_sql('seo_pagespeed', conn, if_exists='replace', index=False)
```

---

## Recommended Implementation Order

1. **Google Search Console** (free, high value) - if not already done with GA4
2. **Ahrefs** (most popular) - if already paying for it
3. **PageSpeed** (free, actionable)
4. **SEMrush** (if already paying for it)
5. **Moz** (optional)

---

## Scheduling

Create cron jobs for automated updates:

```bash
# crontab -e
# Run SEO sync daily at 2am
0 2 * * * cd /var/www/metabase && python3 scripts/seo_sync.py >> logs/seo_sync.log 2>&1
```

---

## Dashboard Ideas

1. **Organic Search Overview**
   - Clicks from GSC
   - Top queries by clicks
   - Average position trend

2. **Keyword Rankings**
   - Ahrefs/SEMrush keyword positions over time
   - Position changes

3. **Technical SEO**
   - PageSpeed scores over time
   - Core Web Vitals trends

4. **Backlinks**
   - New backlinks over time
   - Domain authority
   - Referring domains
