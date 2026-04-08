# dbt Model Prioritization for Marketing Analytics MVP

**Date**: 2026-04-08  
**Project**: Marketing Analytics dbt Project  
**Current State**: 1 SQL file exists, 7 missing

---

## Executive Summary

**Phase 1 MVP Target**: 4 models (3 staging + 1 fact table)  
**Phase 2 Expansion**: +2 dimension tables + 2 staging models  
**Rationale**: Start with revenue-attributed marketing performance, defer customer/campaign dimensions

---

## Current State Analysis

### Existing Artifacts

| Type | File | Status |
|------|------|--------|
| SQL | `stg_prestashop__orders.sql` | **EXISTS** |
| YAML | All schema files | Exists but no SQL implementations |

### Missing SQL Models

```
staging/
├── stg_ga4__events.sql          (missing)
├── stg_ga4__traffic.sql         (missing)
├── stg_facebook__ads.sql        (missing)
├── stg_facebook__campaigns.sql  (missing)
├── stg_prestashop__customers.sql (missing)
└── stg_prestashop__products.sql  (missing)

marts/
├── fct_marketing_performance.sql  (missing)
├── dim_customers.sql              (missing)
└── dim_campaigns.sql              (missing)
```

---

## Priority Classification

### MUST-HAVE (Phase 1) - Critical Path

These models are on the critical path for the marketing performance dashboard.

#### 1. `stg_prestashop__orders` - EXISTS ✓
- **Priority**: CRITICAL
- **Justification**: Revenue attribution source; already implemented
- **Downstream**: `fct_marketing_performance`

#### 2. `stg_facebook__ads` - HIGHEST PRIORITY
- **Priority**: CRITICAL  
- **Justification**: Primary spend data for paid social channel; required for ROAS calculation
- **Dependencies**: Source `facebook_raw.ads` already defined
- **Downstream**: `fct_marketing_performance`
- **Effort**: Low (follows existing pattern from stg_prestashop__orders)

#### 3. `stg_facebook__campaigns` - HIGH PRIORITY
- **Priority**: HIGH
- **Justification**: Campaign dimension needed for channel attribution; provides campaign metadata
- **Dependencies**: Source `facebook_raw.campaigns` already defined
- **Downstream**: `dim_campaigns`, `fct_marketing_performance`
- **Effort**: Low

#### 4. `fct_marketing_performance` - CORE OF MVP
- **Priority**: CRITICAL
- **Justification**: Central fact table for marketing performance dashboard; calculates ROAS, CPA, CTR
- **Dependencies**: `stg_prestashop__orders`, `stg_facebook__ads`
- **Effort**: Medium (aggregation logic required)
- **Key Metrics**:
  - Daily spend by channel/campaign
  - Revenue attributed from orders
  - ROAS (revenue / spend)
  - CPA (spend / conversions)
  - CTR (clicks / impressions)

---

### SHOULD-HAVE (Phase 2) - Enhanced Analytics

#### 5. `stg_ga4__traffic` - HIGH VALUE
- **Priority**: HIGH
- **Justification**: Organic traffic metrics; complements paid social data
- **Dependencies**: Source `ga4_raw.traffic` already defined
- **Downstream**: Enriches `fct_marketing_performance` with organic channel
- **Note**: Can be added incrementally to existing fact table

#### 6. `dim_customers` - ANALYTICS ENRICHMENT
- **Priority**: MEDIUM
- **Justification**: Customer lifetime value, acquisition channel tracking
- **Dependencies**: `stg_prestashop__customers`
- **Use Case**: Cohort analysis, customer segmentation
- **Can defer**: Not required for channel performance ROAS

#### 7. `stg_ga4__events` - DETAILED ANALYTICS
- **Priority**: MEDIUM
- **Justification**: Event-level data for funnel analysis
- **Dependencies**: Source `ga4_raw.events` already defined
- **Use Case**: Conversion tracking, engagement metrics
- **Can defer**: Aggregate metrics sufficient for Phase 1

