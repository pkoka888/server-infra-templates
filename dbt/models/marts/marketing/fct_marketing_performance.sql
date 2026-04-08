{#
  Marketing Performance Fact Model
  Unions data from GA4, Facebook Ads, and PrestaShop
  Provides unified view of marketing performance across channels
#}

with

date_spine as (
    select generate_series(
        current_date - interval '2 years',
        current_date,
        interval '1 day'
    )::date as date_day
),

ga4_data as (
    select
        date as date_day,
        session_default_channel_group as channel_grouping,
        coalesce(source, 'direct') as source,
        coalesce(medium, 'none') as medium,
        'GA4' as data_source,
        coalesce(campaign, '(not set)') as campaign,
        sessions,
        0::bigint as conversions,
        0::numeric as revenue,
        0::numeric as cost,
        device_category,
        country,
        null::bigint as impressions,
        null::bigint as clicks,
        bounce_rate,
        average_session_duration,
        _dlt_load_id,
        loaded_at as _loaded_at
    from {{ ref('stg_ga4__traffic') }}
    where date >= current_date - interval '2 years'
),

fb_ads_data as (
    select
        created_at::date as date_day,
        'paid_social' as channel_grouping,
        'facebook' as source,
        'cpc' as medium,
        'Facebook Ads' as data_source,
        coalesce(ad_name, campaign_id::text) as campaign,
        0::bigint as sessions,
        website_purchases as conversions,
        coalesce(website_purchases_value, 0) as revenue,
        coalesce(spend, 0) as cost,
        null as device_category,
        null as country,
        impressions,
        clicks,
        null as bounce_rate,
        null as average_session_duration,
        _dlt_load_id,
        loaded_at as _loaded_at
    from {{ ref('stg_facebook__ads') }}
    where created_at >= current_date - interval '2 years'
),

prestashop_data as (
    select
        created_at::date as date_day,
        'ecommerce' as channel_grouping,
        'prestashop' as source,
        'direct' as medium,
        'PrestaShop' as data_source,
        'orders' as campaign,
        0::bigint as sessions,
        1::bigint as conversions,
        total_paid as revenue,
        0::numeric as cost,
        null as device_category,
        null as country,
        null::bigint as impressions,
        null::bigint as clicks,
        null as bounce_rate,
        null as average_session_duration,
        _dlt_load_id,
        created_at as _loaded_at
    from {{ ref('stg_prestashop__orders') }}
    where created_at >= current_date - interval '2 years'
),

unified as (
    select * from ga4_data
    union all
    select * from fb_ads_data
    union all
    select * from prestashop_data
),

aggregated as (
    select
        date_day,
        channel_grouping,
        source,
        medium,
        data_source,
        campaign,

        sum(sessions) as total_sessions,
        sum(impressions) as total_impressions,
        sum(clicks) as total_clicks,
        sum(conversions) as total_conversions,
        sum(revenue) as total_revenue,
        sum(cost) as total_cost,

        case
            when sum(cost) > 0 and sum(cost) > 0
            then sum(revenue) / nullif(sum(cost), 0)
            else null
        end as roas,

        case
            when sum(conversions) > 0
            then sum(cost) / nullif(sum(conversions), 0)
            else null
        end as cpa,

        case
            when sum(sessions) > 0
            then sum(conversions)::numeric / nullif(sum(sessions), 0) * 100
            else null
        end as conversion_rate,

        case
            when sum(impressions) > 0
            then sum(clicks)::numeric / nullif(sum(impressions), 0) * 100
            else null
        end as ctr,

        case
            when sum(clicks) > 0
            then sum(cost) / nullif(sum(clicks), 0)
            else null
        end as cpc,

        min(_loaded_at) as first_loaded_at,
        max(_loaded_at) as last_loaded_at,
        count(*) as source_row_count

    from unified
    group by 1, 2, 3, 4, 5, 6
)

select
    {{ dbt_utils.generate_surrogate_key(['date_day', 'source', 'medium', 'campaign']) }}
        as performance_sk,

    date_day,
    channel_grouping,
    source,
    medium,
    data_source,
    campaign,

    total_sessions,
    total_impressions,
    total_clicks,
    total_conversions,
    total_revenue,
    total_cost,

    round(roas, 2) as roas,
    round(cpa, 2) as cpa,
    round(conversion_rate, 2) as conversion_rate_pct,
    round(ctr, 2) as ctr_pct,
    round(cpc, 2) as cpc,

    first_loaded_at,
    last_loaded_at,
    source_row_count,

    current_timestamp as _dbt_loaded_at

from aggregated
