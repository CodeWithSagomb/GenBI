with source as (
    select * from {{ source('raw', 'pharmacies') }}
),

renamed as (
    select
        pharmacy_id,
        name                                           as pharmacy_name,
        country,
        city,
        district
    from source
)

select * from renamed
