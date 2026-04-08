with source as (
    select * from {{ source('facebook_raw', 'campaigns') }}
),

renamed as (
    select
        campaign_id,
        account_id,
        campaign_name,
        campaign_status,
        campaign_objective,
        created_at,
        start_time,
        stop_time,
        daily_budget,
        lifetime_budget,
        budget_remaining,
        _dlt_load_id,
        _dlt_id,
        _dlt_normalized_at,
        _airbyte_extracted_at as loaded_at
    from source
)

select * from renamed
