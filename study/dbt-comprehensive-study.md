# dbt (Data Build Tool) - Comprehensive Study

## Overview
**Date**: 2026-04-08  
**Researcher**: Sisyphus AI Agent  
**Scope**: dbt Core, dbt Cloud, dbt Semantic Layer  
**Purpose**: Evaluate dbt as the transformation layer for marketing analytics

---

## Repository Information

| Property | Value |
|----------|-------|
| **Repository** | [dbt-labs/dbt-core](https://github.com/dbt-labs/dbt-core) |
| **Website** | https://www.getdbt.com/ |
| **License** | Apache-2.0 |
| **Stars** | 12,600+ |
| **Forks** | 2,400+ |
| **Language** | Python (73.4%) |
| **Latest Version** | v1.11.7 (March 2026) |
| **Maintainer** | dbt Labs (formerly Fishtown Analytics) |

---

## What is dbt?

dbt (data build tool) enables data analysts and engineers to transform data in their warehouses by writing SQL select statements. dbt handles the DDL/DML - turning these select statements into tables and views.

### Core Philosophy
- **SQL-first**: Write transformations in SQL, not Python
- **Version control**: Git-based workflow for analytics
- **Modularity**: Reusable, composable models
- **Testing**: Built-in data quality checks
- **Documentation**: Auto-generated from code

---

## Architecture

```
Raw Data (Sources)
       │
       ▼
┌─────────────────┐
│  Staging Layer  │  stg_ga4__events, stg_prestashop__orders
│  (1:1 with src) │  Clean, type, rename
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Intermediate   │  int__customer_touchpoints, int__order_enriched
│     Layer       │  Business logic, joins
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      Marts      │  dim_customers, fct_orders, fct_marketing_performance
│  (Star Schema)  │  Business-facing models
└─────────────────┘
```

### Model Types

| Type | Purpose | Example |
|------|---------|---------|
| **Sources** | Define raw data from external systems | `source('ga4_raw', 'events')` |
| **Staging** | 1:1 transformations of source data | `stg_ga4__events` |
| **Intermediate** | Business logic, complex joins | `int__customer_journey` |
| **Marts** | Final business-facing models | `fct_orders`, `dim_customers` |
| **Snapshots** | Slowly changing dimensions | `snapshot_customers` |
| **Seeds** | Static reference data | `seed_country_codes` |

---

## Key Features

### 1. SQL Templating with Jinja
```sql
-- models/staging/stg_ga4__events.sql
{% set event_types = ['page_view', 'purchase', 'add_to_cart'] %}

WITH events AS (
    SELECT * FROM {{ source('ga4_raw', 'events') }}
),
filtered AS (
    SELECT *
    FROM events
    WHERE event_name IN (
        {% for event_type in event_types %}
        '{{ event_type }}'{% if not loop.last %},{% endif %}
        {% endfor %}
    )
)
SELECT * FROM filtered
```

### 2. Dependency Management
```sql
-- Automatic DAG generation via ref()
SELECT * FROM {{ ref('stg_prestashop__orders') }}

-- Source references
SELECT * FROM {{ source('ga4_raw', 'events') }}
```

### 3. Materializations
```sql
{{ config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge'
) }}

SELECT * FROM {{ ref('stg_orders') }}
{% if is_incremental() %}
WHERE loaded_at > (SELECT MAX(loaded_at) FROM {{ this }})
{% endif %}
```

| Materialization | Use Case |
|-----------------|----------|
| `view` | Lightweight, always-current transformations |
| `table` | Expensive computations, data snapshots |
| `incremental` | Large datasets, append-only or merge |
| `ephemeral` | Intermediate CTEs, not persisted |

### 4. Testing Framework
```yaml
# models/marts/core/schema.yml
version: 2

models:
  - name: fct_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id
      - name: total_amount
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
```

### 5. Documentation
```sql
{{
    config(
        description="Orders fact table with revenue and customer data"
    )
}}

/*
This model combines order data from PrestaShop with
enriched customer and product information.

Key columns:
- order_id: Unique identifier
- total_amount: Order total in USD
- customer_segment: Derived segment (Active, At Risk, Churned)
*/
```

---

## Marketing Analytics Use Cases

### Customer Attribution Model
```sql
-- models/marts/marketing/fct_attribution.sql
WITH touchpoints AS (
    SELECT
        user_id,
        event_timestamp,
        utm_source,
        utm_campaign,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_timestamp) AS touchpoint_number,
        COUNT(*) OVER (PARTITION BY user_id) AS total_touchpoints
    FROM {{ ref('stg_ga4__events') }}
    WHERE user_id IS NOT NULL
      AND utm_source IS NOT NULL
),
conversions AS (
    SELECT
        customer_id AS user_id,
        order_id,
        total_paid_amount AS revenue
    FROM {{ ref('fct_orders') }}
),
attributed AS (
    SELECT
        t.user_id,
        t.utm_source,
        t.utm_campaign,
        c.order_id,
        -- Linear attribution: equal weight to all touchpoints
        c.revenue / t.total_touchpoints AS attributed_revenue
    FROM touchpoints t
    JOIN conversions c ON t.user_id = c.user_id
    WHERE t.event_timestamp < c.created_at
)
SELECT
    utm_source,
    utm_campaign,
    SUM(attributed_revenue) AS total_attributed_revenue,
    COUNT(DISTINCT order_id) AS attributed_orders
FROM attributed
GROUP BY 1, 2
```

### Cohort Analysis
```sql
-- models/marts/marketing/fct_cohorts.sql
WITH customer_cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', first_order_date) AS cohort_month
    FROM {{ ref('dim_customers') }}
),
orders_with_cohorts AS (
    SELECT
        o.*,
        cc.cohort_month,
        DATE_DIFF('month', cc.cohort_month, o.created_at) AS periods_since_first
    FROM {{ ref('fct_orders') }} o
    JOIN customer_cohorts cc ON o.customer_id = cc.customer_id
)
SELECT
    cohort_month,
    periods_since_first,
    COUNT(DISTINCT customer_id) AS active_customers,
    SUM(total_paid_amount) AS revenue
FROM orders_with_cohorts
GROUP BY 1, 2
```

### Marketing Performance Summary
```sql
-- models/marts/marketing/fct_marketing_performance.sql
WITH facebook AS (
    SELECT
        date_start AS date,
        'Facebook Ads' AS channel,
        campaign_name,
        impressions,
        clicks,
        spend,
        0 AS revenue
    FROM {{ ref('stg_facebook__insights') }}
),
ga4_revenue AS (
    SELECT
        event_date AS date,
        'Organic / Direct' AS channel,
        utm_campaign AS campaign_name,
        0 AS impressions,
        0 AS clicks,
        0 AS spend,
        purchase_revenue AS revenue
    FROM {{ ref('stg_ga4__events') }}
    WHERE event_name = 'purchase'
)
SELECT
    date,
    channel,
    campaign_name,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(spend) AS spend,
    SUM(revenue) AS revenue,
    CASE WHEN SUM(spend) > 0 
         THEN SUM(revenue) / SUM(spend) 
         ELSE NULL 
    END AS roas
FROM (
    SELECT * FROM facebook
    UNION ALL
    SELECT * FROM ga4_revenue
)
GROUP BY 1, 2, 3
```

---

## Integration Patterns

### With Airbyte (ELT)
```
Airbyte (Extract & Load) → Raw Tables → dbt (Transform) → Marts
```

### With Prefect (Orchestration)
```python
from prefect import flow
from prefect_dbt.cli.commands import trigger_dbt_cli_command

@flow
def dbt_pipeline():
    # Run dbt models
    trigger_dbt_cli_command(
        command="dbt run --select marts",
        project_dir="./marketing_analytics",
        profiles_dir="."
    )
    
    # Run tests
    trigger_dbt_cli_command(
        command="dbt test",
        project_dir="./marketing_analytics",
        profiles_dir="."
    )
```

### With Metabase (BI)
- Connect Metabase directly to dbt marts tables
- Use dbt exposures to document dashboard dependencies
- Embed dbt docs in Metabase for context

---

## Deployment Options

### dbt Core (Open Source)
- **Cost**: Free
- **Setup**: Self-hosted
- **Best for**: Small teams, cost-conscious organizations
- **Limitations**: No scheduling, no web UI

### dbt Cloud
- **Cost**: $100-500+/month
- **Setup**: SaaS
- **Best for**: Teams needing collaboration features
- **Features**: Scheduling, web IDE, slim CI, observability

### dbt Cloud Developer
- **Cost**: Free tier available
- **Setup**: SaaS with local execution
- **Best for**: Individual developers
- **Limitations**: Limited jobs, no team features

---

## Strengths & Weaknesses

### Strengths
| Strength | Description |
|----------|-------------|
| **SQL-native** | No need to learn new language |
| **Git workflow** | Version control for analytics |
| **Modularity** | Reusable, composable models |
| **Testing** | Built-in data quality framework |
| **Documentation** | Auto-generated from code |
| **Community** | Large ecosystem of packages |
| **Warehouse agnostic** | Works with all major warehouses |

### Weaknesses
| Weakness | Description |
|----------|-------------|
| **SQL only** | Limited Python support (requires plugins) |
| **Learning curve** | Jinja templating takes time |
| **No extraction** | Only handles transformation (need ELT) |
| **Compilation overhead** | Large projects can be slow |
| **Debugging** | Error messages can be cryptic |

---

## Comparison with Alternatives

| Feature | dbt | SQLMesh | Dataform | LookML |
|---------|-----|---------|----------|--------|
| **License** | Apache-2.0 | Apache-2.0 | Commercial (GCP) | Commercial |
| **SQL-first** | ✅ | ✅ | ✅ | ❌ (YAML) |
| **Git workflow** | ✅ | ✅ | ✅ | ✅ |
| **Testing** | ✅ | ✅ | ✅ | Limited |
| **Python models** | ✅ (plugins) | ✅ | ✅ | ❌ |
| **Data contracts** | Limited | ✅ | Limited | ❌ |
| **Community** | Large | Growing | Small | Medium |

---

## Recommended Project Structure

```
marketing_analytics/
├── models/
│   ├── staging/
│   │   ├── ga4/
│   │   ├── facebook/
│   │   └── prestashop/
│   ├── intermediate/
│   ├── marts/
│   │   ├── core/
│   │   └── marketing/
│   └── utilities/
├── seeds/
├── snapshots/
├── macros/
│   ├── cents_to_dollars.sql
│   ├── date_spine.sql
│   └── generate_schema_name.sql
├── tests/
├── analyses/
├── dbt_project.yml
├── packages.yml
└── profiles.yml
```

---

## Common Packages

```yaml
# packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0", "<2.0.0"]
  
  - package: dbt-labs/codegen
    version: [">=0.12.0", "<0.13.0"]
  
  - package: calogica/dbt_expectations
    version: [">=0.10.0", "<0.11.0"]
  
  - package: dbt-labs/audit_helper
    version: [">=0.9.0", "<0.10.0"]
```

---

## Implementation Checklist

### Phase 1: Setup
- [ ] Install dbt-core with warehouse adapter (dbt-postgres, dbt-bigquery)
- [ ] Initialize project with `dbt init`
- [ ] Configure profiles.yml with warehouse credentials
- [ ] Set up sources for raw data

### Phase 2: Development
- [ ] Create staging models (1:1 with sources)
- [ ] Build intermediate models for business logic
- [ ] Create marts models (facts and dimensions)
- [ ] Add tests for critical columns
- [ ] Generate documentation

### Phase 3: Production
- [ ] Set up CI/CD pipeline
- [ ] Configure incremental models for large tables
- [ ] Set up monitoring for run times
- [ ] Document runbooks

---

## Conclusion

**Recommendation**: **Strongly Recommended** for marketing analytics

**Best Fit**:
- Teams comfortable with SQL
- Organizations using modern data warehouses
- Projects requiring version-controlled transformations
- Teams needing built-in testing and documentation

**When to Consider Alternatives**:
- Need Python-first transformations → Consider Dagster with pandas/spark
- Require data contracts → Consider SQLMesh
- GCP-native stack → Consider Dataform

---

## Resources

- [Official Documentation](https://docs.getdbt.com/)
- [dbt Learn](https://learn.getdbt.com/)
- [dbt Community](https://community.getdbt.com/)
- [dbt Packages Hub](https://hub.getdbt.com/)
- [Best Practices Guide](https://docs.getdbt.com/guides/best-practices)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-08 | Initial study |
