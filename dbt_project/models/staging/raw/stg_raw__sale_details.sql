with source as (
    select * from {{ source('raw', 'sale_details') }}
),

renamed as (
    select
        detail_id,
        sale_id,
        product_id,
        quantity,
        unit_price_fcfa,
        total_line_amount_fcfa
    from source
)

select * from renamed
