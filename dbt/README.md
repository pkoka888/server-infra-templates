# Marketing Analytics dbt Project

## Overview

This dbt project transforms marketing data from dlt pipelines into analytics-ready models.

## Structure

```
dbt/
├── models/
│   ├── staging/          # Raw data ingestion
│   │   ├── ga4/         # Google Analytics 4
│   │   ├── facebook/    # Facebook Ads
│   │   └── prestashop/  # E-commerce data
│   └── marts/           # Business logic
│       ├── core/        # Core business entities
│       └── marketing/   # Marketing-specific models
├── macros/              # Reusable SQL macros
├── seeds/               # Static reference data
└── tests/               # Custom tests
```

## Configuration

Set the client ID via vars:

```bash
dbt run --vars '{"client_id": "client1"}'
```

Or set in `dbt_project.yml`:

```yaml
vars:
  client_id: 'client1'
```

## Installation

```bash
cd dbt
dbt deps
dbt debug
```

## Running Models

```bash
# Run all models
dbt run

# Run specific model
dbt run --select stg_prestashop__orders

# Run with different client
dbt run --vars '{"client_id": "client2"}'
```
