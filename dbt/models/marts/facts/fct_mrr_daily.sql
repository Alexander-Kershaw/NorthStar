with subs as (
    select
        user_id,
        plan_id,
        billing_period,
        price_gbp,
        start_date,
        end_date
    from {{ ref('stg_subscriptions') }}
),
calendar as (
    select
        d::date as date_day
    from range(
        (select min(start_date) from subs),
        (select coalesce(max(end_date), current_date) from subs),
        interval 1 day
    ) as t(d)
),
active as (
    select
        c.date_day,
        s.user_id,
        s.plan_id,
        s.billing_period,
        s.price_gbp,
        case
            when s.billing_period = 'annual' then s.price_gbp / 12.0
            when s.billing_period = 'monthly' then s.price_gbp * 1.0
            else 0.0
        end as mrr_gbp
    from calendar c
    join subs s
      on s.start_date <= c.date_day
     and (s.end_date is null or c.date_day < s.end_date)
)

select
    date_day,
    sum(mrr_gbp) as mrr_gbp,
    count(distinct case when mrr_gbp > 0 then user_id end) as paying_users
from active
group by 1
order by 1


-- Note: This model is rather expensive to run 
-- due to the use of a date range and daily granularity (expanding subscriptions over time)
-- With local and smaller data volumes this is okay
-- but for larger production environments pre-aggregating is ideal