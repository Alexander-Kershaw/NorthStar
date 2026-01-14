with daily as (
    select
        d.asset_id,
        d.date_day,
        d.uptime_pct,
        d.downtime_hours,
        d.total_hours,
        a.region,
        a.asset_type,
        a.capacity_kw
    from {{ ref('fct_asset_uptime_daily') }} d
    join {{ ref('dim_asset') }} a
      on d.asset_id = a.asset_id
),
ranked as (
    select
        *,
        row_number() over (
            partition by date_day
            order by uptime_pct asc, downtime_hours desc
        ) as rn
    from daily
)

select
    date_day,
    asset_id,
    region,
    asset_type,
    capacity_kw,
    uptime_pct,
    downtime_hours,
    total_hours
from ranked
where rn <= 10
order by date_day, rn
