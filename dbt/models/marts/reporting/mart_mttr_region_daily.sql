with incidents as (
    select
        cast(start_ts as date) as date_day,
        asset_id,
        duration_hours
    from {{ ref('fct_incidents') }}
),
assets as (
    select
        asset_id,
        region,
        asset_type
    from {{ ref('dim_asset') }}
),
incidents_enriched as (
    select
        i.date_day,
        a.region,
        a.asset_type,
        i.duration_hours,
        i.asset_id
    from incidents i
    join assets a
      on i.asset_id = a.asset_id
),
fleet as (
    select
        region,
        asset_type,
        count(*) as fleet_assets
    from {{ ref('dim_asset') }}
    group by 1, 2
)

select
    ie.date_day,
    ie.region,
    ie.asset_type,
    avg(ie.duration_hours) as mttr_hours,
    count(*) as incident_count,
    f.fleet_assets,
    (count(*) * 100.0) / nullif(f.fleet_assets, 0) as incidents_per_100_assets
from incidents_enriched ie
join fleet f
  on ie.region = f.region
 and ie.asset_type = f.asset_type
group by 1, 2, 3, 6
