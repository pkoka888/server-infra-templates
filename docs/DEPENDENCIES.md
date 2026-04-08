# Dependencies Map

## Service Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           METABASE                                          │
│                           Port: 8096                                         │
│                           Image: metabase:v0.59.5                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ MB_DB_HOST=metabase-db
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         METABASE-DB                                          │
│                         Port: 5432 (internal)                               │
│                         Image: postgres:17-alpine                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Databases                                     │   │
│  │  - metabase (Metabase metadata)                                     │   │
│  │  - ga4_client1 (GA4 data)                                           │   │
│  │  - fbads_client1 (Facebook Ads data)                               │   │
│  │  - prestashop_client1 (PrestaShop data)                           │   │
│  │  - staging (dbt staging models)                                    │   │
│  │  - marts (dbt mart models)                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         PREFECT-SERVER                                       │
│                         Port: 4200 (internal)                               │
│                         Image: prefecthq/prefect:3-latest                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ PREFECT_API_URL
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PREFECT-WORKER                                       │
│                         Image: prefecthq/prefect:3-latest                    │
│                         Work Pool: docker-pool                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Uses Docker socket
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOCKER SOCKET                                      │
│                         /var/run/docker.sock                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                      │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  GA4 API    │  │  FB Ads API │  │  G Ads API  │  │ PrestaShop  │      │
│  │             │  │             │  │             │  │   REST API   │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│         │                │                │                │              │
└─────────┼────────────────┼────────────────┼────────────────┼──────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        dlt PIPELINE (scripts/pipeline.py)                    │
│                                                                             │
│  python scripts/pipeline.py --source ga4 --client client1                   │
│                                                                             │
│  Dependencies:                                                               │
│  - dlt[postgres]                                                           │
│  - dlt-hub/dlt-verified-sources                                            │
│  - google-analytics-data                                                   │
│  - facebook-business                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Loads data to
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       POSTGRESQL WAREHOUSE                                  │
│                                                                             │
│  Raw Schemas:                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │ga4_client1  │  │fbads_client1│  │prestashop  │                         │
│  │             │  │             │  │ _client1    │                         │
│  │ - events    │  │ - ads       │  │             │                         │
│  │ - traffic   │  │ - campaigns │  │ - orders    │                         │
│  │ - sessions  │  │ - insights  │  │ - customers │                         │
│  └─────────────┘  └─────────────┘  │ - products │                         │
│                                      └─────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ dbt reads from
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          dbt TRANSFORMATIONS                                 │
│                                                                             │
│  Staging Layer (views):                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ stg_ga4__events, stg_ga4__traffic                                    │   │
│  │ stg_facebook__ads, stg_facebook__campaigns                            │   │
│  │ stg_prestashop__orders, stg_prestashop__customers                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│                                      ▼                                       │
│  Mart Layer (tables):                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ fct_marketing_performance (ROAS, CTR, CPC metrics)                  │   │
│  │ dim_customers (customer dimensions)                                  │   │
│  │ dim_campaigns (campaign dimensions)                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Dependencies:                                                               │
│  - dbt-core                                                                │
│  - dbt-postgres                                                            │
│  - dbt-labs/dbt_utils                                                     │
│  - metaplane/dbt_expectations                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Reads from
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         METABASE (Visualization)                             │
│                                                                             │
│  Dashboards:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Marketing Performance Dashboard                                       │   │
│  │ - Channel comparison                                                 │   │
│  │ - ROAS by campaign                                                   │   │
│  │ - Spend vs Revenue trend                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ E-commerce Dashboard                                                 │   │
│  │ - Orders trend                                                       │   │
│  │ - Customer metrics                                                    │   │
│  │ - Product performance                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Orchestration Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PREFECT ORCHESTRATION                               │
│                                                                             │
│  marketing_analytics_pipeline                                                │
│  │                                                                          │
│  ├─── Task: run_dlt_sync (GA4) ─────────────────────────────────────────   │
│  │    └── Runs: python scripts/pipeline.py --source ga4 --client {id}      │
│  │                                                                          │
│  ├─── Task: run_dlt_sync (Facebook) ──────────────────────────────────    │
│  │    └── Runs: python scripts/pipeline.py --source fbads --client {id}    │
│  │                                                                          │
│  ├─── Task: run_dlt_sync (PrestaShop) ───────────────────────────────    │
│  │    └── Runs: python scripts/pipeline.py --source prestashop --client {id}│
│  │                                                                          │
│  └─── Task: run_dbt_models ────────────────────────────────────────────    │
│       └── Runs: dbt run --vars '{"client_id": "{id}"}'                     │
│                                                                             │
│       └─── Task: run_dbt_tests ────────────────────────────────────────    │
│            └── Runs: dbt test                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Docker Compose Dependencies

