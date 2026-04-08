# Business Metrics Definition Library

## Overview
Comprehensive library of standardized business metrics for marketing analytics, financial analysis, and performance tracking. This library enables AI agents to understand, calculate, and recommend appropriate metrics for various business scenarios.

## Marketing Performance Metrics

### Core ROI Metrics

#### 1. Return on Investment (ROI)
```sql
-- Basic ROI calculation
SUM(revenue) / NULLIF(SUM(spend), 0) AS roi

-- Example with formatting
ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 2) AS roi
```

**Description**: Measures the efficiency of marketing investments  
**Formula**: Revenue / Marketing Spend  
**Interpretation**: >1 = Profitable, <1 = Losing money  
**Best For**: Campaign evaluation, channel performance

#### 2. Return on Marketing Investment (ROMI)
```sql
-- ROMI calculation
(SUM(revenue) - SUM(spend)) / NULLIF(SUM(spend), 0) AS romi

-- Percentage format  
ROUND(((SUM(revenue) - SUM(spend)) / NULLIF(SUM(spend), 0)) * 100, 1) AS romi_percent
```

**Description**: Measures net return from marketing activities  
**Formula**: (Revenue - Marketing Spend) / Marketing Spend  
**Interpretation**: >0 = Positive return, <0 = Negative return  
**Best For**: Overall marketing effectiveness

#### 3. Marketing Efficiency Ratio (MER)
```sql
-- MER calculation  
SUM(revenue) / NULLIF(SUM(spend), 0) AS mer
```

**Description**: Revenue generated per dollar spent  
**Formula**: Revenue / Marketing Spend  
**Interpretation**: Higher values indicate better efficiency  
**Best For**: Budget allocation decisions

### Customer Acquisition Metrics

#### 4. Customer Acquisition Cost (CAC)
```sql
-- Basic CAC calculation
SUM(spend) / NULLIF(COUNT(DISTINCT customer_id), 0) AS cac

-- CAC by channel
SUM(spend) / NULLIF(COUNT(DISTINCT customer_id), 0) AS cac,
channel
```

**Description**: Cost to acquire a new customer  
**Formula**: Total Marketing Spend / New Customers Acquired  
**Interpretation**: Lower values indicate more efficient acquisition  
**Best For**: Channel efficiency analysis

#### 5. Lifetime Value (LTV)
```sql
-- LTV calculation
SUM(revenue) / NULLIF(COUNT(DISTINCT customer_id), 0) AS ltv

-- LTV with time period
SUM(revenue) / NULLIF(COUNT(DISTINCT customer_id), 0) AS ltv,
DATE_TRUNC('month', date) AS month
```

**Description**: Average revenue per customer over their lifetime  
**Formula**: Total Revenue / Total Customers  
**Interpretation**: Higher values indicate more valuable customers  
**Best For**: Customer value analysis

#### 6. LTV to CAC Ratio
```sql
-- LTV:CAC ratio
(SUM(revenue) / NULLIF(COUNT(DISTINCT customer_id), 0)) / 
NULLIF(SUM(spend) / NULLIF(COUNT(DISTINCT customer_id), 0), 0) AS ltv_cac_ratio
```

**Description**: Compares customer value to acquisition cost  
**Formula**: LTV / CAC  
**Interpretation**: >3 = Excellent, 1-3 = Good, <1 = Problematic  
**Best For**: Business sustainability analysis

### Conversion Metrics

#### 7. Conversion Rate
```sql
-- Conversion rate calculation
SUM(conversions) / NULLIF(SUM(clicks), 0) AS conversion_rate

-- Percentage format
ROUND((SUM(conversions) / NULLIF(SUM(clicks), 0)) * 100, 2) AS conversion_rate_percent
```

**Description**: Percentage of clicks that result in conversions  
**Formula**: Conversions / Clicks  
**Interpretation**: Higher values indicate better targeting  
**Best For**: Campaign optimization

#### 8. Cost Per Acquisition (CPA)
```sql
-- CPA calculation
SUM(spend) / NULLIF(SUM(conversions), 0) AS cpa
```

