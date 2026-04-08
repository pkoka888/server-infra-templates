# Research Document: Data Pipeline Implementation Patterns

## Executive Summary

This document consolidates research findings for four critical work items in the Metabase/Prefect data pipeline project. The research covers industry best practices, implementation patterns, concrete code examples, and authoritative references for:

1. **e2e-verification**: End-to-end pipeline testing with real API credentials
2. **dashboard-phase1**: Marketing Performance executive dashboard in Metabase
3. **scheduling-wiring**: Prefect flow scheduling with crontab integration
4. **phase2-planning**: Attribution modeling approaches and data requirements

---

## 1. E2E Verification

### 1.1 Best Practices

**Industry Standards**
- Use pytest as the standard testing framework for Python data pipelines
- Implement fixtures for test isolation and resource management
- Apply the "Given-When-Then" pattern for test clarity
- Maintain separate test environments from production

**Security Best Practices for Credential Handling**
- Never hardcode secrets in test files or configuration
- Use SOPS (Mozilla Secrets OPerationS) for encrypting test credentials
- Implement credential rotation every 90 days
- Use service accounts with least-privilege access for testing
- Store test credentials separately from production credentials

**Testing Patterns for Data Pipelines**
- **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification phases
- **Test Pyramid**: Unit tests (70%) → Integration tests (20%) → E2E tests (10%)
- **Idempotency Tests**: Ensure pipeline reruns produce consistent results
- **Data Quality Tests**: Schema validation, null checks, referential integrity
- **Performance Tests**: SLA compliance for pipeline execution times

### 1.2 Implementation Patterns

**E2E Test Architecture**
```
tests/
├── conftest.py              # Shared fixtures and configuration
├── e2e/
│   ├── __init__.py
│   ├── test_pipeline.py     # Main pipeline E2E tests
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── credentials.py   # SOPS-encrypted credential loading
│   │   └── test_data.py     # Test data generation
│   └── helpers/
│       ├── __init__.py
│       └── assertions.py    # Custom test assertions
```

**Secret Management Pattern (SOPS + Ansible)**

```yaml
# .sops.yaml - SOPS configuration file
creation_rules:
  - path_regex: secrets/test/.*\.yaml$
    pgp: 'FBC7B9E2A4F9289AC0C1D4843D16CEE4A27381B4'
    # Or use age for modern encryption:
    # age: age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
```

### 1.3 Concrete Code Snippets

**E2E Test Harness Scaffold**

```python
# tests/e2e/conftest.py
import pytest
import os
from pathlib import Path
from typing import Generator
from subprocess import run

# Pipeline imports
from scripts.pipeline import run_pipeline
from scripts.config import PipelineConfig


@pytest.fixture(scope="session")
def test_credentials() -> dict:
    """Load SOPS-encrypted test credentials."""
    sops_file = Path("secrets/test/credentials.sops.yaml")
    
    # Decrypt using SOPS
    result = run(
        ["sops", "-d", str(sops_file)],
        capture_output=True,
        text=True,
        check=True
    )
    
    import yaml
    return yaml.safe_load(result.stdout)


@pytest.fixture(scope="function")
def isolated_test_db(test_credentials) -> Generator[str, None, None]:
    """Create isolated test database for each test."""
    import psycopg2
    
    db_name = f"test_pipeline_{pytest.current_test_id}"
    conn = psycopg2.connect(
        host=test_credentials["db_host"],
        user=test_credentials["db_user"],
        password=test_credentials["db_password"],
        database="postgres"
    )
    conn.autocommit = True
    
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE {db_name}")
    
    yield f"postgresql://{test_credentials['db_user']}:{test_credentials['db_password']}"
          f"@{test_credentials['db_host']}/{db_name}"
    
    # Cleanup
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE {db_name} WITH (FORCE)")
    conn.close()


@pytest.fixture(scope="function")
def test_client_config(test_credentials) -> PipelineConfig:
    """Create test configuration for a specific client."""
    return PipelineConfig(
        client_id="test_client_e2e",
        ga4_property_id=test_credentials["ga4_test_property_id"],
        ga4_credentials=test_credentials["ga4_test_credentials"],
        # ... other API credentials
    )
```

**E2E Pipeline Test Example**

