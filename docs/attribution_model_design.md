# Attribution Model Design Document

## Executive Summary

This document outlines the design for implementing multi-touch attribution modeling in the marketing analytics platform. Attribution modeling will enable accurate measurement of marketing channel contribution to conversions and revenue.

## Current State

The platform currently uses:
- **GA4**: Last non-direct click attribution
- **Facebook Ads**: Platform-native attribution
- **PrestaShop**: First-click UTM attribution

This creates fragmented attribution data that cannot be reconciled across channels.

## Attribution Model Options

### 1. First-Touch Attribution

**Description**: 100% credit to the first touchpoint in the customer journey.

**Pros**:
- Simple to implement
- Identifies top-of-funnel effectiveness
- Good for brand awareness measurement

**Cons**:
- Ignores all subsequent touchpoints
- Over-values awareness channels
- Not suitable for multi-touch journeys

**Use Case**: Brand awareness campaigns, new customer acquisition

**Implementation Complexity**: Low

---

### 2. Last-Touch Attribution

**Description**: 100% credit to the final touchpoint before conversion.

**Pros**:
- Simple to implement
- Identifies bottom-of-funnel effectiveness
- Standard in most analytics platforms

**Cons**:
- Ignores awareness and consideration touchpoints
- Over-values conversion channels
- Doesn't reflect modern buyer journeys

**Use Case**: Conversion-focused campaigns, e-commerce

**Implementation Complexity**: Low

---

### 3. Linear Attribution

**Description**: Equal credit distributed across all touchpoints.

**Pros**:
- Acknowledges all touchpoints
- Simple to understand
- Fair distribution

**Cons**:
- All touchpoints weighted equally
- Doesn't account for position importance
- Can dilute high-impact touchpoints

**Use Case**: Complex B2B sales cycles, long consideration periods

**Implementation Complexity**: Medium

---

### 4. Time-Decay Attribution

**Description**: Credit increases as touchpoints approach conversion.

**Formula**: Weight = e^(-λ × days_before_conversion)
where λ is the decay factor (default: 0.1)

**Pros**:
- Reflects recency importance
- Intuitive for e-commerce
- Configurable decay rate

**Cons**:
- Under-values early touchpoints
- Requires tuning of decay parameter

**Use Case**: Short sales cycles, e-commerce, promotional campaigns

**Implementation Complexity**: Medium

---

### 5. Position-Based (U-Shaped) Attribution

**Description**: 40% first touch, 40% last touch, 20% distributed among middle touches.

**Pros**:
- Balances first and last touch importance
- Acknowledges middle touchpoints
- Widely accepted in B2B

**Cons**:
- Arbitrary weight distribution
- May not fit all business models

**Use Case**: B2B marketing, consideration-heavy purchases

**Implementation Complexity**: Medium

---

### 6. Data-Driven Attribution

**Description**: Algorithmic attribution using machine learning.

**Approaches**:
- **Shapley Value**: Cooperative game theory
- **Markov Chains**: Removal effect analysis
- **Logistic Regression**: Conversion probability modeling

**Pros**:
- Most accurate representation
- Adapts to business patterns
- Handles complex journeys

**Cons**:
- Requires significant data volume
- Complex to implement and maintain
- "Black box" nature

**Use Case**: High-volume e-commerce, enterprise marketing

**Implementation Complexity**: High

## Model Comparison Matrix

| Model | Complexity | Data Required | Accuracy | Maintainability |
|-------|------------|---------------|----------|-----------------|
| First-Touch | Low | Low | Low | High |
| Last-Touch | Low | Low | Low | High |
| Linear | Medium | Medium | Medium | High |
| Time-Decay | Medium | Medium | Medium | Medium |
| Position-Based | Medium | Medium | Medium | High |
| Data-Driven | High | High | High | Low |

## Recommended Approach

### Phase 2A: Position-Based Attribution (Immediate)

**Rationale**:
- Balance of accuracy and complexity
- Industry standard for B2B
- Configurable for different business models
- Foundation for future ML models