**Description**: Cost to generate one conversion  
**Formula**: Marketing Spend / Conversions  
**Interpretation**: Lower values indicate more efficient conversions  
**Best For**: Conversion efficiency analysis

#### 9. Click-Through Rate (CTR)
```sql
-- CTR calculation
SUM(clicks) / NULLIF(SUM(impressions), 0) AS ctr

-- Percentage format  
ROUND((SUM(clicks) / NULLIF(SUM(impressions), 0)) * 100, 2) AS ctr_percent
```

**Description**: Percentage of impressions that result in clicks  
**Formula**: Clicks / Impressions  
**Interpretation**: Higher values indicate more engaging ads  
**Best For**: Ad performance analysis

## Financial Metrics

### Revenue Metrics

#### 10. Monthly Recurring Revenue (MRR)
```sql
-- MRR calculation
SUM(recurring_revenue) AS mrr,
DATE_TRUNC('month', date) AS month
```

**Description**: Predictable monthly revenue from subscriptions  
**Formula**: Sum of all active subscription revenues  
**Interpretation**: Growing MRR indicates business health  
**Best For**: SaaS businesses, subscription models

#### 11. Annual Recurring Revenue (ARR)
```sql
-- ARR calculation  
SUM(recurring_revenue) * 12 AS arr,
DATE_TRUNC('month', date) AS month
```

**Description**: Annualized version of MRR  
**Formula**: MRR × 12  
**Interpretation**: Key metric for SaaS valuation  
**Best For**: Annual planning, investor reporting

#### 12. Average Revenue Per User (ARPU)
```sql
-- ARPU calculation
SUM(revenue) / NULLIF(COUNT(DISTINCT user_id), 0) AS arpu,
DATE_TRUNC('month', date) AS month
```

**Description**: Average revenue generated per user  
**Formula**: Total Revenue / Active Users  
**Interpretation**: Increasing ARPU indicates better monetization  
**Best For**: User monetization analysis

### Profitability Metrics

#### 13. Gross Profit Margin
```sql
-- Gross margin calculation
(SUM(revenue) - SUM(cost_of_goods_sold)) / NULLIF(SUM(revenue), 0) AS gross_margin

-- Percentage format
ROUND(((SUM(revenue) - SUM(cost_of_goods_sold)) / NULLIF(SUM(revenue), 0)) * 100, 1) AS gross_margin_percent
```

**Description**: Profitability after accounting for direct costs  
**Formula**: (Revenue - COGS) / Revenue  
**Interpretation**: Higher values indicate better profitability  
**Best For**: Product profitability analysis

#### 14. Net Profit Margin
```sql
-- Net margin calculation
(SUM(revenue) - SUM(total_costs)) / NULLIF(SUM(revenue), 0) AS net_margin

-- Percentage format
ROUND(((SUM(revenue) - SUM(total_costs)) / NULLIF(SUM(revenue), 0)) * 100, 1) AS net_margin_percent
```

**Description**: Overall profitability after all expenses  
**Formula**: (Revenue - Total Costs) / Revenue  
**Interpretation**: Measures overall business efficiency  
**Best For**: Company-wide profitability analysis

#### 15. Contribution Margin
```sql
-- Contribution margin calculation
(SUM(revenue) - SUM(variable_costs)) / NULLIF(SUM(revenue), 0) AS contribution_margin
```

**Description**: Profitability per unit after variable costs  
**Formula**: (Revenue - Variable Costs) / Revenue  
**Interpretation**: Helps with pricing and scaling decisions  
**Best For**: Unit economics analysis

## Cash Flow Metrics

### 16. Net Cash Flow
```sql
-- Net cash flow calculation
SUM(revenue) - SUM(spend) AS net_cash_flow,
DATE_TRUNC('month', date) AS month
```

**Description**: Difference between revenue and expenses  
**Formula**: Revenue - Expenses  
**Interpretation**: Positive = Cash generation, Negative = Cash burn  
**Best For**: Financial health monitoring

### 17. Cumulative Cash Flow
```sql
-- Cumulative cash flow calculation
SUM(SUM(revenue) - SUM(spend)) OVER (
  ORDER BY DATE_TRUNC('month', date)
) AS cumulative_cash_flow,
DATE_TRUNC('month', date) AS month
```

