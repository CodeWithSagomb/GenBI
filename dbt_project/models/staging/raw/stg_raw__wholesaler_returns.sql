with source as (
    select * from {{ source('raw', 'wholesaler_returns') }}
),

renamed as (
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
    from source
)

select * from renamed
