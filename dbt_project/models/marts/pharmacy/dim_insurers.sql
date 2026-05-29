with stg as (
    select * from {{ ref('stg_raw__insurers') }}
)

select
    insurer_id,
    insurer_name,
    default_coverage_rate,
    coverage_pct
from stg