```python
# tests/e2e/test_pipeline.py
import pytest
from datetime import datetime, timedelta


class TestMarketingPipelineE2E:
    """End-to-end tests for marketing analytics pipeline."""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_full_pipeline_execution(
        self,
        test_client_config,
        isolated_test_db
    ):
        """
        GIVEN: Valid API credentials and test date range
        WHEN: Pipeline runs with --all flag
        THEN: Data is correctly ingested to all staging tables
        """
        # Arrange
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        # Act
        result = run_pipeline(
            config=test_client_config,
            start_date=start_date,
            end_date=end_date,
            sources=["ga4", "facebook", "prestashop"],
            db_connection=isolated_test_db
        )
        
        # Assert
        assert result.status == "success"
        assert result.rows_processed["ga4"] > 0
        assert result.rows_processed["facebook"] > 0
        
        # Verify data quality
        assert self._verify_ga4_schema(isolated_test_db)
        assert self._verify_facebook_schema(isolated_test_db)
        assert self._verify_no_duplicate_keys(isolated_test_db)
    
    @pytest.mark.e2e
    def test_pipeline_idempotency(
        self,
        test_client_config,
        isolated_test_db
    ):
        """
        GIVEN: Pipeline has already run for a date range
        WHEN: Pipeline runs again for same range
        THEN: No duplicate records are created
        """
        date_range = {
            "start": datetime.now().date() - timedelta(days=3),
            "end": datetime.now().date() - timedelta(days=1)
        }
        
        # First run
        run_pipeline(config=test_client_config, **date_range)
        count_first = self._get_total_row_count(isolated_test_db)
        
        # Second run (should be idempotent)
        run_pipeline(config=test_client_config, **date_range)
        count_second = self._get_total_row_count(isolated_test_db)
        
        assert count_first == count_second
    
    def _verify_ga4_schema(self, db_connection: str) -> bool:
        """Verify GA4 staging table has expected schema."""
        import psycopg2
        conn = psycopg2.connect(db_connection)
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'stg_ga4__traffic'
        """)
        columns = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
        
        required_columns = [
            "event_date", "event_name", "user_pseudo_id",
            "session_id", "page_location", "traffic_source"
        ]
        return all(col in columns for col in required_columns)
```

**Credential Rotation Strategy**

```python
# scripts/credentials_rotation.py
"""Automated credential rotation for test environments."""
import json
from datetime import datetime, timedelta
from pathlib import Path
import subprocess


class CredentialRotator:
    """Manages rotation of API credentials for testing."""
    
    ROTATION_DAYS = 90
    
    def __init__(self, sops_key_id: str):
        self.sops_key_id = sops_key_id
        self.secrets_dir = Path("secrets/test")
    
    def check_rotation_needed(self) -> list[str]:
        """Check which credentials need rotation."""
        credentials_needing_rotation = []
        
        for cred_file in self.secrets_dir.glob("*.sops.yaml"):
            metadata = self._get_metadata(cred_file)
            last_rotated = datetime.fromisoformat(metadata["last_rotated"])
            
            if datetime.now() - last_rotated > timedelta(days=self.ROTATION_DAYS):
                credentials_needing_rotation.append(cred_file.stem)
        
        return credentials_needing_rotation
    
    def rotate_ga4_credentials(self):
        """Rotate GA4 test credentials via OAuth refresh."""
        # Implementation depends on GA4 OAuth flow
        pass
    
    def update_encrypted_file(self, file_path: Path, new_credentials: dict):
        """Update SOPS-encrypted file with new credentials."""
        import yaml
        
        # Decrypt existing
        result = subprocess.run(
            ["sops", "-d", str(file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        data = yaml.safe_load(result.stdout)
        
        # Update with new credentials and rotation timestamp
        data.update(new_credentials)
        data["last_rotated"] = datetime.now().isoformat()
        
        # Re-encrypt
        yaml_content = yaml.dump(data)
        subprocess.run(
            ["sops", "--encrypt", "--in-place", str(file_path)],
            input=yaml_content,
            text=True,
            check=True
        )
```

### 1.4 Reference Implementations

- **pytest documentation**: https://docs.pytest.org/
- **SOPS GitHub**: https://github.com/getsops/sops
- **Ansible SOPS Collection**: https://docs.ansible.com/ansible/latest/collections/community/sops/
- **Data Pipeline Testing Patterns**: https://medium.com/@brunouy/automated-tests-data-pipelines

---

## 2. Dashboard Phase 1: Marketing Performance Executive Dashboard

### 2.1 Best Practices

