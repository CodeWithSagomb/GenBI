with stg as (
    select * from {{ ref('stg_raw__pharmacies') }}
)

select
    pharmacy_id,
    pharmacy_name,
    country,
    city,
    district
from stg
