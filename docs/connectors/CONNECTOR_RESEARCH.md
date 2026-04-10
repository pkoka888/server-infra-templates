# Connector Research Memo

Research on common failure modes for GA4, Facebook Ads, and PrestaShop connectors.

## Google Analytics 4 (GA4)

### Common Failure Modes

| Issue | Cause | Mitigation |
|-------|-------|------------|
| **Sampling** | Reports with >10M events sampled | Use `entityUserProperty` or BigQuery export |
| **Quota exhaustion** | 10K requests/day limit | Implement exponential backoff, batch requests |
| **Schema drift** | Custom dimensions change without notice | Pin report config, validate field existence |
| **Date range gaps** | Backfill misses events | Use `runInBatches: true` for historical loads |
| **OAuth token expiry** | Refresh tokens expire after 7 days unused | Schedule regular syncs, monitor token validity |

### Verified Configuration

```yaml
source: google-analytics-data (dlt)
auth: OAuth2 with refresh token
sync_mode: incremental
write_disposition: merge
state: last_date_loaded
```

## Facebook Ads

### Common Failure Modes

| Issue | Cause | Mitigation |
|-------|-------|------------|
| **Ad account access** | Token lacks required scopes | Request `ads_read`, `ads_management` |
| **Rate limiting** | 200 calls/hour per token | Queue requests, respect `X-Business-Use-Case` header |
| **Attribution window mismatch** | 1-day vs 7-day vs 28-day | Store window in metadata, warn on mismatch |
| **Inactive campaigns** | Filtered by default | Include `effective_status` in API calls |
| **Field deprecation** | `impressions` → `spend` naming | Pin API version, validate response schema |

### Verified Configuration

```yaml
source: facebook-ads (dlt)
auth: Access token
fields: campaign_id, adset_id, ad_id, spend, impressions, clicks
breakdowns: [age, gender, country]
date_preset: last_90_days
```

## PrestaShop

### Common Failure Modes

| Issue | Cause | Mitigation |
|-------|-------|------------|
| **Rate limiting** | PS REST API throttles after 5 requests/sec | Add 200ms delay between requests |
| **Image URL expiry** | Product images use temporary URLs | Cache locally or use CDN |
| **Order state inconsistency** | PS order states vary by shop | Normalize states in staging |
| **Tax calculation drift** | Manual vs automatic tax | Use `total_paid_tax_incl` as source of truth |
| **Guest checkout** | No customer_id linkage | Join on email where available |

### Verified Configuration

```yaml
source: prestashop (custom API via requests)
endpoints:
  - /api/orders?display=full
  - /api/customers
  - /api/products?display=full
auth: API key via X-PS-Key header
pagination: 50 items per page
```

## Sync Strategy

### Recommended Order

1. **PrestaShop orders** — establishes revenue baseline
2. **Facebook Ads** — provides spend attribution
3. **GA4** — provides traffic and conversion data

### Watering Hole Pattern

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PrestaShop │ ──► │    dbt      │ ──► │  Metabase   │
│   (Orders)  │     │  Staging    │     │ Dashboards  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
┌─────────────┐            │
│ FB Ads      │ ───────────┤
│ (Spend)     │            │
└─────────────┘            │
                          │
┌─────────────┐            │
│ GA4         │ ───────────┘
│ (Traffic)   │
└─────────────┘
```

## Extension Points

- **Google Ads**: `google-ads` dlt source, attribution modeling
- **Google Search Console**: `google-search-console` dlt source, SEO tracking
- **Ahrefs/SEMrush**: Custom API calls for backlink data