**Executive Dashboard Design Principles**
1. **Lead with KPIs**: Place most important metrics at top left
2. **Use Trends Over Static Numbers**: Show context with trend lines
3. **Limit to 5-7 Key Metrics**: Executives need focus, not overwhelming detail
4. **Color Coding**: Consistent meaning (green=good, red=attention needed)
5. **Mobile-First Consideration**: Executives often review on mobile devices

**Marketing KPIs for Executive Dashboard**

| Category | Metric | Definition | Refresh Frequency |
|----------|--------|------------|-------------------|
| Acquisition | Total Sessions | Sum of all sessions across channels | Daily |
| Acquisition | Cost Per Acquisition (CPA) | Total spend / New customers | Daily |
| Conversion | Conversion Rate | Conversions / Sessions | Daily |
| Revenue | Revenue by Channel | Sum of revenue attributed to each channel | Daily |
| Revenue | Return on Ad Spend (ROAS) | Revenue / Ad Spend | Daily |
| Engagement | Customer Lifetime Value (LTV) | Average revenue per customer over time | Weekly |

### 2.2 Implementation Patterns

**Data Model Pattern for Marts Tables**

```sql
-- models/marts/marketing/fct_marketing_performance.sql
with ga4_sessions as (
    select * from {{ ref('stg_ga4__traffic') }}
),

facebook_ads as (
    select * from {{ ref('stg_facebook__ads') }}
),

google_ads as (
    select * from {{ ref('stg_google_ads__campaigns') }}
),

prestashop_orders as (
    select * from {{ ref('stg_prestashop__orders') }}
),

daily_channel_metrics as (
    select
        date_trunc('day', event_date) as report_date,
        traffic_source as channel,
        count(distinct session_id) as sessions,
        count(distinct user_pseudo_id) as unique_users,
        count(*) as pageviews
    from ga4_sessions
    group by 1, 2
),

daily_revenue as (
    select
        date_trunc('day', order_date) as report_date,
        'prestashop' as channel,
        count(*) as conversions,
        sum(total_paid) as revenue
    from prestashop_orders
    where order_state = 'paid'
    group by 1, 2
),

final as (
    select
        coalesce(m.report_date, r.report_date) as report_date,
        coalesce(m.channel, r.channel) as channel,
        coalesce(m.sessions, 0) as sessions,
        coalesce(m.unique_users, 0) as unique_users,
        coalesce(m.pageviews, 0) as pageviews,
        coalesce(r.conversions, 0) as conversions,
        coalesce(r.revenue, 0) as revenue,
        case 
            when m.sessions > 0 then r.conversions::float / m.sessions 
            else 0 
        end as conversion_rate
    from daily_channel_metrics m
    full outer join daily_revenue r
        on m.report_date = r.report_date
        and m.channel = r.channel
)

select * from final
```

**Metabase Dashboard JSON Structure**

```json
{
  "name": "Marketing Performance Executive Dashboard",
  "description": "Key marketing metrics for executive review",
  "collection_id": null,
  "collection_position": null,
  "cache_ttl": 3600,
  "parameters": [
    {
      "id": "date_range",
      "type": "date/range",
      "name": "Date Range",
      "slug": "date_range",
      "default": "past30days"
    },
    {
      "id": "channel",
      "type": "string/=",
      "name": "Channel",
      "slug": "channel",
      "values_query_type": "list"
    }
  ],
  "ordered_cards": [
    {
      "size_x": 4,
      "size_y": 3,
      "col": 0,
      "row": 0,
      "visualization_settings": {
        "card.title": "Total Revenue",
        "scalar.compact_numbers": true,
        "scalar.decimal_places": 0,
        "scalar.prefix": "$",
        "scalar.suffix": ""
      },
      "parameter_mappings": [
        {
          "parameter_id": "date_range",
          "card_id": 1,
          "target": ["dimension", ["template-tag", "date_range"]]
        }
      ]
    }
  ]
}
```

### 2.3 Concrete Code Snippets

**Metabase API Client for Dashboard Management**

