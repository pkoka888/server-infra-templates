/*
  Macro: positive_amount
  Purpose: Validates that a column contains non-negative values (>= 0)
  Usage: {{ positive_amount('column_name') }}
  Severity: Error
*/
{% macro positive_amount(column_name) %}
{{ return(adapter.dispatch('positive_amount', 'dbt_expectations')(column_name)) }}
{% endmacro %}

{% macro default__positive_amount(column_name) %}
    {{ column_name }} >= 0
{% endmacro %}

/*
  Macro: valid_email
  Purpose: Validates email format using regex pattern
  Pattern: Standard email validation (local@domain.tld)
  Usage: {{ valid_email('column_name') }}
  Severity: Error
*/
{% macro valid_email(column_name) %}
{{ return(adapter.dispatch('valid_email', 'dbt_expectations')(column_name)) }}
{% endmacro %}

{% macro default__valid_email(column_name) %}
    {{ column_name }} ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
{% endmacro %}

/*
  Macro: not_null_and_positive
  Purpose: Validates that a column is not null and contains positive values
  Usage: {{ not_null_and_positive('column_name') }}
  Severity: Error
*/
{% macro not_null_and_positive(column_name) %}
{{ return(adapter.dispatch('not_null_and_positive', 'dbt_expectations')(column_name)) }}
{% endmacro %}

{% macro default__not_null_and_positive(column_name) %}
    {{ column_name }} IS NOT NULL AND {{ column_name }} > 0
{% endmacro %}
