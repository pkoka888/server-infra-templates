# Cash-Flow Visualization Templates & Patterns

## Overview
Comprehensive templates and patterns for visualizing business cash-flow with marketing data integration. These templates work across multiple BI platforms and provide actionable insights for financial decision-making.

## 1. SQL Templates for Cash-Flow Analysis

### Basic Cash-Flow Query
```sql
-- Monthly cash flow by channel
SELECT 
  DATE_TRUNC('month', date) AS month,
  channel,
  SUM(revenue) AS revenue,
  SUM(spend) AS spend,
  SUM(revenue) - SUM(spend) AS net_cash_flow,
  SUM(revenue) / NULLIF(SUM(spend), 0) AS roi
FROM marketing_performance
WHERE date >= '2024-01-01'
GROUP BY 1, 2
ORDER BY 1, 2;
```

### Cumulative Cash-Flow Analysis
```sql
-- Cumulative cash flow with running totals
WITH monthly_cash_flow AS (
  SELECT 
    DATE_TRUNC('month', date) AS month,
    channel,
    SUM(revenue) AS revenue,
    SUM(spend) AS spend,
    SUM(revenue) - SUM(spend) AS net_cash_flow
  FROM marketing_performance
  GROUP BY 1, 2
)

SELECT 
  month,
  channel,
  revenue,
  spend,
  net_cash_flow,
  SUM(net_cash_flow) OVER (
    PARTITION BY channel 
    ORDER BY month 
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_cash_flow
FROM monthly_cash_flow
ORDER BY channel, month;
```

### Cash-Flow Forecast Query
```sql
-- 6-month cash flow forecast
WITH historical_data AS (
  SELECT 
    DATE_TRUNC('month', date) AS month,
    channel,
    AVG(revenue) AS avg_revenue,
    AVG(spend) AS avg_spend,
    AVG(revenue - spend) AS avg_net_cash_flow
  FROM marketing_performance
  WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
  GROUP BY 1, 2
),

forecast_periods AS (
  SELECT 
    DATE_ADD(
      DATE_TRUNC('month', CURRENT_DATE()), 
      INTERVAL n MONTH
    ) AS forecast_month,
    n
  FROM UNNEST(GENERATE_ARRAY(0, 5)) AS n
)

SELECT 
  f.forecast_month,
  h.channel,
  h.avg_revenue AS projected_revenue,
  h.avg_spend AS projected_spend,
  h.avg_net_cash_flow AS projected_net_cash_flow
FROM forecast_periods f
CROSS JOIN (
  SELECT DISTINCT channel, avg_revenue, avg_spend, avg_net_cash_flow
  FROM historical_data
  WHERE month = DATE_TRUNC('month', CURRENT_DATE())
) h
ORDER BY f.forecast_month, h.channel;
```

## 2. Metabase Dashboard Templates

### Cash-Flow Dashboard Configuration
```yaml
# metabase-cash-flow-dashboard.yaml
name: "Business Cash-Flow Dashboard"
description: "Comprehensive view of cash flow from marketing activities"

cards:
  - name: "Monthly Cash Flow Trend"
    type: "line"
    query: |
      SELECT 
        DATE_TRUNC('month', date) AS month,
        SUM(revenue) AS revenue,
        SUM(spend) AS spend,
        SUM(revenue) - SUM(spend) AS net_cash_flow
      FROM marketing_performance
      GROUP BY 1
      ORDER BY 1
    
  - name: "Cumulative Cash Flow by Channel"
    type: "area"
    query: |
      WITH monthly_data AS (
        SELECT 
          DATE_TRUNC('month', date) AS month,
          channel,
          SUM(revenue) - SUM(spend) AS net_cash_flow
        FROM marketing_performance
        GROUP BY 1, 2
      )
      
      SELECT 
        month,
        channel,
        net_cash_flow,
        SUM(net_cash_flow) OVER (
          PARTITION BY channel 
          ORDER BY month
        ) AS cumulative_cash_flow
      FROM monthly_data
      ORDER BY channel, month
    
  - name: "ROI vs Cash Flow"
    type: "scatter"
    query: |
      SELECT 
        channel,
        SUM(revenue) / SUM(spend) AS roi,
        SUM(revenue) - SUM(spend) AS total_cash_flow,
        COUNT(DISTINCT campaign_id) AS campaigns
      FROM marketing_performance
      GROUP BY 1
      HAVING SUM(spend) > 0
```

