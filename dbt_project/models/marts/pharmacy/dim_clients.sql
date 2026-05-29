with stg as (
    select * from {{ ref('stg_raw__clients') }}
)

select
    client_id,
    full_name,
    phone_number,
    client_type,
    is_chronic,
    loyalty_points,
    created_at
from stg
