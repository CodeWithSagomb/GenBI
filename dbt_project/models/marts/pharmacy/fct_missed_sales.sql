with stg as (
    select * from {{ ref('stg_raw__missed_sales') }}
)

select
    missed_sale_id,
    pharmacy_id,
    product_id,
    missed_date,
    missed_date_day,
    extract(year  from missed_date)::int    as missed_year,
    extract(month from missed_date)::int    as missed_month,
    requested_quantity,
    client_type
from stg
