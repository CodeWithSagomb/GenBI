with stg as (
    select * from {{ ref('stg_raw__purchases') }}
)

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
    delivery_status,
    service_rate_pct,
    quantity_ordered * purchase_price_fcfa      as total_ordered_fcfa,
    quantity_received * purchase_price_fcfa     as total_received_fcfa
from stg
