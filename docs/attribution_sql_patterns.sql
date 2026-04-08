-- Attribution Model SQL Patterns
-- Run these in dbt as ephemeral models or macros

-- ============================================================
-- 1. FIRST-TOUCH ATTRIBUTION
-- Assigns 100% credit to the first touchpoint
-- ============================================================

with journey_touchpoints as (
    select
        customer_id,
        order_id,
        order_date,
        total_revenue,
        channel_grouping,
        source,
        medium,
        campaign,
        touchpoint_timestamp,
        row_number() over (
            partition by customer_id, order_id
            order by touchpoint_timestamp asc
        ) as touchpoint_number
    from {{ ref('int_customer_touchpoints') }}
),

first_touch as (
    select
        customer_id,
        order_id,
        order_date,
        total_revenue,
        channel_grouping as first_touch_channel,
        source as first_touch_source,
        medium as first_touch_medium,
        campaign as first_touch_campaign,
        1.0 as attribution_weight,
        total_revenue as attributed_revenue
    from journey_touchpoints
    where touchpoint_number = 1
)

select * from first_touch;


-- ============================================================
-- 2. LAST-TOUCH ATTRIBUTION
-- Assigns 100% credit to the last touchpoint before conversion
-- ============================================================

with journey_touchpoints as (
    select
        customer_id,
        order_id,
        order_date,
        total_revenue,
        channel_grouping,
        source,
        medium,
        campaign,
        touchpoint_timestamp,
        row_number() over (
            partition by customer_id, order_id
            order by touchpoint_timestamp desc
        ) as touchpoint_number_desc
    from {{ ref('int_customer_touchpoints') }}
),

last_touch as (
    select
        customer_id,
        order_id,
        order_date,
        total_revenue,
        channel_grouping as last_touch_channel,
        source as last_touch_source,
        medium as last_touch_medium,
        campaign as last_touch_campaign,
        1.0 as attribution_weight,
        total_revenue as attributed_revenue
    from journey_touchpoints
    where touchpoint_number_desc = 1
)

select * from last_touch;


-- ============================================================
-- 3. LINEAR ATTRIBUTION
-- Distributes credit equally across all touchpoints
-- ============================================================

with journey_touchpoints as (
    select
        customer_id,
        order_id,
        order_date,
        total_revenue,
        channel_grouping,
        source,
        medium,
        campaign,
        touchpoint_timestamp,
        count(*) over (partition by customer_id, order_id) as total_touchpoints
    from {{ ref('int_customer_touchpoints') }}
),

linear_attribution as (
    select
        customer_id,
        order_id,
        order_date,
        total_revenue,
        channel_grouping,
        source,
        medium,
        campaign,
        touchpoint_timestamp,
        total_touchpoints,
        1.0 / total_touchpoints as attribution_weight,
        total_revenue / total_touchpoints as attributed_revenue
    from journey_touchpoints
)

select * from linear_attribution;


-- ============================================================
-- 4. TIME-DECAY ATTRIBUTION
-- Credit increases as touchpoints approach conversion
-- Formula: weight = exp(-lambda * days_before_conversion)
-- ============================================================

with journey_touchpoints as (
    select
        customer_id,
        order_id,
        order_date,
        total_revenue,
        channel_grouping,
        source,
        medium,
        campaign,
        touchpoint_timestamp,
        -- Calculate days before conversion
        extract(epoch from (order_date - touchpoint_timestamp)) / 86400.0
            as days_before_conversion
    from {{ ref('int_customer_touchpoints') }}
),

decay_weights as (
    select
        *,
        -- Lambda = 0.1 means touchpoint loses ~10% value per day
        exp(-0.1 * days_before_conversion) as raw_weight
    from journey_touchpoints
),

normalized_weights as (
    select
        *,
        raw_weight / sum(raw_weight) over (partition by customer_id, order_id)
            as attribution_weight,
        total_revenue * raw_weight / sum(raw_weight) over (partition by customer_id, order_id)
            as attributed_revenue
    from decay_weights
)

