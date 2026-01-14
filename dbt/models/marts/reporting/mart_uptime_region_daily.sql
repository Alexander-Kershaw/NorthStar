with daily as (
    select
        asset_id,
        date_day,
        uptime_pct,
        downtime_hours,
        total_hours
    from {{ ref('fct_asset_uptime_daily') }}
),
assets as (
    select
        asset_id,
        region,
        asset_type,
        capacity_kw
    from {{ ref('dim_asset') }}
)

select
    d.date_day,
    a.region,
    a.asset_type,

    -- averages across assets
    avg(d.uptime_pct) as avg_uptime_pct,

    -- totals downtime and total hours across assets
    sum(d.downtime_hours) as downtime_hours,
    sum(d.total_hours) as total_hours,
    count(distinct d.asset_id) as n_assets

from daily d
join assets a
  on d.asset_id = a.asset_id
group by 1, 2, 3
