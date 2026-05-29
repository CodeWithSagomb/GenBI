with source as (
    select * from {{ source('raw', 'missed_sales') }}
),

renamed as (
    select
        missed_sale_id,
        pharmacy_id,
        product_id,
        missed_date::timestamp                           as missed_date,
        missed_date::date                                as missed_date_day,
        requested_quantity,
        client_type
    from source
)

select * from renamed
