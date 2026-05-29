with source as (
    select * from {{ source('raw', 'insurers') }}
),

renamed as (
    select
        insurer_id,
        name                                           as insurer_name,
        default_coverage_rate,
        round(default_coverage_rate * 100)::int        as coverage_pct
    from source
)

select * from renamed
