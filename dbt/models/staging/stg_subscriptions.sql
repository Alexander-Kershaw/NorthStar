with src as (
    select *
    from read_parquet('../data/bronze/subscriptions.parquet')
)

select
    subscription_id,
    user_id,

    -- normalize plan_id casing
    lower(cast(plan_id as varchar)) as plan_id,

    -- cast dates (normalize to DATE type))
    cast(start_date as date) as start_date,
    cast(end_date as date) as end_date,

    -- billing metadata
    lower(cast(billing_period as varchar)) as billing_period,
    cast(price_gbp as integer) as price_gbp

from src