### Embedded Cash-Flow Dashboard
```javascript
// React component for cash-flow dashboard
import { useState, useEffect } from 'react';

const CashFlowDashboard = ({ startDate, endDate }) => {
  const [dashboardConfig, setDashboardConfig] = useState(null);

  useEffect(() => {
    const loadDashboard = async () => {
      const response = await fetch(`/api/metabase/cash-flow-dashboard`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date_range: {
            start: startDate,
            end: endDate
          },
          channels: ['google_ads', 'facebook_ads', 'organic']
        })
      });
      
      const config = await response.json();
      setDashboardConfig(config);
    };

    loadDashboard();
  }, [startDate, endDate]);

  return (
    <div className="cash-flow-dashboard">
      {dashboardConfig && (
        <iframe
          src={dashboardConfig.embed_url}
          style={{ width: '100%', height: '600px', border: 'none' }}
          title="Cash Flow Dashboard"
        />
      )}
    </div>
  );
};

export default CashFlowDashboard;
```

## 3. Evidence SQL+Markdown Templates

### Comprehensive Cash-Flow Report
```markdown
# Business Cash-Flow Analysis

## Executive Summary

**Total Net Cash Flow**: ${summary[0].total_net_cash_flow}  
**Total Revenue**: ${summary[0].total_revenue}  
**Total Marketing Spend**: ${summary[0].total_spend}  
**Overall ROI**: {summary[0].overall_roi}

```sql summary
SELECT 
  SUM(revenue) - SUM(spend) AS total_net_cash_flow,
  SUM(revenue) AS total_revenue,
  SUM(spend) AS total_spend,
  SUM(revenue) / SUM(spend) AS overall_roi
FROM marketing_performance
WHERE date >= '2024-01-01'
```

## Monthly Cash Flow Trends

<LineChart 
  data={monthly_cash_flow} 
  x="month" 
  y="net_cash_flow" 
  title="Monthly Net Cash Flow"
  color="channel"
/>

```sql monthly_cash_flow
SELECT 
  DATE_TRUNC('month', date) AS month,
  channel,
  SUM(revenue) AS revenue,
  SUM(spend) AS spend,
  SUM(revenue) - SUM(spend) AS net_cash_flow
FROM marketing_performance
GROUP BY 1, 2
ORDER BY 1, 2
```

## Cumulative Cash Flow by Channel

<AreaChart
  data={cumulative_cash_flow}
  x="month"
  y="cumulative_cash_flow"
  color="channel"
  title="Cumulative Cash Flow by Channel"
  stacked=true
/>

```sql cumulative_cash_flow
WITH monthly_data AS (
  SELECT 
    DATE_TRUNC('month', date) AS month,
    channel,
    SUM(revenue) - SUM(spend) AS net_cash_flow
  FROM marketing_performance
  GROUP BY 1, 2
)

SELECT 
  month,
  channel,
  net_cash_flow,
  SUM(net_cash_flow) OVER (
    PARTITION BY channel 
    ORDER BY month
  ) AS cumulative_cash_flow
FROM monthly_data
ORDER BY channel, month
```

## ROI vs Cash Flow Analysis

<ScatterChart
  data={roi_vs_cash_flow}
  x="roi"
  y="total_cash_flow"
  size="total_spend"
  color="channel"
  title="ROI vs Total Cash Flow"
  xTitle="Return on Investment (ROI)"
  yTitle="Total Cash Flow"
/>

```sql roi_vs_cash_flow
SELECT 
  channel,
  SUM(revenue) / SUM(spend) AS roi,
  SUM(revenue) - SUM(spend) AS total_cash_flow,
  SUM(spend) AS total_spend,
  COUNT(DISTINCT campaign_id) AS campaigns
FROM marketing_performance
GROUP BY 1
HAVING SUM(spend) > 0
```

## Cash Flow Forecast

<LineChart
  data={cash_flow_forecast}
  x="forecast_month"
  y="projected_net_cash_flow"
  color="channel"
  title="6-Month Cash Flow Forecast"
  dashed={true}
/>

```sql cash_flow_forecast
WITH historical_avg AS (
  SELECT 
    channel,
    AVG(revenue) AS avg_revenue,
    AVG(spend) AS avg_spend,
    AVG(revenue - spend) AS avg_net_cash_flow
  FROM marketing_performance
  WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
  GROUP BY 1
),

forecast_months AS (
  SELECT 
    DATE_ADD(DATE_TRUNC('month', CURRENT_DATE()), INTERVAL n MONTH) AS forecast_month,
    n
  FROM UNNEST(GENERATE_ARRAY(0, 5)) AS n
)

SELECT 
  f.forecast_month,
  h.channel,
  h.avg_net_cash_flow AS projected_net_cash_flow,
  h.avg_revenue AS projected_revenue,
  h.avg_spend AS projected_spend