```python
# scripts/metabase_client.py
import requests
from typing import Dict, List, Optional
import json


class MetabaseClient:
    """Client for Metabase API operations."""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self._authenticate(username, password)
    
    def _authenticate(self, username: str, password: str):
        """Authenticate and store session token."""
        response = self.session.post(
            f"{self.base_url}/api/session",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        token = response.json()["id"]
        self.session.headers["X-Metabase-Session"] = token
    
    def create_question(self, question_config: Dict) -> Dict:
        """Create a new question/card."""
        response = self.session.post(
            f"{self.base_url}/api/card",
            json=question_config
        )
        response.raise_for_status()
        return response.json()
    
    def create_dashboard(self, name: str, description: str = "") -> Dict:
        """Create a new dashboard."""
        payload = {
            "name": name,
            "description": description,
            "parameters": []
        }
        response = self.session.post(
            f"{self.base_url}/api/dashboard",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def add_card_to_dashboard(
        self,
        dashboard_id: int,
        card_id: int,
        position: Dict,
        parameter_mappings: List[Dict] = None
    ) -> Dict:
        """Add a card to a dashboard."""
        payload = {
            "cardId": card_id,
            "row": position.get("row", 0),
            "col": position.get("col", 0),
            "size_x": position.get("size_x", 4),
            "size_y": position.get("size_y", 4),
            "parameter_mappings": parameter_mappings or []
        }
        response = self.session.post(
            f"{self.base_url}/api/dashboard/{dashboard_id}/cards",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def export_dashboard(self, dashboard_id: int) -> Dict:
        """Export dashboard configuration as JSON."""
        response = self.session.get(
            f"{self.base_url}/api/dashboard/{dashboard_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def import_dashboard(self, dashboard_config: Dict) -> Dict:
        """Import dashboard from JSON configuration."""
        # Note: Metabase doesn't have a native import endpoint
        # This requires creating questions first, then dashboard, then linking
        pass


# Usage example for creating executive dashboard
def create_marketing_executive_dashboard(client: MetabaseClient) -> int:
    """Create the Phase 1 Marketing Performance Executive Dashboard."""
    
    # Create dashboard
    dashboard = client.create_dashboard(
        name="Marketing Performance - Executive",
        description="Key marketing KPIs for executive review"
    )
    dashboard_id = dashboard["id"]
    
    # Define questions/cards
    questions = [
        {
            "name": "Total Revenue (MTD)",
            "dataset_query": {
                "type": "native",
                "native": {
                    "query": """
                        SELECT SUM(revenue) as total_revenue
                        FROM fct_marketing_performance
                        WHERE report_date >= date_trunc('month', current_date)
                    """
                },
                "database": 1  # Database ID
            },
            "display": "scalar",
            "visualization_settings": {
                "scalar.prefix": "$",
                "scalar.decimal_places": 0
            }
        },
        {
            "name": "Revenue by Channel",
            "dataset_query": {
                "type": "native",
                "native": {
                    "query": """
                        SELECT 
                            channel,
                            SUM(revenue) as revenue,
                            SUM(sessions) as sessions
                        FROM fct_marketing_performance
                        WHERE report_date >= {{date_range}}
                        GROUP BY channel
                        ORDER BY revenue DESC
                    """,
                    "template-tags": {
                        "date_range": {
                            "type": "dimension",
                            "name": "date_range",
                            "id": "date_range",
                            "dimension": ["field", 123, None],  # Field reference
                            "widget-type": "date/range"
                        }
                    }
                },
                "database": 1
            },
            "display": "bar",
            "visualization_settings": {}
        }
    ]
    
    # Create questions and add to dashboard
    for i, q_config in enumerate(questions):
        card = client.create_question(q_config)
        client.add_card_to_dashboard(
            dashboard_id=dashboard_id,
            card_id=card["id"],
            position={"row": 0 if i < 2 else 4, "col": (i % 2) * 6, "size_x": 6, "size_y": 4}
        )
    
    return dashboard_id
```

### 2.4 Reference Implementations

- **Metabase Documentation**: https://www.metabase.com/docs/latest/
- **BI Dashboard Best Practices**: https://www.metabase.com/learn/metabase-basics/querying-and-dashboards/dashboards/bi-dashboard-best-practices
- **dbt Marts Best Practices**: https://docs.getdbt.com/best-practices/how-we-structure/4-marts
- **Metabase Export/Import Tool**: https://github.com/24eme/metabase_export_import

---

## 3. Scheduling Wiring: Prefect + Crontab Integration

### 3.1 Best Practices

**Prefect Schedule Patterns**
1. **Native Prefect Schedules**: Use for complex scheduling logic, timezone handling
2. **Crontab Integration**: Use for simple recurring schedules, system-level cron
3. **Hybrid Approach**: Use crontab to trigger Prefect deployments via API

**Monitoring and Alerting Patterns**
- Set up flow run state change webhooks
- Configure Slack/email notifications for failures
- Implement health check endpoints for scheduled flows
- Track SLA compliance (data freshness)

