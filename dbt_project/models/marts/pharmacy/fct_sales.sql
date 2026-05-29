with sales as (
    select * from {{ ref('stg_raw__sales') }}
),

details_agg as (
    select
        sale_id,
        count(*)                    as nb_products_in_cart,
        sum(quantity)               as total_units_sold
    from {{ ref('stg_raw__sale_details') }}
    group by sale_id
)

select
    s.sale_id,
    s.pharmacy_id,
    s.client_id,
    s.sale_date,
    s.sale_date_day,
    extract(year  from s.sale_date)::int    as sale_year,
    extract(month from s.sale_date)::int    as sale_month,
    extract(dow   from s.sale_date)::int    as sale_dow,
    s.payment_method,
    s.client_type,
    s.insurer_id,
    s.total_amount_fcfa,
    s.patient_share_fcfa,
    s.insurer_share_fcfa,
    s.vat_amount_fcfa,
    s.is_anonymous,
    coalesce(d.nb_products_in_cart, 0)      as nb_products_in_cart,
    coalesce(d.total_units_sold, 0)         as total_units_sold
from sales s
left join details_agg d using (sale_id)