FROM forecast_months f
CROSS JOIN historical_avg h
ORDER BY f.forecast_month, h.channel
```

## 4. Python Visualization Templates

### Plotly Cash-Flow Dashboard
```python
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_cash_flow_dashboard(df):
    """Create comprehensive cash-flow visualization dashboard"""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Monthly Cash Flow Trend",
            "Cumulative Cash Flow by Channel", 
            "ROI vs Cash Flow Analysis",
            "Cash Flow Forecast"
        ),
        specs=[[{"secondary_y": True}, {}], [{}, {}]]
    )
    
    # Monthly cash flow trend
    monthly_data = df.groupby(['month', 'channel']).agg({
        'net_cash_flow': 'sum'
    }).reset_index()
    
    for channel in monthly_data['channel'].unique():
        channel_data = monthly_data[monthly_data['channel'] == channel]
        fig.add_trace(
            go.Scatter(
                x=channel_data['month'],
                y=channel_data['net_cash_flow'],
                name=f"{channel} Cash Flow",
                mode='lines+markers'
            ),
            row=1, col=1
        )
    
    # Cumulative cash flow
    cumulative_data = df.copy()
    cumulative_data['cumulative_cash_flow'] = cumulative_data.groupby('channel')['net_cash_flow'].cumsum()
    
    for channel in cumulative_data['channel'].unique():
        channel_data = cumulative_data[cumulative_data['channel'] == channel]
        fig.add_trace(
            go.Scatter(
                x=channel_data['month'],
                y=channel_data['cumulative_cash_flow'],
                name=f"{channel} Cumulative",
                fill='tozeroy',
                mode='lines'
            ),
            row=1, col=2
        )
    
    # ROI vs Cash Flow scatter
    roi_data = df.groupby('channel').agg({
        'roi': 'mean',
        'net_cash_flow': 'sum',
        'spend': 'sum'
    }).reset_index()
    
    fig.add_trace(
        go.Scatter(
            x=roi_data['roi'],
            y=roi_data['net_cash_flow'],
            mode='markers',
            marker=dict(
                size=roi_data['spend'] / 1000,  # Scale by spend
                color=roi_data['roi'],
                colorscale="Viridis",
                showscale=True
            ),
            text=roi_data['channel'],
            name="ROI vs Cash Flow"
        ),
        row=2, col=1
    )
    
    # Forecast
    forecast_data = df[df['is_forecast'] == True]
    for channel in forecast_data['channel'].unique():
        channel_data = forecast_data[forecast_data['channel'] == channel]
        fig.add_trace(
            go.Scatter(
                x=channel_data['month'],
                y=channel_data['net_cash_flow'],
                name=f"{channel} Forecast",
                mode='lines',
                line=dict(dash='dash')
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        title="Comprehensive Cash-Flow Analysis Dashboard",
        height=800,
        showlegend=True
    )
    
    return fig

# Example usage
df = pd.read_sql("""
    SELECT 
        DATE_TRUNC('month', date) AS month,
        channel,
        SUM(revenue) AS revenue,
        SUM(spend) AS spend,
        SUM(revenue) - SUM(spend) AS net_cash_flow,
        SUM(revenue) / NULLIF(SUM(spend), 0) AS roi,
        FALSE AS is_forecast
    FROM marketing_performance
    GROUP BY 1, 2
""", connection)

fig = create_cash_flow_dashboard(df)
fig.show()
```

### Streamlit Cash-Flow App
```python
# streamlit_cash_flow_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.title("Business Cash-Flow Analysis Dashboard")

# Date range selector
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime(2024, 1, 1))
with col2:
    end_date = st.date_input("End Date", datetime.today())

# Load data
@st.cache_data
def load_cash_flow_data(start_date, end_date):
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
    return pd.read_sql(query, connection)

df = load_cash_flow_data(start_date, end_date)

# Summary metrics
total_revenue = df['revenue'].sum()
total_spend = df['spend'].sum()
total_net_cash_flow = df['net_cash_flow'].sum()
overall_roi = total_revenue / total_spend if total_spend > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.0f}")
col2.metric("Total Spend", f"${total_spend:,.0f}")
col3.metric("Net Cash Flow", f"${total_net_cash_flow:,.0f}")
col4.metric("Overall ROI", f"{overall_roi:.2f}")

# Visualizations
tab1, tab2, tab3 = st.tabs(["Trends", "Channel Analysis", "Forecast"])

