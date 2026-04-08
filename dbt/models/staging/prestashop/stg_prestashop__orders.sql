with source as (
    select * from {{ source('prestashop_raw', 'orders') }}
),

renamed as (
    select
        id_order as order_id,
        id_customer as customer_id,
        id_cart as cart_id,
        reference as order_reference,
        total_paid as total_paid,
        total_products as total_products,
        total_shipping as total_shipping,
        date_add as created_at,
        date_upd as updated_at,
        current_state as status_id
    from source
)

select * from renamed