**Docker + Cron Integration Patterns**
- Use `supercronic` for reliable cron in containers
- Or use separate cron container alongside Prefect
- Ensure proper timezone configuration (Europe/Prague)

### 3.2 Implementation Patterns

**Pattern A: Native Prefect Schedules (Recommended)**

```python
# prefect/deployments/marketing_analytics.py
from prefect import flow
from prefect.schedules import CronSchedule
from prefect.deployments import Deployment
from datetime import timedelta


@flow(name="marketing-analytics-pipeline")
def marketing_pipeline(client_id: str):
    """Main marketing analytics pipeline flow."""
    # Pipeline implementation
    pass


# Create deployment with cron schedule
deployment = Deployment.build_from_flow(
    flow=marketing_pipeline,
    name="daily-marketing-pipeline",
    schedule=CronSchedule(
        cron="0 2 * * *",  # Daily at 2 AM
        timezone="Europe/Prague"
    ),
    work_pool_name="docker-pool",
    parameters={"client_id": "default_client"}
)

if __name__ == "__main__":
    deployment.apply()
```

**Pattern B: Docker Compose with Cron Sidecar**

```yaml
# docker-compose.yml (scheduling section)
services:
  prefect-server:
    image: prefecthq/prefect:3-latest
    # ... existing server config

  prefect-worker:
    image: prefecthq/prefect:3-latest
    environment:
      PREFECT_API_URL: http://prefect-server:4200/api
    command: prefect worker start --pool docker-pool
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  prefect-scheduler:
    image: prefecthq/prefect:3-latest
    environment:
      PREFECT_API_URL: http://prefect-server:4200/api
    volumes:
      - ./crontab:/etc/cron.d/prefect-scheduler:ro
      - ./scripts:/scripts:ro
    command: >
      sh -c "
        apt-get update && apt-get install -y cron &&
        crontab /etc/cron.d/prefect-scheduler &&
        cron -f
      "
```

```bash
# crontab file
TZ=Europe/Prague

# Daily marketing pipeline at 2 AM
0 2 * * * /scripts/run_prefect_flow.sh marketing-analytics-pipeline daily-marketing-pipeline '{"client_id": "client1"}'

# Health check every 15 minutes
*/15 * * * * /scripts/health_check.sh
```

```bash
# scripts/run_prefect_flow.sh
#!/bin/bash
set -e

FLOW_NAME=$1
DEPLOYMENT_NAME=$2
PARAMETERS=$3
PREFECT_API_URL=${PREFECT_API_URL:-"http://prefect-server:4200/api"}

echo "[$(date)] Triggering flow: $FLOW_NAME/$DEPLOYMENT_NAME"

# Trigger deployment via Prefect API
RESPONSE=$(curl -s -X POST \
  "${PREFECT_API_URL}/deployments/${DEPLOYMENT_NAME}/create_flow_run" \
  -H "Content-Type: application/json" \
  -d "{
    \"parameters\": $PARAMETERS,
    \"idempotency_key\": \"${DEPLOYMENT_NAME}-$(date +%Y%m%d)\"
  }")

if [ $? -eq 0 ]; then
    echo "[$(date)] Flow triggered successfully"
    echo "$RESPONSE" | jq -r '.id'
else
    echo "[$(date)] Failed to trigger flow"
    exit 1
fi
```

### 3.3 Concrete Code Snippets

**Health Check and Failure Notification**

