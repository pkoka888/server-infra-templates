# Marketing Automation Dashboard Code Examples

## Overview
Comprehensive implementation examples for marketing automation dashboards using various BI tools. These examples demonstrate real-world patterns for cash-flow visualization, ROI tracking, and marketing performance monitoring.

## 1. Metabase - Comprehensive Marketing Dashboard

### Dashboard Configuration
```yaml
# metabase-dashboard.yaml
name: "Marketing Performance Dashboard"
description: "Comprehensive view of marketing ROI, cash flow, and campaign performance"
cards:
  - name: "Monthly Revenue Trends"
    type: "line"
    query: |
      SELECT 
        DATE_TRUNC('month', date) AS month,
        SUM(revenue) AS revenue,
        SUM(spend) AS spend,
        SUM(revenue) / SUM(spend) AS roi
      FROM marketing_performance
      GROUP BY 1
      ORDER BY 1
    
  - name: "Channel Performance"
    type: "bar"
    query: |
      SELECT 
        channel,
        SUM(revenue) AS revenue,
        SUM(spend) AS spend,
        SUM(revenue) / SUM(spend) AS roi
      FROM marketing_performance
      GROUP BY 1
      ORDER BY revenue DESC
    
  - name: "ROI by Campaign"
    type: "scatter"
    query: |
      SELECT 
        campaign_name,
        SUM(revenue) AS revenue,
        SUM(spend) AS spend,
        SUM(revenue) / SUM(spend) AS roi,
        COUNT(DISTINCT customer_id) AS customers
      FROM campaign_performance
      GROUP BY 1
      HAVING SUM(spend) > 1000
```

### Embedded Dashboard Example
```javascript
// React component for embedded marketing dashboard
import { useEffect, useState } from 'react';

const MarketingDashboard = () => {
  const [dashboardUrl, setDashboardUrl] = useState('');

  useEffect(() => {
    const generateEmbedUrl = async () => {
      const response = await fetch('/api/metabase/embed/marketing-dashboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          params: {
            date_filter: 'last_90_days',
            show_roi: true
          }
        })
      });
      
      const { url } = await response.json();
      setDashboardUrl(url);
    };

    generateEmbedUrl();
  }, []);

  return (
    <div className="dashboard-container">
      {dashboardUrl && (
        <iframe
          src={dashboardUrl}
          style={{ width: '100%', height: '800px', border: 'none' }}
          title="Marketing Performance Dashboard"
        />
      )}
    </div>
  );
};

export default MarketingDashboard;
```

## 2. Evidence - SQL+Markdown Marketing Analytics

### Complete Marketing Dashboard
```markdown
# Marketing Performance Analytics

## Executive Summary

**Total ROI**: {summary[0].overall_roi}  
**Total Revenue**: ${summary[0].total_revenue}  
**Total Spend**: ${summary[0].total_spend}  
**Customer Acquisition Cost**: ${summary[0].cac}

```sql summary
SELECT 
  SUM(revenue) / SUM(spend) AS overall_roi,
  SUM(revenue) AS total_revenue,
  SUM(spend) AS total_spend,
  SUM(spend) / COUNT(DISTINCT customer_id) AS cac
FROM marketing_performance
WHERE date >= '2024-01-01'
```

## Revenue Trends

<LineChart 
  data={revenue_trends} 
  x="month" 
  y="revenue" 
  title="Monthly Revenue Trend"
/>

```sql revenue_trends
SELECT 
  DATE_TRUNC('month', date) AS month,
  SUM(revenue) AS revenue,
  SUM(spend) AS spend
FROM marketing_performance
GROUP BY 1
ORDER BY 1
```

## Channel Performance

<BarChart
  data={channel_performance}
  x="channel"
  y="roi"
  title="ROI by Marketing Channel"
/>

```sql channel_performance
SELECT 
  channel,
  SUM(revenue) AS revenue,
  SUM(spend) AS spend,
  SUM(revenue) / SUM(spend) AS roi,
  COUNT(DISTINCT campaign_id) AS campaigns
