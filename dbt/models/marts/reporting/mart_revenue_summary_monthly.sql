with daily as (
    select
        date_day,
        mrr_gbp,
        paying_users,
        date_trunc('month', date_day) as month_start
    from {{ ref('fct_mrr_daily') }}
),
monthly as (
    select
        month_start,

        avg(mrr_gbp) as avg_mrr_gbp,
        max_by(mrr_gbp, date_day) as end_of_month_mrr_gbp,

        avg(paying_users) as avg_paying_users,
        max_by(paying_users, date_day) as end_of_month_paying_users

    from daily
    group by 1
)

select
    month_start,
    avg_mrr_gbp,
    end_of_month_mrr_gbp,
    avg_paying_users,
    end_of_month_paying_users
from monthly
order by month_start
