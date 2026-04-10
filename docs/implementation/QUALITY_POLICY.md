# Data Quality Policy

Validation strategy for the marketing analytics pipeline.

## Quality Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Quality Gates                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. INGESTION     → Row counts, schema validation          │
│                    → Null keys, duplicate detection         │
│                                                              │
│  2. TRANSFORM     → dbt singular tests                      │
│                    → dbt schema tests                       │
│                    → dbt-expectations assertions           │
│                                                              │
│  3. AGGREGATION   → Mart-level sanity checks               │
│                    → Cross-model referential integrity     │
│                                                              │
│  4. BUSINESS       → Revenue reconciliation                │
│                    → Attribution window validation          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Ingestion Validation

Run immediately after each source sync.

### Row Count Checks

| Source | Minimum Rows | Maximum Rows | Window |
|--------|-------------|--------------|--------|
| GA4 traffic | 100 | 1,000,000 | per day |
| FB Ads | 50 | 100,000 | per day |
| PrestaShop orders | 1 | 10,000 | per day |

### Schema Validation

```python
# scripts/validate_schema.py
"""Validate loaded data against expected schema."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ColumnSpec:
    name: str
    type: str
    nullable: bool = True
    tests: list[str] | None = None


class SchemaValidator:
    """Validates loaded data against expected schema."""
    
    GA4_TRAFFIC_SCHEMA = [
        ColumnSpec("date", "date", nullable=False),
        ColumnSpec("source", "string", nullable=False),
        ColumnSpec("medium", "string", nullable=True),
        ColumnSpec("campaign", "string", nullable=True),
        ColumnSpec("sessions", "integer", nullable=False),
        ColumnSpec("users", "integer", nullable=False),
        ColumnSpec("conversions", "integer", nullable=True),
    ]
    
    def validate(self, df, schema: list[ColumnSpec]) -> list[str]:
        errors = []
        
        # Check required columns exist
        for spec in schema:
            if spec.name not in df.columns:
                errors.append(f"Missing required column: {spec.name}")
        
        # Check nulls on non-nullable columns
        for spec in schema:
            if not spec.nullable:
                null_count = df[spec.name].isna().sum()
                if null_count > 0:
                    errors.append(
                        f"Non-nullable column has {null_count} nulls: {spec.name}"
                    )
        
        return errors
```

## Transform Validation (dbt Tests)

### Core Tests

```yaml
# models/marts/_marts.yml
version: 2

models:
  - name: fct_marketing_performance
    description: Marketing metrics by date and channel
    columns:
      - name: performance_key
        description: Surrogate key for this record
        tests:
          - unique
          - not_null

      - name: reporting_date
        description: Date of metrics
        tests:
          - not_null

      - name: sessions
        description: Total sessions
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0

      - name: ad_spend
        description: Advertising spend in EUR
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 1000000

      - name: revenue
        description: Total attributed revenue
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 10000000

      - name: roas
        description: Return on ad spend
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 100

  - name: stg_prestashop__orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null

      - name: order_total
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 50000
```

### Custom Validation Tests

```sql
-- tests/marts/test_revenue_reconciliation.sql
"""
Verify revenue matches source orders within 0.1% tolerance.
"""

{{ config(tags=["critical", "reconciliation"]) }}

with order_revenue as (
    select 
        date_trunc('day', order_date) as revenue_date,
        sum(total_paid) as source_revenue
    from {{ ref("stg_prestashop__orders") }}
    group by 1
),

mart_revenue as (
    select
        reporting_date as revenue_date,
        sum(revenue) as reported_revenue
    from {{ ref("fct_marketing_performance") }}
    group by 1
),

comparison as (
    select
        o.revenue_date,
        o.source_revenue,
        m.reported_revenue,
        abs(o.source_revenue - m.reported_revenue) as difference,
        case when o.source_revenue > 0 
            then abs(o.source_revenue - m.reported_revenue) / o.source_revenue 
            else 0 
        end as pct_difference
    from order_revenue o
    inner join mart_revenue m on o.revenue_date = m.revenue_date
)

select
    revenue_date,
    source_revenue,
    reported_revenue,
    difference,
    pct_difference
from comparison
where pct_difference > 0.001  -- Allow 0.1% tolerance
```

## Business Logic Validation

### Anomaly Detection

```sql
-- tests/marts/test_anomaly_sessions.sql
"""
Alert if sessions deviate more than 50% from 7-day average.
"""

{{ config(tags=["anomaly"]) }}

with daily_sessions as (
    select
        reporting_date,
        sessions,
        avg(sessions) over (
            order by reporting_date
            rows between 7 preceding and current row
        ) as avg_sessions_7d,
        sessions / nullif(avg(sessions) over (
            order by reporting_date
            rows between 7 preceding and current row
        ), 0) as ratio_to_avg
    from {{ ref("fct_marketing_performance") }}
),

anomalies as (
    select *
    from daily_sessions
    where abs(1 - ratio_to_avg) > 0.5
      and reporting_date >= current_date - interval '7 days'
)

select
    reporting_date,
    sessions,
    avg_sessions_7d,
    ratio_to_avg
from anomalies
```

## Alerting Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Row count | < 80% expected | < 50% expected | Pause pipeline, alert |
| Null rate | > 1% | > 5% | Alert, investigate |
| Revenue gap | > 0.1% | > 1% | Block, notify |
| ROAS | < 0 | N/A | Alert, investigate |
| Latency | > 30 min | > 60 min | Alert |

## Slack Alert Format

```
🚨 [CRITICAL] Marketing Pipeline Failed

Source: GA4
Client: client1
Error: Row count 45% below expected
Time: 2024-01-15 02:15 UTC
Run: prefect/run-id/abc123

Action Required:
- [ ] Check GA4 API quota
- [ ] Verify property access
- [ ] Re-run after fix
```

## Quality Report

Generated after each pipeline run.

```markdown
# Quality Report - 2024-01-15

## Summary
- Sources synced: 3/3 ✓
- Models built: 12/12 ✓
- Tests passed: 47/48 (98.9%) ⚠️
- Duration: 23m 45s

## Failed Tests
| Test | Model | Error |
|------|-------|-------|
| test_anomaly_sessions | fct_marketing | 3 anomalies detected |

## Recommendations
- Investigate Jan 12 traffic spike (150% above average)
- Review Facebook campaign "summer_sale" for anomalies
```

## Tool Selection

| Layer | Tool | Why |
|-------|------|-----|
| Ingestion | Python assertions | Fast, catches schema issues early |
| Transform | dbt core tests | Native, schema-scoped |
| Business | dbt-expectations | Expressive, ML-ready |
| Monitoring | Prefect | Orchestration + alerting |
| Visualization | Metabase | Pipeline health dashboards |
