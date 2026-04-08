# dbt Macro Best Practices Research

**Date:** 2026-04-08  
**Context:** Duplicate `valid_email` macro found in `valid_email.sql` and `positive_amount.sql`

---

## 1. Current Issue Analysis

### Duplicate Macro Found

The `valid_email` macro exists in two files:

| File | Line | Status |
|------|------|--------|
| `macros/data_quality/valid_email.sql` | 8-13 | Original |
| `macros/data_quality/positive_amount.sql` | 22-28 | Duplicate |

Both files contain identical implementations:
- Dispatch wrapper macro
- `default__valid_email` implementation

**Impact:** This is a naming collision that will cause undefined behavior or errors when dbt tries to compile.

---

## 2. Macro Organization

### Recommended Directory Structure

```
macros/
├── _macros.yml           # Documentation for all macros (optional)
├── utils/
│   ├── date_helpers.sql  # Date manipulation macros
│   ├── string_helpers.sql # String manipulation macros
│   └── etl_helpers.sql   # ETL-related utilities
├── data_quality/
│   ├── validations.sql  # All validation macros in one file
│   └── assertions.sql    # Assertion helpers
├── cross_db/
│   └── compatibility.sql # Adapter-specific implementations
└── migrations/
    └── schema_migrations.sql # Schema versioning helpers
```

### Key Principles

1. **One Macro Per File vs Multiple Per File**
   - **Small/simple macros (< 10 lines):** Group related macros in single file
   - **Complex macros (> 50 lines):** Separate file per macro
   - **Rationale:** Improves discoverability without excessive file proliferation

2. **Directory Organization by Purpose**
   - `utils/` - Helper functions (date, string, type conversion)
   - `data_quality/` - Validations and assertions
   - `cross_db/` - Adapter-specific implementations
   - `etl/` - Pipeline-specific transformations

3. **Private vs Public Macros**
   - Prefix private macros with `_` (e.g., `_internal_helper`)
   - Only export documented, stable macros

---

## 3. Naming Conventions

### Community-Recommended Prefixes (dbt Discourse)

Based on dbt community conventions inspired by dplyr:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `is_` | Boolean outputs | `is_valid_email()`, `is_positive()` |
| `filter_` | Row filtering conditions | `filter_recent_records()` |
| `mutate_` | Column transformations | `mutate_full_name()` |
| `calculate_` | Computations | `calculate_discount()` |
| `summarize_` | Aggregations | `summarize_monthly_totals()` |
| `compat_` | Cross-database compatibility | `compat_date_trunc()` |

### Avoiding Name Collisions

1. **Use Namespace Prefixes**
   - Company/project prefix: `ma_valid_email()` (marketing_analytics)
   - Package prefix: `dq_is_valid()` (data quality)

2. **Dispatch Namespace**
   - Use a unique package name in `adapter.dispatch()`:
   ```sql
   {{ return(adapter.dispatch('valid_email', 'my_project')(column_name)) }}
   ```

3. **File Naming Matches Macro Name**
   - `valid_email.sql` contains `valid_email()` macro
   - Avoid: `positive_amount.sql` containing `valid_email()`

---

## 4. Dispatch Pattern Decision

### When to Use `adapter.dispatch`

| Use Case | Recommendation |
|----------|----------------|
| Multi-database project (Postgres + Snowflake) | **Use dispatch** |
| Single database (PostgreSQL only) | **Direct implementation** |
| Package maintainers | **Use dispatch** |
| Internal utilities | Direct implementation acceptable |

### Your Current Implementation

```sql
{% macro valid_email(column_name) %}
{{ return(adapter.dispatch('valid_email', 'dbt_expectations')(column_name)) }}
{% endmacro %}

{% macro default__valid_email(column_name) %}
    {{ column_name }} ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
{% endmacro %}
```

### Recommendation: **Keep Dispatch Pattern**

Reasons:
1. You're already using it - consistency is valuable
2. Future-proofs for multi-database scenarios
3. Aligns with `dbt_expectations` package conventions
4. Minimal overhead for single-database use

### Alternative: Direct Implementation

If you only target PostgreSQL:

```sql
{% macro valid_email(column_name) %}
    {{ column_name }} ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
{% endmacro %}
```

**Decision:** Keep dispatch pattern. It's already in place and follows community patterns.

---

## 5. Macro Testing

### Testing Strategies

1. **Unit Testing (dbt v1.8+)**
   ```yaml
   # tests/unit/test_validations.yml
   unit_tests:
     - name: test_valid_email_macro
       model: test_model
       given:
         - input: ref('test_data')
           rows:
             - {email: 'test@example.com'}
             - {email: 'invalid-email'}
       expect:
         rows:
           - {email: 'test@example.com', is_valid: true}
           - {email: 'invalid-email', is_valid: false}
   ```