```yaml
services:
  metabase:
    depends_on:
      metabase-db:
        condition: service_healthy
    environment:
      - MB_DB_HOST=metabase-db

  metabase-db:
    # No depends_on - base service
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${MB_DB_USER} -d metabase"]

  dbt:
    depends_on:
      metabase-db:
        condition: service_healthy
    volumes:
      - ./dbt:/usr/app/dbt
    environment:
      - DBT_PROFILES_DIR=/usr/app/dbt

  prefect-server:
    depends_on:
      - metabase-db  # Optional: shares state
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4200/api/health"]

  prefect-worker:
    depends_on:
      prefect-server:
        condition: service_healthy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

## Python Package Dependencies

```
scripts/pipeline.py
├── dlt
│   ├── dlt[postgres]
│   └── dlt_hub.dlt_verified_sources
│       ├── google_analytics
│       ├── google_ads
│       └── facebook_ads
└── google-analytics-data
    └── google-auth

prefect/flows/marketing_pipeline.py
├── prefect>=3.0.0
├── prefect-dbt>=0.5.0
└── dbt (via subprocess)

dbt project
├── dbt-core
├── dbt-postgres
├── dbt-labs/dbt_utils
└── metaplane/dbt_expectations
```

## Environment Variable Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        REQUIRED ENVIRONMENT VARIABLES                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  POSTGRES_PASSWORD ──────────────────────┬──▶ metabase-db                  │
│  (Used by: metabase, dbt)                │     metabase                    │
│                                           │     dbt (profiles.yml)          │
├───────────────────────────────────────────┼─────────────────────────────────┤
│                                           │                                  │
│  GA4_* ──────────────────────────────────┼──▶ dlt pipeline                 │
│  (GA4_PROPERTY_ID, GA4_CLIENT_*,          │     scripts/pipeline.py         │
│   GA4_REFRESH_TOKEN)                       │                                  │
│                                           │                                  │
├───────────────────────────────────────────┼─────────────────────────────────┤
│                                           │                                  │
│  FB_* ────────────────────────────────────┼──▶ dlt pipeline                 │
│  (FB_AD_ACCOUNT_ID, FB_ACCESS_TOKEN)      │     scripts/pipeline.py         │
│                                           │                                  │
├───────────────────────────────────────────┼─────────────────────────────────┤
│                                           │                                  │
│  PS_* ────────────────────────────────────┼──▶ dlt pipeline                 │
│  (PS_SHOP_URL, PS_API_KEY)               │     scripts/pipeline.py         │
│                                           │                                  │
├───────────────────────────────────────────┼─────────────────────────────────┤
│                                           │                                  │
│  PREFECT_API_URL ─────────────────────────┼──▶ prefect-worker               │
│  (http://prefect-server:4200/api)        │                                  │
│                                           │                                  │
└───────────────────────────────────────────┴─────────────────────────────────┘
```

## Network Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NETWORK: metabase-net                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Services Connected:                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  metabase   │  │ metabase-db │  │     dbt     │  │prefect-srv │      │
│  │   :3000    │  │    :5432    │  │             │  │    :4200    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│        │                │                │                │                │
│        └────────────────┴────────────────┴────────────────┘                │
│                              Internal communication                           │
└─────────────────────────────────────────────────────────────────────────────┘

External Access:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  GA4 API   │     │  FB Ads API │     │ PrestaShop │     │   Users     │
│googleapis.com│   │ graph.facebook│   │  REST API  │     │  Browser   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      └───────────────────┴───────────────────┴───────────────────┘
                          External APIs & Users
```
