with stg as (
    select * from {{ ref('stg_raw__wholesaler_returns') }}
)

select
    return_id,
    pharmacy_id,
    wholesaler_name,
    return_date,
    product_id,
    batch_number,
    quantity_returned,
    credit_note_amount_fcfa,
    status
from stg