FROM marketing_performance
GROUP BY 1
ORDER BY revenue DESC
```

## Campaign ROI Analysis

<ScatterChart
  data={campaign_roi}
  x="spend"
  y="revenue"
  size="roi"
  color="channel"
  title="Campaign ROI vs Spend"
/>

```sql campaign_roi
SELECT 
  campaign_name,
  channel,
  SUM(revenue) AS revenue,
  SUM(spend) AS spend,
  SUM(revenue) / SUM(spend) AS roi,
  COUNT(DISTINCT customer_id) AS customers
FROM campaign_performance
GROUP BY 1, 2
HAVING SUM(spend) > 500
```

## Customer Acquisition Metrics

**CAC by Channel**:

| Channel | CAC | LTV | LTV:CAC Ratio |
|---------|-----|-----|---------------|
| {cac_metrics[0].channel} | ${cac_metrics[0].cac} | ${cac_metrics[0].ltv} | {cac_metrics[0].ltv_cac_ratio} |
| {cac_metrics[1].channel} | ${cac_metrics[1].cac} | ${cac_metrics[1].ltv} | {cac_metrics[1].ltv_cac_ratio} |

```sql cac_metrics
SELECT 
  channel,
  SUM(spend) / COUNT(DISTINCT customer_id) AS cac,
  SUM(revenue) / COUNT(DISTINCT customer_id) AS ltv,
  (SUM(revenue) / COUNT(DISTINCT customer_id)) / 
  (SUM(spend) / COUNT(DISTINCT customer_id)) AS ltv_cac_ratio
FROM marketing_performance
WHERE date >= '2024-01-01'
GROUP BY 1
ORDER BY cac ASC
```
```

## 3. Lightdash - dbt Metric Definitions

### dbt Models for Marketing Analytics
```yaml
# models/marketing/schema.yml
version: 2

models:
  - name: marketing_performance
    description: "Marketing performance metrics and dimensions"
    
    columns:
      - name: date
        description: "Date of performance metric"
        meta:
          dimension:
            type: time
            time_granularity: day
      
      - name: channel
        description: "Marketing channel (Google Ads, Facebook, etc.)"
        meta:
          dimension:
            type: string
    
    metrics:
      - name: marketing_roi
        label: "Marketing ROI"
        description: "Return on investment for marketing campaigns"
        type: ratio
        numerator: revenue
        denominator: spend
        
      - name: customer_acquisition_cost
        label: "Customer Acquisition Cost"
        description: "Cost to acquire a new customer"
        type: average
        sql: "${spend} / ${new_customers}"
        
      - name: lifetime_value
        label: "Lifetime Value"
        description: "Average lifetime value of a customer"
        type: average
        sql: "${revenue} / ${customers}"
        
      - name: romi
        label: "Return on Marketing Investment"
        description: "(Revenue - Spend) / Spend"
        type: derived
        sql: "(${revenue} - ${spend}) / ${spend}"

  - name: campaign_performance
    description: "Campaign-level performance metrics"
    
    columns:
      - name: campaign_id
        description: "Unique campaign identifier"
      
      - name: campaign_name
        description: "Campaign name"
        meta:
          dimension:
            type: string
    
    metrics:
      - name: campaign_roi
        label: "Campaign ROI"
        description: "Return on investment for specific campaigns"
        type: ratio
        numerator: revenue
        denominator: spend
```

### Lightdash Dashboard Configuration
```yaml
# lightdash-dashboard.yaml
name: "Marketing Performance Dashboard"
description: "Comprehensive view of marketing metrics and ROI"

tiles:
  - name: "Overall Marketing ROI"
    type: "big_number"
    metric: "marketing_roi"
    show_mini_chart: true
    
  - name: "Monthly Revenue Trend"
    type: "line_chart"
    x_axis: "date"
    y_axis: ["revenue", "spend"]
    group_by: ["channel"]
    
  - name: "ROI by Channel"
    type: "bar_chart"
    x_axis: "channel"
    y_axis: ["marketing_roi"]
    
  - name: "CAC vs LTV by Channel"
    type: "scatter_chart"
    x_axis: "customer_acquisition_cost"
    y_axis: "lifetime_value"
    group_by: ["channel"]
    size: "romi"
```

## 4. Airbyte - Marketing Data Pipeline

