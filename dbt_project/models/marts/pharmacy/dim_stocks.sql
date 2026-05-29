with stg as (
    select * from {{ ref('stg_raw__stocks') }}
),

products as (
    select product_id, commercial_name, therapeutic_class
    from {{ ref('stg_raw__products') }}
)

select
    s.stock_id,
    s.product_id,
    p.commercial_name,
    p.therapeutic_class,
    s.batch_number,
    s.expiration_date,
    s.quantity_in_stock,
    s.safety_stock_threshold,
    s.shelf_location,
    s.last_updated_at,
    s.days_until_expiry,
    s.expiry_status,
    s.is_below_safety_threshold
from stg s
left join products p using (product_id)
