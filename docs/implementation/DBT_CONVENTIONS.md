# dbt Project Convention Guide

Standards for analytics engineering with dbt Core 1.8+.

## Project Structure

```
dbt/
├── dbt_project.yml          # Project configuration
├── profiles.yml              # Database connections (not in repo)
├── packages.yml              # Package dependencies
├── README.md                 # Project documentation
│
├── macros/
│   ├── data_quality/
│   │   └── _validations.sql  # Shared validation macros
│   └── utils/
│       └── _dates.sql       # Date utility macros
│
├── models/
│   ├── staging/              # Source-conformed models
│   │   ├── _staging.yml     # Staging source definitions
│   │   ├── ga4/
│   │   │   ├── stg_ga4__traffic.sql
│   │   │   └── stg_ga4__conversions.sql
│   │   ├── facebook/
│   │   │   ├── stg_facebook__ads.sql
│   │   │   └── stg_facebook__campaigns.sql
│   │   └── prestashop/
│   │       ├── stg_prestashop__orders.sql
│   │       └── stg_prestashop__customers.sql
│   │
│   ├── intermediate/         # Business logic layer
│   │   ├── int_marketing_spend.sql
│   │   └── int_order_attribution.sql
│   │
│   └── marts/
│       ├── _marts.yml        # Mart documentation
│       ├── core/
│       │   └── dim_customers.sql
│       └── marketing/
│           └── fct_marketing_performance.sql
│
├── seeds/                    # Static reference data
│   └── marketing_channels.csv
│
├── tests/
│   └── marts/
│       └── test_fct_marketing.yml
│
└── docs/
    └── dbt_project_docs.md
```

## Naming Conventions

| Layer | Pattern | Example |
|-------|---------|---------|
| Staging | `stg_{source}__{entity}` | `stg_ga4__traffic` |
| Intermediate | `int_{concept}` | `int_marketing_spend` |
| Mart | `fct_{entity}` or `dim_{entity}` | `fct_marketing_performance` |
| Metrics | Metricflow YAML | `marketing_metrics.yml` |

## dbt_project.yml

```yaml
name: marketing_analytics
version: 1.0.0
config-version: 2

profile: marketing_analytics

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

clean-targets:
  - target
  - dbt_packages

models:
  marketing_analytics:
    +materialized: view
    +schema: "{{ target.schema }}"
    
    staging:
      +materialized: view
      +schema: staging
      +tags: ["staging"]
      ga4:
        +schema: staging_ga4
      facebook:
        +schema: staging_facebook
      prestashop:
        +schema: staging_prestashop
    
    intermediate:
      +materialized: view
      +schema: intermediate
      +tags: ["intermediate"]
    
    marts:
      +materialized: table
      +schema: marts
      +tags: ["marts"]
      +persist_docs:
        relation: true
        columns: true

vars:
  timezone: "Europe/Prague"
  client_id: "default"
  etl_date: "{{ modules.datetime.date.today() }}"
```

## Staging Model Template

```sql
-- stg_ga4__traffic.sql
{{
    config(
        materialized="view",
        schema="staging_ga4",
        tags=["staging"]
    )
}}

with source as (
    select *
    from {{ source("ga4", "traffic") }}
    where _loaded_at = (select max(_loaded_at) from {{ source("ga4", "traffic") }})
),

renamed as (
    select
        -- Primary key
        {{ dbt_utils.generate_surrogate_key(["date", "source", "medium"]) }} as traffic_key,
        
        -- Dimensions
        date,
        source,
        medium,
        campaign,
        device_category,
        country,
        
        -- Metrics
        sessions::int64 as sessions,
        users::int64 as users,
        new_users::int64 as new_users,
        bounces::int64 as bounces,
        session_duration::int64 as session_duration_seconds,
        
        -- Metadata
        _loaded_at,
        'ga4' as source_system
        
    from source
)

select * from renamed
```

## Mart Model Template

```sql
-- fct_marketing_performance.sql
{{
    config(
        materialized="incremental",
        schema="marts",
        unique_key="reporting_date",
        incremental_strategy="merge",
        tags=["mart", "marketing"]
    )
}}

with traffic as (
    select * from {{ ref("stg_ga4__traffic") }}
),

spend as (
    select * from {{ ref("stg_facebook__ads") }}
),

orders as (
    select * from {{ ref("stg_prestashop__orders") }}
),

enriched as (
    select
        traffic.reporting_date,
        traffic.source,
        traffic.medium,
        traffic.campaign,
        traffic.sessions,
        traffic.users,
        traffic.conversions as ga4_conversions,
        coalesce(sum(spend.spend), 0) as ad_spend,
        coalesce(count(orders.order_id), 0) as orders,
        coalesce(sum(orders.total_paid), 0) as revenue
        
    from traffic
    left join spend
        on traffic.reporting_date = spend.ad_date
        and traffic.source = spend.source
    left join orders
        on traffic.reporting_date = orders.order_date
        and traffic.source = orders.source
        
    {% if is_incremental() %}
    where traffic.reporting_date >= coalesce(
        (select max(reporting_date) from {{ this }}),
        '2024-01-01'
    )
    {% endif %}
    
    group by 1, 2, 3, 4, 5, 6, 7
)

select
    *,
    case when sessions > 0 
        then ad_spend / sessions 
        else 0 
    end as cpc,
    case when sessions > 0 
        then orders::float / sessions 
        else 0 
    end as conversion_rate,
    case when ad_spend > 0 
        then revenue / ad_spend 
        else 0 
    end as roas,
    {{ dbt_utils.generate_surrogate_key(["reporting_date", "source", "medium"]) }} as performance_key
    
from enriched
```

## Test Standards

### Column Tests (in schema.yml)

```yaml
version: 2

models:
  - name: fct_marketing_performance
    columns:
      - name: performance_key
        tests:
          - unique
          - not_null
        
      - name: reporting_date
        tests:
          - not_null
          
      - name: sessions
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              
      - name: ad_spend
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
```

### Singular Tests

```sql
-- tests/marts/test_roas_calculation.sql
{{ config(tags=["sanity"]) }}

with modeled as (
    select * from {{ ref("fct_marketing_performance") }}
),

validation_errors as (
    select
        performance_key,
        ad_spend,
        revenue,
        roas
    from modeled
    where ad_spend > 0 
      and (roas < 0 or roas > 1000)
)

select
    performance_key,
    ad_spend,
    revenue,
    roas
from validation_errors
```

## Documentation Standards

Every model should have:

1. **Description** in `schema.yml` or doc block
2. **Column descriptions** for metrics and keys
3. **Test documentation** explaining failure implications

```sql
{{
    config(
        meta={
            "owner": "analytics_team",
            "reviewer": "data_engineer",
            "slack_channel": "#analytics"
        }
    )
}}

/**
 * Marketing Performance Fact Table
 * 
 * Combines traffic, ad spend, and order data to calculate
 * marketing ROI metrics.
 * 
 * @metrics roas, conversion_rate, cpc, cpa
 * @refreshed daily at 03:00 UTC
 */
```