select * from normalized_weights;


-- ============================================================
-- 5. POSITION-BASED (U-SHAPED) ATTRIBUTION
-- 40% first, 40% last, 20% distributed among middle touches
-- ============================================================

with journey_touchpoints as (
    select
        customer_id,
        order_id,
        order_date,
        total_revenue,
        channel_grouping,
        source,
        medium,
        campaign,
        touchpoint_timestamp,
        row_number() over (
            partition by customer_id, order_id
            order by touchpoint_timestamp asc
        ) as touchpoint_number,
        count(*) over (partition by customer_id, order_id) as total_touchpoints
    from {{ ref('int_customer_touchpoints') }}
),

position_weights as (
    select
        *,
        case
            -- Single touchpoint: 100%
            when total_touchpoints = 1 then 1.0
            -- Two touchpoints: 50% each
            when total_touchpoints = 2 then 0.5
            -- First touch: 40%
            when touchpoint_number = 1 then 0.4
            -- Last touch: 40%
            when touchpoint_number = total_touchpoints then 0.4
            -- Middle touches: 20% / (n-2)
            else 0.2 / (total_touchpoints - 2)
        end as attribution_weight,
        total_revenue * case
            when total_touchpoints = 1 then 1.0
            when total_touchpoints = 2 then 0.5
            when touchpoint_number = 1 then 0.4
            when touchpoint_number = total_touchpoints then 0.4
            else 0.2 / (total_touchpoints - 2)
        end as attributed_revenue
    from journey_touchpoints
)

select * from position_weights;


-- ============================================================
-- AGGREGATION: Channel-Level Attribution Summary
-- ============================================================

with all_attribution_models as (
    -- Combine all models using dbt model references
    select
        'first_touch' as model,
        first_touch_channel as channel,
        first_touch_source as source,
        first_touch_medium as medium,
        count(distinct order_id) as conversions,
        sum(attributed_revenue) as attributed_revenue
    from {{ ref('attribution_first_touch') }}
    group by 1, 2, 3, 4

    union all

    select
        'last_touch' as model,
        last_touch_channel as channel,
        last_touch_source as source,
        last_touch_medium as medium,
        count(distinct order_id) as conversions,
        sum(attributed_revenue) as attributed_revenue
    from {{ ref('attribution_last_touch') }}
    group by 1, 2, 3, 4

    union all

    select
        'linear' as model,
        channel_grouping as channel,
        source,
        medium,
        count(distinct order_id) as conversions,
        sum(attributed_revenue) as attributed_revenue
    from {{ ref('attribution_linear') }}
    group by 1, 2, 3, 4

    union all

    select
        'time_decay' as model,
        channel_grouping as channel,
        source,
        medium,
        count(distinct order_id) as conversions,
        sum(attributed_revenue) as attributed_revenue
    from {{ ref('attribution_time_decay') }}
    group by 1, 2, 3, 4

    union all

    select
        'position_based' as model,
        channel_grouping as channel,
        source,
        medium,
        count(distinct order_id) as conversions,
        sum(attributed_revenue) as attributed_revenue
    from {{ ref('attribution_position_based') }}
    group by 1, 2, 3, 4
)

select * from all_attribution_models;


-- ============================================================
-- VALIDATION: Attribution Totals Should Equal Actual Revenue
-- ============================================================

with validation as (
    select
        model,
        sum(attributed_revenue) as total_attributed,
        (select sum(total_revenue) from {{ ref('stg_prestashop__orders') }}) as actual_revenue,
        abs(sum(attributed_revenue) - (select sum(total_revenue) from {{ ref('stg_prestashop__orders') }}))
            / nullif((select sum(total_revenue) from {{ ref('stg_prestashop__orders') }}), 0) * 100
            as variance_percent
    from all_attribution_models
    group by model
)

select
    model,
    total_attributed,
    actual_revenue,
    variance_percent,
    case
        when variance_percent < 1 then 'PASS'
        else 'FAIL'
    end as validation_status
from validation;
