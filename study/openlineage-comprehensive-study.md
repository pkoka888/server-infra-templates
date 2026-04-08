# OpenLineage - Comprehensive Study

## Overview
**Date**: 2026-04-08  
**Researcher**: Sisyphus AI Agent  
**Scope**: OpenLineage Core, Marquez, Data Lineage  
**Purpose**: Evaluate OpenLineage for data lineage tracking in marketing analytics pipelines

---

## Repository Information

| Property | Value |
|----------|-------|
| **Repository** | [OpenLineage/OpenLineage](https://github.com/OpenLineage/OpenLineage) |
| **Website** | https://openlineage.io/ |
| **License** | Apache-2.0 |
| **Stars** | 2,400+ |
| **Forks** | 448+ |
| **Language** | Java (65.8%), Python |
| **Latest Version** | 1.45.0 (March 2026) |
| **Founded** | 2020 |
| **Maintainer** | LF AI & Data Foundation |

---

## What is OpenLineage?

OpenLineage is an open standard for metadata and lineage collection. It standardizes the definition of data lineage by introducing a consistent nomenclature to define job, run, and dataset entities.

### Core Philosophy
- **Standardization**: Common language for lineage across tools
- **Open standard**: Vendor-neutral, community-driven
- **Metadata collection**: Automatic instrumentation
- **Extensible**: Facets for custom metadata

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   OpenLineage Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Data Tools                     OpenLineage                      │
│  ┌──────────┐  ┌──────────┐     ┌──────────┐  ┌──────────┐     │
│  │  Airflow │  │   Spark  │     │  Client  │  │ Marquez  │     │
│  │   dbt    │  │  Flink   │────▶│  Library │─▶│ Backend  │     │
│  │ Prefect  │  │   ...    │     │          │  │          │     │
│  └──────────┘  └──────────┘     └──────────┘  └────┬─────┘     │
│                                                     │          │
│                                                     ▼          │
│                                            ┌──────────────┐   │
│                                            │ Lineage Graph│   │
│                                            │   Storage    │   │
│                                            └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Core Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Job** | Process that transforms data | dbt model, Airflow DAG |
| **Run** | Instance of a job execution | Single dbt run |
| **Dataset** | Collection of data | Table, file, stream |
| **Facet** | Additional metadata | Schema, ownership, quality |

---

## Key Features

### 1. Standardized Lineage Model

```json
{
  "eventTime": "2026-04-08T10:00:00Z",
  "producer": "https://github.com/OpenLineage/OpenLineage/blob/v1.45.0/client/python",
  "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json",
  "run": {
    "runId": "3f5c8c9a-1234-5678-9abc-def012345678"
  },
  "job": {
    "namespace": "marketing-analytics",
    "name": "fct_orders"
  },
  "inputs": [
    {
      "namespace": "postgresql://warehouse",
      "name": "staging.orders",
      "facets": {
        "schema": {
          "fields": [
            {"name": "order_id", "type": "INTEGER"},
            {"name": "total", "type": "DECIMAL"}
          ]
        }
      }
    }
  ],
  "outputs": [
    {
      "namespace": "postgresql://warehouse",
      "name": "marts.fct_orders",
      "facets": {
        "schema": {
          "fields": [
            {"name": "order_id", "type": "INTEGER"},
            {"name": "total", "type": "DECIMAL"},
            {"name": "customer_id", "type": "INTEGER"}
          ]
        }
      }
    }
  ]
}
```

### 2. Integration Libraries

| Tool | Integration Method |
|------|-------------------|
| **dbt** | dbt OpenLineage adapter |
| **Airflow** | Airflow OpenLineage provider |
| **Spark** | SparkListener integration |
| **Prefect** | OpenLineage block |
| **Flink** | Flink job listener |

### 3. Facets (Metadata Extensions)

```json
{
  "facets": {
    "documentation": {
      "description": "Orders fact table with revenue metrics"
    },
    "ownership": {
      "owners": [
        {"name": "data-team", "type": "team"}
      ]
    },
    "dataQuality": {
      "assertions": [
        {
          "assertion": "order_id_not_null",
          "success": true
        }
      ]
    },
    "schema": {
      "fields": [...]
    }
  }
}
```

---

## Marketing Analytics Use Cases

### Tracking dbt Transformations
```python
# dbt integration automatically captures lineage
# dbt_project.yml
vars:
  openlineage_url: "http://marquez:5000"

# Models are automatically tracked:
# stg_orders.sql -> int_orders_enriched.sql -> fct_orders.sql
```

### Visualizing Marketing Data Flow
```
┌─────────────────────────────────────────────────────────────┐
│                   Marketing Data Lineage                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Airbyte                        dbt                         │
│  ┌──────────┐                  ┌──────────┐                │
│  │  GA4     │──▶ ga4_raw      │ staging  │──▶ stg_ga4    │
│  │ Facebook │──▶ facebook_raw  │   .sql   │               │
│  │Prestashop│──▶ ps_raw       └────┬─────┘               │
│  └──────────┘                       │                      │
│                                     ▼                      │
│                              ┌──────────┐                 │
│                              │ int_*.sql│                 │
│                              └────┬─────┘                 │
│                                   │                        │
│                                   ▼                        │
│                            ┌──────────┐                   │
│                            │ fct_*.sql│──▶ Dashboard      │
│                            │ dim_*.sql│                   │
│                            └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Column-Level Lineage
```python
# Track transformations at column level
{
  "inputs": [
    {
      "namespace": "warehouse",
      "name": "staging.orders",
      "facets": {
        "columnLineage": {
          "fields": {
            "total_paid": {
              "inputFields": [
                {
                  "namespace": "warehouse",
                  "name": "staging.orders",
                  "field": "total_cents"
                }
              ],
              "transformationType": "DIVIDE",
              "transformationDescription": "total_cents / 100"
            }
          }
        }
      }
    }
  ]
}
```

### Data Impact Analysis
```python
# Find downstream impact of changes
def find_downstream_tables(table_name: str):
    """Find all tables dependent on given table"""
    # Query Marquez API
    response = requests.get(
        f"{MARQUEZ_URL}/api/v1/namespaces/marketing/tables/{table_name}/downstream"
    )
    return response.json()

# Example: What breaks if we change ga4_raw.events?
affected = find_downstream_tables("ga4_raw.events")
# Returns: [stg_ga4__events, int__customer_touchpoints, fct_marketing_performance]
```

---

## Integration Patterns

### With dbt
```yaml
# packages.yml
packages:
  - package: OpenLineage/OpenLineage
    version: 1.0.0

# dbt_project.yml
models:
  +openlineage_enabled: true

vars:
  openlineage_url: "http://marquez:5000"
```

### With Airflow
```python
from airflow.providers.openlineage.extractors import TaskMetadata
from openlineage.client import OpenLineageClient

# Automatic integration via provider
# lineage is emitted for each task
```

### With Prefect
```python
from prefect import flow
from prefect_openlineage.blocks import OpenLineageBlock

@flow
def tracked_flow():
    block = OpenLineageBlock.load("marquez")
    
    with block.track():
        # All data operations tracked
        extract_data()
        transform_data()
        load_data()
```

### With Marquez
```yaml
# docker-compose.yml
version: '3'
services:
  marquez:
    image: marquezproject/marquez:latest
    ports:
      - "5000:5000"
      - "5001:5001"
    environment:
      - MARQUEZ_DB=postgres
    depends_on:
      - postgres
  
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: marquez
      POSTGRES_PASSWORD: marquez
```

---

## Marquez (Reference Implementation)

Marquez is the reference implementation of an OpenLineage backend.

### Features
- **Lineage Graph**: Visualize data dependencies
- **Dataset Metadata**: Schema, ownership, tags
- **Job Runs**: Execution history and statistics
- **Search**: Find datasets and jobs

### API Example
```bash
# Get dataset lineage
curl http://marquez:5000/api/v1/namespaces/marketing/datasets/orders/lineage

# Get job runs
curl http://marquez:5000/api/v1/namespaces/marketing/jobs/fct_orders/runs
```

---

## Deployment Options

### Self-Hosted (Marquez)
```bash
# Run with Docker
docker run -p 5000:5000 -p 5001:5001 marquezproject/marquez

# Or use Helm
helm repo add marquez https://marquezproject.github.io/marquez
helm install marquez marquez/marquez
```

### Integration-Only (No Backend)
```python
# Just emit lineage without storing
from openlineage.client import OpenLineageClient

client = OpenLineageClient(url="http://my-custom-backend:5000")
client.emit(event)
```

---

## Strengths & Weaknesses

### Strengths
| Strength | Description |
|----------|-------------|
| **Open standard** | Vendor-neutral, community-driven |
| **Wide integration** | Works with major data tools |
| **LF AI & Data** | Backed by Linux Foundation |
| **Extensible** | Facets for custom metadata |
| **Apache-2.0** | Fully open source |
| **Column lineage** | Track transformations at column level |

### Weaknesses
| Weakness | Description |
|----------|-------------|
| **Not standalone** | Requires other tools for collection |
| **Marquez complexity** | Can be complex to operate |
| **Adoption** | Still gaining traction |
| **Documentation** | Limited examples for custom facets |
| **Visualization** | Basic UI in Marquez |

---

## Comparison with Alternatives

| Feature | OpenLineage | DataHub | Amundsen | Monte Carlo |
|---------|-------------|---------|----------|-------------|
| **License** | Apache-2.0 | Apache-2.0 | Apache-2.0 | Commercial |
| **Self-hosted** | ✅ | ✅ | ✅ | ❌ |
| **Open standard** | ✅ | ❌ | ❌ | ❌ |
| **Lineage only** | ✅ | ❌ (full catalog) | ❌ (discovery) | ❌ (observability) |
| **Column lineage** | ✅ | ✅ | ❌ | ✅ |
| **Cost** | Free | Free | Free | $$$ |
| **Complexity** | Medium | High | Medium | N/A |

### When to Choose OpenLineage
- Need vendor-neutral lineage standard
- Already using compatible tools (dbt, Airflow, Spark)
- Want open standard backed by foundation
- Need column-level lineage

### When to Choose DataHub
- Need full data catalog
- Want metadata management
- Require complex search
- Need rich UI

### When to Choose Amundsen
- Focus on data discovery
- Want people-focused metadata
- Need simple setup

---

## Implementation Checklist

### Phase 1: Setup
- [ ] Deploy Marquez (or choose backend)
- [ ] Configure OpenLineage client
- [ ] Set up namespaces

### Phase 2: Integration
- [ ] Enable dbt OpenLineage
- [ ] Configure Airflow provider
- [ ] Add Prefect integration
- [ ] Test lineage emission

### Phase 3: Usage
- [ ] Explore lineage graph
- [ ] Document data dependencies
- [ ] Set up impact analysis
- [ ] Train team on lineage

---

## Conclusion

**Recommendation**: **Recommended** for marketing analytics

**Best Fit**:
- Need vendor-neutral lineage standard
- Use compatible tools (dbt, Airflow)
- Want open standard backed by foundation
- Need column-level lineage tracking

**Consider Alternatives**:
- Need full data catalog → DataHub
- Want data observability → Monte Carlo
- Simple lineage needs → Tool-native lineage

---

## Resources

- [Official Documentation](https://openlineage.io/)
- [Marquez Project](https://marquezproject.ai/)
- [OpenLineage GitHub](https://github.com/OpenLineage/OpenLineage)
- [Specification](https://openlineage.io/spec/)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-08 | Initial study |