**Description**: Running total of net cash flow over time  
**Formula**: Sum of monthly net cash flows  
**Interpretation**: Shows overall cash position trend  
**Best For**: Long-term financial planning

### 18. Cash Flow Forecast
```sql
-- 6-month cash flow forecast
WITH historical_avg AS (
  SELECT 
    AVG(revenue) AS avg_revenue,
    AVG(spend) AS avg_spend,
    AVG(revenue - spend) AS avg_net_cash_flow
  FROM financial_data
  WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
)

SELECT 
  DATE_ADD(DATE_TRUNC('month', CURRENT_DATE()), INTERVAL n MONTH) AS forecast_month,
  avg_net_cash_flow AS projected_cash_flow
FROM UNNEST(GENERATE_ARRAY(0, 5)) AS n
CROSS JOIN historical_avg
```

**Description**: Projected future cash flow based on historical averages  
**Formula**: Historical average net cash flow × time period  
**Interpretation**: Helps with liquidity planning  
**Best For**: Budgeting and financial forecasting

## Customer Behavior Metrics

### 19. Customer Retention Rate
```sql
-- Retention rate calculation
COUNT(DISTINCT retained_customers) / NULLIF(COUNT(DISTINCT total_customers), 0) AS retention_rate

-- Monthly retention
COUNT(DISTINCT 
  CASE WHEN status = 'active' THEN customer_id END
) / NULLIF(COUNT(DISTINCT customer_id), 0) AS monthly_retention_rate
```

**Description**: Percentage of customers who continue doing business  
**Formula**: Retained Customers / Total Customers  
**Interpretation**: Higher values indicate better customer satisfaction  
**Best For**: Customer success measurement

### 20. Churn Rate
```sql
-- Churn rate calculation
COUNT(DISTINCT churned_customers) / NULLIF(COUNT(DISTINCT total_customers), 0) AS churn_rate

-- Monthly churn
COUNT(DISTINCT 
  CASE WHEN status = 'churned' THEN customer_id END
) / NULLIF(COUNT(DISTINCT customer_id), 0) AS monthly_churn_rate
```

**Description**: Percentage of customers who stop doing business  
**Formula**: Churned Customers / Total Customers  
**Interpretation**: Lower values indicate better retention  
**Best For**: Customer retention analysis

### 21. Customer Lifetime Duration
```sql
-- Average customer lifetime
AVG(DATEDIFF('day', first_purchase_date, last_purchase_date)) AS avg_customer_lifetime_days
```

**Description**: Average duration of customer relationship  
**Formula**: Average(Last Purchase Date - First Purchase Date)  
**Interpretation**: Longer durations indicate better retention  
**Best For**: Customer value analysis

## Marketing Channel Metrics

### 22. Channel Efficiency Score
```sql
-- Channel efficiency calculation
(SUM(revenue) / NULLIF(SUM(spend), 0)) * 
(SUM(conversions) / NULLIF(SUM(clicks), 0)) AS channel_efficiency_score,
channel
```

**Description**: Combined metric of ROI and conversion efficiency  
**Formula**: ROI × Conversion Rate  
**Interpretation**: Higher scores indicate more efficient channels  
**Best For**: Channel optimization decisions

### 23. Marketing Share of Voice
```sql
-- Share of voice calculation
SUM(spend) / NULLIF(
  SUM(SUM(spend)) OVER (), 
  0
) AS share_of_voice,
channel
```

**Description**: Percentage of total budget allocated to each channel  
**Formula**: Channel Spend / Total Marketing Spend  
**Interpretation**: Helps with budget allocation analysis  
**Best For**: Marketing mix optimization

### 24. Channel Contribution Margin
```sql
-- Channel contribution calculation
(SUM(revenue) - SUM(spend)) AS channel_contribution,
channel
```

**Description**: Net contribution of each channel to overall profit  
**Formula**: Channel Revenue - Channel Spend  
**Interpretation**: Positive values indicate profitable channels  
**Best For**: Channel performance evaluation

## Implementation Templates

