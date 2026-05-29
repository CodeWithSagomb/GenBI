with source as (
    select * from {{ source('raw', 'products') }}
),

renamed as (
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
        vat_rate::numeric(5,2)                        as vat_rate,
        public_price_fcfa,
        case when vat_rate > 0
             then 'Parapharmacie'
             else 'Médicament' end                    as product_category
    from source
)

select * from renamed
