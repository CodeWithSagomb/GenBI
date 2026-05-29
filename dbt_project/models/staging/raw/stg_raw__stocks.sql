with source as (
    select * from {{ source('raw', 'stocks') }}
),

renamed as (
    select
        stock_id,
        product_id,
        batch_number,
        expiration_date,
        quantity_in_stock,
        safety_stock_threshold,
        shelf_location,
        last_updated_at::timestamp                        as last_updated_at,
        expiration_date - current_date                    as days_until_expiry,
        case
            when expiration_date < current_date
                then 'Expiré'
            when expiration_date < current_date + interval '30 days'
                then 'Critique (< 30j)'
            when expiration_date < current_date + interval '90 days'
                then 'Attention (< 90j)'
            else 'OK'
        end                                               as expiry_status,
        quantity_in_stock <= safety_stock_threshold       as is_below_safety_threshold
    from source
)

select * from renamed