```python
# prefect/flows/health_monitor.py
from prefect import flow, task, get_run_logger
from prefect.blocks.notifications import SlackWebhook
import requests
from datetime import datetime, timedelta


@task(retries=3, retry_delay_seconds=30)
def check_pipeline_health() -> dict:
    """Check health of scheduled pipelines."""
    logger = get_run_logger()
    
    # Query Prefect API for recent flow runs
    api_url = "http://prefect-server:4200/api"
    
    # Check flows that should have run in last 4 hours
    since = (datetime.utcnow() - timedelta(hours=4)).isoformat()
    
    response = requests.post(
        f"{api_url}/flow_runs/filter",
        json={
            "flow_runs": {
                "expected_start_time": {"after_": since}
            }
        }
    )
    response.raise_for_status()
    
    flow_runs = response.json()
    
    failed_runs = [r for r in flow_runs if r["state"]["type"] == "FAILED"]
    late_runs = [r for r in flow_runs if r["state"]["type"] == "LATE"]
    
    return {
        "total_checked": len(flow_runs),
        "failed": len(failed_runs),
        "late": len(late_runs),
        "failed_details": failed_runs,
        "late_details": late_runs
    }


@task
async def send_alert(health_status: dict):
    """Send notification if issues detected."""
    if health_status["failed"] == 0 and health_status["late"] == 0:
        return
    
    slack_webhook = await SlackWebhook.load("pipeline-alerts")
    
    message = f"""
:warning: *Pipeline Health Alert*

Failed Flows: {health_status['failed']}
Late Flows: {health_status['late']}

Details:
"""
    for run in health_status.get("failed_details", []):
        message += f"• `{run['name']}` failed at {run['state']['timestamp']}\n"
    
    await slack_webhook.notify(message)


@flow(name="pipeline-health-monitor")
def health_monitor_flow():
    """Scheduled health check for all pipelines."""
    health = check_pipeline_health()
    send_alert(health)
```

**Multi-Client Deployment Configuration**

```python
# prefect/deployments/deploy_all_clients.py
import argparse
from prefect.deployments import Deployment
from prefect.schedules import CronSchedule
from marketing_analytics import marketing_pipeline

CLIENTS = ["client1", "client2", "client3"]


def deploy_for_client(client_id: str):
    """Create deployment for a specific client."""
    deployment = Deployment.build_from_flow(
        flow=marketing_pipeline,
        name=f"daily-marketing-{client_id}",
        schedule=CronSchedule(
            cron="0 2 * * *",
            timezone="Europe/Prague"
        ),
        work_pool_name="docker-pool",
        parameters={"client_id": client_id},
        tags=["marketing", "daily", client_id],
        description=f"Daily marketing pipeline for {client_id}"
    )
    deployment.apply()
    print(f"Deployed: daily-marketing-{client_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", help="Specific client to deploy for")
    parser.add_argument("--all", action="store_true", help="Deploy for all clients")
    args = parser.parse_args()
    
    if args.all:
        for client in CLIENTS:
            deploy_for_client(client)
    elif args.client:
        deploy_for_client(args.client)
    else:
        print("Specify --client <name> or --all")


if __name__ == "__main__":
    main()
```

### 3.4 Reference Implementations

- **Prefect Docker Compose Guide**: https://docs.prefect.io/v3/how-to-guides/self-hosted/docker-compose
- **Prefect Schedules Documentation**: https://docs-3.prefect.io/v3/how-to-guides/deployments/manage-schedules
- **Prefect Notifications**: https://github.com/wsargent/prefect-notifications

---

## 4. Phase 2 Planning: Attribution Modeling

### 4.1 Attribution Model Approaches

**First-Touch Attribution**
- 100% credit to first touchpoint in customer journey
- Best for: Understanding acquisition channels
- SQL Pattern: `FIRST_VALUE(channel) OVER (PARTITION BY customer_id ORDER BY touch_date)`

**Last-Touch Attribution**
- 100% credit to final touchpoint before conversion
- Best for: Understanding closing channels
- Limitation: Ignores upper-funnel contribution

**Linear Attribution**
- Equal credit distributed across all touchpoints
- Best for: Understanding full journey contribution
- Fair but dilutes impact of key moments

**Time-Decay Attribution**
- More credit to touchpoints closer to conversion
- Best for: Long sales cycles where recency matters
- Formula: Weight = 2^(-days_to_conversion/halflife)

**Position-Based (U-Shaped)**
- 40% first touch, 40% last touch, 20% distributed among middle
- Best for: Balancing discovery and closing

**Data-Driven (Algorithmic)**
- Uses statistical models to determine actual influence
- Best for: Large datasets with sufficient conversion volume
- Requires: ML infrastructure, significant data volume

### 4.2 Data Requirements

**Minimum Data Model for Attribution**