### Complete ETL Configuration
```yaml
# airbyte-marketing-pipeline.yaml
version: "2.0"

connections:
  # Google Ads data
  - name: "google-ads-to-warehouse"
    source:
      sourceDefinitionId: "google-ads"
      configuration:
        credentials:
          auth_type: "oauth"
          client_id: "${GOOGLE_ADS_CLIENT_ID}"
          client_secret: "${GOOGLE_ADS_CLIENT_SECRET}"
          refresh_token: "${GOOGLE_ADS_REFRESH_TOKEN}"
        customer_id: "${GOOGLE_ADS_CUSTOMER_ID}"
        start_date: "2024-01-01"
    destination:
      destinationDefinitionId: "bigquery"
      configuration:
        dataset_id: "marketing_raw"
        project_id: "${GCP_PROJECT_ID}"
        credentials_json: "${GCP_CREDENTIALS_JSON}"
    schedule:
      units: 24
      timeUnit: "hours"

  # Facebook Ads data
  - name: "facebook-ads-to-warehouse"
    source:
      sourceDefinitionId: "facebook-marketing"
      configuration:
        account_id: "${FB_ACCOUNT_ID}"
        access_token: "${FB_ACCESS_TOKEN}"
        start_date: "2024-01-01"
    destination:
      destinationDefinitionId: "bigquery"
      configuration:
        dataset_id: "marketing_raw"
        project_id: "${GCP_PROJECT_ID}"
        credentials_json: "${GCP_CREDENTIALS_JSON}"

  # Salesforce CRM data
  - name: "salesforce-to-warehouse"
    source:
      sourceDefinitionId: "salesforce"
      configuration:
        client_id: "${SALESFORCE_CLIENT_ID}"
        client_secret: "${SALESFORCE_CLIENT_SECRET}"
        refresh_token: "${SALESFORCE_REFRESH_TOKEN}"
    destination:
      destinationDefinitionId: "bigquery"
      configuration:
        dataset_id: "crm_raw"
        project_id: "${GCP_PROJECT_ID}"
        credentials_json: "${GCP_CREDENTIALS_JSON}"
```

## 5. Python - Custom Marketing Analytics

### Data Processing Pipeline
```python
# marketing_analytics_pipeline.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MarketingAnalytics:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def calculate_roi_metrics(self, start_date, end_date):
        """Calculate comprehensive ROI metrics"""
        query = f"""
        SELECT 
            channel,
            campaign_name,
            SUM(revenue) AS revenue,
            SUM(spend) AS spend,
            SUM(revenue) / NULLIF(SUM(spend), 0) AS roi,
            COUNT(DISTINCT customer_id) AS customers,
            SUM(spend) / NULLIF(COUNT(DISTINCT customer_id), 0) AS cac,
            SUM(revenue) / NULLIF(COUNT(DISTINCT customer_id), 0) AS ltv
        FROM marketing_performance
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY channel, campaign_name
        HAVING SUM(spend) > 0
        """
        
        df = pd.read_sql(query, self.db)
        
        # Calculate additional metrics
        df['romi'] = (df['revenue'] - df['spend']) / df['spend']
        df['ltv_cac_ratio'] = df['ltv'] / df['cac']
        df['profit'] = df['revenue'] - df['spend']
        
        return df
    
    def generate_cash_flow_report(self, start_date, end_date):
        """Generate cash flow analysis report"""
        query = f"""
        SELECT 
            DATE_TRUNC('month', date) AS month,
            channel,
            SUM(revenue) AS revenue,
            SUM(spend) AS spend,
            SUM(revenue) - SUM(spend) AS net_cash_flow,
            SUM(revenue) / NULLIF(SUM(spend), 0) AS roi
        FROM marketing_performance
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY 1, 2
        ORDER BY 1, 2
        """
        
        df = pd.read_sql(query, self.db)
        
        # Calculate cumulative cash flow
        df['cumulative_cash_flow'] = df.groupby('channel')['net_cash_flow'].cumsum()
        
        return df
    
    def calculate_campaign_effectiveness(self):
        """Calculate campaign effectiveness metrics"""
        query = """
        SELECT 
            campaign_name,
            channel,
            SUM(revenue) AS revenue,
            SUM(spend) AS spend,
            COUNT(DISTINCT customer_id) AS customers,
            SUM(conversions) AS conversions,
            SUM(impressions) AS impressions,
            SUM(clicks) AS clicks
        FROM campaign_performance
        GROUP BY campaign_name, channel
        """
        
        df = pd.read_sql(query, self.db)
        
        # Calculate marketing metrics
        df['ctr'] = df['clicks'] / df['impressions']
        df['conversion_rate'] = df['conversions'] / df['clicks']
        df['cpa'] = df['spend'] / df['conversions']
        df['roi'] = df['revenue'] / df['spend']
        
        return df
```

