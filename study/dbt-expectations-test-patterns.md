# dbt-expectations Column Relationship Tests

## The Problem with `expect_column_pair_values_to_be_equal` for Inequality

The current usage is **semantically incorrect**:

```yaml
# WRONG - This tests equality on a filtered subset
- dbt_expectations.expect_column_pair_values_to_be_equal:
    column_A: clicks
    column_B: impressions
    row_condition: "clicks > impressions"
```

**What this actually does:**
1. Filters to only rows where `clicks > impressions`
2. Tests that `clicks = impressions` on those rows
3. This is nonsensical - it will always pass because equality can't be true when A > B

**What you want:** Test that `clicks <= impressions` for ALL rows.

---

## Solution: `expect_column_pair_values_A_to_be_greater_than_B`

The `metaplane/dbt-expectations` package provides this test for column comparisons:

```sql
{% test expect_column_pair_values_A_to_be_greater_than_B(model,
    column_A,
    column_B,
    or_equal=False,
    row_condition=None
) %}
```

### Key Parameters

| Parameter | Description |
|-----------|-------------|
| `column_A` | The column that should be greater |
| `column_B` | The column that should be less |
| `or_equal` | If `true`, allows `A >= B` (default: `false` for strict `A > B`) |
| `row_condition` | Optional SQL WHERE clause to filter rows |

---

## 1. Correct YAML for `clicks <= impressions`

```yaml
columns:
  - name: clicks
    description: "Total clicks - must be <= impressions"
    tests:
      - dbt_expectations.expect_column_pair_values_A_to_be_greater_than_B:
          column_A: impressions
          column_B: clicks
          or_equal: true
          row_condition: "clicks IS NOT NULL AND impressions IS NOT NULL"
          severity: warn
```

**Logic:** `impressions >= clicks` is equivalent to `clicks <= impressions`

**Why `row_condition` includes both columns:** The test needs both values to be non-NULL to perform the comparison. NULL comparisons return NULL (not TRUE or FALSE), so NULLs are excluded.

---

## 2. Correct YAML for `end_date >= start_date`

```yaml
columns:
  - name: end_date
    description: "Campaign end date - must be >= start_date"
    tests:
      - dbt_expectations.expect_column_pair_values_A_to_be_greater_than_B:
          column_A: end_date
          column_B: start_date
          or_equal: true
          row_condition: "end_date IS NOT NULL AND start_date IS NOT NULL"
          severity: warn
```

**Logic:** `end_date >= start_date` means the campaign ends on or after it starts.

### Handling NULL Dates

For date ranges where NULLs are meaningful (e.g., ongoing campaigns with no end date):

```yaml
columns:
  - name: end_date
    description: "Campaign end date - NULL for ongoing campaigns, >= start_date when set"
    tests:
      - dbt_expectations.expect_column_pair_values_A_to_be_greater_than_B:
          column_A: end_date
          column_B: start_date
          or_equal: true
          # Only test rows where end_date is NOT NULL
          row_condition: "end_date IS NOT NULL"
          severity: warn
```

---

## 3. General Patterns for Cross-Column Validation

### Pattern A: Column A <= Column B (less than or equal)

```yaml
tests:
  - dbt_expectations.expect_column_pair_values_A_to_be_greater_than_B:
      column_A: column_B_name   # The "greater" column
      column_B: column_A_name   # The "less" column
      or_equal: true
      row_condition: "column_A_name IS NOT NULL AND column_B_name IS NOT NULL"
```

### Pattern B: Column A > Column B (strictly greater)

```yaml
tests:
  - dbt_expectations.expect_column_pair_values_A_to_be_greater_than_B:
      column_A: column_A_name
      column_B: column_B_name
      or_equal: false  # Default, but explicit for clarity
```

### Pattern C: Computed Column Matches Formula

For testing `total_amount = unit_price * quantity`:

```yaml
columns:
  - name: total_amount
    tests:
      - dbt_expectations.expect_column_pair_values_A_to_be_greater_than_B:
          column_A: total_amount
          column_B: total_amount  # Self-reference trick
          row_condition: |
            total_amount = unit_price * quantity
          # Or better - use expect_column_values_to_be_between with computed tolerance
```

Actually, for computed columns, consider `expect_multicolumn_sum_to_equal`:

```yaml
tests:
  - dbt_expectations.expect_multicolumn_sum_to_equal:
      column_list: ["tax", "shipping", "subtotal"]
      sum_column: "total"
      tolerance: 0.01
```

### Pattern D: Date Range Validity

```yaml
# start_date must be in the past, end_date must be >= start_date
columns:
  - name: start_date
    tests:
      - dbt_expectations.expect_column_values_to_be_between:
          min_value: "'2020-01-01'"
          max_value: "CURRENT_DATE"
          strictly: false

  - name: end_date
    tests:
      - dbt_expectations.expect_column_pair_values_A_to_be_greater_than_B:
          column_A: end_date
          column_B: start_date
          or_equal: true
          row_condition: "end_date IS NOT NULL"
```

---

## 4. Severity Guidelines

| Severity | Behavior | When to Use |
|----------|----------|-------------|
| `error` | Fails the dbt build pipeline | **Critical business rules** that must never fail: |
|          |                            | - Primary keys, foreign keys |
|          |                            | - Non-negative financials (spend >= 0) |
|          |                            | - Unique constraints |
|          |                            | - Revenue calculations |
| `warn` | Logs warning, build continues | **Data quality checks** with valid exceptions: |
|         |                               | - CTR between 0-1 (edge cases exist) |
|         |                               | - Date range validation (NULLs valid) |
|         |                               | - Non-critical metrics |

### Decision Matrix

Use `error` when:
- A violation indicates a **bug in the pipeline**
- The data is **fundamentally incorrect**
- You want CI/CD to **fail on violations**

Use `warn` when:
- Violations might be **expected in some cases** (e.g., test data)
- You want to **monitor** but not block
- The check is **advisory** rather than mandatory

---

## Quick Reference

| Test | Use For | YAML |
|------|---------|------|
| `clicks <= impressions` | clicks should not exceed impressions | `column_A: impressions, column_B: clicks, or_equal: true` |
| `end_date >= start_date` | end date must be on or after start | `column_A: end_date, column_B: start_date, or_equal: true` |
| `column_a < column_b` | strict inequality | `column_A: column_b, column_B: column_a, or_equal: false` |
| `NULL dates allowed` | date range with NULL end_date | Add `row_condition: "column_A IS NOT NULL"` |

---

## References

- [metaplane/dbt-expectations GitHub](https://github.com/metaplane/dbt-expectations)
- [Test Documentation](https://github.com/metaplane/dbt-expectations#available-tests)
- Multi-column tests section: `expect_column_pair_values_A_to_be_greater_than_B`