```sql
-- Core attribution tables structure

-- 1. Touchpoints (all customer interactions)
CREATE TABLE fct_touchpoints (
    touchpoint_id BIGINT PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    touch_timestamp TIMESTAMP NOT NULL,
    channel VARCHAR(100) NOT NULL,  -- paid_search, organic, email, etc.
    campaign VARCHAR(255),
    ad_group VARCHAR(255),
    keyword VARCHAR(255),
    landing_page VARCHAR(500),
    device_type VARCHAR(50),
    geo_region VARCHAR(100),
    -- Metadata
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Conversions (desired outcomes)
CREATE TABLE fct_conversions (
    conversion_id BIGINT PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    conversion_timestamp TIMESTAMP NOT NULL,
    conversion_type VARCHAR(50) NOT NULL,  -- purchase, signup, lead
    revenue DECIMAL(12,2),
    order_id VARCHAR(255),
    attribution_window_days INT DEFAULT 30,
    -- Metadata
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Customer Journey (linking touchpoints to conversions)
CREATE TABLE fct_customer_journeys (
    journey_id BIGINT PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    conversion_id BIGINT REFERENCES fct_conversions(conversion_id),
    touchpoint_count INT,
    first_touch_timestamp TIMESTAMP,
    last_touch_timestamp TIMESTAMP,
    journey_duration_hours DECIMAL(8,2),
    -- Metadata
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 Attribution Model SQL Patterns

**Linear Attribution Model**

```sql
-- models/marts/attribution/attribution_linear.sql

with customer_journeys as (
    select
        t.customer_id,
        c.conversion_id,
        c.revenue,
        t.touchpoint_id,
        t.channel,
        t.touch_timestamp,
        count(*) over (
            partition by t.customer_id, c.conversion_id
        ) as total_touchpoints
    from fct_touchpoints t
    inner join fct_conversions c
        on t.customer_id = c.customer_id
        and t.touch_timestamp <= c.conversion_timestamp
        and t.touch_timestamp >= c.conversion_timestamp - interval '30 days'
),

attributed as (
    select
        conversion_id,
        touchpoint_id,
        channel,
        touch_timestamp,
        revenue / total_touchpoints as attributed_revenue,
        1.0 / total_touchpoints as attribution_weight
    from customer_journeys
)

select * from attributed
```

**Time-Decay Attribution Model**

```sql
-- models/marts/attribution/attribution_time_decay.sql

with journey_touchpoints as (
    select
        t.customer_id,
        c.conversion_id,
        c.revenue,
        c.conversion_timestamp,
        t.touchpoint_id,
        t.channel,
        t.touch_timestamp,
        -- Days before conversion
        extract(epoch from (c.conversion_timestamp - t.touch_timestamp)) / 86400 
            as days_before_conversion,
        -- Halflife parameter (7 days = 50% weight reduction per week)
        7.0 as halflife_days
    from fct_touchpoints t
    inner join fct_conversions c
        on t.customer_id = c.customer_id
        and t.touch_timestamp <= c.conversion_timestamp
        and t.touch_timestamp >= c.conversion_timestamp - interval '30 days'
),

weighted_touchpoints as (
    select
        *,
        -- Time decay weight: 2^(-days/halflife)
        power(2, -days_before_conversion / halflife_days) as time_weight
    from journey_touchpoints
),

normalized as (
    select
        *,
        time_weight / sum(time_weight) over (partition by conversion_id) 
            as normalized_weight,
        revenue * (time_weight / sum(time_weight) over (partition by conversion_id)) 
            as attributed_revenue
    from weighted_touchpoints
)

select
    conversion_id,
    touchpoint_id,
    channel,
    touch_timestamp,
    days_before_conversion,
    normalized_weight as attribution_weight,
    attributed_revenue
from normalized
```

**Position-Based (U-Shaped) Attribution**

```sql
-- models/marts/attribution/attribution_position_based.sql

with journey_touchpoints as (
    select
        t.customer_id,
        c.conversion_id,
        c.revenue,
        t.touchpoint_id,
        t.channel,
        t.touch_timestamp,
        row_number() over (
            partition by t.customer_id, c.conversion_id
            order by t.touch_timestamp
        ) as touch_position,
        count(*) over (
            partition by t.customer_id, c.conversion_id
        ) as total_touchpoints
    from fct_touchpoints t
    inner join fct_conversions c
        on t.customer_id = c.customer_id
        and t.touch_timestamp <= c.conversion_timestamp
        and t.touch_timestamp >= c.conversion_timestamp - interval '30 days'
),

position_weights as (
    select
        *,
        case
            when total_touchpoints = 1 then 1.0
            when touch_position = 1 then 0.40  -- First touch
            when touch_position = total_touchpoints then 0.40  -- Last touch
            else 0.20 / (total_touchpoints - 2)  -- Middle touches split remaining 20%
        end as position_weight
    from journey_touchpoints
)