with tab1:
    st.header("Monthly Cash Flow Trends")
    
    fig = px.line(
        df, 
        x='month', 
        y='net_cash_flow', 
        color='channel',
        title="Monthly Net Cash Flow by Channel"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Cumulative cash flow
    cumulative_df = df.copy()
    cumulative_df['cumulative'] = cumulative_df.groupby('channel')['net_cash_flow'].cumsum()
    
    fig2 = px.area(
        cumulative_df,
        x='month',
        y='cumulative',
        color='channel',
        title="Cumulative Cash Flow by Channel"
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.header("Channel Performance Analysis")
    
    channel_summary = df.groupby('channel').agg({
        'revenue': 'sum',
        'spend': 'sum',
        'net_cash_flow': 'sum',
        'roi': 'mean'
    }).reset_index()
    
    fig3 = px.scatter(
        channel_summary,
        x='roi',
        y='net_cash_flow',
        size='spend',
        color='channel',
        hover_data=['revenue', 'spend'],
        title="ROI vs Cash Flow by Channel"
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.header("Cash Flow Forecast")
    
    # Simple forecast based on historical averages
    forecast_df = df.copy()
    forecast_df['forecast'] = forecast_df['net_cash_flow'] * 1.1  # 10% growth assumption
    
    fig4 = px.line(
        forecast_df,
        x='month',
        y='forecast',
        color='channel',
        title="6-Month Cash Flow Forecast",
        line_dash='channel'
    )
    st.plotly_chart(fig4, use_container_width=True)
```

## 5. Key Performance Indicators (KPIs)

### Essential Cash-Flow Metrics
```sql
-- Cash-Flow KPIs for executive reporting
SELECT 
  -- Basic metrics
  SUM(revenue) AS total_revenue,
  SUM(spend) AS total_spend,
  SUM(revenue) - SUM(spend) AS net_cash_flow,
  
  -- ROI metrics
  SUM(revenue) / NULLIF(SUM(spend), 0) AS overall_roi,
  (SUM(revenue) - SUM(spend)) / NULLIF(SUM(spend), 0) AS romi,
  
  -- Efficiency metrics
  SUM(spend) / COUNT(DISTINCT customer_id) AS cac,
  SUM(revenue) / COUNT(DISTINCT customer_id) AS ltv,
  
  -- Growth metrics
  COUNT(DISTINCT customer_id) AS total_customers,
  SUM(revenue) / NULLIF(
    LAG(SUM(revenue)) OVER (ORDER BY MIN(date)), 
    0
  ) AS revenue_growth
FROM marketing_performance
WHERE date >= '2024-01-01';
```

### Monthly KPI Tracking
```sql
-- Monthly KPI dashboard
SELECT 
  DATE_TRUNC('month', date) AS month,
  channel,
  
  -- Financial metrics
  SUM(revenue) AS revenue,
  SUM(spend) AS spend,
  SUM(revenue) - SUM(spend) AS net_cash_flow,
  SUM(revenue) / NULLIF(SUM(spend), 0) AS roi,
  
  -- Customer metrics
  COUNT(DISTINCT customer_id) AS customers,
  SUM(spend) / NULLIF(COUNT(DISTINCT customer_id), 0) AS cac,
  
  -- Efficiency metrics
  SUM(conversions) / NULLIF(SUM(spend), 0) AS conversion_efficiency,
  SUM(revenue) / NULLIF(SUM(spend), 0) AS revenue_efficiency
FROM marketing_performance
GROUP BY 1, 2
ORDER BY 1, 2;
```

## Usage Examples

### 1. Quick Cash-Flow Analysis
```bash
# Run SQL queries for quick analysis
psql -c "$(cat cash_flow_analysis.sql)"

# Generate Evidence report
evidence build

# Start Streamlit app
streamlit run streamlit_cash_flow_app.py
```

### 2. Automated Reporting
```python
# automated_cash_flow_reporting.py
from datetime import datetime, timedelta
import pandas as pd
from visualization_helper import create_cash_flow_dashboard

def generate_daily_cash_flow_report():
    """Generate daily cash-flow report"""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=90)  # Last 90 days
    
    # Load data
    df = load_cash_flow_data(start_date, end_date)
    
    # Create visualization
    fig = create_cash_flow_dashboard(df)
    
    # Save report
    fig.write_html(f"cash_flow_report_{end_date.strftime('%Y%m%d')}.html")
    
    # Generate summary metrics
    summary = df.agg({
        'revenue': 'sum',
        'spend': 'sum', 
        'net_cash_flow': 'sum'
    })
    
    return summary

# Run daily report
daily_summary = generate_daily_cash_flow_report()
print(f"Daily Cash Flow Summary: {daily_summary}")
```

These templates provide comprehensive patterns for cash-flow visualization across multiple BI platforms, enabling businesses to effectively track and analyze their financial performance from marketing activities.