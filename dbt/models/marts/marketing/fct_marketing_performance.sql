with facebook_ads as (
    select
        date(created_at) as date,
        'Facebook Ads' as channel,
        campaign_id,
        impressions,
        clicks,
        spend as revenue,
        case when spend > 0 then purchase_value / spend else null end as roas,
        case when impressions > 0 then clicks::float / nullif(impressions, 0) * 100 else null end as ctr_percent,
        case when clicks > 0 then spend / nullif(clicks, 0) else null end as cpc
    from {{ ref('stg_facebook__ads') }}
    where ad_status = 'ACTIVE'
)

select
    date,
    channel,
    campaign_id,
    impressions,
    clicks,
    revenue,
    roas,
    ctr_percent,
    cpc,
    current_timestamp as computed_at
from facebook_ads
