with source as (
    select * from {{ source('facebook_raw', 'ads') }}
),

renamed as (
    select
        ad_id,
        campaign_id,
        adset_id,
        account_id,
        created_at,
        updated_at,
        ad_name,
        ad_status,
        impressions,
        clicks,
        spend,
        reach,
        frequency,
        cpc,
        cpm,
        impressions_purchases,
        purchases_granular_search,
        cost_per_purchase,
        amount_spent,
        purchase_value,
        website_purchases,
        website_purchases_value,
        _dlt_load_id,
        _dlt_id,
        _dlt_normalized_at,
        _airbyte_extracted_at as loaded_at
    from source
)

select * from renamed
