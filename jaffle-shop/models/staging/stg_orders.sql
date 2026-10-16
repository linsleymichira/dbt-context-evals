with source as (

    {#-
    Normally we would select from the table here, but we are using seeds to load
    our data in this project
    #}
    select * from {{ ref('raw_orders') }}

),

renamed as (

    select
        id as order_id,
        user_id as customer_id,
        order_date,
        -- Seeded for the eval: company-style status codes, so a model
        -- cannot answer status questions from memory of jaffle_shop.
        case status
            when 'placed' then '10'
            when 'shipped' then '20'
            when 'completed' then '30'
            when 'return_pending' then '40'
            when 'returned' then '50'
        end as status

    from source

)

select * from renamed