2. **Compile-Time Testing**
   ```bash
   dbt compile
   # Inspect target/compiled/*/macros/*.sql
   ```

3. **Integration Testing via `dbt run-operation`**
   ```bash
   dbt run-operation test_valid_email --args '{"email": "test@example.com"}'
   ```

4. **Schema Tests That Consume Macros**
   ```yaml
   models:
     - name: customers
       columns:
         - name: email
           tests:
             - not_null
             - dbt_expectations.expect_column_values_to_match_regex:
                 regex: '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
   ```

### What to Test

| Macro Type | Test Approach |
|------------|---------------|
| Simple regex | Unit test with valid/invalid inputs |
| Complex logic | Integration test in model context |
| Cross-db adapter | Test on each adapter |
| Date helpers | Unit test edge cases (leap years, timezones) |

---

## 6. Macro Documentation Best Practices

### Header Documentation Block

```sql
{#
/*
  Macro: valid_email
  Purpose: Validates email format using regex pattern
  Created: 2026-04-08
  Author: Your Name
  
  Parameters:
    - column_name (required): Column containing email values
  
  Returns:
    SQL expression that evaluates to true/false
  
  Usage:
    {{ valid_email('email_column') }}
  
  Examples:
    -- Basic usage in model
    SELECT * FROM customers WHERE {{ valid_email('email') }}
    
    -- In dbt schema test
    columns:
      - name: email
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_match_regex:
              row_condition: "{{ valid_email('email') }}"
  
  Notes:
    - Uses RFC 5322 simplified pattern
    - Case-insensitive matching
*/
#}
{% macro valid_email(column_name) %}
    {{ return(adapter.dispatch('valid_email', 'my_project')(column_name)) }}
{% endmacro %}
```

### Documentation Checklist

- [ ] Macro name and purpose
- [ ] Parameter descriptions with types
- [ ] Return value description
- [ ] Usage examples (model, test, seed contexts)
- [ ] Version history or created date
- [ ] Dependencies (other macros, packages)
- [ ] Known limitations or edge cases

---

## 7. Recommended Actions for Current Project

### Immediate Fixes

1. **Remove Duplicate `valid_email`**
   - Delete `macros/data_quality/valid_email.sql`
   - Keep definition in `macros/data_quality/positive_amount.sql`

2. **Rename File for Clarity**
   - Rename to `validations.sql` (contains all validation macros)

### Proposed New Structure

```
macros/
├── _helpers.sql          # Generic helpers (if needed)
├── data_quality/
│   ├── _validations.sql  # All validation macros (rename positive_amount.sql)
│   └── _patterns.sql     # Reusable regex patterns
└── cross_db/
    └── _compatibility.sql # Adapter-specific overrides
```

### Consolidated `_validations.sql`

```sql
{#
/*
  Data Quality Validation Macros
  
  This file contains reusable validation macros for:
  - Email format validation
  - Numeric range validation
  - Null and positivity checks
  
  Usage: {{ macro_name('column_name') }}
*/
#}

{% macro valid_email(column_name) %}
    {{ return(adapter.dispatch('valid_email', 'marketing_analytics')(column_name)) }}
{% endmacro %}

{% macro default__valid_email(column_name) %}
    {{ column_name }} ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
{% endmacro %}

{% macro positive_amount(column_name) %}
    {{ return(adapter.dispatch('positive_amount', 'marketing_analytics')(column_name)) }}
{% endmacro %}

{% macro default__positive_amount(column_name) %}
    {{ column_name }} >= 0
{% endmacro %}

{% macro not_null_and_positive(column_name) %}
    {{ return(adapter.dispatch('not_null_and_positive', 'marketing_analytics')(column_name)) }}
{% endmacro %}

{% macro default__not_null_and_positive(column_name) %}
    {{ column_name }} IS NOT NULL AND {{ column_name }} > 0
{% endmacro %}
```

---

## 8. Summary of Recommendations

| Aspect | Recommendation |
|--------|----------------|
| **Directory Structure** | Organize by purpose (utils, data_quality, cross_db) |
| **File Organization** | Group related macros; single file if < 10 lines each |
| **Naming** | Use `is_`, `filter_`, `mutate_` prefixes; prefix with project name |
| **Dispatch Pattern** | Keep dispatch pattern for future-proofing |
| **Testing** | Use dbt unit tests (v1.8+) for complex macros |
| **Documentation** | Include header block with all parameters and examples |

### Implementation Checklist

- [ ] Consolidate `valid_email` to single file
- [ ] Rename `positive_amount.sql` to `validations.sql`
- [ ] Update dispatch namespace to `marketing_analytics`
- [ ] Add documentation headers
- [ ] Consider adding unit tests for validation macros
- [ ] Update any models referencing old file location
