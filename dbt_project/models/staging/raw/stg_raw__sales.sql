with source as (
    select * from {{ source('raw', 'sales') }}
),

renamed as (
    select
        sale_id,
        pharmacy_id,
        client_id,
        sale_date::timestamp                          as sale_date,
        sale_date::date                               as sale_date_day,
        payment_method,
        client_type,
        insurer_id,
        total_amount_fcfa,
        patient_share_fcfa,
        insurer_share_fcfa,
        vat_amount_fcfa,
        case when client_id is null then true
             else false end                           as is_anonymous
    from source
)

select * from renamed