### dbt Metric Definitions
```yaml
# models/marketing/schema.yml
version: 2

models:
  - name: marketing_performance
    description: "Marketing performance metrics"
    
    metrics:
      - name: marketing_roi
        label: "Marketing ROI"
        description: "Return on investment for marketing campaigns"
        type: ratio
        numerator: revenue
        denominator: spend
        
      - name: customer_acquisition_cost
        label: "CAC"
        description: "Customer acquisition cost"
        type: average
        sql: "${spend} / ${new_customers}"
        
      - name: lifetime_value
        label: "LTV"
        description: "Customer lifetime value"
        type: average
        sql: "${revenue} / ${customers}"

    dimensions:
      - name: channel
        description: "Marketing channel"
        type: string
```

### Evidence Dashboard Metrics
```markdown
# Marketing Performance Dashboard

## Key Metrics
- **ROI**: {roi_metrics[0].roi}
- **CAC**: ${roi_metrics[0].cac}
- **LTV**: ${roi_metrics[0].ltv}
- **LTV:CAC**: {roi_metrics[0].ltv_cac_ratio}

```sql roi_metrics
SELECT 
  SUM(revenue) / SUM(spend) AS roi,
  SUM(spend) / COUNT(DISTINCT customer_id) AS cac,
  SUM(revenue) / COUNT(DISTINCT customer_id) AS ltv,
  (SUM(revenue) / COUNT(DISTINCT customer_id)) / 
  (SUM(spend) / COUNT(DISTINCT customer_id)) AS ltv_cac_ratio
FROM marketing_performance
WHERE date >= '2024-01-01'
```
```

### Metabase Question Template
```sql
-- Marketing ROI dashboard question
SELECT 
  DATE_TRUNC('month', date) AS month,
  channel,
  SUM(revenue) AS revenue,
  SUM(spend) AS spend,
  SUM(revenue) / NULLIF(SUM(spend), 0) AS roi,
  SUM(revenue) - SUM(spend) AS net_cash_flow
FROM marketing_performance
WHERE date >= '2024-01-01'
GROUP BY 1, 2
ORDER BY 1, 2
```

## Metric Selection Guide

### By Business Goal

| Goal | Recommended Metrics |
|------|---------------------|
| **Profitability** | ROI, ROMI, Net Margin, Contribution Margin |
| **Growth** | CAC, LTV, LTV:CAC Ratio, ARR, MRR |
| **Efficiency** | Conversion Rate, CPA, CTR, Channel Efficiency |
| **Retention** | Retention Rate, Churn Rate, Customer Lifetime |
| **Cash Flow** | Net Cash Flow, Cumulative Cash Flow, Forecast |

### By Business Type

| Business Type | Key Metrics |
|---------------|------------|
| **SaaS** | MRR, ARR, CAC, LTV, Churn Rate |
| **E-commerce** | ROI, Conversion Rate, AOV, CAC |
| **B2B** | CAC, LTV, Deal Size, Sales Cycle Length |
| **Subscription** | MRR, Churn Rate, Retention Rate, ARPU |
| **Agency** | ROI, Client Retention, Project Margin |

### By Marketing Channel

| Channel | Key Metrics |
|---------|------------|
| **Paid Search** | ROI, CTR, Conversion Rate, CPA |
| **Social Media** | Engagement Rate, CPC, Conversion Rate |
| **Email** | Open Rate, CTR, Conversion Rate, ROI |
| **Content** | Traffic, Engagement, Conversion Rate, ROI |
| **Affiliate** | Commission Rate, ROI, Conversion Rate |

## AI Agent Usage Patterns

### When users ask for:
- "marketing roi calculation" → Recommend ROI, ROMI formulas
- "customer acquisition cost" → Provide CAC formula and benchmarks  
- "lifetime value analysis" → Share LTV formula and interpretation
- "cash flow visualization" → Recommend net cash flow and cumulative formulas
- "channel performance" → Suggest channel-specific metrics

### Search Patterns:
- "[metric name] formula calculation"
- "[business type] key performance indicators"  
- "[industry] standard metrics benchmarks"
- "[tool name] metric implementation example"

This metric library provides AI agents with comprehensive knowledge of business metrics, enabling them to recommend appropriate measurements, provide calculation formulas, and suggest implementation patterns for various business scenarios.