select
    conversion_id,
    touchpoint_id,
    channel,
    touch_timestamp,
    touch_position,
    total_touchpoints,
    position_weight as attribution_weight,
    revenue * position_weight as attributed_revenue
from position_weights
```

**Attribution Summary by Channel**

```sql
-- models/marts/attribution/fct_channel_attribution.sql

with all_models as (
    -- First touch
    select
        'first_touch' as model,
        channel,
        sum(attributed_revenue) as attributed_revenue,
        count(distinct conversion_id) as attributed_conversions
    from {{ ref('attribution_first_touch') }}
    group by channel
    
    union all
    
    -- Last touch
    select
        'last_touch' as model,
        channel,
        sum(attributed_revenue) as attributed_revenue,
        count(distinct conversion_id) as attributed_conversions
    from {{ ref('attribution_last_touch') }}
    group by channel
    
    union all
    
    -- Linear
    select
        'linear' as model,
        channel,
        sum(attributed_revenue) as attributed_revenue,
        count(distinct conversion_id) as attributed_conversions
    from {{ ref('attribution_linear') }}
    group by channel
    
    union all
    
    -- Time decay
    select
        'time_decay' as model,
        channel,
        sum(attributed_revenue) as attributed_revenue,
        count(distinct conversion_id) as attributed_conversions
    from {{ ref('attribution_time_decay') }}
    group by channel
)

select * from all_models
```

### 4.4 Common Pitfalls and Mitigations

| Pitfall | Impact | Mitigation |
|---------|--------|------------|
| **Attribution Window Too Long** | Credits old touchpoints that didn't influence | Use 7-30 day windows based on typical sales cycle |
| **Ignoring View-Through Conversions** | Undervalues display/video channels | Track impression data alongside clicks |
| **Cross-Device Journeys** | Broken customer journeys | Implement device graph / user stitching |
| **Offline Conversions** | Missing CRM/in-store data | Import offline conversion events |
| **Multi-Touch Conflicts** | Multiple models show different "truths" | Present multiple models, explain assumptions |
| **Data Sparsity** | Unreliable model with few conversions | Set minimum conversion thresholds before enabling |

### 4.5 Reference Implementations

- **Snowplow Attribution dbt Package**: https://docs.snowplow.io/docs/modeling-your-data/modeling-your-data-with-dbt/dbt-models/dbt-attribution-data-model/
- **SQL Attribution Models**: https://medium.com/gopenai/10-attribution-models-you-can-build-using-pure-sql-29503a648acd
- **Multi-Touch Attribution with SQL**: https://risingwave.com/blog/marketing-attribution-multi-touch-streaming/

---

## 5. Recommendations Summary

### Immediate Actions (Phase 1)

1. **E2E Testing**: Implement SOPS + pytest framework before any credential-dependent testing
2. **Dashboard**: Build Marketing Performance dashboard with 5-7 KPIs using dbt marts pattern
3. **Scheduling**: Deploy Prefect with native cron schedules (Pattern A) for reliability

### Deferred Scope (Phase 2)

1. **Attribution Modeling**: Start with Linear and Time-Decay models (pure SQL)
2. **Data Requirements**: Ensure touchpoint and conversion tables are populated
3. **Avoid**: Data-driven/ML models until 1000+ monthly conversions achieved

### Tool Integration Decisions

| Decision | Recommendation | Rationale |
|----------|----------------|-----------|
| Secret Management | SOPS + Ansible | Industry standard, Git-friendly encryption |
| Schedule Method | Native Prefect Cron | Better observability than crontab |
| Dashboard Tool | Metabase Native | Proven, cost-effective for current needs |
| Attribution Start | Linear + Time-Decay | Implementable with existing data |

---

## Appendix: Quick Reference Commands

```bash
# SOPS Operations
sops -d secrets/test/credentials.sops.yaml          # Decrypt
sops --encrypt --in-place secrets/test/credentials.yaml  # Encrypt
sops secrets/test/credentials.sops.yaml             # Edit in-place

# Prefect Deployment
prefect deployment apply prefect/deployments/marketing_analytics.py
prefect deployment schedule ls marketing-analytics-pipeline/daily-marketing-client1
prefect deployment schedule pause --all

# dbt
 cd dbt && dbt run --select marts.marketing
 dbt test --select marts.marketing

# Metabase API
 curl -X POST http://localhost:3000/api/session \
   -d '{"username": "admin", "password": "xxx"}'
```

---

*Document generated: 2026-04-08*
*Research scope: Best practices for data pipeline implementation*
