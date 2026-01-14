with hourly as (
    select
        asset_id,
        cast(ts as date) as date_day,
        is_up
    from {{ ref('fct_asset_uptime_hourly') }}
)

select
    asset_id,
    date_day,
    avg(is_up) as uptime_pct,
    sum(case when is_up = 0 then 1 else 0 end) as downtime_hours,
    count(*) as total_hours
from hourly
group by 1, 2
