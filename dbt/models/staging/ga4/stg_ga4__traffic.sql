{{ config(materialized="view", schema="staging", tags=["staging"]) }}

with source as (
    select * from {{ source('ga4_raw', 'traffic') }}
),

renamed as (
    select
        {{ dbt_utils.generate_surrogate_key(['date', 'source', 'medium', 'device_category']) }} as traffic_id,
        date,
        sessions,
        total_users,
        new_users,
        bounce_rate,
        average_session_duration,
        goal_completions_all,
        session_default_channel_group,
        source,
        medium,
        campaign,
        country,
        device_category,
        _dlt_load_id,
        _dlt_id,
        _airbyte_extracted_at as loaded_at
    from source
)

select * from renamed
