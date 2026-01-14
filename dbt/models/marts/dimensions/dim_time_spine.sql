-- Daily time spine is required by dbt Semantic Layer / MetricFlow
-- MetricFlow warrants knowledge of all dates in the fact tables -> essentailly a cannonical calendar
-- One row per day

with bounds as (
    select
        least(
            (select min(date_day) from {{ ref('fct_mrr_daily') }}),
            (select min(date_day) from {{ ref('fct_usage_daily') }}),
            (select min(date_day) from {{ ref('fct_asset_uptime_daily') }})
        ) as min_day,
        greatest(
            (select max(date_day) from {{ ref('fct_mrr_daily') }}),
            (select max(date_day) from {{ ref('fct_usage_daily') }}),
            (select max(date_day) from {{ ref('fct_asset_uptime_daily') }})
        ) as max_day
)

select
    d::date as date_day
from bounds,
range(min_day, max_day + interval 1 day, interval 1 day) as t(d)