---

### NICE-TO-HAVE (Phase 3+) - Future Expansion

#### 8. `stg_prestashop__customers`
- **Priority**: LOW for MVP
- **Justification**: Customer profiles for `dim_customers`
- **Dependencies**: Source `prestashop_raw.customers` already defined
- **Can defer**: Only needed when building customer dimension

#### 9. `stg_prestashop__products`
- **Priority**: LOW for MVP
- **Justification**: Product catalog for product analytics
- **Use Case**: Product performance, SKU-level ROAS
- **Can defer**: Not needed for channel-level marketing performance

#### 10. `dim_campaigns`
- **Priority**: LOW for MVP
- **Justification**: Campaign dimension table
- **Dependencies**: `stg_facebook__campaigns`
- **Can defer**: Metadata only; fact table uses campaign_name directly

---

## Recommended Phase 1 Implementation Order

```
Priority 1: stg_facebook__ads
           ↓
Priority 2: stg_facebook__campaigns  
           ↓
Priority 3: fct_marketing_performance
           ↓
Priority 4: stg_ga4__traffic (optional but recommended)
```

### Why This Order?

1. **stg_facebook__ads first**: Low effort, establishes spend data pattern
2. **stg_facebook__campaigns second**: Provides campaign context, simple model
3. **fct_marketing_performance third**: Core MVP deliverable, combines data
4. **stg_ga4__traffic fourth**: Adds organic channel to complete the picture

---

## Phase 1 Model Set Summary

| Model | Type | Purpose | Lines Est. |
|-------|------|---------|------------|
| `stg_prestashop__orders` | Staging | Revenue source | 20 (exists) |
| `stg_facebook__ads` | Staging | Spend data | 25-30 |
| `stg_facebook__campaigns` | Staging | Campaign metadata | 20 |
| `fct_marketing_performance` | Mart | Core fact table | 80-100 |
| `stg_ga4__traffic` | Staging | Organic traffic | 25 |

**Total new SQL**: ~150-175 lines across 4 files

---

## Staging Model Pattern

### Template Pattern

```sql
{{ config(
    materialized='view',
    schema='staging'
) }}

with source as (
    select * from {{ source('<source_name>', '<table_name>') }}
),

renamed as (
    select
        -- Primary key
        {{ dbt_utils.generate_surrogate_key(['<unique_column>']) }} as <model>_id,
        
        -- Standardized columns
        <source_column> as <target_column>,
        
        -- Date normalization
        date_trunc('day', {{ source_column }}) as date,
        
        -- Metric columns (always include *_id for joins)
        ...
    from source
)

select * from renamed
```

### Example: stg_facebook__ads.sql

```sql
{{ config(
    materialized='view',
    schema='staging'
) }}

with source as (
    select * from {{ source('facebook_raw', 'ads') }}
),

renamed as (
    select
        {{ dbt_utils.generate_surrogate_key(['ad_id', 'date']) }} as ad_id,
        ad_id as source_ad_id,
        ad_name,
        campaign_id,
        date as ad_date,
        spend,
        impressions,
        clicks,
        ctr,
        cpc,
        conversions,
        cost_per_conversion
    from source
)

select * from renamed
```

### Example: stg_facebook__campaigns.sql

```sql
{{ config(
    materialized='view',
    schema='staging'
) }}

with source as (
    select * from {{ source('facebook_raw', 'campaigns') }}
),

renamed as (
    select
        {{ dbt_utils.generate_surrogate_key(['campaign_id']) }} as campaign_key,
        campaign_id,
        campaign_name,
        status,
        'paid_social' as channel  -- Standardize channel
    from source
)

select * from renamed
```

---

## Fact Table Architecture

### fct_marketing_performance Design

