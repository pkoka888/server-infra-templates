# Great Expectations - Comprehensive Study

## Overview
**Date**: 2026-04-08  
**Researcher**: Sisyphus AI Agent  
**Scope**: Great Expectations Core, Data Quality Framework  
**Purpose**: Evaluate Great Expectations for data quality validation in marketing analytics pipelines

---

## Repository Information

| Property | Value |
|----------|-------|
| **Repository** | [great-expectations/great_expectations](https://github.com/great-expectations/great_expectations) |
| **Website** | https://greatexpectations.io/ |
| **License** | Apache-2.0 |
| **Stars** | 11,400+ |
| **Forks** | 1,700+ |
| **Language** | Python (99.4%) |
| **Latest Version** | 1.15.2 (April 2026) |
| **Founded** | 2017 |
| **Maintainer** | Great Expectations (company) |

---

## What is Great Expectations?

Great Expectations (GX) is an open-source Python framework for data validation, documentation, and profiling. It helps data teams eliminate pipeline debt by validating, documenting, and profiling data.

### Core Philosophy
- **Unit tests for data**: Apply software testing practices to data
- **Documentation as code**: Auto-generate data docs from expectations
- **Collaborative**: Share expectations across teams
- **Extensible**: Custom expectations for domain-specific needs

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Great Expectations Architecture                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Data       │───▶│ Expectations │───▶│  Validation  │      │
│  │   Source     │    │   (Tests)    │    │   Results    │      │
│  └──────────────┘    └──────────────┘    └──────┬───────┘      │
│                                                  │              │
│                           ┌──────────────────────┘              │
│                           ▼                                     │
│                  ┌─────────────────┐  ┌──────────────┐         │
│                  │  Documentation  │  │   Actions    │         │
│                  │  (Data Docs)    │  │  (Alerts)    │         │
│                  └─────────────────┘  └──────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **Expectations** | Declarative assertions about data |
| **Validators** | Execute expectations against data |
| **Checkpoints** | Run suites of expectations |
| **Data Docs** | Auto-generated documentation |
| **Stores** | Metadata storage (expectations, validations, checkpoints) |

---

## Key Features

### 1. Expectations (Data Assertions)

```python
import great_expectations as gx

# Create context
context = gx.get_context()

# Connect to data source
datasource = context.data_sources.add_postgres(
    name="warehouse",
    connection_string="postgresql://..."
)

# Define expectations
suite = context.suites.add(
    gx.ExpectationSuite(name="orders_suite")
)

# Column should not be null
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(
        column="order_id"
    )
)

# Column values should be unique
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeUnique(
        column="order_id"
    )
)

# Column values should be between
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="total_amount",
        min_value=0,
        max_value=100000
    )
)

# Column values should match regex
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToMatchRegex(
        column="email",
        regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )
)
```

### 2. Built-in Expectation Types

| Category | Examples |
|----------|----------|
| **Table Level** | `expect_table_row_count_to_be_between`, `expect_table_columns_to_match_set` |
| **Missingness** | `expect_column_values_to_not_be_null`, `expect_column_proportion_of_unique_values_to_be_between` |
| **Ranges** | `expect_column_values_to_be_between`, `expect_column_mean_to_be_between` |
| **Sets** | `expect_column_values_to_be_in_set`, `expect_column_distinct_values_to_equal_set` |
| **Types** | `expect_column_values_to_be_of_type`, `expect_column_values_to_be_dateutil_parseable` |
| **Regex** | `expect_column_values_to_match_regex`, `expect_column_values_to_not_match_regex` |
| **Statistical** | `expect_column_stdev_to_be_between`, `expect_column_kl_divergence_to_be_less_than` |
| **Relational** | `expect_compound_columns_to_be_unique`, `expect_select_column_values_to_be_unique_within_record` |

### 3. Validation Results

```python
# Run validation
validation_results = context.run_checkpoint(
    checkpoint_name="orders_checkpoint"
)

# Check success
if validation_results.success:
    print("✅ All data quality checks passed")
else:
    print("❌ Some checks failed")
    
    for result in validation_results.results:
        if not result.success:
            print(f"Failed: {result.expectation_config.expectation_type}")
            print(f"Unexpected count: {result.result.get('unexpected_count', 'N/A')}")
```

### 4. Checkpoints (Scheduled Validation)

```python
# Define checkpoint
checkpoint = context.add_checkpoint(
    name="daily_orders_checkpoint",
    validations=[
        {
            "batch_request": {
                "datasource_name": "warehouse",
                "data_asset_name": "orders"
            },
            "expectation_suite_name": "orders_suite"
        }
    ],
    action_list=[
        {
            "name": "store_validation_result",
            "action": {"class_name": "StoreValidationResultAction"}
        },
        {
            "name": "update_data_docs",
            "action": {"class_name": "UpdateDataDocsAction"}
        },
        {
            "name": "send_slack_notification",
            "action": {
                "class_name": "SlackNotificationAction",
                "slack_webhook": "${SLACK_WEBHOOK_URL}",
                "notify_on": "failure",
                "renderer": {
                    "module_name": "great_expectations.render.renderer.slack_renderer",
                    "class_name": "SlackRenderer"
                }
            }
        }
    ]
)
```

### 5. Data Docs

```python
# Build documentation
context.build_data_docs()

# Open in browser
context.open_data_docs()
```

Generated docs include:
- **Expectation Suites**: All defined expectations
- **Validation Results**: Pass/fail history
- **Profiling Results**: Data statistics and distributions

---

## Marketing Analytics Use Cases

### Order Data Quality Suite
```python
# great_expectations/expectations/orders_suite.json
{
  "expectation_suite_name": "orders_suite",
  "expectations": [
    {
      "expectation_type": "expect_table_row_count_to_be_between",
      "kwargs": {
        "min_value": 100,
        "max_value": 1000000
      },
      "meta": {
        "notes": "Orders table should have 100-1M rows"
      }
    },
    {
      "expectation_type": "expect_column_values_to_not_be_null",
      "kwargs": {
        "column": "order_id"
      }
    },
    {
      "expectation_type": "expect_column_values_to_be_unique",
      "kwargs": {
        "column": "order_id"
      }
    },
    {
      "expectation_type": "expect_column_values_to_be_between",
      "kwargs": {
        "column": "total_paid_amount",
        "min_value": 0,
        "max_value": 50000,
        "mostly": 0.99
      },
      "meta": {
        "notes": "99% of orders should be between $0-$50k"
      }
    },
    {
      "expectation_type": "expect_column_values_to_be_in_set",
      "kwargs": {
        "column": "order_status",
        "value_set": ["pending", "processing", "completed", "cancelled", "refunded"]
      }
    },
    {
      "expectation_type": "expect_column_values_to_be_dateutil_parseable",
      "kwargs": {
        "column": "created_at"
      }
    },
    {
      "expectation_type": "expect_column_values_to_be_between",
      "kwargs": {
        "column": "created_at",
        "min_value": "2024-01-01",
        "max_value": "2026-12-31",
        "parse_strings_as_datetimes": true
      }
    }
  ],
  "meta": {
    "version": "1.0.0",
    "description": "Data quality suite for orders table"
  }
}
```

### Marketing Performance Validation
```python
# Validating marketing data freshness
from datetime import datetime, timedelta

def validate_marketing_freshness():
    """Ensure marketing data is not stale"""
    
    suite = context.suites.add(
        gx.ExpectationSuite(name="marketing_freshness")
    )
    
    # Data should be from last 24 hours
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="date",
            min_value=yesterday,
            max_value=datetime.now().strftime("%Y-%m-%d"),
            parse_strings_as_datetimes=True
        )
    )
    
    # ROAS should be within reasonable bounds
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="roas",
            min_value=0,
            max_value=100
        )
    )
    
    return suite
```

### Custom Expectations for Marketing
```python
# Custom expectation for ROAS validation
from great_expectations.expectations import RegexBasedColumnMapExpectation

class ExpectCampaignRoasToBeProfitable(RegexBasedColumnMapExpectation):
    """Expect campaign ROAS to be above 1.0 (profitable)"""
    
    regex_camel_name = "CampaignRoasToBeProfitable"
    regex_snake_name = "campaign_roas_to_be_profitable"
    
    def validate_configuration(self, configuration):
        super().validate_configuration(configuration)
        # Additional validation logic
    
    def _validate(
        self,
        configuration,
        metrics,
        runtime_configuration=None,
        execution_engine=None
    ):
        # Custom validation logic
        pass

# Register custom expectation
context.plugins_directory = "./custom_expectations"
```

### Data Drift Detection
```python
# Detect changes in data distribution over time
def detect_data_drift():
    """Compare current data distribution to historical"""
    
    suite = context.suites.add(
        gx.ExpectationSuite(name="data_drift")
    )
    
    # KL divergence for order amounts
    suite.add_expectation(
        gx.expectations.ExpectColumnKlDivergenceToBeLessThan(
            column="total_paid_amount",
            partition_object={
                "bins": [0, 50, 100, 200, 500, 1000, 5000],
                "weights": [0.3, 0.25, 0.2, 0.15, 0.08, 0.02]
            },
            threshold=0.1
        )
    )
    
    # Check for new values in categorical columns
    suite.add_expectation(
        gx.expectations.ExpectColumnDistinctValuesToEqualSet(
            column="order_status",
            value_set=["pending", "processing", "completed", "cancelled", "refunded"]
        )
    )
    
    return suite
```

---

## Integration Patterns

### With dbt
```python
# Run Great Expectations after dbt models
from prefect import flow, task
from prefect.tasks.great_expectations import RunGreatExpectationsValidation

@task
def run_gx_checkpoint(checkpoint_name: str):
    """Run Great Expectations checkpoint"""
    validation = RunGreatExpectationsValidation(
        checkpoint_name=checkpoint_name,
        context_root_dir="./great_expectations"
    )
    return validation.run()

@flow
def dbt_with_validation():
    # Run dbt
    dbt_run()
    
    # Validate output
    result = run_gx_checkpoint("post_dbt_validation")
    
    if not result.success:
        raise Exception("Data validation failed")
```

### With Prefect
```python
from prefect import flow, task
from prefect.blocks.notifications import SlackWebhook
import great_expectations as gx

@task
def validate_orders():
    """Validate orders data quality"""
    context = gx.get_context()
    
    results = context.run_checkpoint(
        checkpoint_name="orders_checkpoint"
    )
    
    return {
        "success": results.success,
        "statistics": results.statistics,
        "evaluated_expectations": results.statistics["evaluated_expectations"],
        "successful_expectations": results.statistics["successful_expectations"]
    }

@task
async def send_validation_alert(results: dict):
    """Send Slack alert on validation failure"""
    if not results["success"]:
        slack = await SlackWebhook.load("data-quality-alerts")
        await slack.notify(
            f"🚨 Data Quality Alert\n"
            f"Passed: {results['successful_expectations']}/{results['evaluated_expectations']}"
        )

@flow
def data_quality_pipeline():
    results = validate_orders()
    send_validation_alert(results)
```

### With Airbyte
```python
# Validate data after Airbyte sync
@task
def validate_airbyte_output(connection_name: str):
    """Validate data loaded by Airbyte"""
    context = gx.get_context()
    
    # Map connection to checkpoint
    checkpoint_map = {
        "ga4": "ga4_validation",
        "facebook": "facebook_validation",
        "prestashop": "prestashop_validation"
    }
    
    checkpoint = checkpoint_map.get(connection_name)
    if checkpoint:
        results = context.run_checkpoint(checkpoint_name=checkpoint)
        return results.success
    
    return True
```

---

## Deployment Options

### Open Source (Self-Hosted)
```bash
# Install
pip install great_expectations

# Initialize project
gx init

# Start using
context = gx.get_context()
```

**Pros:**
- Free
- Full control
- Apache-2.0 license

**Cons:**
- Self-managed
- No built-in UI (generate static docs)

### GX Cloud (Beta)
```python
# Use GX Cloud
import great_expectations as gx

context = gx.get_context(mode="cloud")
```

**Features:**
- Managed UI
- Collaboration features
- Cloud storage for expectations

**Pricing:**
- Free tier available
- Enterprise pricing TBD

---

## Strengths & Weaknesses

### Strengths
| Strength | Description |
|----------|-------------|
| **Comprehensive expectations** | 50+ built-in expectation types |
| **Auto-documentation** | Generates data docs automatically |
| **Extensible** | Custom expectations for domain needs |
| **Integration-friendly** | Works with dbt, Prefect, Airflow |
| **Apache-2.0** | Fully open source |
| **Data profiling** | Auto-generate expectations from data |
| **Team collaboration** | Share suites across teams |

### Weaknesses
| Weakness | Description |
|----------|-------------|
| **Not a pipeline tool** | Only validates, doesn't orchestrate |
| **Learning curve** | Configuration can be complex |
| **Storage overhead** | Stores validation history |
| **Performance** | Can be slow on very large datasets |
| **Documentation gaps** | Some advanced features unclear |

---

## Comparison with Alternatives

| Feature | Great Expectations | Soda | Deequ | dbt Tests |
|---------|-------------------|------|-------|-----------|
| **License** | Apache-2.0 | Commercial | Apache-2.0 | Apache-2.0 |
| **Self-hosted** | ✅ | ❌ | ✅ | ✅ |
| **SQL-based** | ❌ (Python) | ✅ | ❌ (Scala) | ✅ |
| **Expectation library** | 50+ | Growing | Moderate | Basic |
| **Data docs** | ✅ | ✅ | ❌ | ✅ |
| **Custom expectations** | ✅ | ✅ | ✅ | Limited |
| **Profiling** | ✅ | ✅ | ✅ | ❌ |
| **Lineage** | ❌ | ✅ | ❌ | ✅ |

### When to Choose Great Expectations
- Need comprehensive expectation library
- Want auto-generated documentation
- Require custom domain-specific validations
- Prefer Python-based configuration

### When to Choose Soda
- Want SQL-first approach
- Prefer SaaS with managed UI
- Need collaboration features
- Want quick setup

### When to Choose Deequ
- On AWS with Spark
- Need Scala-based validation
- Processing very large datasets
- Part of AWS analytics stack

---

## Project Structure

```
great_expectations/
├── checkpoints/
│   ├── orders_checkpoint.yml
│   └── marketing_checkpoint.yml
├── expectations/
│   ├── orders_suite.json
│   ├── customers_suite.json
│   └── .ge_store_backend_id
├── plugins/
│   └── custom_expectations/
│       └── marketing_expectations.py
├── profilers/
├── uncommitted/
│   ├── validations/
│   └── data_docs/
├── great_expectations.yml
└── .gitignore
```

---

## Implementation Checklist

### Phase 1: Setup
- [ ] Install Great Expectations
- [ ] Initialize project
- [ ] Configure data sources
- [ ] Set up stores

### Phase 2: Development
- [ ] Create expectation suites
- [ ] Define critical data quality rules
- [ ] Set up checkpoints
- [ ] Configure notifications

### Phase 3: Integration
- [ ] Integrate with dbt
- [ ] Add to Prefect flows
- [ ] Set up post-Airbyte validation
- [ ] Configure alerting

### Phase 4: Production
- [ ] Schedule regular validations
- [ ] Monitor validation history
- [ ] Document data quality SLAs
- [ ] Train team on data docs

---

## Conclusion

**Recommendation**: **Recommended** for marketing analytics

**Best Fit**:
- Need comprehensive data validation
- Want auto-generated documentation
- Require custom domain-specific tests
- Value open source (Apache-2.0)

**Consider Alternatives**:
- Want SQL-first → Soda
- AWS + Spark → Deequ
- Simple tests only → dbt tests

---

## Resources

- [Official Documentation](https://docs.greatexpectations.io/)
- [Expectation Gallery](https://greatexpectations.io/expectations/)
- [Community Forum](https://discuss.greatexpectations.io/)
- [GitHub Repository](https://github.com/great-expectations/great_expectations)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-08 | Initial study |
