with stg as (
    select * from {{ ref('stg_raw__products') }}
)

select
    product_id,
    cip_code,
    commercial_name,
    dci,
    therapeutic_class,
    form,
    dosage,
    laboratory,
    origin,
    is_generic,
    is_regulated,
    vat_rate,
    public_price_fcfa,
    product_category
from stg