```sql
{{ config(
    materialized='table',
    schema='marts',
    unique_key='performance_id'
) }}

with 
-- Spend data (Facebook Ads)
fb_ads as (
    select
        date as performance_date,
        'paid_social' as channel,
        campaign_id,
        campaign_name,
        sum(spend) as channel_spend,
        sum(impressions) as channel_impressions,
        sum(clicks) as channel_clicks,
        sum(conversions) as channel_conversions
    from {{ ref('stg_facebook__ads') }}
    group by 1, 2, 3, 4
),

-- Revenue attribution (orders with UTM/campaign mapping)
revenue as (
    select
        date_trunc('day', created_at) as performance_date,
        campaign_source as channel,
        campaign_name,
        sum(total_paid) as attributed_revenue,
        count(*) as order_count
    from {{ ref('stg_prestashop__orders') }}
    group by 1, 2, 3
),

-- Combine metrics
combined as (
    select
        coalesce(a.performance_date, r.performance_date) as date,
        coalesce(a.channel, r.channel) as channel,
        coalesce(a.campaign_name, r.campaign_name) as campaign_name,
        coalesce(a.channel_spend, 0) as spend,
        coalesce(a.channel_impressions, 0) as impressions,
        coalesce(a.channel_clicks, 0) as clicks,
        coalesce(a.channel_conversions, 0) as conversions,
        coalesce(r.attributed_revenue, 0) as revenue
    from fb_ads a
    full outer join revenue r
        on a.performance_date = r.performance_date
        and a.channel = r.channel
),

-- Calculate derived metrics
final as (
    select
        {{ dbt_utils.generate_surrogate_key(['date', 'channel', 'campaign_name']) }} as performance_id,
        date,
        channel,
        campaign_name,
        spend,
        impressions,
        clicks,
        conversions,
        revenue,
        -- ROAS: revenue / spend (NULL if no spend)
        case 
            when spend > 0 then revenue / spend 
            else null 
        end as roas,
        -- CPA: spend / conversions
        case 
            when conversions > 0 then spend / conversions 
            else null 
        end as cpa,
        -- CTR: clicks / impressions
        case 
            when impressions > 0 then clicks::numeric / impressions 
            else null 
        end as ctr
    from combined
)

select * from final
```

---

## Dependency Graph

```
                    ┌─────────────────────┐
                    │  prestashop_raw.orders │ (source)
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ stg_prestashop__orders │ (EXISTS)
                    └──────────┬──────────┘
                               │
          ┌────────────────────┴────────────────────┐
          │                                         │
┌─────────▼─────────┐              ┌───────────────▼────────────────┐
│ facebook_raw.ads  │ (source)     │     facebook_raw.campaigns     │
└─────────┬─────────┘              └───────────────┬────────────────┘
          │                                         │
┌─────────▼─────────┐                               │
│ stg_facebook__ads │ ◄─────────────────────────────┘
└─────────┬─────────┘
          │
          │         ┌─────────────────────┐
          └────────►│ fct_marketing_      │ ◄─── MVP CORE
                    │ performance         │
                    └─────────────────────┘

Phase 2 additions:
    ga4_raw.traffic ──► stg_ga4__traffic ──► fct_marketing_performance

Phase 3 additions:
    prestashop_raw.customers ──► stg_prestashop__customers ──► dim_customers
    stg_facebook__campaigns ──────────────────────────────────► dim_campaigns
```

---

## Recommendation

**Start with Phase 1 MVP**: 4 models total (1 exists + 3 new staging + 1 fact)

This gives you a working marketing performance dashboard showing:
- Daily spend by Facebook campaign
- Revenue attribution from orders
- ROAS calculation per channel
- Basic channel performance metrics

**Defer to Phase 2**:
- Customer dimensions (requires customer staging)
- GA4 events (requires more complex event attribution logic)
- Product analytics (out of scope for channel performance)

---

## Next Steps

1. Create `stg_facebook__ads.sql` - follow existing pattern
2. Create `stg_facebook__campaigns.sql` - simple transformation
3. Create `fct_marketing_performance.sql` - aggregate and calculate metrics
4. Test with `dbt run` and `dbt test`
5. Add to Metabase dashboard

