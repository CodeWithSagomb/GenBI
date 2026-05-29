with source as (
    select * from {{ source('raw', 'purchases') }}
),

renamed as (
    select
        purchase_id,
        pharmacy_id,
        wholesaler_name,
        order_date,
        delivery_date,
        product_id,
        quantity_ordered,
        quantity_received,
        purchase_price_fcfa,
        batch_number,
        expiration_date,
        case
            when quantity_received = 0             then 'Rupture totale'
            when quantity_received < quantity_ordered then 'Livraison partielle'
            else 'Livraison complète'
        end                                              as delivery_status,
        round(
            quantity_received::numeric / nullif(quantity_ordered, 0) * 100
        )::int                                           as service_rate_pct
    from source
)

select * from renamed