**Implementation**:
```sql
-- First touch: 40%
-- Last touch: 40%
-- Middle touches: 20% / (count - 2)
```

### Phase 2B: Time-Decay Alternative

**Rationale**:
- Better for e-commerce use cases
- Complements position-based model

### Phase 2C: Data-Driven (Future)

**Rationale**:
- Ultimate accuracy
- Requires 6+ months of data
- ML infrastructure needed

## Data Model Extensions

### New Tables

```sql
-- Customer journey tracking
CREATE TABLE marts.fct_customer_journeys (
    journey_id UUID PRIMARY KEY,
    customer_id VARCHAR,
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    conversion_at TIMESTAMP,
    total_touchpoints INT,
    total_revenue DECIMAL,
    attribution_model VARCHAR
);

-- Touchpoint-level data
CREATE TABLE marts.fct_attribution_touchpoints (
    touchpoint_id UUID PRIMARY KEY,
    journey_id UUID REFERENCES marts.fct_customer_journeys,
    touchpoint_number INT,
    channel_grouping VARCHAR,
    source VARCHAR,
    medium VARCHAR,
    campaign VARCHAR,
    timestamp TIMESTAMP,
    time_to_conversion INTERVAL,
    first_touch_weight DECIMAL(5,4),
    last_touch_weight DECIMAL(5,4),
    linear_weight DECIMAL(5,4),
    time_decay_weight DECIMAL(5,4),
    position_based_weight DECIMAL(5,4)
);

-- Aggregated attribution results
CREATE TABLE marts.fct_attributed_revenue (
    date_day DATE,
    channel_grouping VARCHAR,
    source VARCHAR,
    medium VARCHAR,
    campaign VARCHAR,
    attribution_model VARCHAR,
    total_conversions INT,
    attributed_revenue DECIMAL(12,2),
    _loaded_at TIMESTAMP
);
```

### Modified Tables

```sql
-- Add attribution columns to fct_marketing_performance
ALTER TABLE marts.fct_marketing_performance ADD COLUMN
    attributed_revenue_position_based DECIMAL(12,2),
    attributed_revenue_time_decay DECIMAL(12,2),
    attributed_conversions_position_based INT,
    attributed_conversions_time_decay INT;
```

## Implementation Considerations

### Data Requirements

1. **User Identification**: Cross-device user stitching
2. **Session Stitching**: 30-day lookback window
3. **Touchpoint Collection**: All marketing interactions
4. **Conversion Events**: Order/purchase tracking
5. **Timestamps**: Accurate event timing

### Performance Impact

- **Storage**: +50% for journey tables
- **Compute**: +30% for attribution calculations
- **Latency**: +2 hours for daily attribution refresh

### Data Quality Requirements

- 95%+ user identification rate
- <5% missing timestamps
- <1% duplicate touchpoints

## Testing Strategy

### Unit Tests

```sql
-- Test first-touch attribution
SELECT assert_equals(
    1.0,
    first_touch_weight
) FROM marts.fct_attribution_touchpoints
WHERE touchpoint_number = 1;

-- Test position-based weights sum to 1
SELECT assert_equals(
    1.0,
    SUM(position_based_weight)
) FROM marts.fct_attribution_touchpoints
GROUP BY journey_id;
```

### Integration Tests

- End-to-end journey reconstruction
- Cross-channel attribution validation
- Revenue reconciliation with source systems

### Validation Metrics

- Attribution total equals actual revenue (±2%)
- Journey completion rate >90%
- Average touchpoints per journey matches expected

## Rollback Plan

1. **Schema Changes**: Versioned migrations with down scripts
2. **Data Pipeline**: Feature flag to disable attribution
3. **Dashboards**: Separate attribution dashboards (not replacing existing)
4. **Reporting**: Dual-run period with comparison validation

## References

1. Google Analytics Attribution Models
2. Facebook Attribution Window Documentation
3. IAB Attribution Best Practices
4. Marketing Attribution: Practical Guide (Think With Google)
