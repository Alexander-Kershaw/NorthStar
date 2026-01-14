with users as (
    select
        user_id,
        cast(created_at as date) as signup_date,
        date_trunc('month', cast(created_at as date)) as cohort_month
    from {{ ref('dim_user') }}
),
usage as (
    select
        user_id,
        date_day
    from {{ ref('fct_usage_daily') }}
    where is_active = 1
),
joined as (
    select
        u.user_id,
        u.cohort_month,
        u.signup_date,
        usg.date_day,
        datediff('day', u.signup_date, usg.date_day) as day_n
    from users u
    left join usage usg
      on u.user_id = usg.user_id
)

select
    cohort_month,
    count(distinct user_id) as cohort_size,

    count(distinct case when day_n between 7 and 13 then user_id end) as retained_d7_users,
    count(distinct case when day_n between 30 and 36 then user_id end) as retained_d30_users,

    (count(distinct case when day_n between 7 and 13 then user_id end) * 1.0)
      / nullif(count(distinct user_id), 0) as retained_d7_rate,

    (count(distinct case when day_n between 30 and 36 then user_id end) * 1.0)
      / nullif(count(distinct user_id), 0) as retained_d30_rate

from joined
group by 1
order by 1
