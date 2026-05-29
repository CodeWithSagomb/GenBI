with source as (
    select * from {{ source('raw', 'clients') }}
),

renamed as (
    select
        client_id,
        first_name,
        last_name,
        first_name || ' ' || last_name                as full_name,
        phone_number,
        client_type,
        is_chronic,
        loyalty_points,
        created_at::timestamp                          as created_at
    from source
)

select * from renamed