### Visualization Helper
```python
# visualization_helper.py
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_marketing_dashboard(df):
    """Create comprehensive marketing dashboard"""
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Monthly Revenue Trend", 
            "ROI by Channel",
            "CAC vs LTV", 
            "Campaign Performance"
        )
    )
    
    # Revenue trend
    fig.add_trace(
        go.Scatter(
            x=df['month'],
            y=df['revenue'],
            name="Revenue",
            line=dict(color="#2E86AB")
        ),
        row=1, col=1
    )
    
    # ROI by channel
    roi_by_channel = df.groupby('channel')['roi'].mean().reset_index()
    fig.add_trace(
        go.Bar(
            x=roi_by_channel['channel'],
            y=roi_by_channel['roi'],
            name="ROI by Channel",
            marker_color="#A23B72"
        ),
        row=1, col=2
    )
    
    # CAC vs LTV scatter
    fig.add_trace(
        go.Scatter(
            x=df['cac'],
            y=df['ltv'],
            mode='markers',
            marker=dict(
                size=df['customers'],
                color=df['roi'],
                colorscale="Viridis",
                showscale=True
            ),
            text=df['channel'],
            name="CAC vs LTV"
        ),
        row=2, col=1
    )
    
    # Campaign performance
    fig.add_trace(
        go.Bar(
            x=df['campaign_name'],
            y=df['revenue'],
            name="Revenue",
            marker_color="#F18F01"
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        title="Marketing Performance Dashboard",
        height=800,
        showlegend=True
    )
    
    return fig
```

## Usage Examples

### 1. Quick ROI Dashboard Setup
```bash
# Set up data pipeline
airbyte setup --config airbyte-marketing-pipeline.yaml

# Run dbt transformations
dbt run --models marketing

# Start Metabase
metabase start

# Access dashboard at http://localhost:3000
```

### 2. Python Analytics Pipeline
```python
from marketing_analytics_pipeline import MarketingAnalytics
from visualization_helper import create_marketing_dashboard

# Initialize analytics
analytics = MarketingAnalytics(db_connection)

# Get ROI metrics
df = analytics.calculate_roi_metrics('2024-01-01', '2024-03-31')

# Create visualization
fig = create_marketing_dashboard(df)
fig.show()

# Generate cash flow report
cash_flow_df = analytics.generate_cash_flow_report('2024-01-01', '2024-03-31')
print(cash_flow_df)
```

## Key Performance Indicators (KPIs)

### Essential Marketing Metrics:
1. **ROI (Return on Investment)**: Revenue / Spend
2. **ROMI (Return on Marketing Investment)**: (Revenue - Spend) / Spend
3. **CAC (Customer Acquisition Cost)**: Spend / New Customers
4. **LTV (Lifetime Value)**: Revenue / Total Customers
5. **LTV:CAC Ratio**: LTV / CAC
6. **CTR (Click-Through Rate)**: Clicks / Impressions
7. **Conversion Rate**: Conversions / Clicks
8. **CPA (Cost Per Acquisition)**: Spend / Conversions

### Cash Flow Metrics:
1. **Net Cash Flow**: Revenue - Spend
2. **Cumulative Cash Flow**: Running total of net cash flow
3. **Cash Flow by Channel**: Breakdown by marketing channel
4. **Monthly Trends**: Time-based cash flow analysis

This comprehensive set of examples provides production-ready code for implementing marketing automation dashboards across multiple BI platforms, enabling effective cash-flow visualization and marketing performance tracking.