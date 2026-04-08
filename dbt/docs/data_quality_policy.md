# Data Quality Policy

## Overview

This document outlines the data quality framework implemented using `dbt-expectations` and custom macros for the marketing analytics dbt project.

## Test Severity Levels

| Severity | Behavior | Use Case |
|----------|----------|----------|
| `error` | Fails the dbt build pipeline | Critical business rules, primary keys, non-negative financials |
| `warn` | Logs warning but allows build | Data quality checks that may have valid exceptions, soft constraints |

## dbt-expectations Tests Used

### Column-Level Tests

| Test | Purpose | Example Usage |
|------|---------|---------------|
| `expect_column_values_to_be_between` | Range validation | spend >= 0, CTR between 0-1 |
| `expect_column_values_to_match_regex` | Format validation | email format validation |
| `expect_column_values_to_be_in_set` | Enum validation | channel, status fields |
| `expect_compound_columns_to_be_unique` | Composite uniqueness | date + channel + campaign |
| `expect_column_pair_values_to_be_equal` | Column relationship | clicks <= impressions |

### Table-Level Tests

| Test | Purpose | Example Usage |
|------|---------|---------------|
| `expect_table_row_count_to_be_between` | Non-empty validation | Table has at least 1 row |

## Custom Macros

### `positive_amount(column_name)`
- **Location**: `macros/data_quality/positive_amount.sql`
- **Purpose**: Validates that a column contains non-negative values (>= 0)
- **Usage**: `{{ positive_amount('column_name') }}`
- **Severity**: Error

### `valid_email(column_name)`
- **Location**: `macros/data_quality/valid_email.sql`
- **Purpose**: Validates email format using regex pattern (RFC 5322 compliant)
- **Pattern**: `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$`
- **Usage**: `{{ valid_email('email') }}`
- **Severity**: Error

## Source Freshness Rules

| Source | Table | Warning Threshold | Error Threshold | Field |
|--------|-------|-------------------|-----------------|-------|
| PrestaShop | orders | 30 minutes | 1 hour | `date_add` |
| PrestaShop | customers | 1 hour | 2 hours | `date_add` |
| GA4 | events | 12 hours | 24 hours | `_dlt_load_time` |
| GA4 | traffic | 12 hours | 24 hours | `_dlt_load_time` |
| Facebook | ads | 12 hours | 24 hours | `_dlt_load_time` |
| Facebook | campaigns | 12 hours | 24 hours | `_dlt_load_time` |

## Model-Specific Quality Rules

### Staging Models

#### stg_prestashop__orders
- `order_id`: Unique, not null (ERROR)
- `total_paid`: >= 0 (ERROR)
- `total_products`: >= 0 (WARN)
- `total_shipping`: >= 0 (WARN)
- `created_at`: Not null, date range (WARN)

#### stg_ga4__events
- `event_id`: Unique, not null (ERROR)
- `event_date`: Not null, valid format (ERROR)
- `session_id`: Not null (ERROR)
- `event_name`: Valid enum values (WARN)
- `engagement_time_msec`: >= 0 (WARN)

#### stg_facebook__ads
- `ad_id`: Unique, not null (ERROR)
- `spend`: >= 0 (ERROR)
- `impressions`: >= 0 (WARN)
- `clicks`: >= 0, <= impressions (WARN)
- `ctr`: Between 0-1 (WARN)

### Mart Models

#### fct_marketing_performance
- Composite unique: date + channel + campaign_name (ERROR)
- `spend`: >= 0 (ERROR)
- `revenue`: >= 0 (ERROR)
- `roas`: >= 0 when spend > 0 (ERROR)
- `ctr`: Between 0-1 (WARN)

#### dim_customers
- `customer_id`: Unique, not null (ERROR)
- `email`: Valid format (ERROR)
- `lifetime_value`: >= 0 (ERROR)
- `total_orders`: >= 0 (ERROR)

## Running Tests

```bash
# Run all tests
dbt test

# Run tests for specific model
dbt test --select stg_prestashop__orders

# Run only dbt-expectations tests
dbt test --select package:dbt_expectations

# Run freshness tests
dbt source freshness

# Run tests with warnings as errors
dbt test --warn-error
```

## Adding New Tests

When adding new tests:

1. **Use standard dbt tests** for:
   - Uniqueness constraints
   - Not null constraints
   - Referential integrity (relationships)

2. **Use dbt-expectations** for:
   - Range validations (between min/max)
   - Regex pattern matching
   - Set membership (enums)
   - Compound uniqueness
   - Statistical expectations

3. **Use custom macros** for:
   - Reusable business logic
   - Complex validations
   - Cross-database compatibility

## Maintenance

- Review warnings weekly to identify data quality trends
- Adjust thresholds based on historical patterns
- Document any severity changes in commit messages
- Test new rules in development before deploying to production
